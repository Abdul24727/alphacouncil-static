# Ingestion repair, 2026-10-28: the raw output of the before/after run

Produced by running the pipeline's own parser and the repaired one over the same pages,
copied read-only from the server, into two local scratch databases. Nothing on the server
was written. Patch: docs/pipeline-fix-statements-2026-10-28.patch. Report:
docs/ingestion-repair-reconciliation-2026-10-28.md.

```
the Arabic count markers resolve: True True | per-share earnings stay summable: True True

==============================================================================
BEFORE / AFTER, fundamentals_lineitems (what the gauge stage and the API read)
==============================================================================
ticker         section                        before                 after
2222_TADAWUL   Balance Sheet          42 rows / 2025        42 rows / 2025
2222_TADAWUL   Income Statement               absent        18 rows / 2026
               mode               quarterly_reconstructedquarterly_reconstructed
               quarterly rows                      -                   246

1120_TADAWUL   Balance Sheet          32 rows / 2025        32 rows / 2025
1120_TADAWUL   Income Statement               absent        24 rows / 2026
               mode               quarterly_reconstructedquarterly_reconstructed
               quarterly rows                      -                   179

2010_TADAWUL   Balance Sheet          58 rows / 2025        58 rows / 2025
2010_TADAWUL   Income Statement               absent        15 rows / 2026
               mode               quarterly_reconstructedquarterly_reconstructed
               quarterly rows                      -                   234

4061_TADAWUL   Balance Sheet          55 rows / 2025        55 rows / 2025
4061_TADAWUL   Income Statement               absent        20 rows / 2026
               mode               quarterly_reconstructedquarterly_reconstructed
               quarterly rows                      -                   294

4190_TADAWUL   Balance Sheet          60 rows / 2025        60 rows / 2025
4190_TADAWUL   Income Statement               absent        20 rows / 2026
               mode               quarterly_reconstructedquarterly_reconstructed
               quarterly rows                      -                   246

ABNIC_ADX      (none)                  1 rows / 2021         1 rows / 2021
ABNIC_ADX      Balance Sheet      51 rows / 2021,2022,2023,2024,202551 rows / 2021,2022,2023,2024,2025
ABNIC_ADX      Income Statement   68 rows / 2021,2022,2023,2024,202568 rows / 2021,2022,2023,2024,2025
               mode                    annual_direct         annual_direct
               quarterly rows                      -                     0

==============================================================================
REPORTING MODES now carried on every row
==============================================================================
  1120_TADAWUL   Balance Sheet      FY   2025-12    32 rows
  1120_TADAWUL   Income Statement   TTM  2026-06    24 rows
  2010_TADAWUL   Balance Sheet      FY   2025-12    58 rows
  2010_TADAWUL   Income Statement   TTM  2026-06    15 rows
  2222_TADAWUL   Balance Sheet      FY   2025-12    42 rows
  2222_TADAWUL   Income Statement   TTM  2026-06    18 rows
  4061_TADAWUL   Balance Sheet      FY   2025-12    55 rows
  4061_TADAWUL   Income Statement   TTM  2026-06    20 rows
  4190_TADAWUL   Balance Sheet      FY   2025-12    60 rows
  4190_TADAWUL   Income Statement   TTM  2026-06    20 rows
  ABNIC_ADX      (none)             FY   2021-12     1 rows
  ABNIC_ADX      Balance Sheet      FY   2021-12    11 rows
  ABNIC_ADX      Balance Sheet      FY   2022-12    10 rows
  ABNIC_ADX      Balance Sheet      FY   2023-12    10 rows
  ABNIC_ADX      Balance Sheet      FY   2024-12    10 rows
  ABNIC_ADX      Balance Sheet      FY   2025-12    10 rows
  ABNIC_ADX      Income Statement   FY   2021-12     8 rows
  ABNIC_ADX      Income Statement   FY   2022-12    15 rows
  ABNIC_ADX      Income Statement   FY   2023-12    15 rows
  ABNIC_ADX      Income Statement   FY   2024-12    15 rows
  ABNIC_ADX      Income Statement   FY   2025-12    15 rows

==============================================================================
THE THREE CASES: the lines that were missing
==============================================================================
--- 2222_TADAWUL
    Sales                                           1,823,483.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Cost of Sales                                    -887,177.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Gross Income                                      936,306.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Operating Income                                  816,723.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Profit Before Unusual Items                   444,901.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Extraordinary income/expense                      -36,530.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Income                                        408,371.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Shares Outstanding (Million)                      242,000.00  TTM@2026-06  end_quarter_count 2026-06
    Earning Per Share (Riyal)                               1.69  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Earnings Per Share before unusual items (Riyal)          1.83  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Financing Expense                                  -9,997.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Zakat & Tax                                      -370,579.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']

--- 1120_TADAWUL
    Operating Income                                   41,703.95  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Profit Before Unusual Items                    26,498.39  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Extraordinary income/expense                            0.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Income                                         26,498.39  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Shares Outstanding (Million)                        6,000.00  TTM@2026-06  end_quarter_count 2026-06
    Earning Per Share (Riyal)                               4.42  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Earnings Per Share before unusual items (Riyal)          4.42  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']

--- 2010_TADAWUL
    Sales                                             113,241.07  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Cost of Sales                                     -93,783.75  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Gross Income                                       19,457.32  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Operating Income                                      486.64  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    EBITDA                                             16,960.00  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Profit Before Unusual Items                    -4,509.71  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Extraordinary income/expense                      -16,812.35  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Net Income                                        -21,322.06  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Shares Outstanding (Million)                        3,000.00  TTM@2026-06  end_quarter_count 2026-06
    Earning Per Share (Riyal)                              -7.11  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Earnings Per Share before unusual items (Riyal)         -1.51  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Financing Expense                                  -3,549.95  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
    Zakat & Tax                                        -1,536.42  TTM@2026-06  sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']

```

