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
#   file-contents <n>  occurrences in every file version the range adds - including binary files and files deleted
#                      again inside the range (`git rev-list --objects <range>`) - plus every file in the tip
#   file-names <n>     paths (files and folders) in the full tree of every commit in the range that contain it,
#                      read with `ls-tree -z`, which never quotes non-ASCII names
# Matching is byte-exact under LC_ALL=C, ignoring ASCII case only. It prints exactly those three lines: no
# matching text and no file name.
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

# One pattern, exactly: strip a trailing CR, refuse an empty value or more than one line,
# because an empty line in a grep -f file would match everything.
tr -d '\r' < "$vf" > "$tmp/pat"
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
git cat-file --batch < "$tmp/commits" > "$tmp/commit-objects" || fail "git cat-file failed on commits"
count "$tmp/commit-objects" commits
c=$COUNT

# 2. every blob the range adds, plus every blob in the tip
git rev-list --objects --no-object-names "$range" > "$tmp/objects" || fail "git rev-list --objects failed"
git cat-file --batch-check='%(objecttype) %(objectname)' < "$tmp/objects" > "$tmp/types" \
  || fail "git cat-file failed on object types"
awk '$1 == "blob" { print $2 }' "$tmp/types" > "$tmp/blobs"
git ls-tree -r "$tip" > "$tmp/tip-tree" || fail "git ls-tree failed on the tip"
awk '$2 == "blob" { print $3 }' "$tmp/tip-tree" >> "$tmp/blobs"
sort -u "$tmp/blobs" -o "$tmp/blobs"
git cat-file --batch < "$tmp/blobs" > "$tmp/blob-data" || fail "git cat-file failed on blobs"
count "$tmp/blob-data" file-contents
f=$COUNT

# 3. every path in every commit of the range, raw and NUL-separated
: > "$tmp/names"
while read -r sha; do
  git ls-tree -r -t -z --name-only "$sha" >> "$tmp/names" || fail "git ls-tree failed on a commit"
done < "$tmp/commits"
tr '\0' '\n' < "$tmp/names" | sort -u > "$tmp/names.txt"
COUNT=$(grep -c -i -F -f "$tmp/pat" "$tmp/names.txt"; exit $?)
[ $? -le 1 ] || fail "grep failed on file names"
n=$COUNT

echo "commits $c"
echo "file-contents $f"
echo "file-names $n"
[ "$c" -eq 0 ] && [ "$f" -eq 0 ] && [ "$n" -eq 0 ] && exit 0
exit 3
