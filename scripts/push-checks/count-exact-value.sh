#!/usr/bin/env bash
# Count one private value in a git range without printing it (Step 2's pre-push check).
#
#   scripts/push-checks/count-exact-value.sh <range> <value-file>
#   scripts/push-checks/count-exact-value.sh origin/rebuild..rebuild /path/outside/the/repo/value.txt
#
# <value-file> holds the value on one line, UTF-8 (for example the Argaam account name). Keep it outside the
# repository and delete it afterwards. The value is never printed and never passed on a command line.
#
# WHAT IT READS. The snapshots are every commit in the range, each boundary commit (the range's start: parents
# outside the range) and the tip. Every version any patch in the range shows, before or after a change, is in
# one of their trees: an older version is either at the boundary or inside the range. Git lists every object in
# those trees once (`git rev-list --objects --no-walk`), and the script searches git's raw objects:
#   commits <n>        matching lines in the raw commit objects of the range (messages, authors, committers)
#   file-contents <n>  matching lines in every blob of every snapshot: binary files, files deleted inside the range,
#                      and content the range deletes or changes from the base all included
#   file-names <n>     matching lines in every tree object of every snapshot. Tree objects hold each file and
#                      folder name raw, so nothing is quoted or escaped, non-ASCII names included
# So a value already anywhere in the base's tree also stops the push: the patch that deletes or edits it would
# show it again. Matching is byte-exact under LC_ALL=C, ignoring ASCII case. For an ASCII value it also matches
# the value with NUL bytes between its characters, which is how UTF-16 text stores it.
#
# WHAT IT TRUSTS. Only git and grep do work; everything else is bash builtins. No awk, sed, sort, tr, wc or cat
# touches the data, so none of them can drop part of it. grep must pass a positive control first: it must find
# the value in a copy of itself, so a grep that fails or stays silent cannot pass as "none found". Every git and
# grep exit status is checked, every count must be a number, and the lists bash writes are read back and counted.
# git itself is trusted: a git that returns wrong data with exit 0 is outside what this can detect.
#
# WHAT IT CANNOT SEE: text drawn in images (screenshots), text inside compressed files (zip, docx, PDF streams,
# PNG text chunks), encoded forms (URL %40, HTML entities, base64), another Unicode normalisation (NFC/NFD) of a
# non-ASCII value, UTF-16 text of a non-ASCII value, or a value spanning a "/" in a path (names are searched per
# folder level). Screenshots need a person's eyes; run it once per variant if one is plausible.
# A tree object also holds binary object ids, so a very short value can match one by chance (a false stop, never
# a false pass).
#
# It prints exactly three lines, counts only: no matching text and no file name.
# Exit 0: all three are 0. Exit 3: any is not (stop the push). Exit 2: bad input or any failed step (stop).
# Only exit 0 clears a push.
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

