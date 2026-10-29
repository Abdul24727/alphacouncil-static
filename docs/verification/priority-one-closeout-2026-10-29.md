# Verification: Priority One closeout, 2026-10-29

Raw output for `docs/priority-one-closeout-2026-10-29.md`. Nothing here is retyped; each block is
the stdout of the command above it. Scripts live in this session's scratchpad and are quoted in
full where they are short.

Environment: `api/.venv` (Python 3.12, FastAPI) for the API and its tests; a separate venv with
bs4 4.15.0 for the pipeline scripts. The live databases were copied read-only from
`root@alphacouncil.tech` and nothing on the server was written.


---

## 1. The live published database, read today

`python -I live.py` against a read-only copy of `/opt/alphacouncil/backend/llm-council/det_out/screening.sqlite` (29,040,640 bytes, copied 2026-10-29 14:52).

```
THE LIVE PUBLISHED DATABASE, 2026-10-29 (copied read-only from the server)

statement sections present, by exchange:
   TADAWUL     243 tickers   income    0   balance  243   cash flow    0
   KSE         121 tickers   income  120   balance  121   cash flow    0
   ADX          88 tickers   income   88   balance   88   cash flow    0
   DFM          60 tickers   income   60   balance   60   cash flow    0
   QSE          53 tickers   income   53   balance   53   cash flow    0
   MSM          51 tickers   income   51   balance   51   cash flow    0
   BSE          37 tickers   income   37   balance   37   cash flow    0

gauge statuses and rankings:
   na_sector                 2500   with a ranking      0
   missing_inputs            2048   with a ranking      0
   ok                        1954   with a ranking   1954
   undefined_nonpositive       28   with a ranking      0

bank_metrics (the pipeline's own bank scorecard, step 17 of the nightly run):
   rows: 0   columns: ['ticker_key', 'fy_year', 'cost_income', 'net_margin_bank', 'cost_of_risk', 'npl_ratio', 'npl_coverage', 'equity_assets', 'loans_deposits']
   nightly log: 'bank_metrics: wrote 0/58 banks' then '[OK step 17] (0.2s)'

fundamentals_lineitems columns (no reporting mode yet):
   ['ticker_key', 'ticker', 'exchange', 'fiscal_year', 'section', 'item_index', 'line_item_label', 'value']

the three cases as the advisors receive them today:
   2222_TADAWUL: Balance Sheet 42 rows to FY2025
      current_ratio            1.999  ok                    rank 68.8
      debt_equity              0.201  ok                    rank 53.6
      ev_ebitda                    -  na_sector             rank -
      fcf_yield                    -  na_sector             rank -
      gross_margin                 -  na_sector             rank -
      interest_coverage            -  missing_inputs        rank -
      net_margin                   -  missing_inputs        rank -
      payout                       -  missing_inputs        rank -
      ps                           -  missing_inputs        rank -
      roic                         -  missing_inputs        rank -
   1120_TADAWUL: Balance Sheet 32 rows to FY2025
      current_ratio                -  na_sector             rank -
      debt_equity              1.717  ok                    rank 22.1
      ev_ebitda                    -  na_sector             rank -
      fcf_yield                    -  na_sector             rank -
      gross_margin                 -  na_sector             rank -
      interest_coverage            -  missing_inputs        rank -
      net_margin                   -  missing_inputs        rank -
      payout                       -  missing_inputs        rank -
      ps                           -  missing_inputs        rank -
      roic                         -  na_sector             rank -
   2010_TADAWUL: Balance Sheet 58 rows to FY2025
      current_ratio            1.801  ok                    rank 64.0
      debt_equity              0.261  ok                    rank 50.1
      ev_ebitda                    -  na_sector             rank -
      fcf_yield                    -  na_sector             rank -
      gross_margin                 -  na_sector             rank -
      interest_coverage            -  missing_inputs        rank -
      net_margin                   -  missing_inputs        rank -
      payout                       -  missing_inputs        rank -
      ps                           -  missing_inputs        rank -
      roic                         -  missing_inputs        rank -
```

---

## 2. Standalone or cumulative quarterly columns

`python standalone.py <scratchpad> docs/eval/packs` — Test A reads the columns as cumulative and looks at the quarters that implies; Test B checks both readings against the provider's own `eps_ttm`, which comes from a different page.

