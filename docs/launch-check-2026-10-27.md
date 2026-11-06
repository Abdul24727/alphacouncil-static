# Launch check on production — 2026-10-27

Step 10's run after Steps 22 and 23 went live. **Release `15f5bf8770`** (production moved from `a2e2c318bc`
the same day, on the owner's go-ahead), so this is the first launch check against the advisors' room with
portraits round a table and the three-round format. Billing is still closed.

**Status: COMPLETE, every check green (2026-11-02). Step 10 closes on this record.** The signed-out half ran
on 2026-10-27. The owner ran the signed-in half from their own computer on 2026-11-02 against release
`74ce427bf6`, with billing closed for the run (20:06:56–20:24:55 UTC), as "Before you run those two" lays out:
- **`check-all.mjs`: 9 of 9 runs PASS, 264 PASS / 0 FAIL**, the same count as 2026-10-24.
- **The signed-in `check-advisors.mjs`: "all passed", 53 PASS / 0 FAIL** (20 INFO), in both languages.

See "The owner's two runs (2026-11-02)" below. *(Until 2026-11-02 this said the signed-in half waited on the
owner. Billing had in the meantime been opened, on 2026-11-02 18:20 UTC, before this record was complete: Step
18's Decision.)*

## The release

> **Updated the same day:** production moved on from `15f5bf8770` to **`3228ab57e9`** after the signed-out
> half below had run, to fix F-8 (the Chair's answer and the long round-one answers were coming out as one
> block instead of paragraphs). What changed between the two: one line of the advisors' system prompt, the
> accounting for a failed turn, a test, and the checker script. None of it touches the pages
> `check-seo`, `check-arabic` or `check-data-fixes` read, so those results stand as recorded.
> `check-advisors.mjs VISITOR=1` **was re-run against `3228ab57e9`** and is still "all passed", 24 PASS / 0
> FAIL.
>
> **Updated again, 2026-10-27 21:27 UTC (00:27 Riyadh on the 28th): production moved on to `74ce427bf6`** on
> the owner's go-ahead, to carry **F-10** (a provider refusal on credit reaching members as "the AI service
> could not be reached") and **F-11** (a new HTTP client per model call, never closed). Six files differ from
> `3228ab57e9` in anything a member can reach: `copilot/openai_compat.py`, `debate/engine.py`, `debate/llm.py`,
> `web/messages/{en,ar}.json` and `web/src/components/debate/Stage.tsx`. None of them touches the pages
> `check-seo`, `check-arabic` or `check-data-fixes` read, so those results stand as recorded.
> `check-advisors.mjs VISITOR=1` **was re-run against `74ce427bf6`** — "all passed", **24 PASS / 0 FAIL**
> (`advisors-visitor-74ce427bf6/check-visitor.txt`, with its eight screenshots beside it). **The owner's two
> runs below should be made against `74ce427bf6`.**
>
> The monitor is now at **15 checks**, not 14: the fifteenth reads the model account's credit and is
> **FAILING at $4.74, below its $10 floor**. It alerted by email on the second consecutive round. That line
> cannot go green without a top-up at openrouter.ai/credits, and it is a second line — beside Moyasar's "–" —
> that Step 10 cannot close by itself.

| | |
| --- | --- |
| Production serves | `/opt/alphacouncil-platform/prod/releases/15f5bf8770`, `acp-prod-api` and `acp-prod-web` active |
| Was | `a2e2c318bc` (the options-and-votes room) |
| Beta serves | `15f5bf8770` too — it was moved to HEAD first so `deploy-production.sh`'s "beta must run exactly HEAD" guard passed |
| What changed between the proven beta release and this one | Nothing in the app: `git diff ec620968ac..15f5bf8770 -- api web/src web/messages web/public deploy` is empty. Only `PROJECT.md`, the screenshots and one comment in a dev script. |
| Checkout | `"checkout_open":false` — unchanged, and it stays closed until Step 18 |

## Scripts

All run from `web/` with `BASE_URL=https://alphacouncil.tech`. Output files are in
`docs/screenshots/launch-2026-10-27/`.

| Script | How | Summary line | Result |
| --- | --- | --- | --- |
| `check-seo.mjs` | `BASE_URL=https://alphacouncil.tech` | **"ALL PASS"**, 62 PASS, 0 FAIL | PASS (`check-seo.txt`) |
| `check-data-fixes.mjs` | `SWEEP=1` | **"all passed"**, 44 PASS, 0 FAIL; sweep 714 tickers, `eps_bad` **0**, `vt_reason` **0**, `news_green_old` **0** | PASS (`check-data-fixes.txt`) |
| `check-arabic.mjs` | signed out, `WIDTHS=1440,390` | **"48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list"** | PASS (`check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out) | **"all passed"**, 24 PASS, 0 FAIL | PASS (`check-advisors-visitor.txt`, screenshots in `advisors-visitor/`) |
| `check-all.mjs` | `BASE_URL=https://alphacouncil.tech`, **run by the owner** on 2026-11-02 (it signs up test accounts, which Claude does not do on the live site), billing closed for the run | **Summary: Phases 1–7 PASS, Arabic signed out PASS, Arabic signed in PASS**; 264 PASS / 0 FAIL | PASS (`check-all.txt`) |
| `check-arabic.mjs SIGNED_IN=1` | inside `check-all.mjs` | **"15 Arabic page view(s) signed in; 0 English string(s) outside the allow-list"** | PASS (`check-all.txt`) |
| `check-advisors.mjs` signed in | fresh account per locale, **run by the owner** on 2026-11-02, billing closed for the run, `OUT=…/advisors-signed-in` | **"all passed"**, 53 PASS, 0 FAIL, 20 INFO; two real-model sessions, verdict on screen in 28 s (EN) and 38 s (AR), all six seats answered all three rounds in both | PASS (`advisors-signed-in/check-advisors.txt`, identical line for line to the script's own `check-sessions.txt`; 44 screenshots) |

The sweep reads 714 tickers, not the 716 of 2026-10-24: TAQA_ADX and 624_KSE were dropped from the universe
on 2026-10-24 (`api/app/data/not_listed.json`), as the owner decided.

## The monitor

`python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status`: **13 ok, 1 "–"** when this was first run against
14 checks. **Since 2026-10-27 21:27 UTC it is 15 checks: 13 ok, 1 "–" (Moyasar) and 1 FAILING (model account
credit, $4.74 left against a $10 floor).** The reading below is the 14-check one, kept as it was recorded.

```
ok  alphacouncil.tech/home: answered 200 in 50 ms
ok  alphacouncil.tech/api/v1/health: answered 200 in 33 ms
ok  market data: the health check reports market data: ok
ok  acp-prod-api is active
ok  acp-prod-web is active
ok  Pro renewals job: the last run exited 0
ok  Pro renewals timer: acp-prod-billing.timer is active
-   Moyasar for renewals: no renewal run since the last round
ok  database backup job: the last run exited 0
ok  database backup timer: acp-db-backup.timer is active
ok  off-server backup copy: 2026-10-27 06:00 UTC (09:00 Riyadh), 0.2 days ago, 44 files
ok  disk /: 76% full (51.2 GB free)
ok  disk /boot: 15% full (0.7 GB free)
ok  TLS certificate: expires 2027-01-21, in 86 days
alerts emailed: 0 in 24 hours (limit 8), 3 in 30 days (limit 60)
outside check: PING_URL is set, pinged at the end of every round
```

The "–" is **"Moyasar for renewals"**, and it cannot be `ok` while checkout is closed: with nobody subscribed
there is no renewal run for the monitor to look at. That is Step 10's wording as revised on 2026-10-23, and it
is why **Goal 4's "monitor at 14 of 14" is a Step 18 check, not a Step 10 one** — the fourteenth line can only
turn `ok` after billing opens and the first renewal round runs.

**Read again on 2026-11-02 at 20:25 UTC, after the owner's runs and with billing reopened: 14 ok, 1 "–".**
That is 15 checks, and the model-credit line is `ok` again ($14.74 at 18:19 UTC, after the owner's top-up).
The one "–" is Moyasar for renewals, which is exactly Step 10's revised wording. That line turns `ok` only
when a renewal run talks to Moyasar, which needs a renewing card (Step 18, item 4).

## The owner's two runs (2026-11-02)

- **The window.** Billing was closed for the runs (`BILLING_OPEN` removed, `acp-prod-api` restarted at
  20:06:56 UTC, `api.env` then byte-identical to the pre-opening `api.env.bak-20261102182018`) and reopened
  at 20:24:55 UTC (`api.env` byte-identical to the billing-open file, `api.env.bak-20261102200655`). Both
  changes were made on the owner's go-ahead in chat. After reopening, `check-billing-public.mjs` "all
  passed" (`billing-reopened/`). No payment was taken during the window: production still holds one payment,
  the owner's refunded one.
- **`check-all.mjs`: 9 of 9 PASS, 264 PASS / 0 FAIL** (`check-all.txt`).
  - Phase 3: charts on 689 of 689 tickers with price history, "Data unavailable" on 25 of 25 without.
  - Phase 4: the Copilot (`deepseek/deepseek-v3.2`) answered in 7 s with a working citation.
  - Phase 6: every number on the landing page is a database value equal to the API (7 exchanges, 714
    equities, Pro 79), and the legal texts are full length in both languages.
  - Phase 7: 96 views, 0 failures. Arabic: 24 views signed out and 15 signed in, 0 English strings.
- **The signed-in `check-advisors.mjs`: "all passed", 53 PASS / 0 FAIL / 20 INFO**
  (`advisors-signed-in/check-advisors.txt`; the script's own `check-sessions.txt` is identical line for line).
  - Two real-model sessions on 2222.
  - Verdict on screen in 28 s (EN) and 38 s (AR); every seat answered all three rounds in both languages.
  - Round one ran 275–360 words (EN) and 222–261 (AR), 0 of 12 outside 200–400.
  - The Chair's answer was 301 and 208 words, 5 paragraphs each; headline and answer are assessments, not
    advice.
  - "Play the debate" replays at 390 px in both languages.
  - EN marked 2 figures as not found in the data, AR 0.
- **INFO lines that do not apply to production.** "Seats not citing their own datasets: 6 of 6", "datasets
  … never cited" and "the Chair ruled on 0 of 0 fault lines" come from checks added on `rebuild` after
  `74ce427bf6` for mandates and rulings, which production does not serve. They read as total misses by
  construction and say nothing about this release.
- **Left behind on the live site:** six test accounts made in the window, all `@example.com`:
  - `advisors-*` × 2
  - `audit-*`, `check-*`, `phase1-*` and `phase4-*`

  They are Free now billing is open. Removing them is the owner's ("After them" below), with
  `bash scripts/old-accounts.sh production forget <prefix>-` once per prefix.

## `www` and the certificate

```
$ curl -sI https://www.alphacouncil.tech/
HTTP/1.1 301 Moved Permanently
Location: https://alphacouncil.tech/
Strict-Transport-Security: max-age=15768000
```

Certificate: `CN=alphacouncil.tech`, SAN `alphacouncil.tech, api.alphacouncil.tech, www.alphacouncil.tech`,
valid to 2027-01-21. **Goal 4's third "Done when" is met.**

## Screenshots

`docs/screenshots/launch-2026-10-27/pages/` — `/`, `/pricing`, `/home`, `/t/2222` and `/t/2222/advisors`, in
English and Arabic, at 1440 and 390 px: **20 views, every one 200, no sideways scroll** (`pages.txt` has the
line per view). `advisors-visitor/` holds the signed-out advisors' screenshots the check itself took.

The two scripts that write to their own fixed folders — `check-data-fixes.mjs` into
`docs/screenshots/data-fixes-local/` and `check-seo.mjs` into `docs/screenshots/seo-local/` — had their output
moved into `launch-2026-10-27/data-fixes/` (34 files) and `launch-2026-10-27/seo/` (12 files), and the tracked
local-build set was restored, so the repo keeps the local reference shots and this record keeps the production
ones.

## Where this leaves Step 10 and Goal 4

> **2026-11-02: Step 10 is DONE.** All four of its "Done when" items are met. Both of the owner's runs below
> are in, and passing (see "The owner's two runs (2026-11-02)" above). Goal 4's item 4 is met except for the
> monitor's renewals line, which belongs to Step 18 (item 4) and cannot turn `ok` before a real renewal. The
> text below is kept as it was written on 2026-10-27.

**Met:**

1. Every script Claude runs on production passes: `check-seo` 62/0, `check-data-fixes` SWEEP=1 44/0,
   `check-arabic` 48 views / 0 English strings, `check-advisors VISITOR=1` 24/0.
2. The monitor is 13 ok + renewals "–", which is the revised wording in full.
3. The screenshots exist for each page, both languages, both widths, all 200 and no sideways scroll.
4. `check-arabic.mjs` passes on production.

**Not met, and it is the owner's to do:**

- **`check-all.mjs` on production**, from the owner's own computer:
  ```
  cd web; $env:BASE_URL="https://alphacouncil.tech"; node scripts/check-all.mjs
  ```
  with the output saved into `docs/screenshots/launch-2026-10-27/check-all.txt`. On 2026-10-24 this was 264
  PASS / 0 FAIL across nine runs; it has to run again because production's app changed.
- **The signed-in `check-advisors.mjs`**, which is the one thing the 2026-10-24 interim run could not do at
  all. Production now serves the three-round format, so it will exercise the real room on a real model — the
  same thing proven four times on beta today with zero round-one absences.

Once both are in this file, Step 10 closes, and **Step 7** (the lawyer reviews the finished site) and then
**Step 18** (open Pro billing) are all that remain.

## Before you run those two 

> **Superseded 2026-11-02 18:20 UTC: billing is OPEN on production** (Step 18; `docs/production.md`,
> "Billing open again (2026-11-02)"). The first bullet below is no longer true: a freshly signed-up account
> is **Free**, and Free has the room at 0 sessions a month and locks financials and ownership.
> - **`check-all.mjs`** signs up its own accounts, so its Pro-data phases would now fail on production. Run
>   it with billing briefly closed. That is a production change (delete the `BILLING_OPEN` line, restart,
>   run, put the line back, restart), so ask Claude for it in chat first. Or accept that this check can no
>   longer run on production as written.
> - **The signed-in `check-advisors.mjs`**: run it with `EMAIL=` (and `PASSWORD=`) set to an account that has
>   Pro, your own once you have paid, or a test account given Pro with
>   `python -m app.billing grant <email> 1`. Signed in that way it spends two of that account's 20 sessions
>   this month.
>
> **The run plan chosen (2026-11-02): both checks in one window with billing closed.** Closing billing
> restores exactly the condition the bullets below were checked for (every account Pro, checkout closed), so
> both scripts run as designed and neither needs a granted account:
> 1. Claude backs up `api.env`, deletes the `BILLING_OPEN` line, restarts `acp-prod-api`, and confirms
>    `"checkout_open":false`. This needs the owner's go-ahead in chat.
> 2. The owner runs, from `web/` in PowerShell, `check-all.mjs` and then the signed-in `check-advisors.mjs`
>    (fresh accounts, about $0.60 of model credit), and pastes both summaries into chat.
> 3. Claude puts `BILLING_OPEN=true` back, restarts, and re-runs `check-billing-public.mjs` (signed out, all
>    must pass). Then it records both summaries here, moves the scripts' screenshots into this folder, and
>    reads the monitor.
>
> While the window is open, checkout is closed and every visitor has Pro. Nobody is subscribed, so nobody is
> affected. The test accounts the runs leave behind turn Free when billing reopens; removing them is the
> owner's (`scripts/old-accounts.sh`, "After them" below).
>
> **Read the INFO lines with production in mind.** The `check-advisors.mjs` on `rebuild` added three
> report-only lines after `74ce427bf6`: seats not citing their own datasets, datasets never cited, and the
> Chair's rulings. Production's room has no mandates and no rulings yet, so those lines will read as total
> misses. They are INFO and cannot fail the run. `check-all.mjs` and its phase scripts are unchanged since
> `74ce427bf6`.

Checked read-only on 2026-10-27, so there are no surprises in the middle of a run:

- **A fresh account can convene.** Production's `api.env` sets none of `BILLING_OPEN`, `EARLY_ACCESS` or any
  `DEBATE_*`, so every default applies and `billing_open` is `False`. `plans.plan_of` returns **`pro` for
  everyone while billing is closed**, so a newly signed-up account has the room. The signed-in check will not
  hit the Free lock.
- **The allowance is not in the way.** Pro has 20 sessions a month, and the check **signs up a new account per
  locale** (`advisors-<locale>-<timestamp>@example.com`), so it never spends an existing account's allowance
  — yours included.
- **What it costs.** The signed-in advisors check convenes **two sessions**, English and Arabic, on a real
  model. On beta today those ran 59–96 s at about $0.30 each, so expect roughly **$0.60 and a few minutes**.
- **The same script, the same code, already passed four times today** on beta `ec620968ac`, whose app code is
  byte-identical to production's `15f5bf8770`. Those runs were the signed-up path, not the visitor one.

## After them

The two checks leave test accounts on the **live** site — `advisors-*@example.com` and `advisors-free-*@example.com`
from the advisors check, and whatever `check-all.mjs` signs up. That is the accepted consequence of the
2026-10-23 decision that the owner, not Claude, runs them there. They can be removed afterwards:

```
bash scripts/old-accounts.sh production forget advisors-
```

`forget` only ever removes `<prefix>*@example.com`, so it cannot reach a real member's account. Deleting data
is an "Always stop" for Claude, so this one is the owner's to run or to skip.

*(2026-11-06: the test accounts these checks left were removed on the owner's go-ahead ("Delete them"): 24
`@example.com` accounts on production, prefixes advisors-, audit-, check-, phase1- and phase4-. Production keeps its
4 real accounts. `PROJECT.md`, changelog 2026-11-06.)*

## Production monitor after the 2026-11-06 release, retention and pilot

Read-only, `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status` at **2026-11-06 12:33:51 UTC**, with
production on `b5655a5064`. **14 ok, 1 failing, 1 pending.**

| Check | Result |
|---|---|
| home, `/api/v1/health`, market data | ok (200 in 40 ms; 200 in 9 ms; market data ok) |
| `acp-prod-api`, `acp-prod-web` | ok, active |
| Pro renewals job and timer | ok (last run exited 0; timer active) |
| **Moyasar for renewals** | **– pending**: no renewal run since the last round. This is not a failure. It turns ok only when a renewal talks to Moyasar: Step 18's item 4, open until a first real renewal. |
| database backup job and timer | ok |
| off-server backup copy | ok (the owner's computer copied 76 files at 06:00 UTC, 0.3 days before) |
| disk `/` | ok: **41 % full, 122.4 GB free** (83 % before the keep-14 retention that morning) |
| disk `/boot` | ok, 15 % |
| TLS certificate | ok, expires 2027-01-21 (76 days) |
| **model account credit** | **FAILING: $7.83 left, below the $10 alert line** (alert emailed). The advisors' room and the Copilot stop when it runs out. The fix is the owner's: add credit at openrouter.ai/credits. |

Alerts: 3 emailed in 24 hours, 10 in 30 days, within the limits of 8 and 60. The outside check is pinged every
round.
