#!/usr/bin/env bash
# Count one private value in a git range without printing it (Step 2's pre-push check).
#
#   scripts/push-checks/count-exact-value.sh <range> <value-file>
#   scripts/push-checks/count-exact-value.sh origin/rebuild..rebuild /path/outside/the/repo/value.txt
#
# <value-file> holds the value on one line (for example the Argaam account name). Keep it outside the
# repository and delete it afterwards. The value is never printed and never passed on a command line.
#
# Prints exactly three lines, counts only, matching case-insensitively:
#   history <n>        lines of `git log -p <range>` that contain it (patches, messages, authors)
#   tracked-files <n>  occurrences, summed over every file in the range's tip (no file names printed)
#   file-names <n>     paths in the tip's tree (`git ls-tree -r --name-only`) that contain it
# Exit 0: all three are 0. Exit 3: any is not (stop the push). Exit 2: bad input or a git error (stop).
set -u

fail() { echo "error: $1" >&2; exit 2; }

[ $# -eq 2 ] || fail "usage: count-exact-value.sh <range> <value-file>"
range=$1
vf=$2
[ -f "$vf" ] || fail "value file not found"
case "$range" in
  *..*) tip=${range##*..} ;;
  *) fail "range must look like A..B" ;;
esac
[ -n "$tip" ] || fail "range has no right-hand side"

tmp=$(mktemp -d) || fail "mktemp failed"
trap 'rm -rf "$tmp"' EXIT

# One pattern, exactly: strip a trailing CR, refuse an empty value or more than one line,
# because an empty line in a grep -f file would match everything.
tr -d '\r' < "$vf" > "$tmp/pat"
lines=$(grep -c '' "$tmp/pat")
[ "$lines" -eq 1 ] || fail "value file must hold exactly one line"
[ -n "$(head -c 1 "$tmp/pat")" ] || fail "value is empty"
[ "$(wc -c < "$tmp/pat" | tr -d ' ')" -ge 3 ] || fail "value is too short to search for"

git rev-parse --verify --quiet "$tip^{commit}" > /dev/null || fail "tip is not a commit"

# 1. history of the range
git log -p "$range" > "$tmp/log" 2> "$tmp/err" || fail "git log failed"
h=$(grep -c -i -F -f "$tmp/pat" "$tmp/log")
[ $? -le 1 ] || fail "grep failed on history"

# 2. contents of every tracked file at the tip (git grep: 0 = found, 1 = none, more = error)
git grep -c -i -F -f "$tmp/pat" "$tip" -- > "$tmp/grep" 2> "$tmp/err"
rc=$?
[ $rc -le 1 ] || fail "git grep failed"
t=$(awk -F: '{ s += $NF } END { print s + 0 }' "$tmp/grep")

# 3. file names in the tip's tree
git ls-tree -r --name-only "$tip" > "$tmp/names" 2> "$tmp/err" || fail "git ls-tree failed"
n=$(grep -c -i -F -f "$tmp/pat" "$tmp/names")
[ $? -le 1 ] || fail "grep failed on file names"

echo "history $h"
echo "tracked-files $t"
echo "file-names $n"
[ "$h" -eq 0 ] && [ "$t" -eq 0 ] && [ "$n" -eq 0 ] && exit 0
exit 3
