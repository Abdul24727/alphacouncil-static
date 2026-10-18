# Market data audit, 2026-10-18 (part 1: measured from outside the server)

Read-only review of the market data behind https://alphacouncil.tech. Measured on Sunday 2026-10-18 between
09:05 and 09:55 UTC. At that time the last expected closes were Thursday 2026-10-15 for Tadawul, QSE,
Boursa Kuwait, Bahrain and Muscat (all trade Sunday to Thursday), and Friday 2026-10-16 for ADX and DFM
(Monday to Friday).

> **Scope limit: no server access.** This session's SSH to `root@alphacouncil.tech` was refused by the
> session's permission check ("Production Reads"), so nothing here was read from the server: no pipeline logs,
> cron or timers, no SQLite file and no raw price CSV. Everything below comes from the site's public API and
> pages (which only show what the databases hold), the repository code, and a public reference site.
> Run history, database-level checks and the Pro-only panels are **not measured**; section 8 lists them,
> with the read-only commands to run once access is granted.
>
> **Nothing found that looks like a stopped pipeline.** The 2026-10-18 nightly run wrote 679 of the 691 price
> files (file times 00:01–01:43 UTC; 4 more were last written on 10-17), refreshed fundamentals (705 rows, 01:47),
> news (707 of 714 rows, 00:01–01:43) and the three indices (02:16). **Watch item:** disclosures were last refreshed on 2026-10-16 for
> all 716 tickers, so the 10-17 and 10-18 runs did not refresh them. That may be the schedule (not visible
> without cron). If the 2026-10-19 run does not refresh them either, the disclosures step has stopped.

## 1. Scorecard

| Area | Verdict | Key numbers |
|---|---|---|
| Scraper performance | **Not measured** (no logs) | Last run on time for 4 of 5 categories; 679 of 691 price files written. The `prices` success stamp is written for every ticker, fetched or not. 6 tickers have had no new prices for 11 days to 3 months although the market traded them (5 confirmed by the reference, KPPC likely): GASCO, Agility (ADX), Gulf Navigation and KPPC since 2026-07-23, TAQA since 2026-08-06, AFG since 2026-10-07. |
| Coverage | Fair | Price files 691/716 (96.5%); 25 tickers have none (12 ADX, 6 DFM, 6 BSE, 1 KSE). Fundamentals row 705/716. Tadawul news and disclosures: 5 of 269 tickers have an item from the last 30 days; the other exchanges 440 of 447. Bahrain dividend yield 0/39. EV/EBITDA 8/716. |
| Freshness | Prices good; news **misleading** | 51 of 691 header prices are stale; at least 5 of them are scraper gaps, the rest suspended, delisted or untraded. All 48 checked pages show the same lights as the API. But 262 Tadawul pages show a **green news light** while their newest item is older than 30 days (median newest item 2026-03-03). |
| Integrity | **Poor** | Tadawul sectors: 98 of 269 in the wrong sector, 24 more with none. EPS in fils/baisa shown as KWD/BHD/OMR on about 170 pages. 12 cross-listed tickers carry the wrong currency. 31 ADX/DFM stocks under 1 AED priced in 2 decimals instead of 3. Phantom bars on Muscat and Bahrain holidays. No turnover on any Tadawul bar. |
| Accuracy (34 tickers vs reference) | Prices good; ratios weak | Close 31/33 exact. Close date 28/32 (1 real error). Market cap within 2%: 26/32. P/E within 5%: **12/23**. Dividend yield within 0.25 pp: 14/18. Last dividend: not compared (Pro-only). |
| Delivery (page ↔ API) | Good | 48 pages: lights, header quote, chart last bar and key metrics equal the API's values. Exceptions: the header rounds 3-decimal prices to 2 (13 of 48 pages), and Arabic names show on English pages where the English name is missing (9 tickers). Database ↔ API not measured. |

Severity used below: **blocker** = wrong numbers at scale on core screens, fix before advertising;
**major** = wrong, missing or mislabelled data for a group of tickers; **minor** = cosmetic, historical or rare.

## 2. How this was measured

- **Site API, public, one request at a time** (a ~0.5 s pause between requests, user agent
  `AlphaCouncil-data-audit`): `GET /api/v1/tickers` (universe, 716), `/screener`, `/market/exchanges`,
  `/market/overview?lang=en|ar`, `/methodology`, and for **every** ticker `/tickers/{slug}` (quote, valuation,
  freshness rows), `/tickers/{slug}/news?limit=50` and `/tickers/{slug}/prices` (the bars the chart gets).
  716 × 3 requests, 0 errors.
