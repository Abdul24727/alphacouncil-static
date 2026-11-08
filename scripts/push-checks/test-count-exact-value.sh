#!/usr/bin/env bash
# Tests count-exact-value.sh in a throwaway repository with a dummy value. Prints PASS/FAIL per case.
#   bash scripts/push-checks/test-count-exact-value.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
script="$here/count-exact-value.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
fails=0

check() { # name, expected exit, actual exit, extra condition (0 = ok)
  if [ "$2" = "$3" ] && [ "$4" = 0 ]; then echo "PASS  $1"; else echo "FAIL  $1 (exit $3, want $2)"; fails=$((fails + 1)); fi
}

repo="$work/repo"
git init -q "$repo"
cd "$repo" || exit 2
git config user.email test@example.invalid
git config user.name test
git config core.autocrlf false
echo base > base.txt
git add base.txt && git commit -q -m base
git tag base
echo "contact: Dummy.Account-42 for the feed" > notes.txt
echo x > "dummy.account-42.txt"
git add . && git commit -q -m "add notes"
git commit -q --allow-empty -m "message names dummy.account-42 only"
git tag tip

dummy="$work/dummy.txt";   printf 'dummy.account-42\n' > "$dummy"
absent="$work/absent.txt"; printf 'NotPresentValue\n' > "$absent"
crlf="$work/crlf.txt";     printf 'dummy.account-42\r\n' > "$crlf"
empty="$work/empty.txt";   : > "$empty"
blank="$work/blank.txt";   printf '\n' > "$blank"
two="$work/two.txt";       printf 'a-value\nb-value\n' > "$two"

out=$("$script" base..tip "$absent"); rc=$?
want=$'history 0\ntracked-files 0\nfile-names 0'
[ "$out" = "$want" ]; check "absent value: three zeros" 0 $rc $?

out=$("$script" base..tip "$dummy"); rc=$?
h=$(echo "$out" | awk '$1=="history"{print $2}')
t=$(echo "$out" | awk '$1=="tracked-files"{print $2}')
n=$(echo "$out" | awk '$1=="file-names"{print $2}')
[ "$h" -gt 0 ] && [ "$t" -eq 1 ] && [ "$n" -eq 1 ]; check "present value: nonzero counts, exit 3" 3 $rc $?
echo "$out" | grep -qiF 'dummy.account' ; [ $? -eq 1 ]; check "present value: value not printed" 3 $rc $?
echo "$out" | grep -qF '.txt' ; [ $? -eq 1 ]; check "present value: no file names printed" 3 $rc $?
[ "$(echo "$out" | wc -l | tr -d ' ')" -eq 3 ]; check "present value: exactly three lines" 3 $rc $?

out=$("$script" tip~1..tip "$dummy"); rc=$?
[ "$(echo "$out" | awk '$1=="history"{print $2}')" -gt 0 ]; check "message-only commit: history counts it" 3 $rc $?

out=$("$script" base..tip "$crlf"); rc=$?
[ "$(echo "$out" | awk '$1=="tracked-files"{print $2}')" -eq 1 ]; check "CRLF value file: CR stripped" 3 $rc $?

"$script" nosuchref..tip "$dummy" > /dev/null 2>&1; check "git error (bad range start)" 2 $? 0
"$script" base..nosuchref "$dummy" > /dev/null 2>&1; check "git error (bad tip)" 2 $? 0
"$script" tip "$dummy" > /dev/null 2>&1; check "not a range" 2 $? 0
"$script" base..tip "$work/missing.txt" > /dev/null 2>&1; check "missing value file" 2 $? 0
"$script" base..tip "$empty" > /dev/null 2>&1; check "empty value file" 2 $? 0
"$script" base..tip "$blank" > /dev/null 2>&1; check "blank line only" 2 $? 0
"$script" base..tip "$two" > /dev/null 2>&1; check "two lines" 2 $? 0

echo "failures: $fails"
[ $fails -eq 0 ]
