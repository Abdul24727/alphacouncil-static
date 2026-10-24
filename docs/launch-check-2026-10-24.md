# Launch check, interim run (2026-10-24)

**Not yet the launch check Step 18 reads, but close.** Both halves have now run — Claude's signed-out
scripts and the owner's signed-in `check-all.mjs` — and everything passes. What is left is Steps 22
and 23 (the advisors' room's look and its three-round format) going live on production, after which
PROJECT.md Step 10 runs once more, including the signed-in advisors check that cannot run until then.

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
- Claude's half ran 16:2x–16:37 UTC, signed out throughout: no account created, no form submitted,
  nothing written. The owner then ran `check-all.mjs` from the same computer (21:5x UTC), which does
  sign up test accounts (`phase*-<time>@example.com`, `audit-ar-<time>@example.com`) and asks the
  Copilot one question.

## Scripts

| Script | How | Summary line | Result |
|---|---|---|---|
| `check-data-fixes.mjs` | `BASE_URL=https://alphacouncil.tech SWEEP=1` (run 05:1x UTC, after the night published; same data as this run) | "all passed", 44 PASS, 0 FAIL; sweep 716 tickers, `eps_bad` 0, **`vt_reason` 0** | PASS (`screenshots/data-fixes-production-20261024/check-data-fixes.txt`) |
| `check-seo.mjs` | `BASE_URL=https://alphacouncil.tech` | "ALL PASS", 62 PASS, 0 FAIL | PASS (`screenshots/launch-2026-10-24/check-seo.txt`) |
| `check-arabic.mjs` | signed out, `WIDTHS=1440,390` | "48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list" | PASS (`…/check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out) | "all passed", 24 PASS, 0 FAIL | PASS (`…/check-advisors-visitor.txt`) |
| `check-all.mjs` | `BASE_URL=https://alphacouncil.tech`, **run by the owner** (it signs up test accounts, which Claude does not do on the live site — decision 2026-10-23) | all nine runs PASS: Phases 1–7, "Arabic, signed out", "Arabic, signed in". **264 PASS, 0 FAIL** | PASS (`screenshots/launch-2026-10-24/check-all.txt`) |
| `check-arabic.mjs SIGNED_IN=1` | inside `check-all.mjs` | "15 Arabic page view(s) signed in; 0 English string(s) outside the allow-list" | PASS (same file) |
| `check-advisors.mjs` signed in | — | **not run, deliberately** | The copy on `rebuild` checks the three-round format (Step 23), which production does not serve: it would fail on the missing `final` stage tab, not on anything wrong with production. It runs when 22 and 23 ship |

`vt_reason` went 5 → **0** between the two interim runs: after the 10-24 night every ticker the app
shows has a real value traded, with no "why this is missing" fallback left anywhere.

Worth keeping from `check-all`, since these are the signed-in facts nothing else here covers:

- **Phase 3**: 716 tickers, 691 with a price file; **charts drawn 691 of 691**, and the 25 without
  history all say "Data unavailable" rather than drawing an empty frame.
- **Phase 4**: the Copilot (`deepseek/deepseek-v3.2`) answered in **9 s**, cited the metrics panel,
  offered three follow-ups, and its citation scrolled that panel into view and highlighted it.
- **Phase 6**: every number on the landing page sits in a database value, and those values equal the
  API — 7 exchanges, **716 equities**, Pro 79. The legal texts are full length in both languages and
  their hashes match.
- **Phase 2**: the stale light is the brand amber and its tooltip dates the data itself ("data as of
  8 Aug 2018" on a long-stale ticker), which is the behaviour the audit asked for.
- **Arabic**: 96 page views in Phase 7, 24 signed out and 15 signed in, **0 English strings** in any
  of them.

When Steps 22 and 23 ship, the landing page's "716 equities" becomes 714: the two dropped listings
leave the universe, and Phase 6 compares the page against the API, so it stays consistent by itself.

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
2. ~~The owner's signed-in run~~ — **done 2026-10-24**, all nine runs PASS (above). Only the
   signed-in `check-advisors.mjs` is left, and it waits on gap 1 rather than on the owner.
3. **Step 7**, the lawyer's review of the finished site, which now comes after this check.
4. Not on production yet, all on `rebuild`: the two dropped listings and the Etihad Energy Holding
   rename, and the not-found room. `check-advisors.mjs` now also checks the three-round format, so
   run it against production only after 22 and 23 ship.
5. Monitor "14 of 14": the renewals line stays "–" while billing is closed, so with billing closed
   the bar is 13 ok plus that line.