- **Pages:** 48 stock pages (`/en/t/{slug}`) loaded in headless Chrome (the repo's `playwright-core`). For each
  page I recorded the `data-freshness` light of each panel, the header and the Key metrics text, plus the API
  responses that page itself received, then compared them.
- **Reference:** stockanalysis.com quote and dividend pages (its robots.txt allows `/quote/`), one request
  every 5 s, for a seeded random sample (`random.Random(20261018)`, stratified 8 Tadawul, 4 ADX, 4 DFM, 4 QSE,
  4 KSE, 3 BSE, 3 MSM from tickers with price files), plus 4 large caps and about 20 targeted checks
  (currencies, stopped tickers). Its data is delayed and third-party; it stamps a stock that did not trade with
  the latest session date. Saudi Exchange, Boursa Kuwait and MarketScreener answered "Access Denied" to a plain
  client, so they were not used. Argaam's robots.txt allows `/en/company/…`, but its company ids were not
  available without the server.
- The API itself filters what it reads (`api/app/prices.py`): it drops rows with a close ≤ 0 or an unreadable
  date, keeps one row per date and blanks O/H/L when they contradict the close. So zero or negative prices and
  duplicate dates in the raw files cannot be seen from outside (section 8).

## 3. Findings

### F1. Tadawul sector labels are wrong for 98 companies, and 24 more have none (blocker, pipeline)

Groups of Tadawul companies carry another group's label. English and Arabic labels agree with each other
(for example "Transportation" / "النقل"), so the pipeline's sector table is wrong, not the translation.
The 24 without a sector are `sector_id` 1, which `universe.py` already blanks.

```
curl -s https://alphacouncil.tech/api/v1/tickers | python -c "import json,sys,collections; \
 d=collections.defaultdict(list); [d[t['sector_en']].append(t['symbol']) for t in json.load(sys.stdin) if t['exchange']=='TADAWUL']; \
 [print(s,len(v),v) for s,v in d.items()]"
```

| Label shown | Companies under it (examples) | What they are | Count |
|---|---|---|---|
| Transportation | 2280 Almarai, 2050 Savola, 2270 SADAFCO, mills, agriculture | Food producers (and 3 restaurant/catering) | 23 |
| Hotels & Restaurants | 1211 Maaden, 1210 Basic Chemicals, 2300 Saudi Paper, 2180 FIPCO, 2070 SPIMACO | Materials (and 3 pharma/medical) | 24 |
| Entertainment | 1320 Saudi Steel Pipes, 2110 Saudi Cable, 2040 Saudi Ceramic, 1302 Bawan | Capital goods | 19 |
| Metals & Mining | 4030 Bahri, 4040 SAPTCO, 4264 flynas, 4263 SAL | Transportation | 10 |
| Tobacco | 4002 Mouwasat, 4004 Dallah, 4007 Al Hammadi, 4009 MEAHCO | Health care providers | 8 |
| Chemicals | 1831 Maharah, 4072 MBC Group, 4210 SRMG, 4070 Tihama | Media; commercial services | 6 |
| Media | 4280 Kingdom Holding, 2030 SARCO, 4080 Sinad, 4130 Darb | Diversified / holding / energy | 6 |
| Food Retail | 4142 Riyadh Cables | Capital goods | 1 |
| Utilities | 1832 Sadr Logistics (the other 6 are right) | Transportation | 1 |
| *(none)* | 1111 Tadawul Group, 6017 Jahez, 1830 Leejam, 4084 Derayah… | sector_id 1, unclassified | 24 |

Affected: the screener's sector filter, peers ("same sector"), the sector templates (Sector vs Sector, the
sector percentiles in Financials), and the Copilot's context. Earlier audits flagged single cases
(`pre-launch-audit.md` D5, `qa-2026-10-16-response.md`); the fault is systematic. Other exchanges have
scattered errors only, e.g. ADX "Aviation" holds ADNH (hotels), ADNHC (catering) and DRIVE (driving school);
MSM "Consumer Discretionary" holds BWPC (water and power) and ASYAD (logistics).

### F2. EPS (TTM) for Kuwait, Bahrain and Oman is in fils/baisa but labelled KWD/BHD/OMR (blocker, pipeline + web app)

Key metrics shows NBK "EPS (TTM) 63.740 KWD" at a price of 0.815 KWD, and BMMI "27.730 BHD" at 0.495 BHD.
P/E is right (0.815 / 0.06374 = 12.79), so only the EPS figure is off by 1000×. Book value is in the main unit
(BMMI 0.44 BHD), so the two rows on the same panel use different units.

Check: for each KWD/BHD/OMR ticker, the ratio of `valuation.eps_ttm` to `last_price / pe`:

| Currency | EPS shown | EPS ≈ 1000× the price's unit | In the price's unit | Unclear | No P/E to check against |
|---|---|---|---|---|---|
| KWD | 133 | 95 | 0 | 3 | 35 |
| BHD | 35 | 24 | 2 | 1 | 8 |
| OMR | 59 | 49 | 1 | 1 | 8 |

The KWD row includes the Kuwaiti companies listed on DFM, which trade in AED (F5): IFA shows EPS 99.13 against a
5.90 price, NIND 236.21 against 3.37.
Cause: `scraped_ratios.eps_ttm` is stored in sub-units (pipeline), and `overview-panels.tsx:166` labels it with
the listing currency (web app).

### F3. News and disclosures: Tadawul collection has nearly stopped, and the news light stays green (major, pipeline + web app)