```
==============================================================================================
TEST A - read the columns as cumulative and look at the quarters that implies
==============================================================================================
A fiscal year's columns, under a cumulative reading, are year-to-date: H1, 9M, FY. The
quarters they imply are the first differences. Impossible implications refute the reading.

--- 1120_TADAWUL: 11 of 25 flow rows give an IMPOSSIBLE cumulative reading
      Investment Income & Other Financing operations FY2026
        columns  2026-03=14,507  2026-06=14,484  2026-09=15,062
        implies  -24  578   <- negative revenue
      Return on time investments                     FY2026
        columns  2026-03=-6,102  2026-06=-6,177  2026-09=-6,448
        implies  -75  -271   <- a quarter at ~0
      Net income from investments and financing acti FY2026
        columns  2026-03=8,405  2026-06=8,307  2026-09=8,614
        implies  -98  307   <- a quarter at ~0
--- 2010_TADAWUL: 8 of 22 flow rows give an IMPOSSIBLE cumulative reading
      Sales                                          FY2025
        columns  2025-06=30,228  2025-09=34,333  2025-12=27,950
        implies  4,105  -6,383   <- negative revenue
      Cost of Sales                                  FY2025
        columns  2025-06=-24,004  2025-09=-28,227  2025-12=-24,080
        implies  -4,223  4,147   <- negative revenue
      Gross Income                                   FY2025
        columns  2025-06=6,224  2025-09=6,106  2025-12=3,870
        implies  -119  -2,236   <- negative revenue
--- 2222_TADAWUL: 7 of 18 flow rows give an IMPOSSIBLE cumulative reading
      Sales                                          FY2025
        columns  2025-06=407,142  2025-09=418,160  2025-12=416,290
        implies  11,018  -1,870   <- negative revenue
      Cost of Sales                                  FY2025
        columns  2025-06=-213,066  2025-09=-194,840  2025-12=-208,797
        implies  18,226  -13,957   <- negative revenue
      Gross Income                                   FY2025
        columns  2025-06=194,076  2025-09=223,320  2025-12=207,493
        implies  29,244  -15,827   <- negative revenue
--- 4061_TADAWUL: 10 of 23 flow rows give an IMPOSSIBLE cumulative reading
      Sales                                          FY2025
        columns  2025-06=6  2025-09=12  2025-12=11
        implies  6  -1   <- negative revenue
      Cost of Sales                                  FY2025
        columns  2025-06=-2  2025-09=-4  2025-12=-5
        implies  -2  -1   <- negative revenue
      Gross Income                                   FY2025
        columns  2025-06=4  2025-09=8  2025-12=5
        implies  3  -2   <- negative revenue
--- 4190_TADAWUL: 4 of 21 flow rows give an IMPOSSIBLE cumulative reading
      Sales                                          FY2026
        columns  2026-03=3,038  2026-06=2,774  2026-09=3,153
        implies  -265  379   <- negative revenue
      Gross Income                                   FY2026
        columns  2026-03=342  2026-06=340  2026-09=499
        implies  -1  159   <- negative revenue
      Operating Income                               FY2026
        columns  2026-03=254  2026-06=252  2026-09=396
        implies  -2  144   <- negative revenue

40 rows across 5 tickers refute the cumulative reading outright.

==============================================================================================
TEST B - the vendor's own eps_ttm, from a different page, against both readings
==============================================================================================
ticker            vendor  standalone  cumulative   standalone  cumulative
                 eps_ttm         EPS         EPS      /vendor     /vendor
1120_TADAWUL        4.42       4.541       1.062        1.03x       0.24x
2010_TADAWUL           -  vendor publishes no eps_ttm (unit_unconfirmed)
2222_TADAWUL        1.84       1.687       0.287        0.92x       0.16x
4061_TADAWUL           -  vendor publishes no eps_ttm (unit_unconfirmed)
4190_TADAWUL        0.94       0.977       0.258        1.04x       0.27x

Only the standalone reading lands on the vendor's figure. The cumulative reading is out
by several times, and it is out in the direction a cumulative reading must be out.

==============================================================================================
Share counts per quarter - does an end-of-period position differ from the mean?
==============================================================================================
1120_TADAWUL    constant  2025-09=6,000  2025-09=6,000  2025-12=6,000  2025-12=6,000  2026-03=6,000  2026-03=6,000  2026-06=6,000  2026-06=6,000  2026-09=6,000  2026-09=6,000
2010_TADAWUL    constant  2025-06=3,000  2025-06=3,000  2025-09=3,000  2025-09=3,000  2025-12=3,000  2025-12=3,000  2026-03=3,000  2026-03=3,000  2026-06=3,000  2026-06=3,000
2222_TADAWUL    constant  2025-06=242,000  2025-06=242,000  2025-09=242,000  2025-09=242,000  2025-12=242,000  2025-12=242,000  2026-03=242,000  2026-03=242,000  2026-06=242,000  2026-06=242,000
4061_TADAWUL    constant  2025-06=32  2025-06=32  2025-09=32  2025-09=32  2025-12=32  2025-12=32  2026-03=32  2026-03=32  2026-06=32  2026-06=32
4190_TADAWUL    constant  2025-09=1,200  2025-09=1,200  2025-12=1,200  2025-12=1,200  2026-03=1,200  2026-03=1,200  2026-06=1,200  2026-06=1,200  2026-09=1,200  2026-09=1,200
```

---

## 3. The gauge patch, on the scratch databases

`python gauge_guard.py <scratchpad>` — provenance on every row, then an attempt to make a stale ranking survive a value change.

```
score column present: True  ->  using the clearing upsert

============================================================================================
1. PROVENANCE on every row, whatever its status
============================================================================================
--- 2222_TADAWUL
   current_ratio            2.003  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   debt_equity              0.189  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   ev_ebitda                    -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   fcf_yield                    -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   gross_margin            51.347  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   interest_coverage       81.697  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   net_margin              22.395  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   payout                       -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   ps                       3.517  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   roic                    23.902  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank

--- 1120_TADAWUL
   current_ratio                -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=bank
   debt_equity              1.509  ok                    FY2026 TTM@2026-06 position@2026-06 sector=bank
   ev_ebitda                    -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=bank
   fcf_yield                    -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=bank
   gross_margin                 -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=bank
   interest_coverage            -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=bank
   net_margin                   -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=bank
   payout                       -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=bank
   ps                           -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=bank
   roic                         -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=bank

--- 2010_TADAWUL
   current_ratio            2.430  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   debt_equity              0.368  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   ev_ebitda                9.780  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   fcf_yield                    -  na_sector             FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   gross_margin            17.182  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   interest_coverage        0.137  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   net_margin             -18.829  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   payout                       -  missing_inputs        FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   ps                       1.339  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank
   roic                    -0.621  ok                    FY2026 TTM@2026-06 position@2026-06 sector=non_bank

============================================================================================
2. A ranking cannot outlive the value it ranked
============================================================================================
the sector stage has ranked every Aramco gauge at 63.5

(a) gauge stage re-run on the SAME statements: 10/10 rankings kept  <- an idempotent re-run must not throw rankings away

(b) Net Income refreshed +10%, gauge stage re-run, sector stage NOT run:
    gauge                      was         now     ranking
    current_ratio            2.003       2.003        63.5
    debt_equity              0.189       0.189        63.5
    ev_ebitda                    -           -        63.5
    fcf_yield                    -           -        63.5
    gross_margin            51.347      51.347        63.5
    interest_coverage       81.697      81.697        63.5
    net_margin              22.395      24.635     cleared   <- value moved
    payout                       -           -        63.5
    ps                       3.517       3.517        63.5
    roic                    23.902      23.902        63.5

    gauges holding a NEW value under an OLD ranking: 0
```

