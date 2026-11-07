# Beta release: the sector-standing fix (2026-11-07)

**What happened:**
- **The go-ahead:** the owner answered "Yes, deploy to beta" to "Deploy the sector-standing fix (026699b906) to beta
  only?".
- **The release:** beta now runs commit **`026699b906ea3a513b4f2dbfc37672fa68ee9d42`** (`release/sector-standing`), as
  `releases/026699b906`. That is today's live `b5655a5` plus the eight-file fix that review 74 accepted
  (`docs/release-request-sector-standing-2026-11-07.md`).
- **Untouched:** production still runs `b5655a5064`. Nothing was pushed, and no model was paid for.

Evidence: `docs/screenshots/sector-standing-beta-2026-11-07/`.

## The deploy, as the request said

1. **The preflight, rerun first:**
   - **The script:** `git diff --quiet c3bcff6 -- scripts/deploy-staging.sh` exited 0, so it is the reviewed one.
   - **The candidate's checkout:** clean, at `## release/sector-standing`, HEAD `026699b906ea3a51…`.
   - **The staging `--check`:** exited 0 and printed the same fields as `deploy-final-check.txt`: the exact commit,
     3,837 paths, prune `2e44ee6fbf` and rollback `releases/b5655a5064 (kept)`.
2. **The deploy command:** the request's own, with nothing added. Log: `deploy-beta.log`, with only trailing spaces
   removed from three build-progress lines.
   ```bash
   cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh
   ```
   - **Upload:** commit `026699b906…`, 519 MB of tar. It took several minutes, limited by this computer's upload
     speed. Beta kept serving `b5655a5064` throughout.
   - **Build:** `npm ci` added 516 packages, `next build` compiled, TypeScript passed, and 93 of 93 static pages were
     generated.
   - **Switch and restart:**
     - **The wait:** the API refused connections for about five seconds while it restarted, so the wait loop retried
       five times.
     - **The result:** `acp-api` and `acp-web` were active, and the API and web both answered 200.
   - **Prune:** `2e44ee6fbf` was removed, as the request said.
   - **Exit:** "deployed 026699b906", exit 0.

## The checks on beta afterwards

All are read-only, through the SSH tunnels to beta's web (`localhost:3201`) and API (`127.0.0.1:8200`), with GET
requests only. Raw output with exit codes is in `beta-checks.txt`, made by `beta-checks-harness.sh`.

| # | Check | Result |
|---|---|---|
| 1 | What runs | beta `releases/026699b906`, releases `026699b906 b5655a5064 5c18a3ae46`, both services active. Production unchanged: `prod/releases/b5655a5064`, releases `b5655a5064 5c18a3ae46 2e44ee6fbf`, both services active |
| 2 | The eight changed files on beta | sha256 equal to the commit's blobs, exit 0 |
| 3 | Every committed file on beta | 3,566 files (all but symlinks), sha256 equal on both sides, exit 0 (`tree-sha256.txt`) |
| 4 | The prototype | `presenter.py` absent; `debate_engine` absent from `settings.py` |
| 5 | The code that serves the values | `git diff --quiet b5655a5 026699b -- api/app/routers web/src` exits 0 |
| 6 | Beta answers | API health `ok`, market data `ok`, 714 tickers as of 2026-11-07. `/home`, `/ar`, `/ar/t/2222/financials` and `/methodology` return 200; `/en` and `/en/…` return 307 to the unprefixed English path, as before |
| 7 | The panel's numbers | equal beta's API for 2222: standings 27.3, 82.1, 74.2 and 45.2, and the metrics 87, 78, 81.4, 57, 69.4, 96.2 and 45.2 |
| 8 | When the candidate's captures were taken | 00:50 UTC, before the nightly's 01:48 UTC refresh (below) |
| 9 | P9's notes (`/evidence`) | "sector standing" once, "sector percentile" none |
| 10 | Production's `--check` for this commit | **exit 0**: "beta now: 026699b906", prune `2e44ee6fbf`, rollback `releases/b5655a5064 (kept)`. It approves nothing |

**The Arabic string check** (`check-arabic.mjs`, signed out, 1440 and 390): 48 Arabic page views, 0 English
strings outside the allow-list, exit 0 (`check-arabic.txt`).

**The captures** (`capture-standing-beta.mjs`, the review-74 script pointed at beta; Chrome at a device scale of 1):
- **The files:** `en-1440-2222.png` and `ar-1440-2222.png` at 1440 × 1000, and `en-390-2222.png` and
  `ar-390-2222.png` at 390 × 844.
- **The record, `viewports.json`:** each capture's innerWidth equals its scrollWidth, so there is no sideways scroll.
  - **The tooltip:** the new one, in each language.
  - **The figures:** "Standing 27 | … | Standing 82 | … | Standing 74 | … | Standing 45" ("الترتيب" in Arabic).
  - **The old labels** ("Sector percentile", المئين): none.
- **The layout:** the same as the reviewed candidate's.

**Why three numbers differ from the candidate's captures** (28 → 27, 82 → 81 on gross margin, 47 → 45):
- **When each was taken:** the candidate's captures were taken at 00:50 UTC (check 8). The pipeline's nightly
  refreshed the fundamentals at 01:48 UTC (`as_of` in check 7).
- **Why it is the data:** the code that computes and serves these numbers is identical in both releases (check 5),
  and the page shows exactly what beta's API returns now (check 7). So the change is the night's data, not the
  release. The fix itself changes no values.

**What could not be checked here:**
- **The room and the Copilot:** their new wording reaches a model only in a paid session. That code is on beta
  byte for byte (checks 2 and 3), and its tests passed in review 74 (578 passed; the focused 129).
- **Production's own database:** not read. Production's API tunnel was refused by the session's permission check,
  and was not needed for the comparison above.

## Production: a separate go-ahead

**What it would do:** run the same exact-commit command against production, from the same checkout:

```bash
cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-production.sh
```

- **Before:** Claude reruns `git diff --quiet c3bcff6 -- scripts/deploy-production.sh` and the same command with
  `--check`. It passes now (check 10).
- **Upload and build:** the same 519 MB upload, to `/opt/alphacouncil-platform/prod/releases/026699b906`, then the
  build on the server. Production keeps serving `b5655a5064` until the switch.
- **Switch:** `prod/current` points at the new release, and `acp-prod-api` and `acp-prod-web` restart.
- **Prune:** production's oldest release, `2e44ee6fbf`, is removed. `b5655a5064` stays as the rollback.
- **Not touched:** nginx, the databases, the pipeline, billing and credentials.
- **After:** the same checks on production through `localhost:3301`.
- **Rollback** (production only):
  ```bash
  ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/prod/releases/b5655a5064 /opt/alphacouncil-platform/prod/current.new && mv -T /opt/alphacouncil-platform/prod/current.new /opt/alphacouncil-platform/prod/current && systemctl restart acp-prod-api acp-prod-web"
  ```

**The beta rollback, if needed before then:** the command in the release request still applies, since
`b5655a5064` is kept on beta.
