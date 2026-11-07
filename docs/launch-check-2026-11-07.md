# Launch check, signed out, on production `026699b906` (2026-11-07)

**Why:** this is Step 10's signed-out half, run again after the sector-standing release reached production today
(`docs/release-production-sector-standing-2026-11-07.md`). That way the site the lawyer will test is checked as it
stands.

**How it ran:**
- **The command:** `docs/screenshots/launch-2026-11-07/run-launch-check.sh`, from `web/` against
  `https://alphacouncil.tech`, 10:01–10:08 UTC.
- **The same as last time:** the scripts and settings are those of `docs/launch-check-2026-11-06.md`. The page-shots
  script is now kept beside its output.
- **Signed out:** no account was made, no session was run, no form was submitted, and nothing was paid for.
- **The output:** `docs/screenshots/launch-2026-11-07/`. Each `.txt` ends with its exit code.

| Script | How | Summary line | Result |
| --- | --- | --- | --- |
| `check-seo.mjs` | `SHOTS_DIR=…/seo` | **"ALL PASS"**, 62 PASS, 0 FAIL | PASS (`check-seo.txt`, 12 screenshots in `seo/`) |
| `check-arabic.mjs` | `WIDTHS=1440,390`, signed out | **"48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list"** | PASS (`../sector-standing-prod-2026-11-07/check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out; it never convenes the room) | **"all passed"**, 24 PASS, 0 FAIL | PASS (`check-advisors-visitor.txt`, screenshots in `advisors-visitor/`) |
| `check-data-fixes.mjs` | `SWEEP=1` | **"all passed"**, 44 PASS, 0 FAIL, 1 INFO; sweep 714 tickers, `eps_bad` 0, `vt_reason` 0, `news_green_old` 0, `no_currency` 8 | PASS (`check-data-fixes.txt`, screenshots in `data-fixes/`) |
| five pages × two languages × two widths | `page-shots.mjs` (GETs only) | **20 views, every one 200, no sideways scroll** | PASS (`pages/pages.txt`) |

Every count equals the 2026-11-06 run on `b5655a5064`.

**What the sweep cannot read here:** the English statement-label sweep prints **UNAVAILABLE**, as before.
Statements are Pro-only on production, and a signed-out visitor cannot read them.

**The production monitor** (`docs/screenshots/sector-standing-prod-2026-11-07/monitor-status.txt`, read at
10:02 UTC):
- **All 15 checks are ok.**
- **Renewals:** "Moyasar for renewals" reads ok for the first time in these records: "the run at 2026-11-07 10:00 UTC
  … reached Moyasar". It was "–" on 2026-11-06.
- **What that does not close:** Step 18's item 4 still waits on a real renewal payment.
- **Alerts:** none came from today's release. The two emailed in the last 24 hours date from 2026-11-06.

**What this check does not cover:**
- **Signed-in and Pro pages,** including the Fundamentals panel's new labels:
  - **Why:** Claude makes no accounts on the live site.
  - **Where the panel is shown instead:** it was captured on beta, which runs the same commit
    (`docs/screenshots/sector-standing-beta-2026-11-07/`), and production's files equal that commit by hash.
  - **What the owner can do:** confirm it signed in.
- **The owner's `check-all.mjs` and signed-in advisors runs:** those of 2026-11-02 closed Step 10
  (`docs/launch-check-2026-10-27.md`).
