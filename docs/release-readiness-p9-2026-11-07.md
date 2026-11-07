# Release readiness: the P9 fix (2026-11-07)

**The candidate:** commit **`ea51de796cf3bbdbea21a45f35682335eab5a2f8`** on local branch `release/p9-no-statements`,
in its own worktree, `C:/AlphaCouncil-Staging/deploy-p9`.
- **Its parent:** production's `026699b906ea3a513b4f2dbfc37672fa68ee9d42`, which beta also runs.
- **Its one commit:** the reviewed patch `docs/screenshots/p9-no-statements-2026-11-07/p9-fix.patch`, which review 84
  accepted.

**What it fixes:** P9, the second issue in the 2026-11-07 comparison audit.
- **The issue:** advisors invented statement figures when a company's data had none. 51 companies on 2026-11-07 had
  no annual statements, and P9 told them they had "an income statement and a balance sheet" and "one window".
- **The fix:** P9's notes now say plainly what is and is not held, and the room gets a note when the pack holds no
  statement figure. The full record is `docs/p9-no-statements-2026-11-07.md`.
- **What it is:** a missing-data instruction plus the room's existing unverified-figure marking. It does not
  guarantee that a model writes no invented figure; only a paid session could measure that.

## The checks, in the candidate's own tree

`docs/screenshots/p9-release-candidate-2026-11-07/candidate-checks.txt`, made by `candidate-checks-harness.sh`; every
step shows its command and exit code.

| # | Check | Result |
|---|---|---|
| 1 | Branch, commit, parent | `## release/p9-no-statements`, clean; commit `ea51de796cf3…`; parent is production's `026699b906` |
| 2 | What changed from production | exactly `api/app/evidence.py`, `api/app/debate/pack.py`, `api/tests/test_evidence.py`, `api/tests/test_debate.py`; `git diff --check` and `git show --check` exit 0 |
| 3 | The four files' blobs | equal to `rebuild` at `2ee892a`, the code review 84 accepted |
| 4 | The rejected prototype | `presenter.py` absent, `debate_engine` absent from `settings.py`; routers, settings and the whole `web/` tree identical to production |
| 5 | Which code the tests run | `app.evidence` and `app.debate.pack` import from `C:/AlphaCouncil-Staging/deploy-p9/api` |
| 6 | The P9 tests | 21 + 4 passed |
| 7 | The related files and the whole API suite | 153 passed; **602 passed, 11 skipped**, which is production's 578 passed, 11 skipped (review 74) plus the 24 new P9 tests |
| 8 | ruff, each changed file | the same findings on the candidate as on production |
| 9 | Review 83's reproductions and the P9 demonstration | run on the candidate's code, identical to `rebuild`'s outputs |
| 10 | The web | `web/` is production's byte for byte, so no web build, typecheck, lint or test can differ |
| 11 | Pushed or deployed | the branch is not on the remote; beta and production both still run `releases/026699b906` |

## Release, on the owner's go-ahead only

- **Beta first:**
  - **The command:** the exact-commit deploy, as for the sector-standing release:
    ```bash
    cd /c/AlphaCouncil-Staging/deploy-p9 && DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=ea51de796cf3bbdbea21a45f35682335eab5a2f8 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh
    ```
  - **The check before it:** the same command with `--check`. It already passes, read-only
    (`docs/screenshots/p9-release-candidate-2026-11-07/staging-preflight.txt`): the commit equals `DEPLOY_SHA`, and
    it would prune `5c18a3ae46` and keep `026699b906` as the rollback.
  - **The prune:** keeping the 3 newest releases, beta's oldest, `5c18a3ae46`, would be removed. `026699b906` stays
    as the rollback.
- **Then production,** on its own go-ahead, after beta is checked.
- **What a release changes on the site:** nothing visible. P9 is read only by the advisors' room and the Copilot.
  - **Beta's checks:** they can show P9's new notes through `/evidence` (for example 4330, ALFIRDOU, 232 and 8010).
  - **The room's behaviour:** that would need a paid session.

**State now:** nothing is deployed or pushed. Both servers run `026699b906`.