## Checks

```
1. BACKWARD COMPATIBILITY - nothing an existing reader sees may change
  [PASS] 2222_TADAWUL balance sheet row-exact: 42 rows before, 42 after, every (year, index, label, value) identical
  [PASS] 1120_TADAWUL balance sheet row-exact: 32 rows before, 32 after, every (year, index, label, value) identical
  [PASS] 2010_TADAWUL balance sheet row-exact: 58 rows before, 58 after, every (year, index, label, value) identical
  [PASS] 4061_TADAWUL balance sheet row-exact: 55 rows before, 55 after, every (year, index, label, value) identical
  [PASS] 4190_TADAWUL balance sheet row-exact: 60 rows before, 60 after, every (year, index, label, value) identical
  [PASS] ABNIC_ADX Income Statement row-exact (annual grid untouched): 68 rows, identical
  [PASS] ABNIC_ADX Balance Sheet row-exact (annual grid untouched): 51 rows, identical
  [PASS] ABNIC_ADX (none) row-exact (annual grid untouched): 1 rows, identical

2. THE 4x SHARE-COUNT ARTIFACT
  [PASS] 2222_TADAWUL income-statement share count equals the balance sheet's: income statement 242000.0, balance sheet 242000.0, was 968000.0
  [PASS] 2010_TADAWUL income-statement share count equals the balance sheet's: income statement 3000.0, balance sheet 3000.0, was 12000.0

3. INTERNAL CONSISTENCY of the reconstructed income statement
  [PASS] 2222_TADAWUL Sales + Cost of Sales = Gross Income: 936,306.00 vs 936,306.00
  [PASS] 2222_TADAWUL pre-unusual + extraordinary = Net Income: 408,371.00 vs 408,371.00
  [PASS] 2010_TADAWUL Sales + Cost of Sales = Gross Income: 19,457.32 vs 19,457.32
  [PASS] 2010_TADAWUL pre-unusual + extraordinary = Net Income: -21,322.06 vs -21,322.06
  [PASS] 4061_TADAWUL Sales + Cost of Sales = Gross Income: 21.60 vs 21.60
  [PASS] 4061_TADAWUL pre-unusual + extraordinary = Net Income: -10.25 vs -10.25
  [PASS] 2222_TADAWUL Net Income / shares reproduces the reported EPS: 1.69 vs reported 1.69
  [PASS] 1120_TADAWUL Net Income / shares reproduces the reported EPS: 4.42 vs reported 4.42
  [PASS] 2010_TADAWUL Net Income / shares reproduces the reported EPS: -7.11 vs reported -7.11
  [PASS] 4061_TADAWUL Net Income / shares reproduces the reported EPS: -0.33 vs reported -0.32
  [PASS] 4190_TADAWUL Net Income / shares reproduces the reported EPS: 0.94 vs reported 0.94

4. AGAINST THE 2026-08-02 LOAD, which had four complete quarters of FY2025
  [PASS] Aramco TTM sales exceed FY2025's 1,671,204 (a newer, overlapping window): TTM 1,823,483 against FY2025 1,671,204
  [PASS] Aramco TTM EPS is close to the vendor's published eps_ttm of 1.68: reconstructed 1.6875 vs vendor 1.68

5. PRESERVED HISTORY
  [PASS] 2222_TADAWUL quarterly history kept: Q: 5 period ends, 210 rows, TTM: 2 period ends, 36 rows
  [PASS] 1120_TADAWUL quarterly history kept: Q: 5 period ends, 140 rows, TTM: 2 period ends, 39 rows
  [PASS] 2010_TADAWUL quarterly history kept: Q: 5 period ends, 204 rows, TTM: 2 period ends, 30 rows
  [PASS] Aramco balance-sheet snapshots kept: 5: ['2025-06', '2025-09', '2025-12', '2026-03', '2026-06']

6. TRACEABILITY - every stored value names its rule and its quarters
  [PASS] every row carries source_json: 464 of 464
         rules used: {'year_end_snapshot': 247, 'sum_quarters': 92, 'end_quarter_count': 5, 'annual_column': 120}

FAILURES: none
```

