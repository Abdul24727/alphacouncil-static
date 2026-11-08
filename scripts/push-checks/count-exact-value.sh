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
#
# It fails closed. Every command and every stage of every pipeline is checked (pipefail), every count must be a
# number, and checks done in bash itself, not by the tools they check, catch a tool that exits 0 but returns too
# little: the tip and every range and boundary commit are among the snapshots read; every file in the tip is in
# the list of file versions searched; the bytes dumped equal what git says those objects hold; and the search must
# find the value in a copy of itself before a zero is believed.
# Exit 0: all three are 0. Exit 3: any is not (stop the push). Exit 2: bad input, any failed step, or a failed
# integrity check (stop). Only exit 0 clears a push.
set -u
set -o pipefail
export LC_ALL=C

fail() { echo "error: $1" >&2; exit 2; }
is_count() { case "$1" in ''|*[!0-9]*) return 1 ;; *) return 0 ;; esac; }

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
[ -n "$tmp" ] && [ -d "$tmp" ] || fail "mktemp gave no folder"
trap 'rm -rf "$tmp"' EXIT

# One pattern, exactly: strip CR and surrounding spaces, refuse an empty value or more than one line,
# because an empty line in a grep -f file would match everything. Checked in bash, not with grep.
tr -d '\r' < "$vf" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' > "$tmp/pat" || fail "reading the value failed"
mapfile -t patlines < "$tmp/pat" || fail "reading the value failed"
[ "${#patlines[@]}" -eq 1 ] || fail "value file must hold exactly one line"
[ -n "${patlines[0]}" ] || fail "value is empty"
[ "${#patlines[0]}" -ge 3 ] || fail "value is too short to search for"

git rev-parse --verify --quiet "$base^{commit}" > /dev/null || fail "range start is not a commit"
tipsha=$(git rev-parse --verify --quiet "$tip^{commit}") || fail "range end is not a commit"
[ -n "$tipsha" ] || fail "range end is not a commit"