---

## 4. The whole chain on the whole live universe

`python chain.py <scratchpad>` — the production gauge stage and the patched one over copies of the live database, then stages 3 and 4, then the ranking guarantee under a refreshed line item.

```
==============================================================================================
1. THE PATCHED GAUGE STAGE AGAINST THE ONE IN PRODUCTION, ON ALL 653 TICKERS
==============================================================================================
   original: 2026-10-29 14:57:02,012 - INFO - DONE: 6530 gauge rows. status: {'missing_inputs': 2325, 'na_sector': 2500, 'ok': 1679, 'undefined_nonpositive': 26}
   patched:  2026-10-29 14:57:04,191 - INFO - DONE: 6530 gauge rows. status: {'missing_inputs': 2325, 'na_sector': 2500, 'ok': 1679, 'undefined_nonpositive': 26}

   gauge rows: original 6,530  patched 6,530
   rows only in one: 0 / 0
   rows whose (value, status) differ: 0
   -> the patch changes provenance and ranking behaviour, not a single value or status

==============================================================================================
2. EVERY GAUGE NOW CARRIES THE VINTAGE AND SECTOR IT WAS COMPUTED FROM
==============================================================================================
   6,530/6,530 rows carry a fiscal year; 6,530/6,530 carry a sector
   sectors seen: {'bank': 2040, 'non_bank': 4080, 'insurance': 410}

==============================================================================================
3. SECTOR AVERAGES AND RANKINGS, AFTER THE GAUGE STAGE
==============================================================================================
   sector_averages: 2026-10-29 14:57:04,473 - INFO - DONE: 30 (sector,gauge) rows upserted.
   gauge_scores:    2026-10-29 14:57:04,723 - INFO - Scored 1679/6530 gauge rows (11 ok (class,gauge) sectors; 0 skipped insufficient).
   gauges with status ok: 1,679, of which ranked: 1,679
   gauges NOT ok that carry a ranking: 0

==============================================================================================
4. CAN A REFRESHED VALUE SIT UNDER AN OLD RANKING?
==============================================================================================
   2222_TADAWUL before: current_ratio=1.999/rank 68.8, debt_equity=0.201/rank 53.6
   a line item was refreshed and the GAUGE STAGE ALONE was re-run:
      current_ratio          1.999 ->      2.498   ranking cleared

   values holding a NEW number under an OLD ranking: 0
   sector_averages: 2026-10-29 14:57:04,985 - INFO - DONE: 30 (sector,gauge) rows upserted.
   gauge_scores:    2026-10-29 14:57:05,238 - INFO - Scored 1679/6530 gauge rows (11 ok (class,gauge) sectors; 0 skipped insufficient).
   after stages 3 and 4, 2222_TADAWUL gauges with status ok and no ranking: 0
   whole universe: 0 ok gauges without a ranking
```

---

## 5. The three companies, before and after

`python demo_packs.py <scratchpad> <repo>` — the P9 dataset built by `api/app/evidence.py` from the current parser's output and from the repaired parser's, with the dividend history and market caps taken from the committed packs.