- **Tadawul items are drying up.** Per-ticker items dated in each month (the 50 newest per ticker): 2026-06:
  125, 07: 62, 08: 64, **09: 16, 10: 3**. That is during the Q3 results season. The newest item per Tadawul
  ticker has a median of 2026-03-03 (Aramco's newest is 2026-03-09, Riyad Bank's 2026-07-11). Only 5 of 269
  Tadawul tickers have an item from the last 30 days and 34 from the last 90; 15 have none at all
  (1212, 1214, 1810, 2220, 4006, 4141, 4333, 4334, 4349, 6002, 8070, 8100, 8160, 8300, 8310). On the other
  six exchanges, 440 of 447 tickers have an item from the last 30 days; the newest per ticker has a median of
  2026-10-14 (QSE 2026-09-29).
- **The light says fresh anyway.** The `news` freshness row's `as_of` is the time of the fetch (2026-10-18
  00:07 for Aramco), not the date of the newest item. `freshness.py` trusts `as_of`, so **262 Tadawul pages show
  a green news light while their newest news or disclosure is more than 30 days old (or there is none)**.
  This breaks the site's rule that missing data is labelled. The same holds for `disclosures`
  (max_age 120 days, as_of = fetch time) and for the index levels (`market_indices.fetched_at`).
- **Languages:** every Tadawul item is English (Argaam `/en/` URLs, 3,283 items) and every item from the other six
  exchanges is Arabic (22,180 items). Of those Arabic items, 989 (4.5%) carry an English headline and 375 (1.7%)
  an English summary. The English home feed's newest English-readable item is from 2026-09-21. Of the 10 newest
  Arabic market items, none has an English headline or summary; the newest that does is from 2026-07-12. So
  `news_ai` has covered nothing recent.
- **Duplicates:** 357 repeated items within a ticker's newest 50 (186 with the same URL, 171 with the same title
  and day). The same-URL repeats are mostly MSM 51, QSE 49 and BSE 47.
- The per-ticker "news" section is nearly empty everywhere (Tadawul 265 of 269 tickers have none); nearly
  everything is filed as "disclosures".

```
curl -s "https://alphacouncil.tech/api/v1/tickers/2222/news?limit=50"   # newest item 2026-03-09
curl -s "https://alphacouncil.tech/api/v1/tickers/2222/freshness"       # news as_of 2026-10-18T00:07, stale false
```

### F4. Six tickers stopped updating while the market traded them, and the pipeline then drops them (major, pipeline)

The site labels their prices stale (amber light, "As of" date), so nothing is passed off as current. But the
data is a scraper gap: the reference shows these stocks trading after our last bar.

| Ticker | Our last bar | Reference | News last fetched | Fundamentals row |
|---|---|---|---|---|
| 2080 GASCO (Tadawul) | 2026-07-23, 67.30 | traded 2026-10-15, 58.80 (vol 58,668) | 2026-07-25 | none |
| AGILITY (ADX) | 2026-07-23, 1.75 | traded 2026-10-16, 1.48 (vol 3.09 M) | 2026-07-25 | none |
| GULFNAV (DFM) | 2026-07-23, 2.84 | traded 2026-10-16, 2.86 | 2026-07-25 | none |
| 624 KPPC (Boursa Kuwait) | 2026-07-23, 0.149 | no reference page | 2026-07-28 | none |
| TAQA (ADX) | 2026-08-06, 2.66 | last trade 2026-08-31, now "inactive" | 2026-10-18 | yes |
| 4240 AFG (Tadawul) | 2026-10-07, 14.54 | traded 2026-10-15, 13.11 (vol 298,051) | 2026-10-08 | none |

Pattern: the pipeline stops writing the ticker's price file (file time 2026-07-24 for the four July tickers,
2026-10-08 for AFG), yet its own `prices` freshness row still records a successful fetch at 2026-10-18 01:47,
as it does for every ticker. That stamp is therefore not evidence of a fetch. One to five days later the ticker
drops out of the news fetch and its `fundamentals` freshness row disappears. BILDCO
(ADX, last bar 2026-09-17, file last written 2026-09-18, news last 2026-09-22, no fundamentals row) and AKIC.AD
(file 2026-09-18, news 2026-09-21) follow the same path; the reference has no BILDCO page. Four tickers on four exchanges stopped on the same day
(2026-07-23), which points to one change in the pipeline's ticker list or source ids, not to the market. The
cause needs the logs (section 8). The list is growing: AFG joined on 2026-10-07.

### F5. Wrong trading currency on 12 cross-listed tickers (major, pipeline)

The pipeline gives some listings their company's home currency instead of the currency the listing trades in.
The header, market cap and the portfolio's currency groups then use the wrong currency.

| Ticker | Shown | Trades in (reference) |
|---|---|---|
| ABC.BH, ARIG.BH, GFH.DU, ITHMR.BH, INOVEST (Bahrain) | BHD | USD ("Price in USD") |
| KFH (Bahrain) | KWD | USD |
| NIND, IFA, EKTTITAB, NIH (DFM) | KWD | AED (verified NIND, IFA) |
| GIH (ADX) | KWD | AED (same pattern; no price file) |
| OEIHC (ADX) | OMR | AED |

Example: ARIG shows "0.94 BHD", market cap 206.8 M "BHD"; the reference has 0.94 USD and 70.21 M BHD.
UGH was checked and is correctly BHD.

