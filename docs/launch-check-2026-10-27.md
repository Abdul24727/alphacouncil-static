# Launch check on production — 2026-10-27

Step 10's run after Steps 22 and 23 went live. **Release `15f5bf8770`** (production moved from `a2e2c318bc`
the same day, on the owner's go-ahead), so this is the first launch check against the advisors' room with
portraits round a table and the three-round format. Billing is still closed.

**Status: the signed-out half is complete and all green. The signed-in half waits on the owner** — the two
checks that sign up test accounts are not run by Claude on the live site (decision 2026-10-23). Until those
run, this is not yet the record Step 18 reads.

## The release

> **Updated the same day:** production moved on from `15f5bf8770` to **`3228ab57e9`** after the signed-out
> half below had run, to fix F-8 (the Chair's answer and the long round-one answers were coming out as one
> block instead of paragraphs). What changed between the two: one line of the advisors' system prompt, the
> accounting for a failed turn, a test, and the checker script. None of it touches the pages
> `check-seo`, `check-arabic` or `check-data-fixes` read, so those results stand as recorded.
> `check-advisors.mjs VISITOR=1` **was re-run against `3228ab57e9`** and is still "all passed", 24 PASS / 0
> FAIL. The owner's two runs below should be made against `3228ab57e9`.

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
| `check-all.mjs` | `BASE_URL=https://alphacouncil.tech`, **the owner runs it** — it signs up test accounts, which Claude does not do on the live site | — | **NOT RUN YET** |
| `check-arabic.mjs SIGNED_IN=1` | inside `check-all.mjs` | — | **NOT RUN YET** (same reason) |
| `check-advisors.mjs` signed in | `BASE_URL=https://alphacouncil.tech EMAIL=… PASSWORD=…` | — | **NOT RUN YET**, and this is the one that changed: on 2026-10-24 it was deliberately skipped because production did not serve the three-round format and it would have failed on a missing `final` tab. Production serves it now, so it can and should run. |

The sweep reads 714 tickers, not the 716 of 2026-10-24: TAQA_ADX and 624_KSE were dropped from the universe
on 2026-10-24 (`api/app/data/not_listed.json`), as the owner decided.

## The monitor

`python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status`: **13 ok, 1 "–"**.

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