```
================================================================================================
2222_TADAWUL - the P9 dataset, before and after
================================================================================================

--- BEFORE: 3,953 chars of a 16,000 budget  (fits), sector=non_bank
    Balance Sheet       None@None  34 rows (+8 omitted)  columns=['label', '2025']  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings        NO VALUE: no net income line in the income statement
      eps_derived                            NO VALUE: no net income line
      roe_on_period_end_common_equity        NO VALUE: no net income line
      payout_cash                            NO VALUE: there is no income statement, so there is no earnings window to match dividends to and no payout rat
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is not, because the source serves a rolling five-quarter gr

--- AFTER: 10,553 chars of a 16,000 budget  (fits), sector=non_bank
    Income Statement    TTM@2026-06  18 rows (+0 omitted)  columns=['label', '2026']  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        Shares Outstanding (Million) is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  34 rows (+8 omitted)  columns=['label', '2026', '2025']  aggregation=quarter_end_snapshot
        source columns: ['2026-06']
    quarters: ['label', '2025-06', '2025-09', '2025-12', '2026-03', '2026-06']
        Sales                                      407,142.0  418,160.0  416,290.0  467,236.0  521,797.0
        Gross Income                               194,076.0  223,320.0  207,493.0  261,232.0  244,261.0
        Operating Income                           170,558.0  198,865.0  178,388.0  222,712.0  216,758.0
        Operating Expenses                         -23,518.0  -24,455.0  -29,105.0  -38,520.0  -27,503.0
        Net Profit Before Unusual Items            89,098.0  102,609.0  93,009.0  123,067.0  126,216.0
        Extraordinary income/expense               -3,466.0  -5,345.0  -23,539.0  -2,936.0  -4,710.0
        Net Income                                 85,632.0  97,264.0  69,470.0  120,131.0  121,506.0
        Earning Per Share (Riyal)                  0.3  0.4  0.3  0.5  0.5
    calculations:
      extraordinary_share_of_earnings              -8.9453 %
      eps_derived                                   1.6875 currency units per share
      eps_unit_confirmation                   408,980.0000 millions of the reporting currency
      roe_on_period_end_common_equity              26.0199 %
      payout_cash                                  79.4351 %
      payout_declared                              79.4351 %
      dps_window                                    1.3400 currency units per share
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income statement is not, because the source serves a rolling f

================================================================================================
1120_TADAWUL - the P9 dataset, before and after
================================================================================================

--- BEFORE: 6,842 chars of a 16,000 budget  (fits), sector=bank
    Balance Sheet       None@None  32 rows (+0 omitted)  columns=['label', '2025']  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings        NO VALUE: no net income line in the income statement
      eps_derived                            NO VALUE: no net income line
      roe_on_period_end_common_equity        NO VALUE: no net income line
      net_financing_margin                   NO VALUE: net financing income or the earning-asset lines are absent
      cost_to_income                         NO VALUE: no operating expense or operating income line
      cost_of_risk                           NO VALUE: no provisions line or no financing-investment balance
      npl_ratio                                     0.7478 %
      npl_coverage                                152.4860 %
      equity_to_assets                             11.0091 %
      financing_to_deposits                       112.8089 %
      payout_cash                            NO VALUE: there is no income statement, so there is no earnings window to match dividends to and no payout rat
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is not, because the source serves a rolling five-quarter gr
      - BANK: revenue, gross margin, net margin on sales, price to sales, current ratio, interest coverage, return on invested capital, EV/EBITDA and free cas

--- AFTER: 14,490 chars of a 16,000 budget  (fits), sector=bank
    Income Statement    TTM@2026-06  24 rows (+0 omitted)  columns=['label', '2026']  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        Shares Outstanding (Million) is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  32 rows (+0 omitted)  columns=['label', '2026', '2025']  aggregation=quarter_end_snapshot
        source columns: ['2026-06']
    quarters: ['label', '2025-09', '2025-12', '2026-03', '2026-06', '2026-09']
        Operating Income                           9,881.8  10,409.2  10,528.5  10,884.5  11,115.0
        Operating Expenses                         -2,216.3  -2,679.6  -2,457.3  -2,394.5  -2,357.0
        Net Profit Before Unusual Items            6,360.2  6,374.5  6,751.6  7,012.1  7,106.0
        Extraordinary income/expense               0.0  0.0  0.0  0.0  0.0
        Net Income                                 6,360.2  6,374.5  6,751.6  7,012.1  7,106.0
        Earning Per Share (Riyal)                  1.1  1.1  1.1  1.2  1.2
    calculations:
      extraordinary_share_of_earnings               0.0000 %
      eps_derived                                   4.4164 currency units per share
      eps_unit_confirmation                    26,520.0000 millions of the reporting currency
      roe_on_period_end_common_equity              21.9588 %
      net_financing_margin                          3.4314 %
      cost_to_income                               23.3736 %
      cost_of_risk                                  0.3576 %
      npl_ratio                                     0.7432 %
      npl_coverage                                153.2247 %
      equity_to_assets                             11.4407 %
      financing_to_deposits                       110.7119 %
      net_income_to_operating_income               63.5393 %
      payout_cash                                  37.7381 %
      payout_declared                              37.7381 %
      dps_window                                    1.6700 currency units per share
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income statement is not, because the source serves a rolling f
      - BANK: revenue, gross margin, net margin on sales, price to sales, current ratio, interest coverage, return on invested capital, EV/EBITDA and free cas

================================================================================================
2010_TADAWUL - the P9 dataset, before and after
================================================================================================

--- BEFORE: 3,908 chars of a 16,000 budget  (fits), sector=non_bank
    Balance Sheet       None@None  34 rows (+24 omitted)  columns=['label', '2025']  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings        NO VALUE: no net income line in the income statement
      eps_derived                            NO VALUE: no net income line
      roe_on_period_end_common_equity        NO VALUE: no net income line
      payout_cash                            NO VALUE: there is no income statement, so there is no earnings window to match dividends to and no payout rat
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is not, because the source serves a rolling five-quarter gr

--- AFTER: 9,253 chars of a 16,000 budget  (fits), sector=non_bank
    Income Statement    TTM@2026-06  15 rows (+0 omitted)  columns=['label', '2026']  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        Shares Outstanding (Million) is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  34 rows (+24 omitted)  columns=['label', '2026', '2025']  aggregation=quarter_end_snapshot
        source columns: ['2026-06']
    quarters: ['label', '2025-06', '2025-09', '2025-12', '2026-03', '2026-06']
        Sales                                      30,227.9  34,332.5  27,950.0  26,151.9  24,806.6
        Gross Income                               6,224.4  6,105.7  3,870.0  5,128.2  4,353.4
        Operating Income                           2,242.6  1,430.5  -2,304.2  1,254.9  105.4
        Operating Expenses                         -3,981.7  -4,675.2  -6,174.2  -3,873.3  -4,248.0
        Net Profit Before Unusual Items            436.9  484.5  -4,957.5  188.8  -225.4
        Extraordinary income/expense               -4,503.0  -49.0  -15,980.2  -175.6  -607.5
        Net Income                                 -4,066.1  435.5  -20,937.8  13.2  -832.9
        Earning Per Share (Riyal)                  -1.4  0.1  -7.0  0.0  -0.3
    calculations:
      extraordinary_share_of_earnings             -78.8496 %
      eps_derived                                  -7.1074 currency units per share
      eps_unit_confirmation                   -21,330.0000 millions of the reporting currency
      roe_on_period_end_common_equity             -17.2605 %
      payout_cash                            NO VALUE: net income over the window is not positive, so a payout ratio is not meaningful
      payout_declared                        NO VALUE: net income over the window is not positive, so a payout ratio is not meaningful
      dps_window                                    3.0000 currency units per share
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet only. Operating cash flow, capital expenditu
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income statement is not, because the source serves a rolling f
```

