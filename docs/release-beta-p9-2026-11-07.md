# Beta release: the P9 fix (2026-11-07)

**What happened:**
- **The go-ahead:** the owner answered "Yes, deploy to beta" to "Deploy the P9 fix (ea51de796c) to beta only?".
- **The release:** beta now runs commit **`ea51de796cf3bbdbea21a45f35682335eab5a2f8`** (`release/p9-no-statements`), as
  `releases/ea51de796c`. That is production's `026699b906` plus the four-file P9 fix that review 84 accepted and review
  85 accepted as a candidate (`docs/release-readiness-p9-2026-11-07.md`).
- **Untouched:** production still runs `026699b906`. Nothing was pushed, and no model was called.

Evidence: `docs/screenshots/p9-beta-2026-11-07/`.

## The deploy, as the readiness report said

1. **The preflight, rerun first** (`preflight-rerun.txt`):
   - **The script:** `git diff --quiet c3bcff6 -- scripts/deploy-staging.sh` exited 0, so it is the reviewed one.
   - **The candidate's checkout:** clean, at `## release/p9-no-statements`, HEAD `ea51de796cf3…`.
   - **The staging `--check`:** exit 0, with the same fields as `staging-preflight.txt`: the exact commit, 3,837
     paths, prune `5c18a3ae46` and rollback `releases/026699b906 (kept)`.
2. **Before the switch:** P9's notes for all 714 tickers were read through the tunnel, GET only, while beta still
   served `026699b906` (`p9-notes-sweep.py`, giving `p9-notes-before.json`, 17:22 to 17:29 UTC).
   - **Which release served them:** `sweep-before-serving.txt` shows `releases/026699b906` both before and after the
     read.
   - **Why:** so that the notes after the release could be compared with them word for word.
3. **The deploy command:** the readiness report's own, with nothing added. The log is `deploy-beta.log`, with only
   trailing spaces and carriage returns removed.
   ```bash
   cd /c/AlphaCouncil-Staging/deploy-p9 && DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=ea51de796cf3bbdbea21a45f35682335eab5a2f8 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh
   ```
   - **Upload:** commit `ea51de796c…`, from 17:21 UTC. Beta kept serving `026699b906` throughout.
   - **Build:** `npm ci` added 516 packages, `next build` compiled, TypeScript passed, and 93 of 93 static pages were
     generated.
   - **Switch and restart:**
     - **The wait:** the API refused connections twice while it restarted, and the wait loop retried.
     - **The result:** `acp-api` and `acp-web` were active, and the API and web both answered 200.
   - **Prune:** `5c18a3ae46` was removed, as the report said.
   - **Exit:** "deployed ea51de796c", exit 0.

## The checks on beta afterwards

All are read-only, through the SSH tunnels to beta's web (`localhost:3201`) and API (`127.0.0.1:8200`), with GET
requests only, and no model is called. Raw output with exit codes is in `beta-checks.txt`, made by
`beta-checks-harness.sh`. Every step exits 0.

| # | Check | Result |
|---|---|---|
| 1 | What runs | beta `releases/ea51de796c`, releases `ea51de796c 026699b906 b5655a5064`, both services active. Production unchanged: `prod/releases/026699b906`, releases `026699b906 b5655a5064 5c18a3ae46`, both services active |
| 2 | What the release changes from production's commit | exactly `api/app/debate/pack.py`, `api/app/evidence.py`, `api/tests/test_debate.py`, `api/tests/test_evidence.py`; `web/` and `api/app/routers` identical |
| 3 | The four changed files on beta | sha256 equal to the commit's blobs |
| 4 | Every committed file on beta | 3,566 files (all but symlinks), sha256 equal on both sides (`tree-sha256.txt`) |
| 5 | The prototype | `presenter.py` absent; `debate_engine` absent from `settings.py` |
| 6 | Beta answers | API health `ok`, market data `ok`, 714 tickers as of 2026-11-07. `/home`, `/ar`, `/t/4330`, `/ar/t/2222/financials`, `/methodology` and `/pricing` return 200 |
| 7 | P9's notes for all 714 tickers, before and after (`p9-notes-compare.py`) | below |
| 8 | What the room is told, from beta's own P9 | below |
| 9 | Production's `--check` for this commit | `deploy-production.sh` equals `c3bcff6`'s; **exit 0**: "beta now: ea51de796c", "prod now: …/026699b906", prune `5c18a3ae46`, rollback `releases/026699b906 (kept)`. It approves nothing |
| 10 | The monitor (`status`, which saves and sends nothing) | 14 checks ok and one with nothing to check (no renewal run since the last round). Production's site, API, services, billing timer, backups, off-server copy, disks (42 %), certificate (75 days) and model credit ($22.85) |

### Check 7: the notes before and after, word for word

The two sweeps read the same 714 tickers, every one answering 200.
- **What was compared:** the statement data's shape is the same in both. 0 tickers differ in statement sections, row
  count, quarter-row count or the number of calculations with a value. The compare script's line "statement data
  itself differs" means exactly these four counts.
- **What was not compared:** the figures themselves, and which years they fall in. The sweeps keep the notes, not the
  values (review 86). So equal counts do not prove identical data.
