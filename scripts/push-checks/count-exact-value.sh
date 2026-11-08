#!/usr/bin/env bash
# Count one private value in a git range without printing it (Step 2's pre-push check).
#
#   scripts/push-checks/count-exact-value.sh <range> <value-file>
#   scripts/push-checks/count-exact-value.sh origin/rebuild..rebuild /path/outside/the/repo/value.txt
#
# <value-file> holds the value on one line, UTF-8 (for example the Argaam account name). Keep it outside the
# repository and delete it afterwards. The value is never printed and never passed on a command line.
#
# It reads git's raw objects, not formatted output, so nothing is escaped, quoted or summarised away:
#   commits <n>        occurrences in the raw commit objects of the range (messages, authors, committers)
#   file-contents <n>  occurrences in every file version in the full tree of every commit in the range, of each
#                      boundary commit (the range's start) and of the tip: binary files, files deleted again inside
#                      the range, and content the range deletes or changes from the base all included
#   file-names <n>     paths (files and folders) in those same trees that contain it, read with `ls-tree -z`, which
#                      never quotes non-ASCII names
# Every version a patch in the range shows, before or after a change, is in one of those trees: an older version
# is either at the boundary or inside the range. So anything already in the base also stops the push: the patch
# that deletes or edits it would show it again.
# Matching is byte-exact under LC_ALL=C, ignoring ASCII case only; file contents are searched with NUL bytes
# removed, so UTF-16 text is found for an ASCII value. It prints exactly those three lines: no matching text and
# no file name.
# It CANNOT see: text drawn in images (screenshots), text inside compressed files (zip, docx, PDF streams, PNG
# text chunks), encoded forms (URL %40, HTML entities, base64), or another Unicode normalisation (NFC/NFD) of a
# non-ASCII value. Screenshots need a person's eyes; run it once per variant if one is plausible.
# Exit 0: all three are 0. Exit 3: any is not (stop the push). Exit 2: bad input or a git error (stop).
set -u
export LC_ALL=C

fail() { echo "error: $1" >&2; exit 2; }

[ $# -eq 2 ] || fail "usage: count-exact-value.sh <range> <value-file>"
range=$1
vf=$2
[ -f "$vf" ] || fail "value file not found"
case "$range" in
  *...*) fail "use A..B, not A...B" ;;
  *..*) base=${range%%..*}; tip=${range##*..} ;;
  *) fail "range must look like A..B" ;;
esac
[ -n "$base" ] && [ -n "$tip" ] || fail "range needs both ends"

tmp=$(mktemp -d) || fail "mktemp failed"
trap 'rm -rf "$tmp"' EXIT

# One pattern, exactly: strip CR and surrounding spaces, refuse an empty value or more than one line,
# because an empty line in a grep -f file would match everything.
tr -d '\r' < "$vf" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' > "$tmp/pat"
lines=$(grep -c '' "$tmp/pat")
[ "$lines" -eq 1 ] || fail "value file must hold exactly one line"
[ -n "$(head -c 1 "$tmp/pat")" ] || fail "value is empty"
[ "$(tr -d '\n' < "$tmp/pat" | wc -c | tr -d ' ')" -ge 3 ] || fail "value is too short to search for"

git rev-parse --verify --quiet "$base^{commit}" > /dev/null || fail "range start is not a commit"
git rev-parse --verify --quiet "$tip^{commit}" > /dev/null || fail "range end is not a commit"

# count <file> <label>: occurrences of the value in <file>, read as bytes; sets COUNT. grep's own
# exit status is checked (0 found, 1 none, 2 error) without writing any match to disk.
count() {
  COUNT=$(grep -a -o -i -F -f "$tmp/pat" "$1" | wc -l; exit "${PIPESTATUS[0]}")
  local rc=$?
  [ $rc -le 1 ] || fail "grep failed on $2"
  COUNT=$(echo "$COUNT" | tr -d ' ')
}

# 1. the range's commits, raw
git rev-list "$range" > "$tmp/commits" || fail "git rev-list failed"
# the boundary: parents of range commits that are outside the range (rev-list marks them with "-")
git rev-list --boundary "$range" > "$tmp/with-boundary" || fail "git rev-list --boundary failed"
sed -n 's/^-//p' "$tmp/with-boundary" > "$tmp/boundary"
git cat-file --batch < "$tmp/commits" > "$tmp/commit-objects" || fail "git cat-file failed on commits"
count "$tmp/commit-objects" commits
c=$COUNT

# 2 and 3. the full tree of every commit in the range, of each boundary commit, and of the tip
{ cat "$tmp/commits" "$tmp/boundary"; git rev-parse "$tip^{commit}"; } | sort -u > "$tmp/snapshots"
: > "$tmp/blobs"
: > "$tmp/names"
while read -r sha; do
  git ls-tree -r "$sha" > "$tmp/tree" || fail "git ls-tree failed on a commit"
  awk '$2 == "blob" { print $3 }' "$tmp/tree" >> "$tmp/blobs"
  git ls-tree -r -t -z --name-only "$sha" >> "$tmp/names" || fail "git ls-tree -z failed on a commit"
done < "$tmp/snapshots"

sort -u "$tmp/blobs" -o "$tmp/blobs"
git cat-file --batch < "$tmp/blobs" > "$tmp/blob-data0" || fail "git cat-file failed on blobs"
# NUL bytes removed, so text saved as UTF-16 is found too (for an ASCII value); in UTF-8 text this changes nothing
tr -d '\000' < "$tmp/blob-data0" > "$tmp/blob-data" || fail "tr failed on blobs"
count "$tmp/blob-data" file-contents
f=$COUNT

tr '\000' '\n' < "$tmp/names" | sort -u > "$tmp/names.txt"
COUNT=$(grep -c -i -F -f "$tmp/pat" "$tmp/names.txt"; exit $?)
[ $? -le 1 ] || fail "grep failed on file names"
n=$COUNT

echo "commits $c"
echo "file-contents $f"
echo "file-names $n"
[ "$c" -eq 0 ] && [ "$f" -eq 0 ] && [ "$n" -eq 0 ] && exit 0
exit 3
