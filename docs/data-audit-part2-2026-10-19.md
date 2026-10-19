# Market data audit, part 2: the server side (2026-10-19)

Part 1 (`docs/data-audit-2026-10-18.md`) measured the data from outside. This part reads the
pipeline on the server (`/opt/alphacouncil/backend`, read-only) to find why five faults happen,
and proposes a fix for each. Nothing on the server was changed.

## How the nightly run works (what was read)

- **Schedule** (root's crontab): `nightly_pipeline.sh` at 00:00 UTC, `MODE=daily WORKERS=4` on
  Sunday to Thursday and Saturday, `MODE=full WORKERS=8` on Friday. Steps: Argaam session gate
  (`argaam/_export_auth_state.py`), scrape (`argaam/run_parallel_universe.py`, which runs
  `argaam/main_patched2026_with_sectors.py` on each worker's chunk of `argaam/tickers.csv`),
  rebuild (`llm-council/run_rebuild_pipeline.py`), backend restart, alert email.
- **Daily mode scrapes only `news` and `chart`** (`DAILY_SECTIONS`, `main_patched…:6582`); overview
  and corporate actions always run. Disclosures, earnings, ownership and the rest run only in
  Friday's full run.
- **Last run**: `logs/LAST_RUN_STATUS.txt` = `[OK] 2026-10-19 02:18:19 … dailyrun_20261019: 716
  tickers`; `logs/cron.log`: `Scrape done count: 716/716`, `Rebuild exit code: 0`.
- **"Done" is not "succeeded"**: a ticker is marked done after any non-crashing attempt —
  success, partial or failed (`mark_done`, `main_patched…:7117-7123`). So 716/716 hides tickers
  whose chart step failed (9 today, see F-A).
- **Logs**: `logs/daily_<date>.log` (rebuild stage only) back to 2026-06-10; logrotate moves the
  content to `daily_<date>.log.1` and leaves an empty `.log`. The scraper's own lines are in
  `argaam/_parallel_runs/worker_<prefix>_w<i>.log` and in each ticker's
  `default_universe/<KEY>/harvest_runs/run_<time>/meta.json` (the newest 2 runs per ticker are
  kept, plus the newest full run).
- **Which code is current**: the server's checkout is git commit `a38dc07` (only
  `llm-council/RELEASE.json` modified). The local checkout `C:\AlphaCouncil-Staging\work\f11-prod-merge`
  (`3027ab5`) is *ahead* of it: `a38dc07` is an ancestor. The server's copy is the truth; a
  code-only copy of it is in `C:\AlphaCouncil-Staging\work\pipeline-fixes-20261019\server\`.
- **Source checks** below fetch Argaam's public pages and its chart endpoint
  (`https://www.argaam.com/en/charts/history?symbol=C_<companyID>&resolution=1D`) from the
  owner's computer, read-only.

## F-A. The six stopped tickers

**Root cause: Argaam renamed company pages; the pipeline still uses the old URLs from
`argaam/tickers.csv`, the old URLs answer 404, and the failure is recorded as "done".** One
exception: TAQA, whose source data itself stops.

| Ticker | URL in `tickers.csv` | Today | Current page | Latest run's chart result |
|---|---|---|---|---|
| 2080 GASCO | `/en/tadawul/tasi/gasco` | 404 | `/en/tadawul/tasi/gasco-holding` (Argaam id 69 redirects there) | `tv_entity_id_not_found` |
| 4240 AFG | `/en/tadawul/tasi/cenomi-retail` | 404 | `/en/tadawul/tasi/afg-retail` (id 917 redirects there) | `tv_entity_id_not_found` |
| AGILITY (ADX) | `/ae-ar/companies/adx/agility-global` | 404 | `/ae-ar/companies/adx/agility-global-plc` (already in `tickers_uae.csv`) | `date_setting_failed_after_2_attempts` (no date box on a 404 page) |
| GULFNAV (DFM) | `/ae-ar/companies/dfm/gulf-navigation` | 404 | `/ae-ar/companies/dfm/gulf-navigation-holding` (page names "الخليج للملاحة") | same |
| 624 KPPC (KSE) | `/kw-ar/companies/kse/kppc` | 404 | **none found**: not in Argaam's Boursa Kuwait menu (128 companies); 4 guessed slugs 404 | same |
| TAQA (ADX) | `/ae-ar/companies/adx/taqa` | 200 | unchanged | ok, 5,174 rows, **newest 06/08/2026**: Argaam's own data stops there |

Evidence on the server:

- `default_universe/2080_TADAWUL/harvest_runs/run_20261019_000549/meta.json`: `sections.chart.errors
  = ["tv_entity_id_not_found"]`, `overview.counts.market_rows = 0`, `company_entity_id_guess = ""`;
  the saved `2080_overview_raw.html` has an empty `<title>` and no canonical link (Aramco's has
  both). `price_history_10y.csv` last written 2026-07-24 00:15, `.news_state.json` 2026-07-25.
- The same `meta.json` field for AGILITY_ADX (`run_20261019_003131`), GULFNAV_DFM (`…_004642`),
  624_KSE (`…_011445`) and 4240_TADAWUL (`…_001850`) shows the errors in the table; their price
  files were last written 2026-07-24 (AFG 2026-10-08). TAQA_ADX (`…_004350`) has `chart ok True`,
  dates max `06/08/2026`, and a price file rewritten today.
- A scan of every ticker's newest run (10-18 or 10-19) finds 9 chart failures: the 5 above plus
  412_KSE (`/kw-ar/companies/kse/eresco`), AKIC.AD_ADX (`…/adx/al-khazna-insurance`), BILDCO_ADX
  (`…/adx/bildco`) and BMUSC.BH_BSE (`/bh-ar/companies/bse/bank-muscat-s-a-o-g`), all
  `date_setting_failed_after_2_attempts`. These four were not part of this audit's six and were
  not checked against Argaam.
- Why nobody was told: `mark_done` (above) and the nightly script count attempts, not price
  files. When a run has no price file, `tools/select_latest_complete.py` reuses an older run's
  (part 1, P2), so the app keeps serving the July bars, correctly marked stale.

**Proposed fix** (server copy): (1) `argaam/tickers.csv` lines 47, 174, 286 and 410: the four
current paths above (company and profile). (2) A post-scrape check,
`argaam/tools/chart_failures.py`, called by `nightly_pipeline.sh` after the scrape. It lists
tickers whose newest run has `sections.chart.ok = false` or no price file newer than 7 days,
and adds the list to the run's alert and `LAST_RUN_STATUS.txt`. KPPC and TAQA need the owner's
call (delisted or suspended?), not code.

**Check after a nightly run:** `price_history_10y.csv` of 2080_TADAWUL, 4240_TADAWUL, AGILITY_ADX
and GULFNAV_DFM has a bar dated after the fix; the alert lists the remaining chart failures.

## F-B. ADX and DFM prices below 1 AED stored with 2 decimals

**Root cause: the UAE price path copies Argaam's HTML price table cell by cell
(`_scrape_chart_ajax_form`, `main_patched…:2797-2817`), and that table prints 2 decimals.** Argaam's
chart endpoint has the full price for the same day and the same volume.

| Day | INVESTB stored (table) | Chart endpoint C_5406 | SHUAA stored | Chart endpoint C_5709 |
|---|---|---|---|---|
| 2026-10-15 | close 0.03, vol 17,325,859 | close 0.026, vol 17,325,859 | 0.24, vol 8,617,497 | 0.237, vol 8,617,497 |
| 2026-10-16 | close 0.03, vol 62,324,264 | close 0.026, vol 62,324,264 | 0.24, vol 8,860,070 | 0.24, vol 8,860,070 |

(Stored rows: `default_universe/INVESTB_ADX/price_history_10y.csv`, `SHUAA_DFM/…`, last rows.
Both chart pages expose the id: `harvest_runs/run_20261019_003829/chart_raw.html: companyID = 5406`.)
The TradingView paths (Tadawul, and the non-KSA fallback) also cut every price to 2 decimals
with `_fmt_price` → `f"{float(val):.2f}"` (`main_patched…:2583-2586`).

**Proposed fix:** in `_scrape_chart_ajax_form`, after the table rows are read, fetch the chart
endpoint for the page's `companyID` and replace Price/Open/High/Low on each row whose date and
volume match and whose rounded close equals the table's. Rows that do not match keep the table's
value, and a fetch failure changes nothing. `_fmt_price` keeps up to 4 decimals (at least 2).
The CSV format (Arabic headers, `yyyy/mm/dd`, quoted thousands) is unchanged.

**Check after a nightly run:** INVESTB_ADX's and SHUAA_DFM's newest bars have 3 decimals and the
same volumes as before; no sub-1 ADX/DFM ticker's last 5 bars are all 2-decimal.

## F-C. Repeated bars on market holidays (Muscat, Bahrain)

**Root cause: the source repeats the last session on closed days. Both Argaam's table and its
chart endpoint have the copies, and the pipeline writes them as they come** (`write_price_csv`,
`main_patched…:6543-6550`; `compute_indicators.py` only removes duplicate dates).

`default_universe/AACT_MSM/price_history_10y.csv`:

```
2026/03/19,0.178,0.00,0.00 %,"1,019,825","180,529",0.178,0.178,0.176
2026/03/22,0.178,0.00,0.00 %,"1,019,825","180,529",0.178,0.178,0.176
2026/03/23,0.178,0.00,0.00 %,"1,019,825","180,529",0.178,0.178,0.176
```

The chart endpoint (C_5524, AACT's `companyID`) returns the same three bars (v 1019825, a 180529).
So switching sources would not help.

**Proposed fix:** `write_price_csv` drops a row whose Price, Open, High, Low, Volume and Turnover
all equal the previous trading row's, when Volume is above 0. The first of the run is kept (the
real session). This applies to every price path.

**Check after a nightly run:** AACT_MSM has no bar on 2026-03-22 or 03-23; part 1's scan of
identical consecutive bars finds 0 on MSM and BSE.

## F-D. Tadawul disclosures stalled

**Root cause, two parts:**

1. **The list the pipeline reads stopped at the source.** For 267 of 269 Tadawul tickers,
   discovery picks the company's English "Disclosures" list, Argaam section 204
   (`…/en/article/entityarticles/sectionid/204/entityid/4/<id>/pageno`, discovery at
   `main_patched…:1652`). On Argaam, Aramco's section 204 ends at **2026-03-10** in English and
   Arabic. Across the 244 Tadawul tickers with dated rows in the 2026-10-16 full run, the newest
   item has a **median of 2026-03-08** (the latest of all: 2026-10-05). Argaam still publishes
   Tadawul disclosures in its **market-wide** lists: section 245 market 3 (Arabic, items dated
   2026-10-19 and 10-18) and section 244 market 3 (English, 2026-10-15). Company news such as
   "Saudi Aramco to disclose Q3 2026 results on Nov. 3" now sits in the company's "Latest News"
   (section 205, newest 2026-10-08), which the pipeline reads as news.
2. **"Since 10-16" is the schedule.** Disclosures run only in Friday's full run (`DAILY_SECTIONS =
   {"news", "chart"}`), and 2026-10-16 was the last Friday. The `.disclosures_state.json` of the
   Tadawul tickers is dated 2026-10-16.

Evidence: `default_universe/2222_TADAWUL/harvest_runs/run_20261016_*/meta.json`: `discovery.disclosures`
= section 204 URL, `counts.listed_total 75, filtered_by_cutoff 64`; its `disclosures_listing.csv`
starts `10/03/2026, 03/02/2026, 26/01/2026`. Other exchanges in the same run: ADX 9,747 rows for 99
tickers, Tadawul 2,700 for 244. Also in that run, 79 Tadawul `news` sections failed with no error
text. Why is not established; it is the next check.

**Proposed fix: needs a new source mapping, so it is not in this patch** (Step 4's rule). Read
the market-wide list (section 245, market 3) once per run and give each item to the ticker its
company link names, as a daily section. It is new code (estimated 100+ lines) and an owner
decision. Until then, the app dates disclosures by their newest item, so the light shows the gap.

**Check after it is built:** Aramco's newest disclosure in the API is within 7 days of the run.

## F-E. No turnover for Tadawul

**Root cause: the TradingView path writes an empty Turnover on purpose (`"",  # turnover — not in
TV response`, `main_patched…:2561`, and `:2636` in the fallback), but the response does carry
it** in field `a`:

| | Volume | `a` from the chart endpoint | Stored turnover |
|---|---|---|---|
| SHUAA_DFM 2026-10-16 (C_5709) | 8,860,070 | 2,119,461 | 2,119,461 (from Argaam's table) |
| 2222_TADAWUL 2026-10-18 (C_3509) | 7,566,565 | 194,479,915 | *(empty)* |

Aramco's stored row: `18/10/2026,25.80,, %,7566565,,25.30,25.82,25.30`: the turnover is empty
(and so is the Change; see "Also found").

**Proposed fix:** both TradingView paths write `int(a[i])` as Turnover when the field is present,
`""` otherwise.

**Check after a nightly run:** 2222_TADAWUL's newest bar has a turnover; turnover ÷ volume lies
between that day's low and high on Tadawul bars.

## Fix table (for the owner, Step 5)

| Fault | Fix | Where (server copy) | Size | Risk | Check after a night |
|---|---|---|---|---|---|
| F-A stopped tickers | 4 new page paths | `argaam/tickers.csv` lines 47, 174, 286, 410 | 4 rows | low: data only | the 4 tickers get a bar after the fix |
| F-A silent failures | list chart failures in the alert | new `argaam/tools/chart_failures.py`; `_bin/nightly_pipeline.sh` (server `/opt/alphacouncil/bin/`) | ~40 lines | low: read-only report | the OK email names the failing tickers |
| F-B 2 decimals | full-precision overlay from the chart endpoint; `_fmt_price` keeps 4 decimals | `main_patched2026_with_sectors.py`: `_scrape_chart_ajax_form`, `_fmt_price`, new `_tv_price_overlay` | ~45 lines | medium: one extra request per UAE ticker; a mismatch keeps the old value | INVESTB, SHUAA newest bars have 3 decimals |
| F-C holiday copies | drop identical consecutive bars | `main_patched…`: `write_price_csv` | ~20 lines | low: a real session identical in 6 fields and volume is not expected | no AACT bar on 2026-03-22/23 |
| F-D disclosures | market-wide list per company, daily | `main_patched…`: `discover_listings_ui_driven` (Tadawul disclosure link, :1652), `scrape_single_ticker` (sections list, :6750), `DAILY_SECTIONS` (:6582); new parser for the 245 list | 100+ lines | owner decision | Aramco's newest disclosure ≤ 7 days old |
| F-E Tadawul turnover | write field `a` | `main_patched…`: the two TradingView paths | 2 lines | low | 2222's newest bar has turnover |

## Dry run (2026-10-19, nothing written on the server)

The fixes are in `docs/pipeline-fixes-2026-10-19.patch`. It holds four commits made against an
exact-bytes copy of the server's tracked files (`a38dc07`) plus `/opt/alphacouncil/bin/*.sh` as
`_bin/`, in the order F-A, F-E, F-B, F-C. F-A, F-E and F-C each apply alone on the baseline
(checked); F-B applies only on top of F-E, whose lines sit next to `_fmt_price`. 172 lines added,
9 removed. On a clean copy:
`git apply --check --exclude='_bin/*'` passes for the backend part, and
`git apply --check -p2 --include='nightly_pipeline.sh'` for the script in `/opt/alphacouncil/bin/`.
Every changed Python file compiles, and `bash -n` passes on the script. `tickers.csv` is CRLF on
the server; the patch keeps it (`*.patch -text` in `.gitattributes`). Outputs:
`C:\AlphaCouncil-Staging\work\pipeline-fixes-20261019\dryrun_{a,b_e,c}.txt`.

**F-A**: `tools/chart_failures.py`, run read-only on the live universe, prints
`no fresh price chart: 33 (…)`. These are the 9 chart failures above plus 24 of part 1's tickers
with no price file (F11). The new page paths answer 200 for overview, profile and chart, with
`companyID` 69 (GASCO), 917 (AFG), 16998 (AGILITY) and 7525 (GULFNAV). The chart endpoint has
bars up to 2026-10-19 for GASCO (59.00), AFG (13.10) and AGILITY (1.45). For GULFNAV it has
none: its prices come from the page's table, which the date box needs. The scrape itself could
not be dry-run here, because it needs the Argaam login and Playwright on the server. It is
checked after the first night (below). The digest's new line was tested on a sample status
text: it picks out `no fresh price chart: 3 (412_KSE, AKIC.AD_ADX, FAMILY B_BSE)` and still
reads the run count as 716.

**F-B**: the patched `_tv_price_overlay` on copies of the stored files, with the live endpoint:

| File | Bars | Changed | Last 3 closes before → after |
|---|---|---|---|
| INVESTB_ADX | 336 | 147 | 0.03, 0.03, 0.03 → 0.027, 0.026, 0.026 |
| SHUAA_DFM | 2,378 | 1,809 | 0.24, 0.24, 0.24 → 0.244, 0.237, 0.24 |
| E7_ADX | 1,038 | 507 | 0.91, 0.91, 0.91 → 0.911, 0.908, **0.905** (part 1's reference: 0.905) |
| EMAAR_DFM (above 1 AED) | 2,500 | 0 | unchanged |

In every file the dates, volumes and turnovers are unchanged, and no close moved by more than
0.005. Of the last 60 bars, 56 of INVESTB's and 51 of SHUAA's now have 3 decimals; the rest
end in 0 (0.24). `_fmt_price` samples: 0.026 → `0.026`, 25.8 → `25.80`, 59 → `59.00`,
2.345 → `2.345`. Side effect: Tadawul history from the chart endpoint is split-adjusted
(e.g. 28.9771 in 2019) and will keep 4 decimals instead of being rounded to 2. Last prices are
unaffected, and `check-data-fixes.mjs` accepts 2 or 3 decimals for the header price.

**F-C**: `_drop_carried_forward_bars`, run read-only over all 691 price files on the server:

| Exchange | Last 12 months | Main dates | 10 years |
|---|---|---|---|
| MSM | 137 bars, 50 tickers | 2026-03-22 (41), 03-23 (38), 2025-11-27 (36) | 2,433 |
| BSE | 47 bars, 19 tickers | 2026-03-23 (12), 2025-12-17 (12), 2026-06-28 (12), 03-24 (10) | 225 |
| DFM / ADX / KSE | 9 / 2 / 3 | isolated | 75 / 53 / 245 |
| QSE / TADAWUL | 0 / 0 | — | 8 / 164 |

This matches part 1's scan (MSM 139 on 50 tickers, BSE 48 on 19). AACT_MSM loses 2026/03/22 and
03/23 and keeps 03/19. The older drops (2,433 on MSM) are the same pattern in earlier years. The
164 Tadawul drops are all from before October 2025 and were not looked at one by one.

**F-E**: the patched `_fmt_turnover` on Aramco's endpoint data (C_3509) gives a turnover for
all 1,710 bars. The stored 15/10 and 18/10 rows have `''`; patched they get 254,682,248 and
194,479,915. Turnover ÷ volume lies inside the day's low–high on 1,702 bars. The 8 outside are
7 split-adjusted bars from 2019–2022 and 2024-06-09, the day of Aramco's secondary offering.
The API already shows value traded whenever a file has it (`value_traded_reason` is set only
when no bar has turnover, `api/app/routers/ticker.py:236`).

## Applying it (Step 6, after the owner's go-ahead)

```bash
# on the server, as root; first back up every file the patch touches
cd /opt/alphacouncil/backend
for f in argaam/tickers.csv argaam/main_patched2026_with_sectors.py llm-council/scripts/health_digest.py; do cp -p "$f" "$f.bak-20261019"; done
cp -p /opt/alphacouncil/bin/nightly_pipeline.sh /opt/alphacouncil/bin/nightly_pipeline.sh.bak-20261019
git apply --check --exclude='_bin/*' /root/pipeline-fixes-2026-10-19.patch && git apply --exclude='_bin/*' /root/pipeline-fixes-2026-10-19.patch
cd /opt/alphacouncil/bin && git apply --check -p2 --include='nightly_pipeline.sh' /root/pipeline-fixes-2026-10-19.patch && git apply -p2 --include='nightly_pipeline.sh' /root/pipeline-fixes-2026-10-19.patch
/opt/alphacouncil/pipeline-venv/bin/python -m py_compile /opt/alphacouncil/backend/argaam/main_patched2026_with_sectors.py && bash -n /opt/alphacouncil/bin/nightly_pipeline.sh
```

To apply only some fixes, apply the matching commits from the patch file (they are separate
`From …` sections). To undo: copy each `.bak-20261019` file back and remove
`argaam/tools/chart_failures.py`.

Also found, not in the patch: `_fmt_change` returns `""` for any change ≥ 0, so Tadawul files have
a blank Change on up days (part 1). One line to fix if the owner wants it.

Not covered by this part: the Pro panels (financials, ownership, calendar) against the database,
listed in PROJECT.md Step 3's description but not in its done-when list. Left for a later
read-only pass.