### F6. ADX and DFM prices below 1 AED have only 2 decimals (major, pipeline/source)

All 31 ADX and DFM stocks priced under 1 AED have only 2-decimal closes in their last 120 bars, while the
exchanges tick in 0.001. E7 shows 0.91 (reference 0.905). SHUAA shows 0.24 and 0.00% for a day the reference has
0.240, +1.27%. Day changes, returns and volatility for these stocks are distorted, and the rounding creates fake
moves: Invest Bank (INVESTB) alternates 0.03 ↔ 0.04 and reads as ±25–33% days, four times in 2026. Affected:
ADNH, ADNHC, AKIC.AD, ALEFEDT, CBI, DANA, E7, ESHRAQ, FCI, INVESTB, JULPHAR, LULU, MANAZEL, METH.AD, OEIHC, PHX,
RAKPROP, RAKWCT, SUDATEL (ADX); ALANSARI, ALFIRDOU, ALSALAMS, AMAN, DEYAAR, DSI, EKTTITAB, ITHMR, MAZAYA,
SHUAA, UPP, WATANIA (DFM). Sub-1 prices on QSE, KSE, BSE and MSM do carry 3 decimals.

### F7. The header rounds 3-decimal prices to 2 (major, web app)

`StockTemplate.tsx:72` formats the header price with `fmtNumber(q?.last_price)` (2 digits), while the peers table
uses `priceDigits(currency)`. On 13 of the 48 pages checked, the header disagrees with the API: NBK 0.815 → "0.82",
Ekttitab 0.031 → "0.03", KMEFIC 0.126 → "0.13", UFCI 0.087 → "0.09". `priceDigits` (`common.tsx:11`) also returns
2 for QAR, so QSE prices such as QCFS 2.345 and UDCD 0.711 lose their third decimal.

### F8. Phantom bars on Muscat and Bahrain market holidays (major, pipeline/source)

During the Eid al-Fitr closure, 38–41 Muscat tickers have bars on 2026-03-19, 03-22 and 03-23. Total volume on
03-19 and 03-22 is identical (214,466,262 shares), so one day's data is repeated under holiday dates. A scan of
the last year for bars identical to the previous one (same O/H/L/C and non-zero volume):

| Exchange | Repeated bars | Tickers | Main dates |
|---|---|---|---|
| MSM | 139 | 50 | 2026-03-22 (41), 03-23 (38), 2025-11-27 (36) |
| BSE | 48 | 19 | 2026-03-23 (12), 2025-12-17 (12), 2026-06-28 (12), 2026-03-24 (10) |
| DFM / ADX / KSE | 10 / 3 / 3 | 6 / 3 / 2 | isolated |

These inflate volume and add 0% days to returns and volatility. Separately, the API blanks O/H/L as
inconsistent on 668 Muscat bars in the last year (about 5% of Muscat bars; other exchanges are at 0.02–0.2% of
all bars).

### F9. No turnover for any Tadawul bar (major, pipeline)

The turnover column is empty in all 269 Tadawul price files (1,040,954 bars), so "Value traded" is N/A on every
Tadawul page. All other exchanges have it on the last bar, except 3 tickers.

### F10. P/E and dividend yield often disagree with the reference (major, pipeline; cause not determined)

On the sample (section 4), the P/E is within 5% of the reference for only 12 of 23 tickers. Large gaps:
UDCD 16.56 vs 6.24, RAPCO 19.86 vs 8.29, 1831 10.60 vs 6.75, PUREHEALTH 18.05 vs 13.56. Amlak shows an EPS of
−0.10 AED (so no P/E), while the reference has net income of +1.53 bn and a P/E of 1.17. This points to stale or
differently based TTM earnings, but which side is right was not established. Dividend yields disagree for 4 of 18
(3060 9.03% vs 10.84%, 7020 4.65% vs 4.98%, 4007 4.88% vs 3.55%, E7 10.72% vs 11.05%). Other ratio checks across
all 716 tickers:
- 4144 (Raoom) shows P/E 98.73 with EPS −1.06. ratios.py nulls a P/E ≤ 0, but this one is positive while the EPS
  is negative.
- ORIENT (DFM) shows a dividend yield of 150.83% and SAWAEED (ADX) 30.22%; both are tickers without a price file.
  Amlak's 41.88% matches the reference (a special distribution).
- Missing: dividend yield for all 39 Bahrain tickers (the reference has them, e.g. ZAINBH 7.56%); EV/EBITDA for
  708 of 716; P/E for 100 of 269 Tadawul tickers.

### F11. 25 tickers have no price file (major, pipeline)

12 ADX (AFNIC, ALAIN, AWNIC, DHAFRA, FIDELITY, GIH, MBME, RAKN.AD, SAGA, SAWAEED, SICO, TNI), 6 DFM (ALLIANCE,
ASNIC, NAHO, ORIENT, ORIENTTKAFUL, UNIKAI), 6 BSE (BMUSC.BH, FAMILY B, SILAH, TAKAFUL, UGH.BHR, UGIC.BH) and
1 KSE (412). Their header shows the briefs price with "Price date unknown" and no chart (AFNIC 230.00 matched
the reference). 412 and BMUSC.BH have no price, fundamentals or news row at all.

