# Production release: the P9 fix (2026-11-07)

**What happened:**
- **The go-ahead:** the owner answered "Yes, deploy to production" to "Deploy the P9 fix (ea51de796c) to
  production?". It came after review 86 accepted the beta release (`docs/release-beta-p9-2026-11-07.md`).
- **The release:** alphacouncil.tech now runs commit **`ea51de796cf3bbdbea21a45f35682335eab5a2f8`**
  (`release/p9-no-statements`) as `prod/releases/ea51de796c`. That is the same commit beta runs: production's previous
  `026699b906` plus the four-file P9 fix.
- **Not done:** nothing was pushed, and no model was called.

Evidence: `docs/screenshots/p9-production-2026-11-07/`.

## The deploy

1. **The preflight, rerun after the go-ahead** (`preflight-rerun.txt`, 19:21:58 UTC):
   - `git diff --quiet c3bcff6 -- scripts/deploy-production.sh` exited 0, so the script is the reviewed one.
   - The checkout was clean at `## release/p9-no-statements`, and HEAD equals `DEPLOY_SHA`.
   - Beta ran `ea51de796c`; production ran `026699b906`, releases `026699b906 b5655a5064 5c18a3ae46`; all four services
     were active.
   - The exact-commit `--check` exited 0, with the same fields as review 86's `production-preflight.txt`: prune
     `5c18a3ae46`, rollback `releases/026699b906 (kept)`.
2. **The command** (from `docs/release-beta-p9-2026-11-07.md`, with nothing added):
   ```bash
   cd /c/AlphaCouncil-Staging/deploy-p9 && DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=ea51de796cf3bbdbea21a45f35682335eab5a2f8 bash /c/projects/alphacouncil-platform/scripts/deploy-production.sh
   ```
   Log: `deploy-production.log`, with only trailing spaces and carriage returns removed. A keyword scan for credentials
   (`grep -i -E 'password|secret|token|key='`) finds 8 lines, all route names (`/forgot-password`, `/reset-password`),
   as last time.
   - **Upload and build:** from 19:22:44 UTC. `npm ci` added 516 packages, `next build` compiled, TypeScript passed,
     and 93 of 93 static pages were generated. The live site served `026699b906` until the switch.
   - **Switch and restart:**
     - **The wait:** the API refused connections three times on the server's own port 8300 while it restarted, and the
       script's wait loop retried.
     - **The result:** `acp-prod-api` and `acp-prod-web` were active, and the API and web answered 200.
   - **Prune:** production's oldest release, `5c18a3ae46`, was removed, as the `--check` said.
   - **Exit:** "deployed ea51de796c to production", exit 0, at 19:35:11 UTC.

## The checks afterwards

All are read-only. The live site is read at https://alphacouncil.tech with GET requests, signed out. The server is
read over read-only ssh. No model is called.

**`prod-checks.txt`** (made by `prod-checks-harness.sh` at 19:35:28 UTC; every step with an exit code exits 0):

| # | Check | Result |
|---|---|---|
| 1 | What runs | production `prod/releases/ea51de796c`, releases `ea51de796c 026699b906 b5655a5064`, both services active. Beta: `releases/ea51de796c`, the same releases, both active |
| 2 | The running processes | `acp-prod-api` and `acp-prod-web` started at 19:34:54 UTC, at the deploy's restart, each with its working folder in `prod/releases/ea51de796c` (`api` and `web`) |
| 3 | What the release changes from production's previous commit | exactly `api/app/debate/pack.py`, `api/app/evidence.py`, `api/tests/test_debate.py`, `api/tests/test_evidence.py`; `web/` and `api/app/routers` identical |
| 4 | The four changed files on production | sha256 equal to the commit's blobs |
| 5 | Every committed file on production | all 3,566 equal by sha256 to the commit's manifest (`../p9-beta-2026-11-07/tree-sha256.txt`) |
| 6 | The prototype | `presenter.py` absent; `debate_engine` absent from `settings.py` |
| 7 | The live site | `/`, `/home`, `/ar`, `/t/4330`, `/t/2222/financials`, `/ar/t/2222/financials`, `/methodology`, `/pricing` and `/api/v1/health` return 200. Health: `ok`, market data `ok`, 714 tickers as of 2026-11-07 |
| 8 | The evidence endpoint | still Pro-only for a signed-out reader: `403 {"detail":"pro_required"}` |
| 9 | The monitor (`status`, which saves and sends nothing) | 14 checks ok and one with nothing to check ("Moyasar for renewals": no renewal run since the last round). The site and API, market data, both services, the renewals job and timer, the backups and their off-server copy, the disks (42 %), the certificate (75 days) and the model account ($22.85). No alert was emailed in the last 24 hours |

**Step 10's signed-out checks, rerun on this release** (`launch-check/`, from `run-launch-check.sh`):
- **How:** the same scripts and settings as this morning's run on `026699b906` (`docs/launch-check-2026-11-07.md`),
  against https://alphacouncil.tech, signed out, GETs only. No account, session or form.