## Derived metrics, with the provenance of every input

```
==============================================================================================
2222_TADAWUL  Saudi Aramco - dividend aggregation and earnings coverage
==============================================================================================
  net margin                         before: missing_inputs         after: 22.40 %
        Net Income 408,371  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        Sales      1,823,483  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']

  interest coverage                  before: missing_inputs         after: 81.7 x
        Operating Income  816,723  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        Financing Expense -9,997  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']

  dividend cover, cash basis         before: not derivable          after: 1.26 x
        Net Income 408,371  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        dividends with an ex-date in the SAME window 324,390
          <- pack P3, ex-dates 2026-06-01, 2026-03-16, 2025-11-17, 2025-08-19

  payout ratio, cash basis           before: missing_inputs         after: 79.4 %
        the same two inputs, on one matched window - which is what the inspection could not
        do: it reached 73.4 % by hand and 92.6 % from the gauge, neither on a matched window

  payout ratio, declared basis       before: missing_inputs         after: 79.9 %
        dividends declared FOR the four quarters 326,340
          <- notes Q 2 _ 2026, Q 1 _ 2026, Q 4 _ 2025, Q 3 _ 2025 
        the pipeline's gauge matches this way; the two bases differ because the ex-date lags
        the quarter it is declared for, and neither is wrong - but they must not be mixed

  share count in the income statement before: 968,000 mn (4x)        after: 242,000 mn
        <- TTM@2026-06 end_quarter_count 2026-06
        balance sheet says 242,000 mn - they now agree

==============================================================================================
1120_TADAWUL  Al Rajhi - the bank measures, three of which were blocked
==============================================================================================
  cost / income                      before: BLOCKED (no income statement) after: 23.4 %
        Operating Expenses -9,747.73  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        Operating Income   41,703.95  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        note: for a bank the revenue line IS 'Operating Income' (total operating income),
        not 'Sales' - which is why the gauge's revenue list still misses it (see the proposal)

  net financing margin               before: BLOCKED                after: 3.47 %
        Net financing income 32,155.26  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        earning assets 927,064.45 = Net Financing Investments 752,759.85 + Investments 174,304.60
           <- FY@2025-12 year_end_snapshot 2025-12

  cost of risk                       before: BLOCKED                after: 0.36 %
        Debt Provisions -2,724.91  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        Net Financing Investments 752,759.85

  NPL ratio                          before: derivable, never exposed after: 0.75 %
        NPL 5,694.22 / (performing 755,748.52 + NPL)  <- balance sheet, unchanged by the repair

  NPL coverage                       before: derivable, never exposed after: 152.5 %
        loss provision -8,682.89 / NPL 5,694.22

  equity / assets                    before: derivable, never exposed after: 11.01 %
        equity 114,854.17 / assets 1,043,268.30

  loans / deposits                   before: derivable, never exposed after: 112.8 %
        net financing 752,759.85 / customer deposits 667,287.50

  return on equity                   before: published only (23.49 %) after: 23.07 %
        Net Income 26,498.39 (TTM) / equity 114,854.17 (FY2025)
        a mixed-period ratio, and the repair is what makes that visible: TTM@2026-06 over
        FY@2025-12. The vendor's 23.49 % cannot be checked at all

==============================================================================================
2010_TADAWUL  SABIC - the loss, and cyclical against structural
==============================================================================================
  net margin                         before: missing_inputs         after: -18.83 %
        Net Income -21,322.06  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        Sales 113,241.07

  gross margin                       before: na_sector (wrongly)    after: 17.18 %
        Gross Income 19,457.32 / Sales 113,241.07

  operating margin                   before: not derivable          after: 0.43 %
        Operating Income 486.64  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        POSITIVE on a trailing-twelve-month basis, against -292.16 for FY2025

  extraordinary share of the loss    before: not derivable          after: 78.8 %
        Extraordinary -16,812.35 of Net Income -21,322.06
        loss before unusual items -4,509.71; EBITDA still 16,960.00
        the structural and headline pictures differ by 4.7x and point opposite ways

  EPS                                before: null, reason 'unit_unconfirmed' after: -7.11 a share
        <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
        and -21,322.06 / 3,000 mn shares = -7.11, so it checks against
        its own statement. The pack's -1.76 reconciles with nothing

==============================================================================================
4061_TADAWUL  the two probes that rested on orphaned gauges
==============================================================================================
  net margin after the repair      -29.28 %   (orphaned gauge: -49.91 %)
  gross margin after the repair    61.70 %   (orphaned gauge: 56.31 %)
  D6's pre-registered band is (-60, -40): OUTSIDE
  inputs: Sales 35.01, Net Income -10.25, Gross 21.60  <- TTM@2026-06 sum_quarters ['2025-09', '2025-12', '2026-03', '2026-06']
```