### F12. Minor findings

- **Freshness ignores holidays** (web app): `freshness.py` knows weekends only, so during a closure such as Eid
  every price light on that exchange turns amber after 2 trading days. Weekends themselves are right:
  Fri/Sat for Tadawul, QSE, KSE, BHB and MSX, and Sat/Sun for ADX and DFM.
- **Missing English names** (pipeline): 9 tickers show their Arabic name on English pages: EMAAR ("إعمار"),
  DEWA, SALIK, TAQA, AMAN, AMLAK, IFA, KFH (Bahrain) and ASYAD.
- **Key metrics light** shows fundamentals freshness, while the panel also holds price-based rows (volume,
  returns). BWPC shows a P/E and yield from a March 2022 price under a green light.
- **Historical glitches** in the 10-year files: on 2017-04-30 / 05-01, closes look swapped between 1213, 2300,
  4140 and 8311 (moves of +395% / −80% that reverse the next day); jumps on 1999–2002 dates; 15 Tadawul bars dated
  Friday 1993-10-01. Tadawul has no move beyond its ±10% limit in the last year, and its only >30% moves since
  2021 are IPO first days (4072, 4324, 6016).
- **Possible gaps to verify:** no QSE bar for any ticker on 2026-07-13 to 07-16, nor ADX/DFM on 2026-03-02/03,
  and no Muscat bars on 2025-10-19 to 10-22. These are not holidays I could confirm. 13 near-daily Tadawul stocks
  all lack 2026-04-01. Recent >30% moves on illiquid Kuwaiti stocks need a corporate-action check: GIH (221)
  0.917 → 0.523 on 2026-09-22 on 18 M shares; GINS (302) 1.2 → 2.707 → 1.613 on 2026-08-03/04.
- **Indices:** only TASI, ADX and DFM are collected; QSE, Boursa Kuwait, BHB and MSX have none.

## 4. Accuracy sample (site API vs stockanalysis.com, 2026-10-18 09:14–09:45 UTC)

Tolerances: close exact, market cap ±2%, P/E ±5%, dividend yield ±0.25 pp. The site's values are from
`/api/v1/tickers/{slug}`.