---

## 6. The test suite

`python -m pytest -q` in `api/`, then the new module alone.

```
........................................................................ [ 95%]
......................                                                   [100%]
515 passed, 11 skipped in 70.47s (0:01:10)
................................                                         [100%]
32 passed in 3.11s
```

---

## 7. What P9 costs a seat's prompt

`python cost.py <scratchpad>` from `api/`, measuring each committed pack's `prompt()` length against the same pack with P9 added.

```
The pack goes into each seat's system prompt, per call (debate/engine.py line 172), and the
debate path does no prompt caching, so this multiplies by the number of calls.

ticker            P1-P8 now     + P9   new total    change
2222_TADAWUL         17,473   10,553      28,772       65%
1120_TADAWUL         20,043   14,490      35,287       76%
2010_TADAWUL         18,421    9,253      28,435       54%
4061_TADAWUL         18,123    7,778      26,588       47%
4190_TADAWUL         18,325    7,884      26,935       47%

mean prompt 18,477 -> 29,203 chars (about 4,619 -> 7,301 tokens)
budgets: every other dataset 12,000, P9 16,000
8 seats (7 advisors + chair) over three stages: on the order of +60,000 input tokens a debate.
```

---

## 8. Priority Two: the advisor mandates

For `docs/advisor-mandates-2026-10-29.md`. A `Debate` built with a hand-made pack, so the prompts are the real ones with no model, no account and no HTTP.

```
WHO IS ANSWERABLE FOR WHAT, in the default roster of six

dataset answerable                              what it is
P1      marks                                   Quote, valuation, returns and technicals
P2      buffett, dalio                          Fundamentals with sector percentiles
P3      alwaleed                                Dividends and capital changes
P4      -- nobody, deliberately --              Council seats (rule-based votes)
P5      alrumayyan                              Sector peers
P6      alrumayyan                              Latest news and disclosures
P7      lynch                                   Price summary, 1 year
P8      marks                                   Price summary, 5 years
P9      buffett, lynch, dalio, marks, alwaleed  Financial statements, their periods, and the measures they support

the seventh seat, not in the default six: alrajhi owns ['P9']

each seat's standing question:
  Buffett       P2, P9       **are these returns real, what were they earned on, and over what period?**
  Lynch         P7, P9       **does the quarterly record support the story the annual figures imply, and which way is it moving?**
  Dalio         P2, P9       **how is this balance sheet funded, and what would have to happen for the funding to become a problem?**
  Marks         P1, P8, P9   **what does this price have to be assuming, and what do we not know?**
  Alwaleed      P3, P9       **what was paid, over which window, out of which earnings, and what has been done to the share count?**
  Al-Rumayyan   P5, P6       **how does this company sit against the companies it is compared with, and what has it itself disclosed?**

==============================================================================================
THE MANDATE AS ONE SEAT RECEIVES IT (marks, the seat answerable for the gaps)
==============================================================================================
YOUR SEAT: Howard Marks (id marks).

YOUR MANDATE IN THIS ROOM (datasets P1, P8, P9):
You are answerable for two things, and the second is yours alone: **what the price assumes**,
and **what this evidence cannot answer**. Read [P1]'s quote and valuation, [P8]'s five-year price
summary, [P9]'s `limitations`, and every entry in [P9] `calculations` that carries `missing`
instead of a value.

The question you answer in every session: **what does this price have to be assuming, and what do
we not know?**

Name the gaps aloud every session, whether or not anyone asked: a measure that could not be
computed and why, a window that cannot be compared, a denominator the source will not disclose, a
statement the source does not publish at all. The room's confidence must not run ahead of its
evidence, and you are the seat answerable for saying when it has. Treat [P4] as what it is —
votes from fixed thresholds, not measurements — and never cite it as a figure.

... and then the seat's own brief, which no longer repeats it:
# Howard Marks (simulated advisor)

## Who they are

A simulated advisor built from the publicly documented thinking of Howard Marks, co-founder of Oaktree Capital
Management, as set out in his widely read client memos and his books on risk and market cycles. This seat is not
Howard Marks and does not speak for him. It never quotes or claims to quote him; it reasons in his manner, in its own
words.

==============================================================================================
THE SHARED RULE THAT MAKES IT A MANDATE AND NOT A CEILING
==============================================================================================
Mandate. Every seat reads the same pack, and each seat is answerable for a different part of it: yours is below, with the datasets it covers. Read those datasets yourself and report what they show, in your own words and for your own reasons - including when they show nothing, which you say plainly and name. The room relies on you for your part and the other seats will take your reading of it as read, so a seat that argues only from the figures every seat can see leaves its own part of the evidence unread. Your mandate is what you are answerable for and not the limit of what you may say: answer the member's question first, and disagree with any seat about anything.

the mandate appears once per prompt, not twice (the brief has it stripped):
  Buffett       1x   system prompt   7,215 chars
  Lynch         1x   system prompt   6,932 chars
  Dalio         1x   system prompt   7,239 chars
  Marks         1x   system prompt   6,999 chars
  Alwaleed      1x   system prompt   7,571 chars
  Al-Rumayyan   1x   system prompt   8,499 chars
  chair         -    system prompt   3,979 chars
```

The suite after the mandates:

```
........................................................................ [ 94%]
.............................                                            [100%]
522 passed, 11 skipped in 71.09s (0:01:11)
```

