# Response to the beta QA audit (2026-10-15/16)

Every FAIL row in the QA report, with what was done. Fixes are on `rebuild` (commits `ce5897c`, `e34112e`, `e5209ff`, `e65c04d`) and deployed to beta.alphacouncil.tech. "Verified" means re-run on staging after the deploy.

## Fixed

| # | Finding | Cause | Fix | Verified |
|---|---|---|---|---|
| 1c, 6a(a), 6b | Intermittent 500s (dividend-hunter, METH.AD prices/peers); panels loading forever (FERTIGLB) | The API's workers were killed at the service's 1 GB memory cap: each cached up to 128 ten-year price histories at ~6 MB each. The web proxy then returned 500, or a retry hung. | Compact price cache (1.35 MB per ticker, at most 48 per worker); memory cap 2 GB. Panels: requests time out after 30 s; a failed load says why and offers "Try again". | The 3 endpoints answer 200. A full run of every check (716 stock pages, 88 sweep pages): API peak 455 MB of 2 GB, no swap, no worker restarts, no proxy failures, no 5xx |
| 4c (blocker) | Header green for prices years old (BMEB.BH, AKIC.AD, 4240) | The header quote used the briefs row's date, which is the nightly run date, not the price date | The quote comes from the price file whenever one exists, dated by its last bar. Without a file, an old briefs row still marks the price stale; a recent one only shows the age as unknown. | BMEB.BH: "As of 8 Aug 2018", amber (`qa-fixes/bmeb-header-1440.png`) |
| 4c (follow-up) | Found while re-checking 4c: the header's own freshness light never showed, and phones hid the "As of" date | The light sat in an inline wrapper, so it rendered 0 px wide; the date was hidden below 1024 px | The light shows; a stale price shows "As of" in the stale colour at every width | BMEB.BH at 390 px, English and Arabic: amber light and the date; 2222 (current) keeps a green light and no date (`qa-fixes/*-390.png`) |
| 5a | 4240: header "No price" while the chart has 4,933 bars | `has_price_history` came from briefs, which disagreed with the price file | The header and the chart use one rule (two bars in the file) | Header price = chart's last close |
| 5b | Key metrics vs Financials show different P/E, P/B, yield (25/30) | Each ratio is stored in three tables refreshed at different times; each screen picked its own order | One rule for every screen (`api/app/ratios.py`): Key metrics, Financials, screener, peers, templates and the council | 30/30 sampled tickers identical on Key metrics, Financials and the screener |
| 5c | P/E 0.00x and P/B −0.13x (METH.AD) | Negative earnings and negative equity passed through | P/E is n/a for zero/negative earnings; P/B and ROE are n/a for negative book value | METH.AD shows n/a |
| 5e | "Same sector" peers of Aramco include Tadawul Group, Jahez, Leejam… | The pipeline puts unclassified Tadawul listings in sector id 1, labelled "Energy" | That bucket is treated as "sector unknown"; peers come only from real sector members | Aramco's peers: 2223, 2382, 2381 |
| 5f | AFNIC header has a price, chart has none | Same as 5a | Same rule; the price is shown without a date (its age is unknown) | Header and chart agree |
| 6a(b) | SMA 200 on 144 bars draws nothing, silently | — | The chart says "SMA 200 needs 200 days of prices; this stock has 144." | SUKOON screenshot |
| 7b | Pins saved only in the browser | — | Pinned items sync to the account with the other preferences | API test |
| 7c | Copilot table shows 121 for 120.60 | The table renderer dropped decimals for values ≥ 100 | Values keep their decimals; the prompt also says to copy table values exactly | Unit level |
| 8a, 8b | English in Arabic pages: statement lines, event names, capital-change types, range buttons, currency, aria-labels, council "no", EV/EBITDA, ISO legend date | Database labels are stored in one language; some UI strings were untranslated | Bilingual dictionary for database labels (`web/src/content/data-labels.json`), Arabic currency abbreviations (ر.س, د.إ…), translated range buttons, aria-labels, yes/no, localized legend date | Aramco financials and calendar read in Arabic; the Arabic/phone sweep passes |
| 8c (part) | English pages show Arabic text under English titles | Summaries fell back to the other language | Summaries show only in the page's language; English pages use the English headline written for an Arabic item when there is one; news lists put the page's language first | See "Data limits" for what remains |
| 9c | One signed-out API call logs testers out of the staging gate | The API answered 401 without a challenge; Chrome treats that as a rejected Basic login | Sign-in failures answer 403, never 401 | Signed-out portfolio/alerts/prefs answer 403; a test covers every protected endpoint |
| 9e | Sequential IDs; cross-account DELETE untested | — | Deletes were already scoped to the owner; now proven by a test: another account's DELETE by id changes nothing | API test |

## By design (no change)

| # | Finding | Why |
|---|---|---|
| 1b | No sidebar at 390 px | The plan's phone layout: one column, bottom tab bar, Copilot as a full-screen sheet. Ctrl+B has no visible effect on a phone because there is no sidebar to collapse. |
| 2b | BRAND.md is not served | It is a repository document (`BRAND.md` at the repo root), not a page. The QA's observed palette matches it exactly: bg #0C0D10, text #ECEEF2, line #272B34, loss #FF4D5E, gain #3FD98A, signal #FF6A1A, stale #F2B134. |
| 9b | /portfolio, /dashboards, /settings answer 200 signed out | They render a sign-in prompt or browser-only settings; no account data is returned (the APIs behind them answer 403). Market data endpoints are public by design. |

## Needs your decision

| # | Finding | What is needed |
|---|---|---|
| 10b (blocker) | No Moyasar checkout | The new app has no checkout yet (audit P1). Building it needs your plan for existing subscribers and the Pro feature list (P2), and test keys you put on the server. |
| 10c | Pro placeholder on /pricing | Pro's features (audit P2). |

## Data limits (pipeline)

- **English news is scarce**: only 21 of 425 stored news items are English (newest 8 Oct), and none of the latest 200 have an English headline. English pages therefore show the latest items in Arabic, tagged as Arabic.
- **Sector labels beyond id 1**: other suspicious labels remain (for example 1201 under "Hotels & Restaurants"); only the default bucket was clearly identifiable.

## Checks after the fixes

Full run of `check-all.mjs` on staging (e5209ff, through the tunnel): Phases 1, 3, 4, 5, 6 and 7 pass (`screenshots/check-all-staging.txt`). Phase 2 failed only because its stale-light step expected a stale panel on 2222; with prices now dated by their last bar every 2222 panel was fresh. The check now uses BMEB.BH (last trade 8 Aug 2018) and also checks the tooltip's "data as of" date; it passes on e65c04d (`screenshots/check-phase2-staging-rerun.txt`). The QA's API-level repros pass 12/12 on e65c04d.
