# Launch check, interim run (2026-10-23)

**Not the launch check Step 18 reads.** PROJECT.md Step 10 runs again once Steps 7–9 (legal advice,
portraits, `www`) are live and the owner has run the signed-in checks. This run records what passes on
production today, signed out, while those steps wait.

- Production: `https://alphacouncil.tech`, release `56476948f5`; data from the 2026-10-23 full run
  (published 05:00:43 UTC), the first with pipeline fixes F-A, F-E, F-B, F-C.
- Billing: `curl -s https://alphacouncil.tech/api/v1/plans` → `"checkout_open":false` (closed, as it
  must be until Step 18).
- Run from the owner's computer, 12:49–12:52 UTC (scripts) and 12:53 UTC (page screenshots). No account
  was created and nothing was submitted.

## Scripts

| Script | How | Summary line | Result |
|---|---|---|---|
| `check-data-fixes.mjs` | `BASE_URL=https://alphacouncil.tech SWEEP=1` (finished 12:27 UTC) | "all passed", 44 PASS, 0 FAIL; sweep 716 tickers, `eps_bad` 0, `vt_reason` 5 | PASS (`screenshots/data-fixes-production-20261023/check-data-fixes.txt`) |
| `check-seo.mjs` | `BASE_URL=https://alphacouncil.tech` | "ALL PASS", 62 PASS, 0 FAIL | PASS (`screenshots/launch-2026-10-23/check-seo.txt`) |
| `check-arabic.mjs` | signed out, `WIDTHS=1440,390` | "48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list" | PASS (`…/check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out) | "all passed", 24 PASS, 0 FAIL | PASS (`…/check-advisors-visitor.txt`) |
| `check-all.mjs` | — | not run | **Owner runs it**: it signs up test accounts, which Claude does not do on the live site |
| `check-advisors.mjs` signed in, `check-arabic.mjs SIGNED_IN=1` | — | not run | **Owner runs them**, same reason |

## Monitor

`python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status` (12:49 UTC): **13 ok, 1 "–"**. The "–"
is "Moyasar for renewals: no renewal run since the last round": with checkout closed nobody renews, so
that line cannot be "ok" until billing is open and a renewal has run. Off-server backup copy 12:15 UTC
(30 files); TLS valid to 2026-12-31; disk 72 %; outside check pinged every round.

## Screenshots (`screenshots/launch-2026-10-23/`)

| Page | English 1440 / 390 | Arabic 1440 / 390 |
|---|---|---|
| `/` (landing) | `seo/landing.en.*` | `seo/landing.ar.*` |
| `/pricing` | `pages/pricing.en.*` | `pages/pricing.ar.*` |
| `/home` | `pages/home.en.*` | `pages/home.ar.*` |
| Tadawul stock `/t/2222` | `seo/stock-2222.en.*` | `seo/stock-2222.ar.*` |
| Its advisors' page `/t/2222/advisors` (visitor) | `advisors-visitor/visitor-en-*` | `advisors-visitor/visitor-ar-*` |

All eight `/pricing` and `/home` views answered 200 with no sideways scroll. Seen: Aramco 25.40 SAR
as of 22 Oct, with **value traded 185.6M SAR** (F-E's turnover reaching the app); the home page lists
Tadawul 269/269 with 22 Oct prices.

## Gaps before the real launch check

1. Steps 7–9: the lawyer's advice on the named advisors, the six portraits (the advisors' page still
   shows initials), the `www` record (NXDOMAIN on 2026-10-23).
2. The owner's signed-in run: `cd web; $env:BASE_URL="https://alphacouncil.tech"; node scripts/check-all.mjs`
   (and the signed-in advisors and Arabic checks), output into this folder.
3. Goal 2: the 2026-10-24 recount (price files, F-F ownership counts), and F-A2 (GULFNAV, now Etihad
   Energy Holding) if the owner approves it.
4. Monitor "14 of 14": the renewals line stays "–" while billing is closed, so with billing closed the
   bar is 13 ok plus that line.
