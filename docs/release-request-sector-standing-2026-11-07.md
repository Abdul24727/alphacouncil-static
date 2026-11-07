# Release request: the sector-standing fix to beta (2026-11-07, amended after review 75)

**The request:** release commit **`026699b906ea3a513b4f2dbfc37672fa68ee9d42`** (branch `release/sector-standing`)
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

## The deploy scripts ship only the approved commit

`scripts/deploy-staging.sh` and `scripts/deploy-production.sh` on `rebuild` (as committed in `c3bcff6`):
- **The branch:** a branch other than `rebuild` is taken only when it is named in `DEPLOY_BRANCH`.
- **The commit:** that branch also needs `DEPLOY_SHA`, the full 40-character approved commit. HEAD must be exactly that
  commit. The script archives and builds the commit it checked, and does not read HEAD again.
- **The default:** with no `DEPLOY_*` set, `rebuild` deploys as before. `DEPLOY_SHA` may also pin a `rebuild` deploy.
- **`--check`:** it only reads the server. Both scripts report the checkout, the commit, the release path, which
  releases a deploy would prune, and the rollback release.
  - **Staging's check** also gives the archive's path count and what beta runs.
  - **Production's check** also gives what beta and production run, and no archive count.
  - **When it fails:** it exits 1 when a deploy would refuse, including production's check while beta runs another
    commit.
  - **A passing check approves nothing.**

**The preflight** (`docs/screenshots/sector-standing-2026-11-07/deploy-preflight.txt`, made by
`deploy-preflight-harness.sh` beside it), every case with its exit code:

| Case | Result |
|---|---|
| `rebuild`, default, staging `--check` | exit 0, as before |
| the candidate with `DEPLOY_BRANCH` and the exact `DEPLOY_SHA`, staging `--check` | **exit 0**, commit `026699b906…`, 3,837 paths, release `releases/026699b906` |
| the candidate without `DEPLOY_BRANCH` | refused, exit 1 |
| the candidate with `DEPLOY_BRANCH` but no `DEPLOY_SHA` | refused, exit 1 |
| a short `DEPLOY_SHA` (`026699b`) | refused, exit 1 |
| a wrong full `DEPLOY_SHA` (`b5655a5…`) | refused, exit 1 |
| a different branch (`rebuild`'s checkout with the candidate's settings) | refused, exit 1 |
| an advanced HEAD (a throwaway clone whose `release/sector-standing` is one commit past `026699b`) | refused, exit 1 |
| `rebuild` pinned to a wrong `DEPLOY_SHA` | refused, exit 1 |
| the same refusals on the deploy path itself, without `--check`, aimed at an unreachable host | each refused, exit 1, before `== upload` |
| production `--check` for the candidate, while beta runs `b5655a5064` | **exit 1**, "NOT READY: beta runs b5655a5064, not 026699b906" |
| production `--check`: no `DEPLOY_SHA`; advanced HEAD; `rebuild` | exit 1 each |

**Afterwards, read-only:**
- **What runs:** beta and production both run `b5655a5064`, and all four services are active.
- **The release lists:** both tiers hold `b5655a5064 5c18a3ae46 2e44ee6fbf`, the same as before.

## What the beta deploy does, if the owner says go

**First, Claude reruns the same command with `--check` and confirms the script is unchanged:**

```bash
git -C /c/projects/alphacouncil-platform diff --quiet c3bcff6 -- scripts/deploy-staging.sh
```

```bash
cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh --check
```

**Then the deploy, in Git Bash, the same command without `--check`:**

```bash
cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh
```

- **Upload:** it uploads commit `026699b906ea3a513b4f2dbfc37672fa68ee9d42` to
  `/opt/alphacouncil-platform/releases/026699b906` and builds it on the server (pip, `npm ci`, `next build`). Nothing
  is pushed.
- **Switch:** it switches beta's `current` symlink and restarts beta's `acp-api` and `acp-web`, then waits for both to
  answer.
- **Prune:** it keeps the 3 newest beta releases, so it **removes `2e44ee6fbf`**, beta's oldest. **`b5655a5064` stays,
  as the rollback**, and so does `5c18a3ae46`.
- **Not touched:** production, its database, nginx, the pipeline and any credentials.

**After it:**
- **The beta checks are repeated on the live beta site:** api and web health, and the Fundamentals panel in en and ar
  at 1440 and 390.
- **Production stays a separate request.** It needs its own go-ahead, and its `--check` must pass first, which it
  does only once beta runs `026699b906`.

**Rollback** (beta only), the script's own switch pointed back:

```bash
ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/releases/b5655a5064 /opt/alphacouncil-platform/current.new && mv -T /opt/alphacouncil-platform/current.new /opt/alphacouncil-platform/current && systemctl restart acp-api acp-web"
```

**State now:** beta and production both run `b5655a5064`. **Nothing has been deployed or pushed**, pending the owner's
go-ahead.
