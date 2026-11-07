# Output 79: the P9 fix-only release candidate (review 84's step)

**The candidate:** commit `ea51de796cf3bbdbea21a45f35682335eab5a2f8` on local branch `release/p9-no-statements`,
built in its own worktree, `C:/AlphaCouncil-Staging/deploy-p9`.
- **Its parent:** production's `026699b906ea3a513b4f2dbfc37672fa68ee9d42`, which beta also runs.
- **Its one commit:** the reviewed `p9-fix.patch`, applied with `git apply`.
- **The record:** `docs/release-readiness-p9-2026-11-07.md`, committed on `rebuild` as `3416ce2`.
- **Not done:** nothing was pushed, deployed or paid for.

**Review 84's DONE WHEN** (`candidate-checks.txt`, from `candidate-checks-harness.sh`; each step has its command
and exit code):
1. **Based on production:** the candidate's parent is `026699b906` (step 1), and
   `git diff --name-status 026699b906 HEAD` lists exactly the four P9 files (step 2).
2. **Whitespace:** `git diff --check 026699b906 HEAD` and `git show --check HEAD` exit 0 (step 2).
3. **The blobs:** the four files' blobs equal `rebuild`'s at `2ee892a`, the code review 84 accepted (step 3). The zip
   holds the candidate's four files and production's four, so they can be recomputed.
4. **The reproductions and the P9 tests, on the candidate:**
   - **The P9 tests:** 21 + 4 passed (step 6).
   - **Review 83's reproductions and `p9-after.py`:** run on the candidate's code, both outputs are identical to
     `rebuild`'s (step 9).
   - **Which code ran:** the tests import `app` from the candidate's own tree (step 5).
5. **The complete API suite and the applicable checks:**
   - **The related files:** 153 passed (step 7).
   - **The whole suite:** 602 passed, 11 skipped. That is production's 578 passed, 11 skipped (review 74's figure
     for the same base) plus the 24 new P9 tests.
   - **ruff:** the same findings as production in each changed file (step 8).
   - **The web:** `web/` is production's byte for byte, so no web check can differ (step 10).
   - **The staging preflight:** `--check` with `DEPLOY_SHA` passes (`staging-preflight.txt`). The commit equals
     `DEPLOY_SHA`, and it would prune `5c18a3ae46` and keep `026699b906` as the rollback.
6. **The prototype and the deployment state:**
   - **The prototype:** `presenter.py` is absent, `debate_engine` is absent, and routers, settings and `web/` are
     identical to production (step 4).
   - **Pushed or deployed:** the branch is not on the remote, and both servers run `026699b906` (step 11).

**Attachments:** this prompt and one zip:
- the report;
- `candidate-checks.txt` and its harness;
- `staging-preflight.txt`;
- the candidate commit as a patch (`candidate-ea51de796c.patch`);
- `candidate/` and `production/`, each with the four files' bytes.

**The question for the review:** is the candidate ready to be put to the owner for a beta release?
