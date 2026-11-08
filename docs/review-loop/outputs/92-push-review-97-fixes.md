# Output 92: review 97's fixes to the exact-value check

**Review 97 said FIX.** It reproduced two false negatives in `count-exact-value.sh`. Both returned three zeros and
exit 0:
1. **A non-ASCII file name:** git's quoted path listing escapes it.
2. **A binary file added then deleted inside the range:** `git log -p` does not show binary content, and the other
   two checks read only the tip.

**What was done** (commits `3517fbe` and `d55db6e` on `rebuild`, local only; diff in `review-97-fixes.diff`):

1. **The script reads git's raw objects, not formatted output.**
   - **`commits <n>`:** the raw commit objects of the range (`git rev-list <range>`, then `git cat-file --batch`):
     messages, authors and committers.
   - **`file-contents <n>`:** every blob the range adds (`git rev-list --objects --no-object-names <range>`, keeping
     type `blob`), plus every blob in the tip. Deduplicated, then dumped with `git cat-file --batch`. This covers
     binary files and files deleted inside the range.
   - **`file-names <n>`:** every path, files and folders, in every commit of the range, from
     `git ls-tree -r -t -z --name-only`. The `-z` output is never quoted, so non-ASCII names stay raw. This also
     catches an old file renamed to the value, whose blob is not new.
   - **Matching:** `LC_ALL=C`, byte-exact, ignoring ASCII case. Counts come from `grep -a -o | wc -l`, with grep's
     own exit status checked through `PIPESTATUS`, so a grep error exits 2 and no match is written to disk.
2. **Found while checking for further gaps:**
   - **UTF-16:** file contents are searched with NUL bytes removed, so text saved as UTF-16 is found for an ASCII
     value.
   - **The value file:** it is trimmed of surrounding spaces, and a value of spaces only is refused.
   - **`A...B`:** refused. Both ends must be commits.
3. **Its limits are now written into the script and Step 2.** No byte search sees:
   - text drawn in images (screenshots);
   - text inside compressed files (zip, docx, PDF streams);
   - encoded forms (URL `%40`, HTML entities, base64).

   Screenshots in a range need a person's look. A plausible encoded variant needs its own run.
4. **The tests:** 24 pass (`count-script-test.txt`).
   - **The original 14:** their checks now read the new output names (`commits`, `file-contents`).
   - **10 new:**
     - both of review 97's cases;
     - a text file added then deleted;
     - an old file renamed to the value;
     - a folder name;
     - a UTF-16 text file;
     - a value file with surrounding spaces;
     - a value of spaces only;
     - a value under 3 characters;
     - an `A...B` range.
   - **The new cases' assertions:** each checks the count and that the output is exactly the three count lines,
     stderr included.
5. **Against the previous script (`9dbf448`):** in a throwaway repository, both of review 97's cases give three zeros
   and exit 0. Here they give exit 3, with `file-names 1` and `file-contents 1` respectively.
6. **Smoke runs on this repository:** `eeb9a9d..dcc4189` takes about 7 s.
   - **An absent value:** three zeros, exit 0.
   - **"moyasar":** `0 / 5141 / 3`, exit 3.
   - **A bad ref:** exit 2.
7. **Step 2's *How*** describes the new reads, the output names and the limits. This push's exception is still
   recorded as unresolved.
8. **Command output** (`git-state-92.txt`):
   - `git diff --check 9dbf448..d55db6e` exits 0.
   - The branch is `[ahead 6]` with a clean tree.
   - The remote's `rebuild` is still `dcc4189`.
   - Both scripts are mode 100755.

**The question for the review:**
- Are the fixes right and complete?
- Does any other way remain for an exact UTF-8 or ASCII value in a pushed range to get past the check?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push of these 6 commits after the checkpoint;
  - Step 18 item 4.
