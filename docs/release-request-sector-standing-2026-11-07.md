# Release request: the sector-standing fix to beta (2026-11-07)

**The request:** release candidate **`026699b906ea3a513b4f2dbfc37672fa68ee9d42`** (branch `release/sector-standing`)
to **beta only**. Production is a separate request, after the beta checks.

**What it is:**
- **The code:** today's live release `b5655a5064` plus the sector-standing fix (two commits: `cae5578` and
  `026699b`), eight files in all.
- **What it does:** the site's "Sector percentile" / "P23" becomes "Sector standing", with a tooltip that higher is
  better on every measure, in English and Arabic. The advisors' room and the Copilot are told the same. No market
  value changes.
- **What it leaves out:** none of the rejected analyst-and-presenter prototype.
- **The reviewer:** it accepted the candidate in review 74.

## Validation (already run, not repeated)

`docs/release-readiness-sector-standing-2026-11-07.md` covers it:
- **The candidate's own tree:**
  - **The API:** 578 tests passed and the focused tests 129, and lint is identical to production in every changed file.
  - **The web:** the build passes, and typecheck, lint and 68 of 68 tests are clean.
- **The screenshots:** native, en and ar at 1440 and 390 px, with no sideways scroll, in
  `docs/screenshots/sector-standing-2026-11-07/` with `viewports.json`.
- **The git checks** (raw, with exit codes): `docs/screenshots/sector-standing-2026-11-07/candidate-git-raw.txt`.
  `git show --check` passes for all four commits, `git diff --check b5655a5 026699b` exits 0, `git status -sb` reads
  `## release/sector-standing`, and the name-status lists exactly the eight files.

## Deployment preflight (read-only; nothing uploaded)

**Why the scripts needed a change:** `scripts/deploy-staging.sh` and `scripts/deploy-production.sh` refused any
branch but `rebuild`. That `rebuild` tree carries the rejected prototype, so it must not ship. The scripts now take
another reviewed branch only when it is named explicitly. They also gained a read-only `--check` mode, which says what
would be deployed and from where, then stops. The default behaviour is unchanged.

**The four runs** (`docs/screenshots/sector-standing-2026-11-07/deploy-preflight.txt`):
1. **`rebuild`, no opt-in:** behaves as before.
2. **The candidate's checkout, no opt-in:** **refuses** (exit 1).
3. **The candidate's checkout with `DEPLOY_BRANCH=release/sector-standing`:**
   - **What it reports:** checkout `C:/AlphaCouncil-Staging/deploy-026699b`, HEAD `026699b906ea3a…`, release
     `/opt/alphacouncil-platform/releases/026699b906`.
   - **What it would ship:** only committed files from that HEAD.
4. **The production check:** it reports that a deploy would **refuse** until beta runs the same HEAD.

## What the beta deploy does

Run from `C:/AlphaCouncil-Staging/deploy-026699b`:
`DEPLOY_BRANCH=release/sector-standing bash <rebuild>/scripts/deploy-staging.sh`
- **Upload:** it uploads that HEAD to `releases/026699b906` and builds it on the server (pip, `npm ci`,
  `next build`).
- **Switch:** it switches beta's `current` symlink and restarts beta's api and web, then waits for both to answer.
- **Prune:** it keeps the 3 newest beta releases, so beta's oldest, `2e44ee6fbf`, is removed. **`b5655a5064` stays,
  as the rollback.**
- **Not touched:** production, its database, nginx, the pipeline and any credentials.

**After it:** the beta checks are repeated on the live beta site (api and web health, the Fundamentals panel in en and
ar at 1440 and 390). Then a separate request for production follows, which deploys the same HEAD once beta runs it.

**Rollback:** point beta's `current` back to `releases/b5655a5064` and restart `acp-api acp-web`.

**State now:** beta and production both run `b5655a5064` (`deploy-preflight.txt`, "beta now" and "prod now"). **Beta
has not been deployed**, pending the owner's go-ahead.