| Ticker | Close (site / ref) | Close date (site / ref) | Market cap, mn | P/E | Dividend yield % |
|---|---|---|---|---|---|
| 3060 | 13.84 / 13.84 ✓ | 10-15 / 10-15 ✓ | 2179.8 / 2180 ✓ | 17.91 / 17.91 ✓ | 9.03 / 10.84 ✗ |
| 4200 | 115.10 / 115.10 ✓ | 10-15 / 10-15 ✓ | 11510 / 11510 ✓ | 25.05 / 25.12 ✓ | 1.74 / 1.74 ✓ |
| 1831 | 3.73 / 3.73 ✓ | 10-15 / 10-15 ✓ | 2238 / 2130 ✗ | 10.60 / 6.75 ✗ | 4.03 / 4.24 ✓ |
| 7020 | 60.25 / 60.25 ✓ | 10-15 / 10-15 ✓ | 46392 / 46240 ✓ | 12.88 / 12.68 ✓ | 4.65 / 4.98 ✗ |
| 8190 | 3.38 / 3.38 ✓ | 09-10 / 09-10 ✓ (no trade since) | 135.2 / 135.2 ✓ | – / – | – / – |
| 2180 | 38.34 / 38.34 ✓ | 10-15 / 10-15 ✓ | 440.9 / 440.9 ✓ | – / 224.1 | – / – |
| 4007 | 22.53 / 22.53 ✓ | 10-15 / 10-15 ✓ | 3604.8 / 3600 ✓ | 15.58 / 15.40 ✓ | 4.88 / 3.55 ✗ |
| 1324 | 38.00 / 38.00 ✓ | 10-15 / 10-15 ✓ | 706.8 / 706.8 ✓ | 10.68 / 10.68 ✓ | 5.26 / 5.26 ✓ |
| RAPCO | 2.50 / 2.50 ✓ | 10-02 / 10-16 (ref: no trade, 0.00%) | 237.6 / 237.6 ✓ | 19.86 / 8.29 ✗ | – / – |
| EASYLEAS | 20.46 / no reference page | | | | |
| E7 | 0.91 / 0.905 ✗ (F6) | 10-16 / 10-16 ✓ | 1906 / 1840 ✗ | 14.03 / 15.10 ✗ | 10.72 / 11.05 ✗ |
| PUREHEALTH | 2.63 / 2.63 ✓ | 10-16 / 10-16 ✓ | 29556 / 29220 ✓ | 18.05 / 13.56 ✗ | 2.06 / 2.06 ✓ |
| UFC | 11.40 / 11.40 ✓ | 10-16 / 10-16 ✓ | 344.9 / 344.9 ✓ | 6.73 / 6.73 ✓ | 4.39 / 4.39 ✓ |
| AMLAK | 1.17 / 1.17 ✓ | 10-16 / 10-16 ✓ | 1740 / 1760 ✓ | – / 1.17 | 41.88 / 41.88 ✓ |
| SHUAA | 0.24 / 0.240 ✓ (F6) | 10-16 / 10-16 ✓ | 867.2 / 878.2 ✓ | – / – | – / – |
| GULFNAV | 2.84 / 2.86 ✗ (F4) | 07-23 / 10-16 ✗ | – / 8950 | – / 246.7 | – / – |
| QCFS | 2.345 / 2.345 ✓ | 10-15 / 10-15 ✓ | 147.3 / 147.3 ✓ | 29.25 / 30.86 ✗ | 4.26 / 4.26 ✓ |
| BEMA | 4.40 / 4.40 ✓ | 10-15 / 10-15 ✓ | 880 / 880 ✓ | 8.45 / 8.47 ✓ | 5.68 / 5.68 ✓ |
| IGRD | 3.92 / 3.92 ✓ | 10-15 / 10-15 ✓ | 17614 / 17610 ✓ | 18.75 / 16.61 ✗ | – / – |
| UDCD | 0.711 / 0.711 ✓ | 10-15 / 10-15 ✓ | 2517.6 / 2520 ✓ | 16.56 / 6.24 ✗ | 7.74 / 7.74 ✓ |
| 237 Ekttitab | 0.031 / 0.031 ✓ | 10-15 / 10-15 ✓ | 9.88 / 9.88 ✓ | – / – | – / – |
| 232 Unicap | 0.250 / 0.250 ✓ | 10-15 / 10-15 ✓ | 59.9 / 57.7 ✗ | 41.77 / – | – / – |
| 214 KMEFIC | 0.126 / 0.126 ✓ | 10-15 / 10-15 ✓ | 27.72 / 27.72 ✓ | – / – | – / – |
| 418 Altijaria | 0.175 / 0.175 ✓ | 10-15 / 10-15 ✓ | 341.7 / 328.8 ✗ | 20.55 / 19.08 ✗ | 1.64 / (ref shows 1714%, its own unit error) |
| BMMI | 0.495 / 0.495 ✓ | 10-06 / 09-27 (ours has a 2,900-share trade on 10-06) | 72.5 / 70.5 ✗ | 17.85 / 17.35 ✓ | – / 10.10 (F10) |
| ZAINBH | 0.119 / 0.119 ✓ | 10-14 / 10-14 ✓ | 43.8 / 43.3 ✓ | 7.28 / 7.20 ✓ | – / 7.56 (F10) |
| ARIG | 0.94 / 0.94 **USD** ✓ | 09-14 / 09-14 ✓ | 206.8 "BHD" / 70.2 BHD ✗ (F5) | 33.24 / 29.93 ✗ | – / 3.44 (F10) |
| UFCI | 0.087 / 0.087 ✓ | 10-15 / 10-15 ✓ | 30.98 / 30.98 ✓ | 8.93 / 9.15 ✓ | 5.75 / 5.75 ✓ |
| RCCI | 0.193 / 0.193 ✓ | 10-15 / 10-15 ✓ | 38.6 / 38.6 ✓ | – / – | – / – |
| AMCI | 0.294 / 0.294 ✓ | 10-13 / 10-15 (ref: no trade, 0.00%) | 16.17 / 16.17 ✓ | 56.15 / 60.36 ✗ | 1.36 / 1.36 ✓ |
| 1010 Riyad Bank | 19.26 / 19.26 ✓ | 10-15 / 10-15 ✓ | 77040 / 76800 ✓ | 7.27 / 7.70 ✗ | 5.43 / 5.45 ✓ |
| AFNIC (no file) | 230.00 / 230.00 ✓ | unknown / 10-16 | 305.9 / 306.1 ✓ | – / 3.49 | 4.35 / 4.35 ✓ |
| EMAAR | 11.46 / 11.46 ✓ | 10-16 / 10-16 ✓ | 100760 / 101290 ✓ | 5.30 / 5.28 ✓ | 8.73 / 8.73 ✓ |
| NBK (101) | 0.815 / 0.815 ✓ | 10-15 / 10-15 ✓ | 7480 / 7480 ✓ | 12.79 / 13.26 ✓ | 4.09 / (ref unit error) |

Totals: close 31/33 exact (both misses explained by F4 and F6); close date 28/32 identical (AFNIC has no date on
our side; one real error, GULFNAV; the other three are reference artefacts). Market cap within 2%: 26/32. P/E within 5%: 12/23.
Dividend yield within 0.25 pp: 14/18. Aramco, checked separately: close, date, market cap and yield match;
P/E 13.75 vs 14.97 (EPS 1.84 vs 1.69); volume 10.08 M vs the reference's 6.55 M (its snapshot was taken at
15:19, which may miss the closing auction; unresolved). **Last dividend** was not compared: the site holds it
only in `/corporate` and `/events`, both Pro-only.

## 5. Coverage by exchange

From `GET /api/v1/tickers/{slug}` (freshness rows) and `/news?limit=50` for all 716 tickers.

