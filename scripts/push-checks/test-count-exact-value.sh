#!/usr/bin/env bash
# Tests count-exact-value.sh in a throwaway repository with dummy values. Prints PASS/FAIL per case.
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
get() { echo "$1" | awk -v k="$2" '$1 == k { print $2 }'; }
# only_counts <output>: 0 when the output is exactly the three count lines and nothing else
only_counts() {
  [ "$(echo "$1" | wc -l | tr -d ' ')" -eq 3 ] || return 1
  echo "$1" | grep -qvE '^(commits|file-contents|file-names) [0-9]+$' && return 1
  return 0
}
val() { printf '%s\n' "$2" > "$work/$1.txt"; echo "$work/$1.txt"; }

repo="$work/repo"
git init -q "$repo"
cd "$repo" || exit 2
git config user.email test@example.invalid
git config user.name test
git config core.autocrlf false
echo base > base.txt
echo "keep dummy.deleted-41 here" > prior.txt                         # review 98: content the range deletes
echo z > "user-dummy.deleted-name-91.txt"                               # review 98: a name the range deletes
echo "line with dummy.edited-63" > edited.txt                           # a line the range edits away
git add . && git commit -q -m base
git tag base
git rm -q prior.txt "user-dummy.deleted-name-91.txt" && echo "line" > edited.txt && git add edited.txt
git commit -q -m "delete and edit what the base had"
echo "contact: Dummy.Account-42 for the feed" > notes.txt
echo x > "dummy.account-42.txt"
git add . && git commit -q -m "add notes"
git commit -q --allow-empty -m "message names dummy.account-42 only"
git tag msg
# review 97's two bypasses, and three neighbours
echo x > "user-مستخدم-42.txt"                                        # a non-ASCII file name
printf 'PNG\000\001 dummy.binary-77 \000\377' > blob.bin                # a binary file, deleted below
echo "secret dummy.text-55 here" > gone.txt                             # a text file, deleted below
mkdir "dir-folder-31" && echo y > "dir-folder-31/inner.txt"             # a folder name
printf 'x dummy.utf16-88 y' | iconv -f UTF-8 -t UTF-16LE > u16.txt      # text saved as UTF-16
git add . && git commit -q -m "scenario files"
git rm -q blob.bin gone.txt && git commit -q -m "delete the binary and text files"
git mv base.txt "renamed-name-99.txt" && git commit -q -m "rename an old file"  # old blob, new name
git tag tip

dummy=$(val dummy 'dummy.account-42')
absent=$(val absent 'NotPresentValue')
crlf="$work/crlf.txt";   printf 'dummy.account-42\r\n' > "$crlf"
empty="$work/empty.txt"; : > "$empty"
blank="$work/blank.txt"; printf '\n' > "$blank"
two="$work/two.txt";     printf 'a-value\nb-value\n' > "$two"

# --- the original 14 cases (output names changed from history/tracked-files to commits/file-contents)
out=$("$script" base..tip "$absent" 2>&1); rc=$?
[ "$out" = $'commits 0\nfile-contents 0\nfile-names 0' ]; check "absent value: three zeros" 0 $rc $?

out=$("$script" base..tip "$dummy" 2>&1); rc=$?
[ "$(get "$out" commits)" -gt 0 ] && [ "$(get "$out" file-contents)" -eq 1 ] && [ "$(get "$out" file-names)" -eq 1 ]
check "present value: nonzero counts, exit 3" 3 $rc $?
echo "$out" | grep -qiF 'dummy.account'; [ $? -eq 1 ]; check "present value: value not printed" 3 $rc $?
echo "$out" | grep -qF '.txt'; [ $? -eq 1 ]; check "present value: no file names printed" 3 $rc $?
only_counts "$out"; check "present value: exactly three lines" 3 $rc $?

out=$("$script" msg~1..msg "$dummy" 2>&1); rc=$?
[ "$(get "$out" commits)" -gt 0 ]; check "message-only commit: commits counts it" 3 $rc $?

