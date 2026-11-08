# Output 90: review 95's two fixes

**Review 95 ACCEPTED the push.** Its step had three parts:
- make Step 2's *How* require the Argaam account check, by exact value, before every future push, as an
  owner-controlled checkpoint;
- correct the screenshot wording;
- keep this push's exception.

**What was done** (commit `e419825` on `rebuild`, local only; diff in `review-95-fixes.diff`):

1. **Step 2's *How* in `PROJECT.md`:** a new sentence after the history scan.
   - **The check:** the account name must appear in 0 added lines, commit messages, tracked files and file names of
     the outgoing range.
   - **Why it is the owner's:** the name is not in the repository. It is in the server's nightly log, and the
     permission check refused Claude's read-only read of that line.
   - **What the owner does, before Claude pushes:** either
     - runs three `grep -cF` counts privately and gives the result in chat; or
     - allows that read for Claude.
   - **The rules:** never print or commit the name, and record only the counts. A count above 0 stops the push.
   - **This push:** the exception stands in the Outcome until the owner runs the check.
2. **The PNG wording**, corrected in three places:
   - `other-checks.md` now says the other six were not opened.
   - The changelog entry now reads: 74 of the 82 are the signed-out launch check's; two of the other 8 were opened
     and show no account detail; six were not opened.
   - Output 89's line carries a dated correction note, and its original words are kept.
3. **Kept unchanged:** this push's exception, in the Step 2 *Done (2026-11-08)* entry and in `other-checks.md`'s
   "Not run" section.
4. **Status:** a changelog sub-bullet and one MASTER-PLAN sub-bullet.

**Review 95's DONE WHEN:**
- `git diff --check 64c59e3..e419825` exits 0.
- `git status -sb` reads `## rebuild...origin/rebuild [ahead 3]`.
- Nothing was pushed, deployed or paid for.

**The question for the review:**
- Are the fixes right and complete?
- What is next on the plan? The items still open are all the owner's:
  - Step 7's lawyer handoff;
  - the Argaam count;
  - Step 18 item 4;
  - the push of these 3 local commits, which waits on the Argaam count under the new rule.