---

## 9. Priority Three: the Chair's rulings

For `docs/chair-adjudication-2026-10-29.md`. The engine's own checks, run against a verdict built by hand, with no model and no HTTP.

```
THE THREE VERDICTS A RULING MAY CARRY (engine.RULINGS)
  settled     the evidence settles it
  unsettled   the evidence cannot settle it
  judgment    not a disagreement about the data

A VERDICT WITH TWO RULINGS, AS CHECKED
  on      : Whether the payout is covered
  between : buffett, marks
  verdict : settled  (the evidence settles it)
  grounds : The payout of 1.00 decides it for Buffett [P1].

  on      : What the cycle is worth
  between : marks, lynch
  verdict : judgment  (not a disagreement about the data)
  grounds : Both weigh the same figures differently.

what is still open, assembled from the rulings that are not settled:
  - What the cycle is worth - Both weigh the same figures differently.

flags: unruled=[]  words=7

WHAT IS REFUSED
  a verdict the room does not recognise:
      each ruling's verdict must be one of settled, unsettled, judgment (settled: the evidence settles it / unsettled: the evidence cannot settle it / judgment: not a disagreement about the data)
  no ruling at all, after naming fault lines:
      rule on each fault line you named: one entry in `rulings` for each

THE CHAIR'S OWN WORDS ON RULING (chair.md, Who the Chair is)
A neutral moderator, not an investor, and the room's adjudicator. The Chair has no view of its own on the stock
and never adds an argument the advisors did not make. Its job is to turn the member's question into a question the
data can answer, keep the advisors on it, name where they disagree — and then, once they have had their last word,
rule on each of those disagreements from the evidence and write the room's complete answer.

Neutral means the Chair arrives with no position and favours no advisor, not that it declines to decide. Naming a
split and leaving it is no answer to a member who cannot weigh one advisor against another from outside the room.
So the Chair rules: on the figures in the pack, never on a head count, and it rules that the evidence cannot
settle something as readily as it rules for one side. What it may never do is invent the grounds — a ruling rests
on a figure an advisor cited or a gap the data itself declares.
```

The suite after the rulings:

```
........................................................................ [ 93%]
....................................                                     [100%]
529 passed, 11 skipped in 71.96s (0:01:11)
```

---

## 10. The evidence module over the whole universe

For `docs/evidence-universe-sweep-2026-10-29.md`. `api/app/evidence.py` run over every ticker in a read-only copy of the published database.

### 10a. Label-group coverage, before and after the widening

```
653 tickers with line items

group                        before  after   gain  exchanges reached
NET_INCOME                      385    385      0  KSE:115 ADX:86 DFM:55 MSM:50 QSE:48 BSE:31
NET_INCOME_BEFORE_UNUSUAL         0    385    385  KSE:115 ADX:86 DFM:55 MSM:50 QSE:48 BSE:31  <-- +385
EXTRAORDINARY                     0    407    407  KSE:120 ADX:88 DFM:60 MSM:51 QSE:51 BSE:37  <-- +407
EPS_REPORTED                    100    406    306  KSE:120 ADX:88 DFM:57 QSE:53 MSM:51 BSE:37  <-- +306
EPS_BEFORE_UNUSUAL                0    406    406  KSE:120 ADX:88 DFM:57 QSE:53 MSM:51 BSE:37  <-- +406
SHARES                          236    243      7  TADAWUL:243  <-- +7
AVERAGE_SHARES                    0    408    408  KSE:121 ADX:88 DFM:58 QSE:53 MSM:51 BSE:37  <-- +408
EQUITY_COMMON                   218    626    408  TADAWUL:218 KSE:121 ADX:88 DFM:58 QSE:53 MSM:51 BSE:37  <-- +408
EQUITY_ALL                      211    625    414  TADAWUL:218 KSE:121 ADX:88 DFM:57 QSE:53 MSM:51 BSE:37  <-- +414
REVENUE                         254    254      0  KSE:71 ADX:61 MSM:37 QSE:35 DFM:32 BSE:18
GROSS_INCOME                      0      0      0  
OPERATING_INCOME                  0     49     49  ADX:11 KSE:10 QSE:9 BSE:7 MSM:6 DFM:6  <-- +49
TOTAL_ASSETS                    243    653    410  TADAWUL:243 KSE:121 ADX:88 DFM:60 QSE:53 MSM:51 BSE:37  <-- +410
TCA                             208    377    169  TADAWUL:208 ADX:59 DFM:33 QSE:31 KSE:24 MSM:18 BSE:4  <-- +169
BANK_NET_FINANCING_INCOME         0     30     30  ADX:9 MSM:6 KSE:5 QSE:4 DFM:4 BSE:2  <-- +30
BANK_PROVISIONS                   0     29     29  ADX:9 MSM:6 KSE:5 QSE:4 DFM:4 BSE:1  <-- +29
BANK_FINANCING                    3     42     39  TADAWUL:10 ADX:9 MSM:6 KSE:5 BSE:4 QSE:4 DFM:4  <-- +39
BANK_PERFORMING                   3     10      7  TADAWUL:10  <-- +7
BANK_NPL                          3     10      7  TADAWUL:10  <-- +7
BANK_LOSS_PROVISION               3     10      7  TADAWUL:10  <-- +7
BANK_DEPOSITS                     3     64     61  ADX:11 TADAWUL:10 KSE:10 BSE:10 QSE:9 MSM:7 DFM:7  <-- +61
BANK_INVESTMENTS                 35    230    195  ADX:68 DFM:38 TADAWUL:35 QSE:35 KSE:25 MSM:24 BSE:5  <-- +195
BANK_DUE_FROM_BANKS             134    166     32  TADAWUL:141 ADX:9 MSM:6 QSE:4 DFM:4 KSE:1 BSE:1  <-- +32
```