- **Screenshots:** they went to a scratch folder outside the repository, because `web/` is unchanged (check 3). Only
  the text outputs are kept. In them, that folder's path is shortened to `<scratch>`.

| Script | Summary line | Result | This morning |
| --- | --- | --- | --- |
| `check-seo.mjs` | "ALL PASS" | 62 PASS, 0 FAIL | the same |
| `check-arabic.mjs` (`WIDTHS=1440,390`) | "48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list" | PASS | the same |
| `check-advisors.mjs` (`VISITOR=1`, never convenes the room) | "all passed" | 24 PASS, 0 FAIL | the same |
| `check-data-fixes.mjs` (`SWEEP=1`) | "all passed" | 44 PASS, 0 FAIL, 1 INFO; sweep 714 tickers, `eps_bad` 0, `vt_reason` 0, `news_green_old` 0, `no_currency` 8 | the same sweep line, field for field |
| `page-shots.mjs` (five pages × two languages × two widths) | "20 views; every one 200 with no sideways scroll" | PASS | the same |

**A connection drop during the first run** (`run.txt`, `rerun.txt`):
- **What happened:** at about 19:39 UTC, `check-data-fixes.mjs` stopped on `ECONNRESET` after 42 PASS and 0 FAIL, and
  `page-shots.mjs` on `ERR_CONNECTION_TIMED_OUT`. Their outputs are kept as `check-data-fixes-attempt1.txt` and
  `pages-attempt1.txt`. Two ssh connections from this computer timed out too, at 19:39:50 and about 19:40:40, with
  a successful one at 19:40:13 between them.
- **What the server shows** (read-only ssh, `connection-drop.txt`):
  - no nginx error and no 5xx response from 19:36 to 19:41, and no fail2ban action;
  - the services stayed active, and the server has been up 21 days;
  - its own monitor's rounds at 19:35 and 19:40 each logged "15 of 15 checks ok".
- **Why it happened:** not known. Connections between this computer and the server failed on and off from about 19:39
  to 19:41 UTC, and the cause is not visible on the server. nginx logged 1,332 requests in the minute of 19:38,
  while the sweep ran; during this morning's run it logged up to 967 a minute without trouble.
- **What this does not show:** whether visitors elsewhere could reach the site in that minute. The monitor checks the
  site from the server itself.
- **The rerun:** both scripts were rerun unchanged from 19:41 to 19:47 UTC, and both passed (above).

## What could not be checked here

- **P9's notes on production itself:** production's evidence endpoint is Pro-only (check 8), Claude makes no accounts
  on the live site, and the session's permission check refused a tunnel to production's API earlier on 2026-11-07. So
  the notes were not read on production. What stands in for it:
  - **The code:** production's files are the commit's byte for byte (checks 4 and 5), and the running processes were
    started from them (check 2).
  - **The comparison:** beta runs the same commit, and its notes were compared word for word for all 714 tickers before
    and after (`docs/release-beta-p9-2026-11-07.md`, check 7).
  - **The data:** production's accounts database is its own.
    - **Its market-data settings** (`EVIDENCE_DB` and the rest): the deploy script is written to copy beta's when it
      first creates production's settings file, and leaves an existing file alone (`scripts/deploy-production.sh`,
      lines 79–99). `docs/production.md` records "the same files, read-only".
    - **Not established:** that the copy ran, since no output of that first setup is on record, and that the two
      tiers' settings match today, since they sit in a file with credentials.
    - **So:** it is not established that production's notes equal beta's (reviews 88 and 89). *(Corrected after review 87: this line said production "has its own database"
    for its notes, which is true only of its accounts.)*
- **The room's and the Copilot's behaviour:** whether the advisors now stop inventing statement figures can only be
  measured in a paid session, and none was run.
- **The site:** nothing visible changes. `web/` is the previous release's byte for byte (check 3).

## Review 87

**ACCEPTED** (`docs/review-loop/replies/87-p9-fix-released-to-production-ea51de796c.md`). Its three notes are
non-blocking, and the record already states each:
- **The advisors' behaviour on production is not proven.** It stays open until an owner-authorised paid test.
- **The 19:39 connection drop is unexplained.** The incident is kept here, to be looked into if it recurs.
- **Some scripts were not attached.** The deploy script and the `check-*.mjs` scripts were not in the review's
  bundle, so it could not audit them.

**Its next step:** a read-only check that the lawyer pack still matches the live site.

## Rollback (production only)

`026699b906` is kept on both tiers.

```bash
ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/prod/releases/026699b906 /opt/alphacouncil-platform/prod/current.new && mv -T /opt/alphacouncil-platform/prod/current.new /opt/alphacouncil-platform/prod/current && systemctl restart acp-prod-api acp-prod-web"
```