# utf8_ok <string>: 0 when every byte sequence is well-formed UTF-8 (no overlongs, no surrogates, nothing above
# U+10FFFF) and no C1 control (U+0080-U+009F) appears. Pure bash, one byte at a time under LC_ALL=C.
utf8_ok() {
  local s=$1 n=${#1} i=0 b c j k lo hi
  while (( i < n )); do
    printf -v b '%d' "'${s:i:1}"
    if (( b < 0x80 )); then (( i += 1 )); continue; fi
    lo=0x80; hi=0xBF
    if   (( b >= 0xC2 && b <= 0xDF )); then k=1
    elif (( b == 0xE0 )); then k=2; lo=0xA0
    elif (( b >= 0xE1 && b <= 0xEC )) || (( b == 0xEE || b == 0xEF )); then k=2
    elif (( b == 0xED )); then k=2; hi=0x9F
    elif (( b == 0xF0 )); then k=3; lo=0x90
    elif (( b >= 0xF1 && b <= 0xF3 )); then k=3
    elif (( b == 0xF4 )); then k=3; hi=0x8F
    else return 1
    fi
    (( i + k < n )) || return 1
    printf -v c '%d' "'${s:i+1:1}"
    (( c >= lo && c <= hi )) || return 1
    (( b == 0xC2 && c <= 0x9F )) && return 1
    for (( j = 2; j <= k; j++ )); do
      printf -v c '%d' "'${s:i+j:1}"
      (( c >= 0x80 && c <= 0xBF )) || return 1
    done
    (( i += k + 1 ))
  done
  return 0
}

# The value: exactly one line of UTF-8; a UTF-8 byte-order mark (Notepad may add one), CR and surrounding spaces
# stripped, in bash. Refused: a NUL byte anywhere in the file (UTF-16 or other wide text), a UTF-16 byte-order
# mark, bytes that are not well-formed UTF-8 (Latin-1, Windows-1252, UTF-16 without a mark), and any control
# character. Each would make the pattern unmatchable, and a pattern that cannot match would report "none found".
# A file written in another encoding whose bytes happen to be valid UTF-8 (for example a value encoded twice)
# cannot be told apart by its bytes; for a non-ASCII value, run a second check with a variant if in doubt.
if IFS= read -r -d '' _ < "$vf"; then fail "the value file holds a NUL byte; save it as UTF-8"; fi
mapfile -t vlines < "$vf" || fail "reading the value failed"
[ "${#vlines[@]}" -ge 1 ] || fail "value file must hold exactly one line"
case "${vlines[0]}" in
  $'\xff\xfe'* | $'\xfe\xff'*) fail "the value file is UTF-16; save it as UTF-8" ;;