### 10b. Does a bank claim survive contact with the balance sheet?

```
the pipeline calls 204 of 653 tickers banks. The site's sector for them:
     56  Financial Services
     53  Banks
     27  Insurance
     20  Real Estate
     13  Industrials
     12  Consumer Discretionary
      5  Consumer Staples
      4  Energy

of those 204: 64 carry a customer-deposit line, 41 a lending
balance, and 140 carry neither.

the 64 that carry one or the other, by the site's sector:
     53  Banks
     10  Financial Services
      1  None

the ones carrying neither, which a positive test would stop calling banks:
     46  Financial Services
     27  Insurance
     20  Real Estate
     13  Industrials
     12  Consumer Discretionary
      5  Consumer Staples
      4  Energy
      4  Investment/Holding

a company the site calls a bank that a positive test would drop: none
```

### 10c. The sweep, before the widening and the two fixes

```
653 tickers with line items; period_aware=False

============================================================================================
1. DID ANYTHING BREAK?
============================================================================================
   exceptions or non-finite values: 0

============================================================================================
2. DOES IT STAY INSIDE ITS BUDGET?
============================================================================================
   budget 16,000; datasets over it: 0
   smallest 3,533  median 4,923  95th 7,130  largest 7,733
   datasets whose statements were trimmed by the row cap or the budget: 436

============================================================================================
3. SECTORS, AS THE API WILL READ THEM
============================================================================================
   non_bank      408
   bank          204
   insurance      41

============================================================================================
4. WHICH MEASURES COME BACK, AND WHICH ARE WITHHELD
============================================================================================
   metric                                  offered  withheld  with a value
   extraordinary_share_of_earnings             653       653             0
   eps_derived                                 653       653             0
   roe_on_period_end_common_equity             653       653             0
   payout_cash                                 653       653             0
   net_financing_margin                        204       204             0
   cost_to_income                              204       204             0
   cost_of_risk                                204       204             0
   npl_ratio                                   204       201             3
   npl_coverage                                204       201             3
   equity_to_assets                            204       194            10
   financing_to_deposits                       204       201             3

============================================================================================
5. ARE THE VALUES PLAUSIBLE? (the ones a wrong window or denominator would betray)
============================================================================================
   npl_ratio                           n=3     min         0.75 (1120_TADAWUL)  median       0.92  max         0.98 (1140_TADAWUL)
   equity_to_assets                    n=10    min         9.06 (1020_TADAWUL)  median      12.34  max        15.34 (1180_TADAWUL)
   financing_to_deposits               n=3     min        91.95 (1140_TADAWUL)  median     101.04  max       112.81 (1120_TADAWUL)

============================================================================================
6. WHAT THE EVIDENCE SAYS IT CANNOT ANSWER
============================================================================================
     653  NO CASH FLOW STATEMENT
     244  ONE INCOME-STATEMENT WINDOW
     204  BANK
```

### 10d. The sweep, after

```
653 tickers with line items; period_aware=False

============================================================================================
1. DID ANYTHING BREAK?
============================================================================================
   exceptions or non-finite values: 0

============================================================================================
2. DOES IT STAY INSIDE ITS BUDGET?
============================================================================================
   budget 16,000; datasets over it: 0
   smallest 3,111  median 4,626  95th 7,764  largest 10,320
   datasets whose statements were trimmed by the row cap or the budget: 436

============================================================================================
3. SECTORS, AS THE API WILL READ THEM
============================================================================================
   non_bank      408
   unknown       140
   bank           64
   insurance      41

============================================================================================
4. WHICH MEASURES COME BACK, AND WHICH ARE WITHHELD
============================================================================================
   metric                                  offered  withheld  with a value
   extraordinary_share_of_earnings             653       269           384
   eps_derived                                 653       271           382
   roe_on_period_end_common_equity             653       279           374
   payout_cash                                 653       653             0
   net_financing_margin                         64        39            25
   cost_to_income                               64        23            41
   cost_of_risk                                 64        35            29
   npl_ratio                                    64        54            10
   npl_coverage                                 64        54            10
   equity_to_assets                             64         0            64
   financing_to_deposits                        64        23            41
   net_income_to_operating_income               32         0            32

============================================================================================
5. ARE THE VALUES PLAUSIBLE? (the ones a wrong window or denominator would betray)
============================================================================================
   roe_on_period_end_common_equity     n=374   min       -86.20 (252_KSE)  median       9.27  max       519.99 (SHPS_MSM)
   extraordinary_share_of_earnings     n=384   min      -473.50 (ERES_QSE)  median       0.00  max     1,586.53 (MANAZEL_ADX)
   eps_derived                         n=382   min        -1.32 (AGLTY_DFM)  median       0.04  max       164.20 (ORIENT_DFM)
   npl_ratio                           n=10    min         0.75 (1120_TADAWUL)  median       0.95  max         2.53 (1060_TADAWUL)
   equity_to_assets                    n=64    min    -2,371.23 (BMEB.BH_BSE)  median      10.89  max        30.46 (EIBANK_DFM)
   financing_to_deposits               n=41    min        28.08 (EIBANK_DFM)  median      96.07  max       118.24 (102_KSE)
   cost_to_income                      n=41    min        22.27 (QIBK_QSE)  median      43.51  max       216.85 (813_KSE)
   net_financing_margin                n=25    min         1.64 (BOS_ADX)  median       2.59  max         5.35 (NBQ_ADX)

============================================================================================
6. WHAT THE EVIDENCE SAYS IT CANNOT ANSWER
============================================================================================
     653  NO CASH FLOW STATEMENT
     244  ONE INCOME-STATEMENT WINDOW
      64  BANK
```

