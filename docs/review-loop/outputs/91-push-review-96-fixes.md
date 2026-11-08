# Output 91: review 96's fixes to Step 2's Argaam check

**Review 96 said FIX.** It made two points about the new Step 2 sentence, and a third about evidence:
1. "The name is not in this repository" is not established.
2. The raw commands could print file names, or print nothing instead of 0, and `git ls-files` reads the index.
3. The git claims needed command output.

**What was done** (commit `9dbf448` on `rebuild`, local only; diff in `review-96-fixes.diff`):

1. **The overclaim** (`PROJECT.md`, Step 2 *How*):
   - **New wording:** Claude has no trusted copy of the name from the repository, so whether it is absent from what a
     push publishes stays unverified until the check runs.
   - **The trusted value:** it is in the server's nightly log, which Claude's read-only read was refused.
2. **The commands:** replaced by `scripts/push-checks/count-exact-value.sh <range> <value-file>`.
   - **Input:** it reads the value from a file, never the command line. It refuses an empty value, more than one line,
     or fewer than 3 characters, because an empty `grep -f` line would match everything. It strips a trailing CR.
   - **Output:** exactly `history <n>` (`git log -p <range>`: patches, messages, authors), `tracked-files <n>`
     (`git grep -c` at the tip, summed, so no file names are printed) and `file-names <n>` (from
     `git ls-tree -r --name-only <tip>`, not the index).
   - **Matching:** case-insensitive.
   - **Exit codes:** 0 only when all three counts are 0; 3 when any is not; 2 on bad input or any git error, with
     every git step's exit status checked.
   - **Step 2's rule:** anything but three explicit zeros (exit 0) stops the push.
3. **The test:** `scripts/push-checks/test-count-exact-value.sh` passes 14 cases with a dummy value in a throwaway
   repository (`count-script-test.txt`).
   - **Absent value:** three zeros.
   - **Present value:** nonzero counts, exit 3; the value and file names are not printed; exactly three lines.
   - **Edge cases:** a value only in a commit message is counted; a CRLF value file works.
   - **Errors, exit 2:** a bad range start, a bad tip, a non-range, and missing, empty, blank or two-line value
     files.
   - **Smoke runs on this repository:**
     - an absent value: `0 0 0`, exit 0;
     - "moyasar", known to be present: `91 / 521 / 3`, exit 3;
     - a bad ref: exit 2.
4. **This push's exception is kept.** It is still recorded as unresolved in Step 2's *How* and Outcome, and in
   `other-checks.md`'s "Not run" section. The owner's Option 1 there now uses the script, and a note records the old
   commands.
5. **Command output** (`git-state-91.txt`):
   - `git diff --check e419825..9dbf448` exits 0.
   - `git status -sb` reads `[ahead 4]`, and the tree is clean.
   - The 4 local commits are listed.
   - The remote's `rebuild` is still `dcc4189`, by anonymous `ls-remote`, so nothing was pushed.
   - Both scripts are mode 100755.

**The question for the review:**
- Are the fixes right and complete?
- What is next on the plan? The items still open are all the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push of these 4 commits after the checkpoint;
  - Step 18 item 4.