out=$("$script" base..tip "$crlf" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -eq 1 ]; check "CRLF value file: CR stripped" 3 $rc $?

"$script" nosuchref..tip "$dummy" > /dev/null 2>&1; check "git error (bad range start)" 2 $? 0
"$script" base..nosuchref "$dummy" > /dev/null 2>&1; check "git error (bad tip)" 2 $? 0
"$script" tip "$dummy" > /dev/null 2>&1; check "not a range" 2 $? 0
"$script" base..tip "$work/missing.txt" > /dev/null 2>&1; check "missing value file" 2 $? 0
"$script" base..tip "$empty" > /dev/null 2>&1; check "empty value file" 2 $? 0
"$script" base..tip "$blank" > /dev/null 2>&1; check "blank line only" 2 $? 0
"$script" base..tip "$two" > /dev/null 2>&1; check "two lines" 2 $? 0

# --- review 97's regressions and neighbours
v=$(val arabic 'مستخدم-42')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-names)" -ge 1 ] && only_counts "$out"; check "non-ASCII file name: found, only counts printed" 3 $rc $?

v=$(val binary 'dummy.binary-77')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "binary file added then deleted: found, only counts printed" 3 $rc $?

v=$(val text 'dummy.text-55')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "text file added then deleted: found" 3 $rc $?

v=$(val renamed 'renamed-name-99')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-names)" -ge 1 ] && only_counts "$out"; check "old file renamed to the value: found" 3 $rc $?

v=$(val folder 'dir-folder-31')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-names)" -ge 1 ] && only_counts "$out"; check "folder name: found" 3 $rc $?

v=$(val utf16 'dummy.utf16-88')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "UTF-16 text file: found" 3 $rc $?

v=$(val spaced '  dummy.account-42 ')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -eq 1 ]; check "value file with surrounding spaces: trimmed" 3 $rc $?

v=$(val spaces '   ')
"$script" base..tip "$v" > /dev/null 2>&1; check "value of spaces only" 2 $? 0

v=$(val deleted 'dummy.deleted-41')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "base content the range deletes: found" 3 $rc $?

v=$(val deletedname 'dummy.deleted-name-91')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-names)" -ge 1 ] && only_counts "$out"; check "base file name the range deletes: found" 3 $rc $?

v=$(val edited 'dummy.edited-63')
out=$("$script" base..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "base line the range edits away: found" 3 $rc $?

v=$(val short 'ab')
"$script" base..tip "$v" > /dev/null 2>&1; check "value shorter than 3 characters" 2 $? 0
"$script" base...tip "$dummy" > /dev/null 2>&1; check "three-dot range refused" 2 $? 0

# --- review 99: a tool that fails, or exits 0 with no output, must give exit 2, never a result.
# Each stand-in sits first on PATH for one run. "fail" exits 1 with no output, "silent" exits 0 with no output,
# "late" runs the real tool and then exits 1.
fakes="$work/fakes"
for tool in sort awk sed tr grep wc mktemp; do
  realtool=$(command -v "$tool")
  for mode in fail silent late; do
    d="$fakes/$tool-$mode"
    mkdir -p "$d"
    case $mode in
      fail)   printf '#!/bin/sh\nexit 1\n' > "$d/$tool" ;;
      silent) printf '#!/bin/sh\nexit 0\n' > "$d/$tool" ;;
      late)   printf '#!/bin/sh\n"%s" "$@"\nexit 1\n' "$realtool" > "$d/$tool" ;;
    esac
    chmod +x "$d/$tool"
    for which in present absent; do
      [ $which = present ] && vfile=$dummy || vfile=$absent
      PATH="$d:$PATH" "$script" base..tip "$vfile" > "$work/out" 2>&1; rc=$?
      check "$tool $mode, value $which: exit 2" 2 $rc 0
    done
  done
done

echo "failures: $fails"
[ $fails -eq 0 ]