- **Why the changes are the release's:** every changed note below is one of the texts the fix writes, on a company in
  the group that text is for, and no other note changed. The market data's `as_of` was 2026-11-07 in both sweeps, and
  both ran between two nightly refreshes (17:22 to 17:46 UTC; the nightly runs near 01:50 UTC).

- **Unchanged word for word:** 638 tickers: every company whose income statement covers two years or comes with
  quarters, 2222 among them, and every company with no note about its statements.
- **Changed:** 76 tickers, all of them in one of the groups the fix was written for, in the numbers the 2026-11-07
  sweep found (`docs/p9-no-statements-2026-11-07.md`).
  - **Other notes:** in none of the 76 did any note other than the statement notes change.

| Group | Tickers | Before | After |
|---|---|---|---|
| No statement figure and no quarter | 48 (19 Tadawul tickers from 4330 to 4350, AGTHIA, …, DIDI) | "NO CASH FLOW STATEMENT: … carry an income statement and a balance sheet only" and "ONE INCOME-STATEMENT WINDOW: … the single quarters are the history there is" | "NO FINANCIAL STATEMENTS: the source holds no reported figure …", alone |
| One income-statement year, no quarters | 25 (24 with a window to 2026-06, 8010 to 8311; 8060 to 2026-09) | "… because the source serves a rolling five-quarter grid … the single quarters are the history there is" | "… and it holds no single quarters: this window is the only income history there is" |
| Quarters only | 2 (ALFIRDOU, TAALEEM) | the same two false notes as the first group | "NO ANNUAL STATEMENTS: …", and the quarters' note no longer says "the annual figures above are the sum …" |
| A balance sheet and quarters | 1 (232) | "NO CASH FLOW STATEMENT" and "ONE INCOME-STATEMENT WINDOW" | "NO CASH FLOW STATEMENT: … a balance sheet and single income-statement quarters only" and "NO ANNUAL INCOME STATEMENT: …"; its "NO SECTOR RANKINGS" note is unchanged |

### Check 8: what the room is told

The candidate's own `no_statements_note` (from `C:/AlphaCouncil-Staging/deploy-p9`), run here on beta's P9 for five
companies. That is the note the room's pack puts after its header. No model is called.
- **4330:** the "NO FINANCIAL STATEMENTS IN THIS PACK ([P9] holds no reported statement figure for this company)" note.
- **ALFIRDOU:** the "NO ANNUAL FINANCIAL STATEMENTS IN THIS PACK" note, which keeps its five reported quarters.
- **232, 8010 and 2222:** no pack note, because each has a reported statement figure. Their notes are as in check 7,
  and 2222's are unchanged.

## What could not be checked here

- **The room's and the Copilot's behaviour:** whether the advisors now stop inventing statement figures can only be
  measured in a paid session. The code that tells them is on beta byte for byte (checks 3 and 4), and its tests passed
  in the candidate's own tree (602 passed, 11 skipped).
- **The site:** nothing visible changes. `web/` is production's byte for byte (check 2), and the pages answer 200
  (check 6).

## Production: a separate go-ahead

**What it would do:** run the same exact-commit command against production, from the same checkout:

```bash
cd /c/AlphaCouncil-Staging/deploy-p9 && DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=ea51de796cf3bbdbea21a45f35682335eab5a2f8 bash /c/projects/alphacouncil-platform/scripts/deploy-production.sh
```

- **Before:** Claude reruns `git diff --quiet c3bcff6 -- scripts/deploy-production.sh` and the same command with
  `--check`.
  - **Review 86 accepted the beta release.** The preflight was rerun at 18:00 UTC as its DONE WHEN, and each step exits
    0 (`production-preflight.txt`): the script equals `c3bcff6`'s, HEAD equals `DEPLOY_SHA`, beta runs `ea51de796c`,
    production runs `026699b906`, and the `--check` would prune `5c18a3ae46` and keep `026699b906`.
  - **It is run once more before the deploy itself.**
- **Upload and build:** the same upload, to `/opt/alphacouncil-platform/prod/releases/ea51de796c`, then the build on
  the server. Production keeps serving `026699b906` until the switch.
- **Switch:** `prod/current` points at the new release, and `acp-prod-api` and `acp-prod-web` restart.
- **Prune:** production's oldest release, `5c18a3ae46`, is removed. `026699b906` stays as the rollback.
- **Not touched:** nginx, the databases, the pipeline, billing and credentials.
- **After:** the same checks on production, read-only: the files against the commit, the services, the pages and the
  monitor. Production's API tunnel was refused by the session's permission check on 2026-11-07, so P9's notes on
  production itself cannot be read from here. Production's code that writes them would be the same bytes as beta's,
  which check 7 covers.
- **Rollback** (production only):
  ```bash
  ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/prod/releases/026699b906 /opt/alphacouncil-platform/prod/current.new && mv -T /opt/alphacouncil-platform/prod/current.new /opt/alphacouncil-platform/prod/current && systemctl restart acp-prod-api acp-prod-web"
  ```

**The beta rollback, if needed:**
```bash
ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/releases/026699b906 /opt/alphacouncil-platform/current.new && mv -T /opt/alphacouncil-platform/current.new /opt/alphacouncil-platform/current && systemctl restart acp-api acp-web"
```