## The wider dry run: 33 tickers, seven exchanges

Six tickers is thin for a market-wide parser change, so the same before/after was run over a
spread of 33: eighteen Tadawul (banks, insurers, industrials), and fifteen on the six other
exchanges as controls. Both parsers, same pages, two local scratch databases.

```
33 tickers, both parsers, same pages

crashes in the repaired parser: none
crashes in the original:        none

REGRESSIONS - a row an existing reader had, now missing or different
  rows LOST:    0
  rows CHANGED: 0

modes (after, before): {('quarterly_reconstructed', 'quarterly_reconstructed'): 18, ('annual_direct', 'annual_direct'): 14, (None, None): 1}

ticker            before   after   gain  quarterly  mode
1010_TADAWUL          33      61     28        189  quarterly_reconstructed
101_KSE              319     319      0          0  annual_direct
1020_TADAWUL          33      61     28        189  quarterly_reconstructed
102_KSE              146     146      0          0  annual_direct
1030_TADAWUL          33      61     28        190  quarterly_reconstructed
103_KSE              135     135      0          0  annual_direct
1050_TADAWUL          33      61     28        190  quarterly_reconstructed
1060_TADAWUL          33      61     28        188  quarterly_reconstructed
1080_TADAWUL          33      61     28        189  quarterly_reconstructed
1111_TADAWUL          47      71     24        283  quarterly_reconstructed
1120_TADAWUL          32      56     24        179  quarterly_reconstructed
1140_TADAWUL          32      56     24        180  quarterly_reconstructed
1150_TADAWUL          32      56     24        180  quarterly_reconstructed
1180_TADAWUL          32      59     27        190  quarterly_reconstructed
1182_TADAWUL           0      53     53        106  quarterly_reconstructed
1183_TADAWUL           0      54     54        108  quarterly_reconstructed
1201_TADAWUL          55      76     21        315  quarterly_reconstructed
2010_TADAWUL          58      73     15        234  quarterly_reconstructed
2222_TADAWUL          42      60     18        246  quarterly_reconstructed
2POINTZERO_ADX       454     454      0          0  annual_direct
4061_TADAWUL          55      75     20        294  quarterly_reconstructed
4190_TADAWUL          60      80     20        246  quarterly_reconstructed
AACT_MSM             450     450      0          0  annual_direct
AAIC_MSM               0       0      0          0  None
ABC.BH_BSE           102     102      0          0  annual_direct
ABNIC_ADX            120     120      0          0  annual_direct
ABQK_QSE             335     335      0          0  annual_direct
ABRAAJ_BSE            51      51      0          0  annual_direct
ADAV.AD_ADX          535     535      0          0  annual_direct
AGLTY_DFM            440     440      0          0  annual_direct
AHCS_QSE             445     445      0          0  annual_direct
AIRARABIA_DFM        415     415      0          0  annual_direct
AJMANBAN_DFM         319     319      0          0  annual_direct

INCOME STATEMENT, by exchange
  ADX          3 tickers   before   3   after   3
  BSE          2 tickers   before   2   after   2
  DFM          3 tickers   before   3   after   3
  KSE          3 tickers   before   3   after   3
  MSM          2 tickers   before   1   after   1
  QSE          2 tickers   before   2   after   2
  TADAWUL     18 tickers   before   0   after  18

PERIODS chosen, after
  FY     30 tickers,  4909 rows
  TTM    18 tickers,   492 rows

flow statements spanning MORE THAN ONE period_end (must be none for a quarterly grid ticker; an annual grid legitimately has one per year): 14
   101_KSE Income Statement: 5 period ends  mode=annual_direct
   102_KSE Income Statement: 5 period ends  mode=annual_direct
   103_KSE Income Statement: 5 period ends  mode=annual_direct
   2POINTZERO_ADX Income Statement: 5 period ends  mode=annual_direct
   AACT_MSM Income Statement: 5 period ends  mode=annual_direct
   ABC.BH_BSE Income Statement: 5 period ends  mode=annual_direct
   ABNIC_ADX Income Statement: 5 period ends  mode=annual_direct
   ABQK_QSE Income Statement: 5 period ends  mode=annual_direct
   ABRAAJ_BSE Income Statement: 3 period ends  mode=annual_direct
   ADAV.AD_ADX Income Statement: 5 period ends  mode=annual_direct
   of those, QUARTERLY-reconstructed (the ones that would be wrong): 0 

rows without source_json: 0
```
