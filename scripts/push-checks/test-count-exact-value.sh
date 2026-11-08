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
printf 'caf\303\251 and \344\270\255\346\226\207\346\265\213\350\257\225\n' > intl.txt  # UTF-8 "café" and "中文测试"
git add . && git commit -q -m "scenario files"
git rm -q blob.bin gone.txt && git commit -q -m "delete the binary and text files"
git mv base.txt "renamed-name-99.txt" && git commit -q -m "rename an old file"  # old blob, new name
git tag tip
# review 102: a side branch from base that diverges from tip; only the side holds the value
git checkout -q -b side base
echo "dummy.secret-987 lives only on the side" > side.txt
git add side.txt && git commit -q -m "side only"
git checkout -q -

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
[ "$(get "$out" commits)" -gt 0 ] && [ "$(get "$out" file-contents)" -eq 1 ] && [ "$(get "$out" file-names)" -ge 1 ]
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

bom="$work/bom.txt"; printf '\357\273\277dummy.account-42\r\n' > "$bom"           # UTF-8 with a byte-order mark
out=$("$script" base..tip "$bom" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -eq 1 ] && only_counts "$out"; check "value file with a UTF-8 byte-order mark: found" 3 $rc $?
u16="$work/u16.txt"; { printf '\377\376'; printf 'dummy.account-42\r\n' | iconv -f UTF-8 -t UTF-16LE; } > "$u16"
"$script" base..tip "$u16" > /dev/null 2>&1; check "UTF-16 value file refused" 2 $? 0
ctl="$work/ctl.txt"; printf 'dummy\001account-42\n' > "$ctl"
"$script" base..tip "$ctl" > /dev/null 2>&1; check "control character in the value refused" 2 $? 0

