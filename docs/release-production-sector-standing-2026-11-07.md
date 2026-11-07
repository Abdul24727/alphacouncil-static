# Production release: the sector-standing fix (2026-11-07)

**What happened:**
- **The go-ahead:** the owner answered "Yes, deploy to production" to "Deploy the sector-standing fix (026699b906) to
  production?". It came after review 77 accepted the beta release.
- **The release:** alphacouncil.tech now runs commit **`026699b906ea3a513b4f2dbfc37672fa68ee9d42`**
  (`release/sector-standing`) as `prod/releases/026699b906`. That is the same commit beta runs.
- **Not done:** nothing was pushed, and no model was paid for.

Evidence: `docs/screenshots/sector-standing-prod-2026-11-07/`.

## The deploy

1. **The preflight first:**
   - `git diff --quiet c3bcff6 -- scripts/deploy-production.sh` exited 0.
   - The checkout was clean at `## release/sector-standing`.
   - The exact-commit `--check` exited 0, with the same fields as review 77's `production-preflight.txt`: beta now
     `026699b906`, prod now `b5655a5064`, prune `2e44ee6fbf`, rollback `releases/b5655a5064 (kept)`.
2. **The command** (from `docs/release-beta-sector-standing-2026-11-07.md`, with nothing added):
   ```bash
   cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-production.sh
   ```
   Log: `deploy-production.log`, with only trailing spaces removed. Its secret scan found 8 hits, all route names
   (`/forgot-password`, `/reset-password`).
   - **Upload and build:** the commit was uploaded and built. `npm ci` added 516 packages, and `next build` passed.
     The live site served `b5655a5064` until the switch.
   - **Switch and restart:**
     - **The wait:** the API refused connections for a few seconds while it restarted, so the wait loop retried
       twice.
     - **The result:** `acp-prod-api` and `acp-prod-web` were active, and the API and web answered 200.
   - **Prune:** production's oldest release, `2e44ee6fbf`, was removed.
   - **Exit:** "deployed 026699b906 to production", exit 0.

## The checks afterwards

All are read-only. The live pages are read at https://alphacouncil.tech with GET requests, signed out. The server is
read over read-only ssh.

**`prod-checks.txt`** (made by `prod-checks-harness.sh`, with exit codes):

| # | Check | Result |
|---|---|---|
| 1 | What runs | production `prod/releases/026699b906`, releases `026699b906 b5655a5064 5c18a3ae46`, both services active. Beta: `releases/026699b906`, both active |
| 2 | The eight changed files on production | sha256 equal to the commit, exit 0 |
| 3 | Every committed file on production | all 3,566 equal by sha256 to the commit's manifest (`../sector-standing-beta-2026-11-07/tree-sha256.txt`), exit 0 |
| 4 | The prototype | `presenter.py` absent; `debate_engine` absent |
| 5 | The live site | `/`, `/home`, `/ar`, `/methodology`, `/pricing`, `/t/2222/financials` and `/ar/t/2222/financials` return 200 |
| 6 | The live wording | `/t/2222/financials`: "Sector percentile" 6 → **0**, "Sector standing" 0 → **6**. `/ar/t/2222/financials`: "المئين" 8 → **0**, "الترتيب داخل القطاع" 0 → **2**. The "before" counts are in `before-labels.txt`, read at 09:45 UTC while production still ran `b5655a5064` |

**Across the public pages:**
- **The pages:** `/methodology`, `/pricing`, `/t/2222` and `/home`, in English and Arabic.
- **The old phrases:** none of them carries "Sector percentile" or "المئين".
- **The bare word "percentile":** it remains only as the message key `"percentile"`, whose value is the new text.
  Visitors never see it.

**The Arabic string check** (`check-arabic.mjs`, signed out, 1440 and 390): 48 Arabic page views, 0 English
strings outside the allow-list, exit 0 (`check-arabic.txt`).
- **Rerun after review 78:** it was rerun at 10:17 UTC with the same result. Review 78 noted that the first output
  did not show which site it read. The file now begins with its exact command:
  `BASE_URL=https://alphacouncil.tech WIDTHS=1440,390 node scripts/check-arabic.mjs`.

**The monitor** (`monitor-status.txt`, the `status` mode, which only reads; read at 10:02 UTC):
- **All 15 checks are ok:** the site and API, market data, both services, the renewals job, timer and Moyasar, the
  backups, the disks, the certificate, and the model account ($22.85 left).
- **Renewals:** "Moyasar for renewals" now reads ok ("the run at 2026-11-07 10:00 UTC … reached Moyasar"). It showed
  "–" at the last launch check.
- **Alerts:** the two emailed in the last 24 hours were sent on 2026-11-06 at 11:15 and 15:20 UTC (the credit alert
  and its all-clear). None came from today's restart, and no check is failing.

**The Fundamentals panel on production is Pro-only for a signed-out visitor** (`signed-out-panel.txt`, from
`signed-out-panel.mjs`):
- **What a visitor sees:** in en and ar, at 1440 and 390, the panel reads "This is part of AlphaCouncil Pro" /
  "هذه الميزة جزء من اشتراك برو". It shows no standings, no old label, and no sideways scroll.
- **Why the captures were not taken:** the beta capture script, pointed at production, timed out waiting for a
  standing, for this reason. It was not kept.
- **Where the rendered panel is shown:** beta captured it with the new labels in both languages and widths
  (`../sector-standing-beta-2026-11-07/`). Production's files equal beta's commit by hash (checks 2 and 3), and the
  served pages carry the new strings (check 6).
- **The gap:** a Pro member's view of the live panel is the one view not captured here. Claude makes no accounts on
  the live site. The owner, signed in, can confirm it on https://alphacouncil.tech/t/2222/financials.

**Step 10's signed-out checks, rerun on this release:** `docs/launch-check-2026-11-07.md`.

## Rollback (production only)

`b5655a5064` is kept on both tiers.

```bash
ssh root@alphacouncil.tech "ln -sfn /opt/alphacouncil-platform/prod/releases/b5655a5064 /opt/alphacouncil-platform/prod/current.new && mv -T /opt/alphacouncil-platform/prod/current.new /opt/alphacouncil-platform/prod/current && systemctl restart acp-prod-api acp-prod-web"
```