# count <file> <label>: occurrences of the value in <file>, read as bytes; sets COUNT. Both pipeline stages'
# exit statuses are checked (grep: 0 found, 1 none, more = error; wc: 0), without writing any match to disk.
count() {
  local out n st g w
  out=$(grep -a -o -i -F -f "$tmp/pat" "$1" | wc -l; echo "status ${PIPESTATUS[0]} ${PIPESTATUS[1]}")
  n=${out%%$'\n'*}
  st=${out##*$'\n'}
  read -r _ g w <<< "$st"
  is_count "$g" && is_count "$w" || fail "no exit status from the search of $2"
  [ "$g" -le 1 ] && [ "$w" -eq 0 ] || fail "the search of $2 failed"
  n=${n//[[:space:]]/}
  is_count "$n" || fail "the search of $2 gave no count"
  COUNT=$n
}

# Positive control: both searches must find the value once in a copy of itself, so a grep or wc that fails
# quietly (exit 0 or 1 with no output) cannot pass as "none found".
count "$tmp/pat" control
[ "$COUNT" -eq 1 ] || fail "the search failed its control"
ctl=$(grep -c -i -F -f "$tmp/pat" "$tmp/pat")
[ $? -eq 0 ] && [ "$ctl" = 1 ] || fail "the name search failed its control"

# dumped_ok <id-list> <dump>: the dump from `git cat-file --batch` must be exactly as long as git says: for each
# object, its header line, its content and one newline. Sizes come from --batch-check; the sum is done in bash.
dumped_ok() {
  local want=0 sha type size have
  git cat-file --batch-check < "$1" > "$tmp/check" || fail "git cat-file --batch-check failed"
  while read -r sha type size; do
    is_count "$size" || fail "object missing or unreadable"
    want=$(( want + ${#sha} + 1 + ${#type} + 1 + ${#size} + 1 + size + 1 ))
  done < "$tmp/check"
  have=$(wc -c < "$2") || fail "measuring a dump failed"
  have=${have//[[:space:]]/}
  is_count "$have" || fail "measuring a dump gave no number"
  [ "$have" -eq "$want" ] || fail "a dump is incomplete ($have of $want bytes)"
}

# 1. the range's commits, raw
git rev-list "$range" > "$tmp/commits" || fail "git rev-list failed"
# the boundary: parents of range commits that are outside the range (rev-list marks them with "-")
git rev-list --boundary "$range" > "$tmp/with-boundary" || fail "git rev-list --boundary failed"
mapfile -t commits < "$tmp/commits" || fail "reading the commit list failed"
mapfile -t marked < "$tmp/with-boundary" || fail "reading the boundary list failed"
boundary=()
for line in "${marked[@]}"; do
  case "$line" in -*) boundary+=("${line#-}") ;; esac
done
git cat-file --batch < "$tmp/commits" > "$tmp/commit-objects" || fail "git cat-file failed on commits"
dumped_ok "$tmp/commits" "$tmp/commit-objects"
count "$tmp/commit-objects" commits
c=$COUNT

# 2 and 3. the full tree of every commit in the range, of each boundary commit, and of the tip
declare -A want_snap=()
for s in "${commits[@]}" "${boundary[@]}" "$tipsha"; do [ -n "$s" ] && want_snap[$s]=1; done
printf '%s\n' "${!want_snap[@]}" > "$tmp/snapshots" || fail "writing the snapshot list failed"
mapfile -t snaps < "$tmp/snapshots" || fail "reading the snapshot list failed"
[ "${#snaps[@]}" -eq "${#want_snap[@]}" ] || fail "the snapshot list is incomplete"

: > "$tmp/blobs" || fail "writing the blob list failed"
: > "$tmp/names" || fail "writing the name list failed"
for sha in "${snaps[@]}"; do
  git ls-tree -r "$sha" > "$tmp/tree" || fail "git ls-tree failed on a commit"
  awk '$2 == "blob" { print $3 }' "$tmp/tree" >> "$tmp/blobs" || fail "listing blobs failed"
  git ls-tree -r -t -z --name-only "$sha" >> "$tmp/names" || fail "git ls-tree -z failed on a commit"
done
sort -u "$tmp/blobs" -o "$tmp/blobs" || fail "sorting the blob list failed"

# every blob in the tip must be in the list (checked in bash)
declare -A have_blob=()
mapfile -t bl < "$tmp/blobs" || fail "reading the blob list failed"
for b in "${bl[@]}"; do have_blob[$b]=1; done
git ls-tree -r "$tipsha" > "$tmp/tip-tree" || fail "git ls-tree failed on the tip"
tipnames=0
while read -r mode type sha path; do
  tipnames=$(( tipnames + 1 ))
  [ "$type" = blob ] || continue
  [ -n "${have_blob[$sha]:-}" ] || fail "the blob list is missing a file from the tip"
done < "$tmp/tip-tree"

git cat-file --batch < "$tmp/blobs" > "$tmp/blob-data0" || fail "git cat-file failed on blobs"
dumped_ok "$tmp/blobs" "$tmp/blob-data0"
# NUL bytes removed, so text saved as UTF-16 is found too (for an ASCII value); in UTF-8 text this changes nothing
tr -d '\000' < "$tmp/blob-data0" > "$tmp/blob-data" || fail "tr failed on blobs"
count "$tmp/blob-data" file-contents
f=$COUNT

tr '\000' '\n' < "$tmp/names" | sort -u > "$tmp/names.txt" || fail "listing names failed"
mapfile -t nm < "$tmp/names.txt" || fail "reading the name list failed"
[ "${#nm[@]}" -ge "$tipnames" ] || fail "the name list is incomplete"
n=$(grep -c -i -F -f "$tmp/pat" "$tmp/names.txt")
[ $? -le 1 ] || fail "the search of file names failed"
is_count "$n" || fail "the search of file names gave no count"

is_count "$c" && is_count "$f" && is_count "$n" || fail "a count is missing"
echo "commits $c"
echo "file-contents $f"
echo "file-names $n"
[ "$c" -eq 0 ] && [ "$f" -eq 0 ] && [ "$n" -eq 0 ] && exit 0
exit 3
