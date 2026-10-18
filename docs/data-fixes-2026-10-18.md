# Market data fixes, 2026-10-18: what the app now does, and what only the pipeline can fix

Follows [data-audit-2026-10-18.md](data-audit-2026-10-18.md). Part 1 lists the app-side fixes (`api/app`, `web/src`). Part 3 is the list for the owner: faults that only the old pipeline can fix, with evidence. Part 4 asks one question before anything more is built.

**How it was measured:**
- Live figures come from the public API: all 716 `/api/v1/tickers/{slug}`, 2026-10-18 between 13:40 and 14:20 UTC.
- Pipeline code was read in the local checkout of the old repo (`C:\AlphaCouncil-Staging\work\f11-prod-merge`, commit `3027ab5`, 2026-09-06). The server copy under `/opt/alphacouncil/backend` could not be read: SSH was refused by this session's permission check, as it was for the audit. Line numbers may differ on the server.
- Data-file checks used the 2026-08-12 database snapshot and the 2026-10-14 price files.
- Nothing in the pipeline or its data was changed.

During the live fetch, 7 consecutive requests (Tadawul 4150–4165) answered 502, then 500, for a few seconds. They answered 200 when retried right after. Most likely this was a restart of `acp-prod-api`; worth a look in `journalctl -u acp-prod-api` around 14:00 UTC.

## 1. App-side fixes

