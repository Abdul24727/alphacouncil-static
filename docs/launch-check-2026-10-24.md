# Launch check, interim run (2026-10-24)

**Not the launch check Step 18 reads.** PROJECT.md Step 10 runs again once Steps 22 and 23 (the
advisors' room's look and its three-round format) are live on production and the owner has run the
signed-in checks. This run records what passes on production today, signed out.

What changed since the 2026-10-23 interim run: **Goal 2 is DONE** (the 2026-10-24 daily night met
every check), **Step 8** put the seven portraits live and **Step 9** made `www` work. Steps 7, 10,
18, 22 and 23 are still ahead.

- Production: `https://alphacouncil.tech`, release **`a2e2c318bc`** (live since 2026-10-23 21:28 UTC).
- Data: the **2026-10-24 daily run**, published 05:03:17 UTC — the first with F-F and F-A2, and the
  run that closed Goal 2. Aramco reads 25.40 SAR as of 2026-10-22 with value traded 185,595,347 SAR.
- Billing: `curl -s https://alphacouncil.tech/api/v1/plans` → `"checkout_open":false` (closed, as it
  must be until Step 18).
- Universe on production: **716 listings** — the two dropped ones (TAQA, KPPC) are on `rebuild` and
  not released, so they are still served here.
- Run from the owner's computer, 16:2x–16:37 UTC. Signed out throughout: no account was created, no
  form submitted, nothing written.

## Scripts

| Script | How | Summary line | Result |
|---|---|---|---|
| `check-data-fixes.mjs` | `BASE_URL=https://alphacouncil.tech SWEEP=1` (run 05:1x UTC, after the night published; same data as this run) | "all passed", 44 PASS, 0 FAIL; sweep 716 tickers, `eps_bad` 0, **`vt_reason` 0** | PASS (`screenshots/data-fixes-production-20261024/check-data-fixes.txt`) |
| `check-seo.mjs` | `BASE_URL=https://alphacouncil.tech` | "ALL PASS", 62 PASS, 0 FAIL | PASS (`screenshots/launch-2026-10-24/check-seo.txt`) |
| `check-arabic.mjs` | signed out, `WIDTHS=1440,390` | "48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list" | PASS (`…/check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out) | "all passed", 24 PASS, 0 FAIL | PASS (`…/check-advisors-visitor.txt`) |
| `check-all.mjs` | — | not run | **Owner runs it**: it signs up test accounts, which Claude does not do on the live site (decision 2026-10-23) |
| `check-advisors.mjs` signed in, `check-arabic.mjs SIGNED_IN=1` | — | not run | **Owner runs them**, same reason |

`vt_reason` went 5 → **0** between the two interim runs: after the 10-24 night every ticker the app
shows has a real value traded, with no "why this is missing" fallback left anywhere.

## Monitor

`python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status`: **13 ok, 1 "–"**. The "–" is "Moyasar
for renewals: no renewal run since the last round" — with checkout closed nobody renews, so that line
cannot be "ok" until billing is open and a renewal has run (Step 10's revised wording).

- `/home` 200 in 82 ms; `/api/v1/health` 200 in 22 ms; market data ok; `acp-prod-api` and
  `acp-prod-web` active; the renewals and backup jobs and timers ok.
- Off-server backup copy: the owner's computer copied at **2026-10-24 06:00 UTC** (09:00 Riyadh),
  33 files, newest `acp_prod-20261024T013019Z.dump`.
- Disk `/` 73 % (57.6 GB free), `/boot` 15 %. Alerts emailed: 0 in 24 h, 3 in 30 days.
- TLS: valid to **2027-01-21** (89 days). It was 2026-12-31 on 10-23: the certificate was reissued
  when Step 9 expanded it to cover `www`.
- Outside check: `PING_URL` is set and pinged at the end of every round.

## `www` (Goal 4, item 3)

`curl -sI https://www.alphacouncil.tech/` → **301** with `Location: https://alphacouncil.tech/`, and
the certificate covers `alphacouncil.tech`, `api.alphacouncil.tech` and `www.alphacouncil.tech`.

## Screenshots (`screenshots/launch-2026-10-24/`)

| Page | English 1440 / 390 | Arabic 1440 / 390 |
|---|---|---|
| `/` (landing) | `seo/landing.en.*` | `seo/landing.ar.*` |
| `/pricing` | `pages/pricing.en.*` | `pages/pricing.ar.*` |
| `/home` | `pages/home.en.*` | `pages/home.ar.*` |
| Tadawul stock `/t/2222` | `seo/stock-2222.en.*` | `seo/stock-2222.ar.*` |
| Its advisors' page `/t/2222/advisors` (visitor) | `advisors-visitor/visitor-en-*` | `advisors-visitor/visitor-ar-*` |

All eight `/pricing` and `/home` views answered 200 with no sideways scroll (`pages/pages.txt`). The
stock page shows the seven portraits live on the Advisors tab (Step 8) and the council panel voting
3 bullish of 5.

## Gaps before the real launch check

1. **Steps 22 and 23** — the advisors' room's look and its three-round format. 23 is built and proven
   on `rebuild` (`b8dc9c7`); 22 waits on the owner's images, and the two release together. This run
   therefore tested the options-and-votes room that production still serves.
2. **The owner's signed-in run**: `cd web; $env:BASE_URL="https://alphacouncil.tech"; node scripts/check-all.mjs`
   (and the signed-in advisors and Arabic checks), output into this folder.
3. **Step 7**, the lawyer's review of the finished site, which now comes after this check.
4. Not on production yet, all on `rebuild`: the two dropped listings and the Etihad Energy Holding
   rename, and the not-found room. `check-advisors.mjs` now also checks the three-round format, so
   run it against production only after 22 and 23 ship.
5. Monitor "14 of 14": the renewals line stays "–" while billing is closed, so with billing closed
   the bar is 13 ok plus that line.