### 10e. The tails, and why no payout resolves

```
THE TAILS
--- WDAM_QSE
    net income    'صافي الدخل' = -125.17 (Income Statement, FY2025)
    before unusual'صافي الدخل قبل البنود الاستثنائية و غير المتكررة' = -164.01 (Income Statement, FY2025)
    equity        'مجموع حقوق المساهمين' = -18.99 (Balance Sheet, FY2025)
    assets        'مجموع الموجودات' = 220.54 (Balance Sheet, FY2025)
    share count   'متوسط عدد الأسهم (مليون)' = 180.00 (Balance Sheet, FY2025)
    reported EPS  'ربح السهم (ريال قطري)' = -0.69 (Income Statement, FY2025)
--- ORIENT_DFM
    net income    'الربح الصافي' = 820.98 (Income Statement, FY2025)
    before unusual'صافي الدخل قبل البنود الاستثنائية وغير المتكررة' = 820.98 (Income Statement, FY2025)
    equity        'إجمالى حقوق المساهمين' = 6,090.24 (Balance Sheet, FY2025)
    assets        'إجمالى الموجودات' = 17,273.98 (Balance Sheet, FY2025)
    share count   'متوسط عدد الاسهم (مليون)' = 5.00 (Balance Sheet, FY2025)
    reported EPS  'ربح السهم (درهم)' = 164.20 (Income Statement, FY2025)
--- MANAZEL_ADX
    net income    'صافي الدخل' = 14.40 (Income Statement, FY2025)
    before unusual'صافي الدخل قبل البنود الاستثنائية و غير المتكررة' = -214.06 (Income Statement, FY2025)
    equity        'مجموع حقوق المساهمين' = 2,950.03 (Balance Sheet, FY2025)
    assets        'مجموع الموجودات' = 5,246.01 (Balance Sheet, FY2025)
    share count   'متوسط عدد الأسهم (مليون)' = 2,600.00 (Balance Sheet, FY2025)
    reported EPS  'ربح السهم (درهم)' = 0.01 (Income Statement, FY2025)
--- BMEB.BH_BSE
    net income    'الربح الصافي' = -0.64 (Income Statement, FY2025)
    before unusual'صافي الدخل قبل البنود الاستثنائية و غير المتكررة' = -0.64 (Income Statement, FY2025)
    equity        'إجمالي حقوق المساهمين' = -47.47 (Balance Sheet, FY2025)
    assets        'إجمالي الموجودات' = 2.00 (Balance Sheet, FY2025)
    share count   'متوسط عدد الأسهم (مليون)' = 400.00 (Balance Sheet, FY2025)
    reported EPS  'ربح السهم (فلس)' = -0.00 (Income Statement, FY2025)

WHY NO PAYOUT RESOLVES ANYWHERE
  tickers with dividend rows: 230
  by exchange:
     TADAWUL     230

  the latest fiscal year in the statements, against the newest dividend, for a few:
     KFH_KSE       statements to FYNone   window None   0 dividends (0 with an amount), newest None
     FAB_ADX       statements to FY2025   window ('2025-01-01', '2025-12-31')   0 dividends (0 with an amount), newest None
     EMAAR_DFM     statements to FY2025   window ('2025-01-01', '2025-12-31')   0 dividends (0 with an amount), newest None
     QIBK_QSE      statements to FY2025   window ('2025-01-01', '2025-12-31')   0 dividends (0 with an amount), newest None
     2222_TADAWUL  statements to FY2025   window ('2025-01-01', '2025-12-31')   10 dividends (10 with an amount), newest 2026-08-27
```

### 10f. The suite

```
........................................................................ [ 92%]
......................................                                   [100%]
531 passed, 11 skipped in 73.95s (0:01:13)
```

### 10g. The same sweep against a repaired parse (period_aware=True)

`python sweep_repaired.py` — the 32 tickers of the dry run, parsed by the repaired parser and
gauged by the patched stage, which is the state after both patches are applied.

```
32 tickers from the repaired parse; period_aware=True

exceptions: 0
budget 16,000: over it 0; median 8,188  largest 12,769
sectors {'bank': 16, 'non_bank': 12, 'unknown': 3, 'insurance': 1}
datasets carrying a quarterly series: 18 of 32
sections carrying the source columns they were summed from: 27

reporting modes seen, by section:
   Balance Sheet FY          14
   Balance Sheet Q           16
   Income Stateme FY         14
   Income Stateme TTM        18

aggregation rules recorded:
   annual_column               28
   sum_quarters                18
   quarter_end_snapshot        16
   row:end_quarter_position     9
   row:mean_of_quarters         2

metric                               offered withheld  value   median
extraordinary_share_of_earnings           32       10     22   0.00
eps_derived                               32        3     29   0.37
roe_on_period_end_common_equity           32        3     29   12.18
payout_cash                               32       32      0   -
eps_unit_confirmation                     16        0     16   5,240.00
net_financing_margin                      16       11      5   2.99
cost_to_income                            16       10      6   38.45
cost_of_risk                              16        2     14   0.30
npl_ratio                                 16        6     10   0.93
npl_coverage                              16        6     10   160.30
equity_to_assets                          16        0     16   11.46
financing_to_deposits                     16        1     15   102.88
net_income_to_operating_income             8        0      8   53.65
```

### 10h. The three cases, re-run after every fix above

```
$ diff demo_packs_before_sweep.out demo_packs.out
IDENTICAL: the three cases are unchanged by the sweep's fixes
```