| Audit | What the app does now | Where | On today's live data |
|---|---|---|---|
| F2 EPS units | EPS is shown only in the price's unit. Each ticker's unit is confirmed against its P/E: EPS × P/E must give the price (within 20%) as stored, or after dividing by the sub-unit of the listing's currency (100 for SAR, AED, QAR, USD; 1000 for KWD, BHD, OMR). Otherwise Key metrics shows **"Unit not confirmed"** with the rule on hover. Nothing is estimated. | `api/app/ratios.py` (`eps_in_price_unit`), `routers/ticker.py`, `overview-panels.tsx` | 305 shown as stored, 195 converted (KSE 93, MSM 49, BSE 24, ADX 14, DFM 11, Tadawul 4). 181 "Unit not confirmed": 166 have no P/E to check against (mostly losses; Tadawul 79), 15 have a P/E but no unit fits: 10,000× (ADNOCDRILL, ADNOCGAS, AMR, BOROUGE, FERTIGLB, LULU, TALABAT), 100,000× (811, 813, OEIHC), cents on a BHD label (GFH.DU), fils of KWD against a USD or AED price (KFH Bahrain, AGLTY, MAZAYA), and 4144 (negative EPS against a positive P/E). 35 have no EPS. |
| F7 header decimals | The header, the peers table and market tables keep a price's own decimals. KWD, BHD and OMR always show 3. Other currencies show 3 when the stored price has a third decimal (QSE 2.345), and never pad a decimal the database lacks (AED 0.24 stays 0.24, F6). | `web/src/lib/format.ts` (`autoPriceDigits`), `StockTemplate.tsx`, `common.tsx` | 223 KWD, BHD and OMR headers, plus 28 prices with a third decimal (QSE 26, ADX 1, DFM 1). |
| F3 news light | News is dated by its newest news or disclosure item, not by the fetch time. It turns amber after 30 calendar days (440 of 447 non-Tadawul tickers had an item within 30 days), or when the nightly fetch itself is late (2 trading days, the pipeline's window). With no item at all, the light is grey ("update time unknown"). Disclosures follow the same rule within the pipeline's own 120 days. The hover still shows the fetch time as "Updated". /methodology states the 30 calendar days in both languages. | `api/app/freshness.py` (`assess_items`, `NEWS_MAX_AGE_DAYS`), `routers/ticker.py`, `routers/site.py`, `messages/*.json` | Tadawul: about 5 of 269 green (was 262 green on items older than 30 days). Other exchanges are about the same as before. |
| F5 currencies | **Cannot be taken from our data.** No table or file records a listing's trading currency, and the source's unit labels contradict themselves: KFH's Bahrain page labels its market cap in KWD while it trades in USD, and NIND's EPS is labelled in AED while it is stored ×1000. What the app does instead: a currency the exchange never trades in is not shown. The header says **"Currency not confirmed"** rather than giving a wrong one. | `api/app/universe.py` (`EXCHANGE_CURRENCIES`), `StockTemplate.tsx` | 7 of the 12: NIND, IFA, EKTTITAB, NIH (DFM, were KWD), GIH (ADX, KWD), OEIHC (ADX, OMR), KFH (Bahrain, KWD). Still wrong: the 5 USD-traded Bahrain listings (ABC.BH, ARIG.BH, GFH.DU, ITHMR.BH, INOVEST) show BHD. Our data has nothing that shows otherwise; see Part 4. |
| F9 value traded | When a ticker's price file has no turnover on any bar, Key metrics shows **"Not in our price data"** (hover: the file does not record value traded) instead of a bare n/a. A file with turnover on earlier bars only still shows n/a. | `routers/ticker.py` (`value_traded_reason`), `overview-panels.tsx` | All 269 Tadawul pages. |

Tests: `api/tests/test_ticker.py` covers the cases above with the real values (NBK, BMMI, ADNOCDIST, ADNOCDRILL, 811, KFH, Mazaya, 4144, ARIG). It also covers the news light (fresh, stale and unknown, plus a late fetch), the methodology window, value traded, and the currency rule. 138 API tests pass. `web/src/lib/format.test.ts` covers the price decimals; 16 web tests pass; typecheck, lint and `next build` are clean.

Page check: `web/scripts/check-data-fixes.mjs`. It loads NBK, Aramco, QCFS, ADNOC Drilling and NIND in English and Arabic, plus /methodology, and compares the header price, EPS, value traded and the news light with the API. With `SWEEP=1` it also counts the rules across all 716 tickers. Screenshots are taken at 1440 and 390 px. The local run on the snapshot data passed 42 of 42 (`screenshots/data-fixes-local/`).

## 2. Release

**Live on alphacouncil.tech since release `3f403b2`.** The advisors'-room session deployed it to beta and then production, with these fixes unchanged from `46bb715`. That session's beta checks covered its own pages; this session had no SSH, so the data fixes were not checked on beta. The owner approved shipping them with that release.

**Checked on production over HTTPS** (2026-10-18), with `check-data-fixes.mjs` and `SWEEP=1`: 46 of 46 checks passed. Output: `screenshots/data-fixes-check-production.txt`. Screenshots in English and Arabic at 1440 and 390 px: `screenshots/data-fixes-production/`.
- NBK's header reads 0.815 KWD and its EPS 0.064 KWD.
- NIND reads "Currency not confirmed", with EPS 0.24 in the price's unit.
- Aramco's value traded reads "Not in our price data".
- ADNOC Drilling's EPS reads "Unit not confirmed".
- /methodology lists news at 30 calendar days.

The sweep of all 716 tickers found:
- 500 EPS figures shown, every one consistent with its P/E and price; 181 "Unit not confirmed".
- 445 green news lights, none on an item older than 30 days.
- 7 listings without a currency label.
- 272 "Not in our price data": all 269 Tadawul tickers, plus 3 other files with no turnover on any bar.

For a later release (SSH needed):

```bash
scripts/deploy-staging.sh
ssh -fN -L 3201:[::1]:3200 root@alphacouncil.tech
BASE_URL=http://localhost:3201 SHOTS_DIR=../../docs/screenshots/data-fixes-beta SWEEP=1 node web/scripts/check-data-fixes.mjs
scripts/deploy-production.sh
BASE_URL=https://alphacouncil.tech SHOTS_DIR=../../docs/screenshots/data-fixes-production SWEEP=1 node web/scripts/check-data-fixes.mjs
```

## 3. For the owner: what only the pipeline can fix

The pipeline only can fix these. The app shows them as they are, or labels them, but cannot correct them.

### P1. Tadawul sectors: 98 of 269 in another sector, 24 unclassified (blocker)
- **Cause.** The scraper reads Argaam's `hdnSectorID` from the company page (`main_patched2026_with_sectors.py:46-60`, again in `llm-council/build_portfolio_inputs_with_sectors.py:19-51`). It looks the number up in `argaam/sector_maps.py:11-36`. That map's names belong to a different numbering than the ids Argaam sends.
- **The ids are consistent.** Every id holds one real group, so only the names are wrong:

  | id | Name shown | What it holds |
  |---|---|---|
  | 8 | Transportation | food and agriculture (2050, 2270, 2280…) |
  | 38 | Hotels & Restaurants | materials (1211, 2300…) |
  | 37 | Entertainment | capital goods (1320, 2040, 2110…) |
  | 35 | Metals & Mining | transport (4030, 4040, 4260–4265) |
  | 27 | Tobacco | health care (4002, 4004, 4007, 4009) |
  | 34 | Chemicals | media and services (1831, 4070, 4072, 4210) |
  | 40 | Media | holdings (2120, 4080, 4130, 4280) |
  | 13 | Food Retail | 4142 |
  | 7 | Utilities | 1832 |

  Commit `8381437` shows the same mismatch: Aramco, SEC and GASCO arrived as id 24, which the map calls "Automobiles".
- **Unclassified.** Id 1 is the scraper's catch-all ("Energy"). The app already hides it.
- **Fix.** Take the sector name Argaam publishes, or rebuild the map for this numbering. `generate_gcc_tickers.py` already does the first for the other markets. Then classify the id-1 companies.

### P2. Six tickers stopped updating while their market traded (major)
- **The tickers.** 2080 GASCO, AGILITY (ADX), GULFNAV (DFM) and 624 KPPC have had no new bars since 2026-07-23. TAQA (ADX) has none since 08-06 and 4240 AFG none since 10-07. The reference shows trades after these dates (audit F4).
- **They are still being fetched.** All six are in `argaam/tickers.csv`, the list the nightly run uses (`run_parallel_universe.py:147`).
- **Why stale bars count as a success.** A fetch counts as successful when it returns any rows at all (`meta["ok"] = len(rows) > 0`, `main_patched…:2578, 2647, 2835`). Nothing checks that the last bar is recent. If newer runs have no price file, `tools/select_latest_complete.py:166-168` reuses an older run's.
- **The `prices` freshness stamp is written for every ticker.** It is stamped at build time whether or not anything was fetched (`llm-council/build_screening_db.py:247-262`). So its "last success" is not evidence of a fetch. The app judges prices by the last bar, so these pages are already amber.
- **Leads to check on the server** (the logs are only there):
  - AGILITY's slug is `agility-global` in `tickers.csv` and `agility-global-plc` in `tickers_uae.csv`.
  - Tadawul bars come from TradingView by the chart page's `companyID`, not the CSV's id (`main_patched…:2501`), so check GASCO's and AFG's.
- **Fix.** Treat a ticker whose last bar lags its exchange's last session as a failure, stamp `prices` only when new bars arrive, and alert on it.

### P3. Prices stored with 2 decimals instead of 3 (major)
- **The data.** Every sub-1 AED bar on ADX (25,606) and DFM (24,103) has 2 decimals, while Kuwait, Muscat and Qatar have 3.
- **Value ÷ volume shows the lost digit.** On 2026-10-13: INVESTB stored 0.03 against 0.0271, SHUAA 0.25 against 0.2430.
- **The effect.** It creates fake ±25–33% days on INVESTB and blurs day changes for 29 stocks.
- **Cause.** The UAE history table copies Argaam's 2-decimal cells as they are (`main_patched…:2805`). The TradingView path rounds with `f"{float(val):.2f}"` (`_fmt_price`, :2583-2586).
- **Fix.** Take UAE history from the full-precision TradingView data (already the fallback) and drop the `.2f`.

### P4. Repeated bars on market holidays (major)
- **The data.** Since 2025-10-01 there are 137 Muscat and 47 Bahrain bars identical to the previous one (same OHLC, volume and value). They fall mainly on the Eid closure (2026-03-22/23) and 2025-11-27. Example: AACT on 03-19, 03-22 and 03-23 (0.178, volume 1,019,825 each day).
- **Cause.** Dates come from the source's rows, which carry the last session forward on closed days. `write_price_csv` (`main_patched…:6543-6550`) writes them as they are, and `compute_indicators.py:172-175` only removes duplicate dates.
- **Fix.** Drop a bar equal to the previous one in OHLC, volume and value. This probably also corrects the derived exchange calendars.

### Also for the pipeline (found on the way)
- **EPS units.** `ingest_scraped_ratios.py:64,85` keeps only the number and ignores the unit in Argaam's label, e.g. "(فلس)" for fils, "(بيسة)" for baisa, "(سنتا)" for cents. Converting at ingest would restore EPS on the 181 "Unit not confirmed" pages.
- **Listing currency.** There is no per-listing currency anywhere. `build_portfolio_inputs_with_sectors.py:262-279` guesses it from Arabic labels and has no USD branch. Add a currency column per listing, with USD for the Bahrain dollar lines.
- **Tadawul turnover.** No Tadawul file has any (1,040,423 rows). The TradingView path writes `""` on purpose (`main_patched…:2561`).
- **Blank Tadawul changes.** `_fmt_change` (:2588-2593) returns an empty string for any change ≥ 0, so 552,830 Tadawul rows have a blank Change. The app does not read that column, but the files are wrong.
- **News and disclosures.** Their `as_of` is the fetch time. Tadawul collection has nearly stopped since September: 5 of 269 tickers have an item from the last 30 days. Disclosures were not refreshed on 10-17 or 10-18 (audit F3). The app now dates news by the newest item, so the lights show the gap.

## 4. Tadawul sectors: the owner's choice and what was built

The owner chose both options, in this order: "Fix the Tadawul sectors: hide the nine wrong sector ids now, and build a sector list from the Saudi Exchange's official classification to replace them."

**A. Hide the nine wrong ids** (commit `25e220b`)
- Ids 7, 8, 13, 27, 34, 35, 37, 38 and 40 are treated like the catch-all id 1: no sector (`api/app/universe.py`).
- The peers panel says the sector is unknown instead of "No peers in this sector".
- The screener labels the cell "Sector unknown".
- The portfolio's sector bars group these holdings under "Sector unknown" (it said "Other").

**B. The Saudi Exchange's own classification**
- **The list:** `api/app/data/tadawul_sectors.json`. It holds the 22 sectors and 273 companies of the Saudi Exchange's Main Market Watch, read from its English and Arabic pages on 2026-10-18. The file keeps both URLs and the date. The two pages list the same companies under the same sectors, and the build checked that symbol by symbol. Names are kept exactly as the exchange writes them, e.g. "Real Estate Mgmt & Dev't" / "إدارة وتطوير العقارات".
- **What changes on screen:**
  - Tadawul sectors now come only from that list; the pipeline's labels are no longer used for Tadawul.
  - A Tadawul company the list does not cover has no sector ("sector unknown"), never a guess. Today that applies to none of our 269.
  - 203 of the 269 change label. The 24 catch-all companies get a sector, e.g. 1111 Saudi Tadawul Group is Financial Services.
  - Bahri (4030) is filed under Energy, as the exchange files it.
- **Peers** now take their members from these sectors, not from the pipeline's labels in `briefs`.
- **/methodology** names the source and its date in both languages.
- **Upkeep:** the list must be refreshed when companies list or move sector. The 4 newest listings (1325, 4328, 6022, 7205) are on it but not yet in our universe.
- **Checks:**
  - API tests: 153 pass.
  - `web/scripts/check-sectors.mjs` checks all Tadawul companies against the list, peers within one sector, and the peers panel and Sector vs Sector page in both languages at 1440 and 390 px.
  - The local run passed 19 of 19 (`screenshots/sectors-local/`).

**Released**, in the owner's order, both through beta and then production:
- **A:** release `ed1b5f4`.
  - On beta (over the tunnel) and on alphacouncil.tech: 122 Tadawul companies without a sector, no mislabelled sector left, and the six right Utilities kept.
  - Almarai's peers panel said "Sector unknown, so no peers are listed" in both languages.
  - Screenshots: `screenshots/sectors-hidden-{beta,production}/`.
- **B:** release `4604fa0`.
  - `check-sectors.mjs` passed 19 of 19 on beta and again on alphacouncil.tech (`screenshots/sectors-check-production.txt`).
  - All 269 Tadawul companies carry the exchange's sector, and peers stay within one sector.
  - /methodology names the source and date.
  - The data-fix check from Part 1 still passes 46 of 46 on production.
  - Screenshots of the peers panel (Almarai, Maaden) and Sector vs Sector, in English and Arabic at 1440 and 390 px: `screenshots/sectors-{beta,production}/`.

The other markets keep the pipeline's sector labels. The audit found only scattered errors there, e.g. ADX "Aviation" holds hotels and a driving school.

The 5 USD-traded Bahrain listings still show BHD (Part 1, F5). Whether to keep a list for them is still the owner's call.