| Exchange | Universe | Price file | Fundamentals row | News/disclosure ≤ 30 d | ≤ 90 d | None at all | Dividend yield present |
|---|---|---|---|---|---|---|---|
| Tadawul | 269 | 269 | 267 | 5 | 34 | 15 | 157 |
| ADX | 102 | 90 | 99 | 99 | 101 | 0 | 57 |
| DFM | 64 | 58 | 63 | 63 | 63 | 0 | 42 |
| QSE | 55 | 55 | 54 | 55 | 55 | 0 | 46 |
| Boursa Kuwait | 129 | 128 | 127 | 127 | 127 | 0 | 70 |
| Bahrain | 39 | 33 | 37 | 38 | 38 | 1 | **0** |
| Muscat | 58 | 58 | 58 | 58 | 58 | 0 | 50 |
| **Total** | **716** | **691** | **705** | **445** | **476** | **16** | **422** |

Ownership coverage: not measured (Pro-only `/insights`).

## 6. Freshness by exchange (header price, 2026-10-18 09:30 UTC)

Age in trading days (exchange weekends, no holidays) from the last bar; "stale" means more than
`max_age_days` = 2, as the site computes it.

| Exchange | With price file | Stale | p50 / p90 / p95 age | Stale tickers and why |
|---|---|---|---|---|
| Tadawul | 269 | 4 | 1 / 1 / 1 | **gap:** 2080, 4240; suspended: 8190 (ref agrees), 2210 (no trade since 04-29) |
| ADX | 90 | 12 | 0 / 9.6 / 40 | **gap:** AGILITY, TAQA (partly); dead: AKIC.AD (2020), METH.AD (2023); untraded small caps: HH, QIC, BILDCO, FNF, RAPCO, NBF, FBI.AD, UNION |
| DFM | 58 | 10 | 0 / 10 / 17 | **gap:** GULFNAV; untraded: DNIR, IFA (ref agrees), ALRAMZ, DIN, NIND (ref agrees), AMCREIT, NIH, DRC, NGI |
| QSE | 55 | 0 | 1 / 1 / 1 | – |
| Boursa Kuwait | 128 | 3 | 1 / 1 / 1 | **gap (likely):** 624; 2012 (2026-03-31), 242 |
| Bahrain | 33 | 13 | 2 / 20 / 731 | dead: BMEB.BH (2018); INOVEST, ARIG, ABC, ITHMR (ref agrees); untraded: CPARK, BCFC, BMMI, SOLID, POLTRY, TRAFCO, DUTYF, BISB |
| Muscat | 58 | 9 | 1 / 4 / 50 | dead: BWPC (2022), LIVA (2023); untraded: DFIN, DICS, OCCI, OCHL, SPSI, AMCI, CMII |

The 25 tickers without a price file show no light ("Price date unknown"). Other categories: `prices` and
`technical` rows agree with the header for all 691 (0 disagreements). `fundamentals` (705) and `disclosures`
(716) rows are all fresh by their 100- and 120-day windows, because their `as_of` is the fetch time (see F3).
`news` (714 rows) is stale for 7, the dropped tickers of F4.

**Lights vs data (about 20 pages asked for; 48 checked):** for every page, each panel light (header, Price,
Key metrics, News) equals the API's `stale` flag. The lights are faithful to the API. The API's flags are wrong
only where the pipeline's `as_of` is a fetch time (F3).

## 7. Delivery (database → API → page)

- **API → page, 48 pages:** header price = `quote.last_price` (apart from F7 rounding); "As of" = `quote.as_of_date`;
  chart last bar = header quote for all pages with a price file; every Key metrics row (market cap, P/E, P/B,
  dividend yield, ROE, ROA, EPS, book value) equals `valuation`; lights equal the API. No value appeared on a
  page that the API did not send.
- **Shown, but wrong in the data:** F1 (sectors), F2 (EPS unit), F5 (currency) and the Arabic names (F12).
- **Database → API:** not measured. That needs the SQLite files (section 8). By code review, every figure on these
  panels is read straight from `briefs`, `scraped_ratios`, `stocks`, `ticker_tech_snapshot`, `ticker_freshness`
  and the price CSVs. Nothing is computed except the quote's day change (last two bars), P/E and P/B nulling
  (`ratios.py`) and staleness (`freshness.py`).