esac
[ "${#vlines[@]}" -eq 1 ] || fail "value file must hold exactly one line"
shopt -s extglob
v=${vlines[0]#$'\xef\xbb\xbf'}
v=${v%$'\r'}
v=${v##+([[:space:]])}
v=${v%%+([[:space:]])}
[ -n "$v" ] || fail "value is empty"
[[ $v == *[[:cntrl:]]* ]] && fail "value holds a control character"
utf8_ok "$v" || fail "the value is not valid UTF-8; save the file as UTF-8"
[ "${#v}" -ge 3 ] || fail "value is too short to search for"

# Pattern files. names: the value. contents: the value, and for a printable-ASCII value also the value with a
# NUL between its characters (UTF-16, either byte order). An empty pattern line would match everything, and
# neither file has one.
printf '%s\n' "$v" > "$tmp/pat-names" || fail "writing the pattern failed"
cp_lines=1
printf '%s\n' "$v" > "$tmp/pat-contents" || fail "writing the pattern failed"
if [[ $v =~ ^[[:print:]]+$ ]]; then
  {
    for (( i = 0; i < ${#v}; i++ )); do
      printf '%s' "${v:i:1}"
      (( i < ${#v} - 1 )) && printf '\0'
    done
    printf '\n'
  } >> "$tmp/pat-contents" || fail "writing the pattern failed"
  cp_lines=2
fi

# search <pattern-file> <data-file-or-dash> <label> [-z]: sets HITS to the number of matching lines (records with
# -z). Reads stdin when the data is "-". grep: 0 found, 1 none, more = error.
search() {
  local n
  if [ "$2" = - ]; then n=$(grep -a ${4:-} -c -i -F -f "$1"); else n=$(grep -a ${4:-} -c -i -F -f "$1" "$2"); fi
  local rc=$?
  [ $rc -le 1 ] || fail "the search of $3 failed"
  is_count "$n" || fail "the search of $3 gave no count"
  HITS=$n
}

# Positive control: each pattern line must find itself.
search "$tmp/pat-contents" "$tmp/pat-contents" control
[ "$HITS" -eq "$cp_lines" ] || fail "the search failed its control"
search "$tmp/pat-names" "$tmp/pat-names" control
[ "$HITS" -eq 1 ] || fail "the search failed its control"

git rev-parse --verify --quiet "$base^{commit}" > /dev/null || fail "range start is not a commit"
tipsha=$(git rev-parse --verify --quiet "$tip^{commit}") || fail "range end is not a commit"
[ -n "$tipsha" ] || fail "range end is not a commit"

# The range's commits and its boundary, from git; parsed in bash.
git rev-list --boundary "$range" > "$tmp/with-boundary" || fail "git rev-list --boundary failed"
mapfile -t marked < "$tmp/with-boundary" || fail "reading the commit list failed"
commits=()
snaps=("$tipsha")
for line in "${marked[@]}"; do
  case "$line" in
    -*) snaps+=("${line#-}") ;;
    ?*) commits+=("$line"); snaps+=("$line") ;;
  esac
done
git rev-list "$range" > "$tmp/plain" || fail "git rev-list failed"
mapfile -t plain < "$tmp/plain" || fail "reading the commit list failed"
[ "${#plain[@]}" -eq "${#commits[@]}" ] || fail "the commit list is inconsistent"

# 1. the range's commit objects
printf '%s\n' "${commits[@]}" > "$tmp/commits.list" || fail "writing the commit list failed"
[ "${#commits[@]}" -gt 0 ] || : > "$tmp/commits.list"
git cat-file --batch < "$tmp/commits.list" > "$tmp/commit-objects" || fail "git cat-file failed on commits"
search "$tmp/pat-contents" "$tmp/commit-objects" commits
c=$HITS

# 2 and 3. every object in every snapshot's tree, listed once by git, sorted by type in bash
printf '%s\n' "${snaps[@]}" > "$tmp/snaps.list" || fail "writing the snapshot list failed"
git rev-list --objects --no-object-names --no-walk=unsorted --stdin < "$tmp/snaps.list" > "$tmp/objects" \
  || fail "git rev-list --objects failed"
git cat-file --batch-check='%(objecttype) %(objectname)' < "$tmp/objects" > "$tmp/types" \
  || fail "git cat-file --batch-check failed"
mapfile -t typed < "$tmp/types" || fail "reading the object list failed"
blobs=()
trees=()
for line in "${typed[@]}"; do
  case "$line" in
    "blob "*) blobs+=("${line#blob }") ;;
    "tree "*) trees+=("${line#tree }") ;;
    "commit "*) ;;
    *) fail "an object is missing or of an unexpected type" ;;
  esac
done
[ "${#trees[@]}" -gt 0 ] || fail "no tree objects listed"
printf '%s\n' "${blobs[@]}" > "$tmp/blobs.list" || fail "writing the blob list failed"
printf '%s\n' "${trees[@]}" > "$tmp/trees.list" || fail "writing the tree list failed"
mapfile -t back < "$tmp/blobs.list" || fail "reading the blob list failed"
[ "${#blobs[@]}" -eq 0 ] || [ "${#back[@]}" -eq "${#blobs[@]}" ] || fail "the blob list is incomplete"
mapfile -t back < "$tmp/trees.list" || fail "reading the tree list failed"
[ "${#back[@]}" -eq "${#trees[@]}" ] || fail "the tree list is incomplete"

f=0
if [ "${#blobs[@]}" -gt 0 ]; then
  git cat-file --batch < "$tmp/blobs.list" > "$tmp/blob-data" || fail "git cat-file failed on blobs"
  search "$tmp/pat-contents" "$tmp/blob-data" file-contents
  f=$HITS
fi
git cat-file --batch < "$tmp/trees.list" > "$tmp/tree-data" || fail "git cat-file failed on trees"
search "$tmp/pat-names" "$tmp/tree-data" file-names
n=$HITS

is_count "$c" && is_count "$f" && is_count "$n" || fail "a count is missing"
echo "commits $c"
echo "file-contents $f"
echo "file-names $n"
[ "$c" -eq 0 ] && [ "$f" -eq 0 ] && [ "$n" -eq 0 ] && exit 0
exit 3
