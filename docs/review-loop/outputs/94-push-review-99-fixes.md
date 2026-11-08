# Output 94: review 99's fix: the exact-value check fails closed

**Review 99 said FIX.** It reproduced a failing `sort` returning three zeros and exit 0 with a dummy value in the
outgoing patch.

**What was done** (commit `2e98f72` on `rebuild`, local only; diff in `review-99-fixes.diff`):

1. **Every step is checked:**
   - the script runs under `set -o pipefail`;
   - every command and pipeline ends in `|| fail`, which means exit 2;
   - `count()` checks both stages' statuses through `PIPESTATUS`: grep must give 0 or 1, and wc must give 0;
   - every count must be a number, or the script exits 2.
2. **Checks done in bash, not by the tools they check**, guard against a tool that exits 0 with too little output:
   - **Snapshots:** the list is built from a bash associative array of the range, boundary and tip commits. It is
     re-read and its length compared.
   - **The tip:** every blob in the tip's `ls-tree -r` must be in the deduplicated blob list.
   - **The dumps:** each `git cat-file --batch` dump (commits and blobs) must be exactly as long as the sizes from
     `--batch-check` say. That is, for each object, its header, its content and one newline, summed in bash.
   - **Names:** the name list must hold at least as many entries as the tip has.
   - **Positive control:** before any zero is believed, both searches must find the value exactly once in a copy of
     itself. That covers the content search (`grep -o | wc -l`) and the name search (`grep -c`).
   - **The value file:** it is now read with `mapfile`, not `grep`.
3. **The tests:** 69 pass (`count-script-test.txt`).
   - **Kept:** the 27 earlier cases.
   - **New:** 42 injected failures.
     - **The tools:** `sort`, `awk`, `sed`, `tr`, `grep`, `wc` and `mktemp`, each replaced first on PATH for one run.
     - **Three ways:** it fails (exit 1, no output); it is silent (exit 0, no output); or it is "late" (it runs the
       real tool, then exits 1).
     - **Two values:** each run uses a value present and one absent.

     All 42 give exit 2.
4. **Against the previous version (`94e191e`), with a dummy value in the patch** (the table in
   `count-script-test.txt`):
   - **Failing open before:** a failing or silent `sort` or `awk` gave exit 0.
   - **Exit 3 without reporting the failure:** several "late" cases.
   - **Now:** all 21 tool cases give exit 2, each with its reason.
5. **Smoke runs on this repository, over `eeb9a9d..dcc4189`:**
   - **Time:** about 18 s.
   - **An absent value:** three zeros, exit 0.
   - **"moyasar":** `0 / 5261 / 3`, exit 3.
   - **A bad ref:** exit 2.
6. **Step 2** now says the check fails closed and lists the checks.
7. **Command output** (`git-state-94.txt`):
   - `git diff --check 94e191e..2e98f72` exits 0.
   - `bash -n` passes for both scripts.
   - The branch is `[ahead 10]`, with a clean tree before this output.
   - The remote's `rebuild` is still `dcc4189`.
   - bash is 5.3.

**Still outside what it can guard:**
- the documented limits (images, compressed files, encoded forms, Unicode normalisation);
- git itself returning wrong data with exit 0;
- a tool that returns *wrong* output rather than failing or returning too little.

**The question for the review:**
- Is the fix right and complete?
- Does any remaining path give exit 0 when the value is present in what the range shows or publishes?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push of these commits after the checkpoint;
  - Step 18 item 4.