- **Pro panels** (financials, statements, council, ownership, calendar): not measured. On alphacouncil.tech they
  answer 403 without Pro (`/tickers/2222/council` → 403 in the page's own requests), and the server-local
  addresses (`127.0.0.1:8300` / `:8200`) need SSH.

## 8. Not measured (needs server access)

| What | Read-only way to measure it |
|---|---|
| Schedule and 30-day run history: start, end, duration, failures, HTTP/parse/timeout errors, retries | `crontab -l; systemctl list-timers --all; ls -lt /opt/alphacouncil/logs \| head; grep -ciE "error\|timeout\|traceback" <log>` per day |
| Why F4's tickers stopped on 2026-07-23 | grep the logs around 2026-07-24/25 for `2080\|AGILITY\|GULFNAV\|624`; compare the pipeline's ticker or id lists before and after |
| Disclosures not refreshed on 10-17/10-18; Tadawul items fading since August | the disclosures step's log lines; `SELECT substr(date,1,7), count(*) FROM items WHERE ticker_key LIKE '%_TADAWUL' GROUP BY 1` |
| Items hidden by the API's date filter (`date GLOB '[0-9]…'`) | `SELECT section, count(*) FROM items WHERE NOT date GLOB '[0-9][0-9][0-9][0-9]-*' OR date IS NULL GROUP BY 1` |
| Raw price files: duplicate dates, close ≤ 0, rows the API drops | a read-only pass over `default_universe/*/price_history_10y.csv` |
| The same ratio across `stocks` / `scraped_ratios` / `briefs`; stale statements | join the three tables on `ticker_key`; `max(fiscal_year)` per ticker in `fundamentals_lineitems` |
| Sector ids behind F1 | `SELECT sector_id, sector_en, count(*) FROM briefs WHERE exchange='TADAWUL' GROUP BY 1,2` |
| Ownership: repeated dates, nameless holders; seasonality | `ticker_insights.data_json` |
| `news_ai` coverage over time | `SELECT substr(created_at,1,7), count(*) FROM news_ai GROUP BY 1` (column name to confirm) |
| Pro panels vs database, and last dividend vs reference | `curl http://127.0.0.1:8300/v1/tickers/{ref}/{statements,corporate,insights,events}` on the server |

(Open SQLite with `file:…?mode=ro&immutable=1`, market-data tables only; `briefs_index.sqlite` also holds the old
site's account tables.)

## 9. Fixes, in order

1. **Tadawul sector table** (F1, pipeline): map `sector_id` to the right Tadawul sector names, and classify the 24
   in id 1. Until then, consider hiding sector labels for Tadawul, since a wrong sector is worse than none.
2. **EPS unit** (F2): store EPS in the price's unit (pipeline), or divide by 1000 for KWD/BHD/OMR and for
   Kuwaiti companies listed on DFM when the API reads it. Check: `|price / EPS − P/E| / P/E < 5%`.
3. **News freshness** (F3): set `as_of` for news and disclosures to the newest item's date (pipeline), or compute it
   in the API from `items`. Then restore Tadawul disclosure collection, and run `news_ai` on recent items.
4. **Stopped tickers** (F4, pipeline): find why the six stopped and re-add them. Write `last_success_utc` only when
   the ticker's fetch actually succeeded. Alert when a ticker that traded on ≥ 90% of the last 60 sessions misses
   two sessions in a row while its exchange traded.
5. **Trading currency** (F5, pipeline): take the currency per listing, not per company (12 tickers).
6. **Header and QAR digits** (F7, web app): use `priceDigits(currency)` in `StockTemplate.tsx:72` and allow
   3 decimals for QAR, and for AED under 1 once F6 is fixed. A small change.
7. **ADX/DFM precision** (F6, pipeline/source): fetch 3-decimal prices, or mark sub-1 AED day changes as approximate.
8. **Holiday bars** (F8, pipeline): drop bars that repeat the previous bar exactly on exchange holidays, at least for
   MSM and BSE.
9. **Tadawul turnover** (F9) and **Bahrain dividend yields** (F10, pipeline).
10. **Ratio basis** (F10): reconcile the TTM EPS used for P/E with a second source for the 11 mismatches. Null the
    P/E when EPS < 0 (4144), and cap or recheck yields above 25% that have no price file (ORIENT, SAWAEED).
11. **Minor** (F12): a holiday calendar in `freshness.py`, the 9 English names, and the 2017 and pre-2002 glitches.

## 10. What to monitor from now on

| Metric | How | Alert when |
|---|---|---|
| Run completed per category | max `ticker_freshness.last_success_utc` per category (but see F4: the prices stamp is written even when nothing was fetched) | older than 26 h for prices, technical, fundamentals and news; disclosures per its real schedule |
| Price files written | count of price files with mtime after the run start (last night 679 of 691) | < 99% of the files of tickers not known to be suspended or delisted |
| Exchange caught up | latest bar per exchange vs the exchange's last session | lagging 1 session after the nightly run |
| Ticker dropped | tickers that traded on ≥ 90% of the last 60 sessions and have no bar for the last 2 | any |
| Tadawul disclosures flowing | Tadawul tickers with an item in the last 30 days | < 50% (now 1.9%) |
| English readability | share of the newest 50 market items with an English headline or summary | < 50% (now 0 of the 10 newest) |
| Sector sanity | Tadawul tickers with no sector, or in a sector that differs from a fixed reference list | > 0 |
| Unit sanity | KWD/BHD/OMR tickers where `price / EPS` differs from P/E by > 5% | > 0 |
| Currency sanity | listings whose currency differs from their exchange's, outside an allow-list (USD in Bahrain) | new entries |
| Bar integrity | bars identical to the previous one on exchange holidays; O/H/L blanked by the API | > 0 a month; > 0.5% of an exchange's bars a month (MSM is at ~5%) |
| Limit breaches | day moves beyond the exchange's daily limit with no corporate action that day | any |
| Accuracy | weekly 30-ticker reference sample, as in section 4 | close exact < 97%; market cap within 2% < 90%; P/E within 5% < 80% |
| Lights | a weekly sample of pages: page light = API flag = data age | any mismatch |