# review 101: a value file in another encoding must be refused, not read as an unmatchable value
enc() { printf "$2" > "$work/enc-$1.txt"; echo "$work/enc-$1.txt"; }
f=$(enc zh8 '\344\270\255\346\226\207\346\265\213\350\257\225\n')                  # "中文测试", UTF-8
out=$("$script" base..tip "$f" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "UTF-8 Chinese value: found" 3 $rc $?
f=$(enc cafe8 'caf\303\251\n')                                                     # "café", UTF-8
out=$("$script" base..tip "$f" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "UTF-8 accented value: found" 3 $rc $?
f="$work/enc-zh16be.txt"; printf '\344\270\255\346\226\207\346\265\213\350\257\225' | iconv -f UTF-8 -t UTF-16BE > "$f"
"$script" base..tip "$f" > /dev/null 2>&1; check "UTF-16BE value without a mark refused (review 101)" 2 $? 0
f=$(enc cafe1 'caf\351\n')                                                         # "café", Latin-1
"$script" base..tip "$f" > /dev/null 2>&1; check "Latin-1 value refused (review 101)" 2 $? 0
f="$work/enc-ascii16le.txt"; printf 'dummy.account-42' | iconv -f UTF-8 -t UTF-16LE > "$f"
"$script" base..tip "$f" > /dev/null 2>&1; check "UTF-16LE value without a mark refused" 2 $? 0
f=$(enc nul 'dummy.account-42\000')
"$script" base..tip "$f" > /dev/null 2>&1; check "value file ending in a NUL byte refused" 2 $? 0
f=$(enc overlong '\300\257dummy\n')
"$script" base..tip "$f" > /dev/null 2>&1; check "overlong UTF-8 refused" 2 $? 0
f=$(enc c1 'dum\302\205my\n')
"$script" base..tip "$f" > /dev/null 2>&1; check "C1 control character refused" 2 $? 0
f=$(enc cut 'dummy\344\270\n')
"$script" base..tip "$f" > /dev/null 2>&1; check "UTF-8 cut short refused" 2 $? 0

v=$(val short 'ab')
"$script" base..tip "$v" > /dev/null 2>&1; check "value shorter than 3 characters" 2 $? 0
"$script" base...tip "$dummy" > /dev/null 2>&1; check "three-dot range refused" 2 $? 0

# review 102: diverged ends. `git diff side..tip` shows side.txt being removed, so the value must be found.
v=$(val diverged 'dummy.secret-987')
out=$("$script" side..tip "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "diverged range, value only at its start: found" 3 $rc $?
out=$("$script" tip..side "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "diverged range, value only at its end: found" 3 $rc $?

# review 103: a replacement ref must not hide the real object, the one a push sends
git checkout -q -b rep tip
echo "dummy.replaced-73 is in the real blob" > rep.txt
git add rep.txt && git commit -q -m "rep"
realblob=$(git rev-parse rep:rep.txt)
fakeblob=$(echo "harmless" | git hash-object -w --stdin)
git replace "$realblob" "$fakeblob"
git checkout -q -
[ "$(git cat-file -p "$realblob")" = harmless ]; check "setup: plain git now reads the replacement" 0 0 $?
v=$(val replaced 'dummy.replaced-73')
out=$("$script" tip..rep "$v" 2>&1); rc=$?
[ "$(get "$out" file-contents)" -ge 1 ] && only_counts "$out"; check "replaced blob: the real content is found" 3 $rc $?
git replace -d "$realblob" > /dev/null

# review 103: a grafts file changes what git reads, so it is refused
gf=$(git rev-parse --git-path info/grafts)
mkdir -p "$(dirname "$gf")" && : > "$gf"
"$script" base..tip "$dummy" > /dev/null 2>&1; check "grafts file refused" 2 $? 0
rm -f "$gf"

# review 103: Step 2's push command must not publish an annotated tag, even with push.followTags on
git checkout -q -b pubtest tip
echo y > pub.txt && git add pub.txt && git commit -q -m pub
git tag -a pubtag -m "tag message with dummy.tagmsg-55"
git config push.followTags true
bare="$work/bare.git"; git init -q --bare "$bare"
git push -q --no-follow-tags "$bare" pubtest 2> /dev/null
[ -z "$(git -C "$bare" tag)" ]; check "push --no-follow-tags with followTags on: no tag published" 0 0 $?
git -C "$bare" cat-file --batch-all-objects --batch | grep -a -q -F 'dummy.tagmsg-55'
[ $? -eq 1 ]; check "push --no-follow-tags: the tag's message is not in the remote" 0 0 $?
bare2="$work/bare2.git"; git init -q --bare "$bare2"
git push -q "$bare2" pubtest 2> /dev/null
[ -n "$(git -C "$bare2" tag)" ]; check "plain push with followTags on: the tag IS published (the flag matters)" 0 0 $?
git config --unset push.followTags
git checkout -q -

# --- reviews 99 and 100: failing or lying helper tools.
# Each stand-in sits first on PATH for one run. "fail" exits 1 with no output, "silent" exits 0 with no output,
# "late" runs the real tool and then exits 1.
# grep and mktemp do work in the script: when they fail or stay silent the result must be exit 2. "late" grep
# exits 1 after a correct answer, which is grep's ordinary "none found" status, so its result must be correct.
fakes="$work/fakes"
for tool in grep mktemp; do
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
      if [ "$tool $mode" = "grep late" ]; then
        [ $which = present ] && want=3 || want=0
        check "$tool $mode, value $which: correct result" $want $rc 0
      else
        check "$tool $mode, value $which: exit 2" 2 $rc 0
      fi
    done
  done
done

# The script uses no other text tool, so none can drop data. With every common one broken (each exits 1 with no
# output) the results must be unchanged. That includes review 100's two cases: a selectively silent awk dropping a
# base-only blob, and a selectively incomplete sort dropping a base-only name.
poison="$fakes/poison"
mkdir -p "$poison"
for tool in awk sort sed tr wc cat head tail cut uniq comm xargs find; do
  printf '#!/bin/sh\nexit 1\n' > "$poison/$tool"
  chmod +x "$poison/$tool"
done
for case in "dummy.account-42 3" "NotPresentValue 0" "dummy.deleted-41 3" "dummy.deleted-name-91 3"; do
  set -- $case
  vfile=$(val "poison-$1" "$1")
  PATH="$poison:$PATH" "$script" base..tip "$vfile" > "$work/out" 2>&1; rc=$?
  only_counts "$(cat "$work/out")"; check "text tools broken, value $1: same result" "$2" $rc $?
done

echo "failures: $fails"
[ $fails -eq 0 ]
