# Output 93: review 98's fixes: every full tree, boundary included

**Review 98 said FIX.** It reproduced two more false negatives, both returning three zeros and exit 0:
1. A file's content present at the range's start and deleted by the range.
2. A file name present at the range's start and deleted by the range.

The outgoing patch shows both.

**What was done** (commits `8598c26`, `8ddd03b` and `94e191e` on `rebuild`, local only; diff in `review-98-fixes.diff`):

1. **The root cause:** the check read only versions the range adds, plus the tip. A patch also shows the
   *pre-change* side, which can come from the commit the range starts from.
2. **The fix, general rather than per case:** `count-exact-value.sh` now builds one set of snapshots and reads the
   full tree of each:
   - every commit in the range (`git rev-list <range>`);
   - each boundary commit, the parents outside the range (`git rev-list --boundary`, the `-` lines);
   - the tip.

   For each snapshot it reads two things: blob ids from `git ls-tree -r`, and names from
   `git ls-tree -r -t -z --name-only`. Blobs are deduplicated, dumped with `git cat-file --batch` and searched with
   NUL bytes removed. This replaces `git rev-list --objects`.
3. **Why this is complete for patches:** every version a patch in the range shows, before or after a change, is in
   the tree of a commit in the range or of its parent. That parent is either in the range or at the boundary. Merge
   parents outside the range are boundary commits too.
4. **A stated consequence** (in the script and Step 2): a value already anywhere in the base's tree also stops the
   push.
5. **The tests:** 27 pass (`count-script-test.txt`).
   - **Kept:** the 24 earlier cases.
   - **New:** content the range deletes from the base, a file name the range deletes from the base, and a base line
     the range edits away.
   - **The assertions:** each new case checks the count and that the output is only the three count lines, stderr
     included.
6. **Against the previous version (`d55db6e`):** in a throwaway repository, review 98's two cases give three zeros
   and exit 0 there, and exit 3 here.
7. **Smoke runs on this repository, over `eeb9a9d..dcc4189`:**
   - **Time:** about 15 s.
   - **An absent value:** three zeros, exit 0.
   - **"moyasar":** `0 / 5261 / 3`, exit 3. It was 5141 before, because the base's versions are now read too.
   - **A bad ref:** exit 2.
8. **A slip, caught and fixed before the commit:** a scripted edit wrote two raw NUL bytes into the `tr` lines.
   The tests caught it (2 failures), and the script was rewritten whole. `git-state-93.txt` shows 0 NUL bytes in the
   committed file.
9. **Command output** (`git-state-93.txt`):
   - `git diff --check d55db6e..94e191e` exits 0.
   - The branch is `[ahead 9]`. The only uncommitted files are this output and its prompt, which are committed with
     the reply.
   - The remote's `rebuild` is still `dcc4189`.
   - Both scripts are mode 100755.

**Known limits, stated in the script and Step 2:**
- **What it cannot see:** text drawn in images, text inside compressed files, and encoded forms (URL `%40`, HTML
  entities, base64).
- **Case:** it ignores ASCII case only.
- **Unicode:** it does not normalise Unicode. An NFD spelling of a non-ASCII value is a different byte string and
  would need its own run. Added to the script and Step 2 in `8ddd03b` and `94e191e`.

**The question for the review:**
- Are the fixes right and complete?
- Does any remaining way exist for an exact UTF-8 or ASCII value shown by `git log -p` or `git show` over the range,
  or present in the pushed tree, to get past the check?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push of these 9 commits after the checkpoint;
  - Step 18 item 4.
