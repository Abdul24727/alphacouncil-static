# Output 95: review 100's fix: only git and grep touch the data

**Review 100 said FIX.** It reproduced two selective omissions, both giving three zeros and exit 0:
1. An `awk` silent only for the base snapshot.
2. A `sort` dropping only a base-only file name.

**The approach:** every round since review 97 has found another way a helper tool could lose part of the data.
Rather than add a completeness check per tool, this commit takes the text tools off the data path entirely
(commits `bec0746` and `6a68598` on `rebuild`, local only; diff in `review-100-fixes.diff`).

1. **Enumeration by git, dedup by git:**
   - **The snapshots:** every range commit, each boundary commit and the tip. Bash builds the list from
     `git rev-list --boundary` and cross-checks it against plain `git rev-list`.
   - **The listing:** git lists every object in those snapshots' trees, once:
     `git rev-list --objects --no-object-names --no-walk=unsorted --stdin`.
   - **Sorting by type:** `git cat-file --batch-check` types each object, and a bash `case` puts each into blobs or
     trees. Anything else, or a missing object, means exit 2.
   - **Read-back:** the lists bash writes are read back with `mapfile` and their counts compared.
2. **The search:**
   - **Contents:** `git cat-file --batch` dumps the blobs, and grep searches them.
   - **Names:** grep searches the tree objects, which hold every file and folder name raw. Nothing is quoted or
     escaped, so no `ls-tree -z` parsing is needed.
   - **Commits:** grep searches the range's commit objects.
   - **Counts:** each is a number of matching lines (`grep -c`), so `wc` is no longer needed.
3. **UTF-16 without `tr`:** for a printable-ASCII value, the content pattern file has a second line, the value with
   a NUL between its characters. That matches UTF-16 text in either byte order. GNU grep accepts NUL in `-f`
   patterns; this was tested.
4. **What does work:** git, grep and mktemp, plus `rm` in the exit trap. `git-state-95.txt` lists the command words
   found in the script.
   - **grep's control:** before any zero is believed, grep must pass a positive control, each pattern line finding
     itself.
   - **Statuses:** every git and grep exit status is checked, and every count must be a number.
   - **What is trusted:** git.
5. **Found while checking, and fixed** (`6a68598`): a value file saved with a UTF-8 byte-order mark made the value
   unmatchable. Notepad may add that mark, so a present value read as clean: exit 0 at `bec0746`.
   - **Now:** the mark is stripped; a UTF-16 value file is refused, and so is a control character in the value.
     Both refusals are exit 2.
6. **The tests:** 46 pass (`count-script-test.txt`).
   - **Data cases:** 27, with one assertion loosened: `file-names` for the present value is now `-ge 1`, because
     several root trees hold the name.
   - **Value files:** 3 (byte-order mark, UTF-16, control character).
   - **grep and mktemp:** 12, each failing, silent, or failing after the work, with the value present and absent.
     All give exit 2, except "late" grep: it exits 1 after a correct answer, which is grep's ordinary "none found"
     status, and its result is correct.
   - **Broken text tools:** 4 runs with 13 common ones broken (`awk sort sed tr wc cat head tail cut uniq comm
     xargs find`, each exits 1). These include review 100's two cases, and the results are unchanged.
7. **Review 100's two cases, reproduced as described:** an `awk` silent only when its input holds the base-only
   file, and a `sort` filtering out the base-only name. Against `2e98f72` both give exit 0; here, exit 3.
8. **Smoke runs on this repository, over `eeb9a9d..dcc4189`:**
   - **Time:** 4 s, down from 18 s.
   - **An absent value:** three zeros, exit 0.
   - **"moyasar":** `0 / 4129 / 3`, exit 3. These are now matching lines, not occurrences.
   - **A bad ref:** exit 2.
9. **Step 2** describes the git-and-grep design, the value-file rules and the full list of limits. One limit is new:
   a value spanning a `/` is not matched, because tree objects store one folder level each.
10. **Command output** (`git-state-95.txt`):
    - `git diff --check 2e98f72..6a68598` exits 0.
    - `bash -n` passes for both scripts.
    - The branch is `[ahead 12]`, with a clean tree before this output.
    - The remote's `rebuild` is still `dcc4189`.

**Outside what it can guard, as stated:**
- git returning wrong data with exit 0;
- a grep that passes its control but hides real matches (a deliberately malicious tool);
- the documented content limits.

**The question for the review:**
- Is this right and complete?
- Does any path remain to exit 0 while the value is in what the range shows or publishes, without git or grep
  lying?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push after the checkpoint;
  - Step 18 item 4.
