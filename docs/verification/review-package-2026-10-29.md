# Acceptance review: raw output

2026-10-29, after the Priority One closeout. Branch `rebuild`. Nothing applied, published, pushed
or deployed, and no paid call made.

Every figure in `docs/review-package-2026-10-29.md` comes from one of the sections below. The
scripts run read-only against local copies of the published databases (`screening.sqlite`,
`briefs_index.sqlite`, copied by `scp` on 2026-10-29) and against the two scratch parses
`demo_before.sqlite` / `demo_after.sqlite`, which are today's parser and the repaired parser run
over the same live pages with the patched gauge stage over each.

## Contents

1. The contamination in the sector rankings, measured by replaying both pipeline stages
2. The vintage check: what can be read back, and what it can never reach
3. Is a simple mean of quarterly average-share columns the window's weighted average?
4. The three closures validated over all 653 tickers
5. What P9 costs a debate, with the counting method
6. The three cases: the P9 pack before and after, and the gauge strip

---

## 1. The contamination in the sector rankings

`compute_gauge_scores.py` (stage 4) ranks each value inside the peer class `compute_sector_averages.py`
(stage 3) bucketed the ticker into, and stage 4 imports stage 3's own `ticker_sector_class`. Both
stages are replayed here against a copy of the published database: once with the pipeline's own
buckets, which reproduces every published score exactly, and once with the 140 bank claims the
balance sheet does not corroborate moved to `non_bank`.

```
tickers carrying gauges: 653
the pipeline's buckets: {'bank': 204, 'non_bank': 408, 'insurance': 41}
bank claims the balance sheet does not corroborate: 140
the corrected buckets: {'bank': 64, 'non_bank': 548, 'insurance': 41}

replay against the published scores: 1954 agree, 0 differ

HOW FAR EVERY ROW MOVES WHEN THE 140 LEAVE THE BANK BUCKET
bucket (as published)     rows  unmoved  >5pts  >20pts  median move   worst
bank                       196       34     91       0          4.8    18.2
insurance                   85       85      0       0          0.0     0.0
non_bank                  1673     1343      0       0          0.0     4.7

THE REAL BANKS: what the contamination did to the 64 corroborated ones
  64 corroborated banks, 82 scored rows
  median move 1.6 points, mean 2.6, worst 9.9; 0 rows move more than 20 points
  the ten largest moves:
     NBQ_ADX         payout              21.4 ->   11.5   (-9.9)
     CBQK_QSE        payout              39.5 ->   30.2   (-9.3)
     103_KSE         payout              31.0 ->   21.9   (-9.1)
     102_KSE         payout              22.4 ->   13.5   (-8.9)
     KHALEEJI_BSE    payout              36.7 ->   28.1   (-8.6)
     KFH_BSE         payout              40.5 ->   32.3   (-8.2)
     101_KSE         payout              42.4 ->   34.4   (-8.0)
     QIIK_QSE        payout              31.9 ->   24.0   (-7.9)
     DUBK_QSE        payout              33.8 ->   26.0   (-7.8)
     ABQK_QSE        payout              23.3 ->   15.6   (-7.7)

THE 140 MIS-BUCKETED COMPANIES: what they were ranked against
  140 companies, 114 scored rows
  median move 8.2 points, worst 18.2; 0 rows move more than 20 points

SO WHICH PERCENTILES ARE SAFE TO SHOW?
  buckets no row of which moves at all: ['insurance']
  of 1954 scored rows, 492 change when the classification is corroborated (25.2%)
```

---

## 2. The vintage check

The guard compared the gauge's recorded fiscal year and period end against the statements'. A
source figure corrected inside the same period keeps both, so a gauge computed from the old
figure passed. Closing that needs the gauge's own operands read back against the lines they came
from, which is possible exactly where the gauge named the line.

```
EVERY KEY EVERY GAUGE WRITES INTO inputs_json
   current_ratio     current_assets(653), current_liabilities(653), note(276)
   debt_equity       total_debt(653), debt_parts(653), equity(653), equity_label(653), sector(653), missing(242), searched(72), expected_section(72), available_in_section(72)
   ev_ebitda         sector(653), note(653)
   fcf_yield         free_cash_flow(653), fcf_source(653), market_cap_m(653), fcf_components(653), sector(653), note(653)
   gross_margin      gross_income(653), revenue(653), revenue_label(653), note(462), missing(2), searched(2), expected_section(2), available_in_section(2)
   interest_coverage operating_income(653), finance_expense(653), finance_expense_label(653), sector(653), missing(446), searched(446), expected_section(446), available_in_section(446), note(41)
   net_margin        net_income(653), revenue(653), revenue_label(653), year(653), missing(360), searched(360), expected_section(360), available_in_section(360)
   payout            dividends(653), net_income(653), dividend_source(653), dividend_rows_matched(653), dividend_matched_rows(653), dividend_ambiguous_rows(653), dividend_csv(653), year(653), missing(376), searched(245), expected_section(245), available_in_section(245), note(131)
   ps                market_cap_m(653), revenue(653), revenue_label(653), missing(550), searched(360), expected_section(360), available_in_section(360)
   roic              operating_income(653), taxes(653), tax_label(653), total_debt(653), equity(653), sector(653), note(245), missing(242), tax_gap(239)

WHICH OF THOSE NAME A LINE ITEM, SO THE FIGURE CAN BE READ BACK
  Two shapes carry a name: `<x>_label` names the line behind operand `<x>`, and
  `debt_parts` is a label-to-value map. `tax_label` names the operand `taxes`, not `tax`,
  which is the one alias in OPERAND_ALIASES; without it roic's tax line was read back for
  0 of 653 tickers instead of 216, invisibly, because a check that never runs says nothing.

  gauge               rows  named operand  + a year stamp  reachable today
  current_ratio        653              0               0               no
  debt_equity          653            625               0               no
  ev_ebitda            653              0               0               no
  fcf_yield            653              0               0               no
  gross_margin         653            293               0               no
  interest_coverage    653            171               0               no
  net_margin           653            293             293              yes
  payout               653              0               0               no
  ps                   653            293               0               no
  roic                 653            216               0               no
  TOTAL               6530           1891             293

  Today only net_margin carries both a named operand and a year (`year`), so the revision
  check reaches 293 of 6,530 rows. The prepared gauge patch stamps `fiscal_year` on EVERY
  row, which takes it to 1,891 of 6,530 across six gauges. Four gauges can never be
  reached as they are written - current_ratio, ev_ebitda, fcf_yield and payout record no
  line-item name at all - and for those the guarantee is the period only, reported as
  vintage=period on the metric rather than left for a reader to assume away.

ONE TICKER'S OPERANDS, READ BACK AGAINST THE STATEMENTS AS THEY STAND
--- FAB_ADX debt_equity  (year stamp: None, vintage basis: period)
      'سندات وتمويل لآجل'                             gauge      82,325.00   statements FY2024=71,649.00, FY2025=82,325.00
      'أرصدة للبنوك والمؤسسات المالية'                gauge     137,801.00   statements FY2024=71,896.00, FY2025=137,801.00
      'مجموع حقوق الملكية'                            gauge     146,885.00   statements FY2024=130,875.00, FY2025=146,885.00
      stale_reason: None
--- 2010_KSE net_margin  (year stamp: 2025, vintage basis: inputs)
      'الايرادات'                                     gauge          23.64   statements FY2024=14.35, FY2025=23.64
      stale_reason: None
--- 2010_KSE roic  (year stamp: None, vintage basis: period)
      stale_reason: None
--- 2010_KSE ps  (year stamp: None, vintage basis: period)
      'الايرادات'                                     gauge          23.64   statements FY2024=14.35, FY2025=23.64
      stale_reason: None
```

---

## 3. Is a simple mean the window's weighted average?

The parser gives an average-share row the `mean` rule, so a four-quarter window takes the mean of
four quarterly columns. That is the annual weighted average only if each quarterly column is that
quarter's own average. The two readings are distinguishable on real data wherever the count moved.

```
rows in the repaired parse: 6004

WHICH AGGREGATION RULE LANDS ON WHICH KIND OF SHARE ROW
   average   FY   annual_column             136
   position  FY   year_end_snapshot          16
   position  Q    quarter_end_snapshot       16
   position  TTM  end_quarter_position        9
   average   TTM  mean_of_quarters            4

THE QUARTERLY SERIES BEHIND EVERY MEANED AVERAGE-SHARE WINDOW
windows meaned: 4
--- 1182_TADAWUL  'Average number of shares (mln)'  (Income Statement, TTM to 2026-06)
      quarters: 2025-09=none, 2025-12=none, 2026-03=none, 2026-06=none
      mean written: 101.9300   (incomplete)
      moves across the window: 0.0000   monotone: False   <- a flat series cannot tell the two readings apart
--- 1182_TADAWUL  'Average number of shares (mln)'  (Income Statement, TTM to 2026-06)
      quarters: 2025-09=none, 2025-12=none, 2026-03=none, 2026-06=none
      mean written: 101.9300   (incomplete)
      moves across the window: 0.0000   monotone: False   <- a flat series cannot tell the two readings apart
--- 1183_TADAWUL  'Average number of shares (mln)'  (Income Statement, TTM to 2026-06)
      quarters: 2025-09=none, 2025-12=none, 2026-03=none, 2026-06=none
      mean written: 100.0000   (incomplete)
      moves across the window: 0.0000   monotone: False   <- a flat series cannot tell the two readings apart
--- 1183_TADAWUL  'Average number of shares (mln)'  (Income Statement, TTM to 2026-06)
      quarters: 2025-09=none, 2025-12=none, 2026-03=none, 2026-06=none
      mean written: 100.0000   (incomplete)
      moves across the window: 0.0000   monotone: False   <- a flat series cannot tell the two readings apart

DOES ANY AVERAGE-SHARE ROW MOVE AT ALL, ANYWHERE IN THE QUARTERLY DATA?
   average-share rows whose quarterly value moves: 0 of 0

AND THE POSITION ROWS: does the count move inside a window?
   position rows whose quarterly count moves: 0 of 16
```

---

## 4. The three closures validated over the universe

A check that withholds a figure has two failure modes and the quiet one is worse: missing a stale
gauge shows a wrong number, but calling a FRESH gauge stale withholds a right one across the whole
universe. So section 1 establishes that the revision check flags nothing on an unmodified
database, and only then that it flags the right thing on a modified one.

```
1. THE REVISION CHECK ON AN UNMODIFIED DATABASE (it must flag nothing)
--- the published database, 653 tickers: 653 tickers
    vintage basis: {'period': 6237, 'inputs': 293}
    gauges the vintage check withholds: 0
    peer classes: {'bank': 204, 'non_bank': 408, 'insurance': 41}
    sector ranks: 196 withheld, 1758 kept
    false positives: 0

2. THE SAME DATABASE WITH ONE FIGURE REVISED INSIDE ITS OWN PERIOD
    net_margin rows whose revenue line is named and dated: 289
      2010_KSE        'الايرادات'                           gauge 23.64  statement 23.64
      2012_KSE        'الايرادات'                           gauge 0.19  statement 0.19
      202_KSE         'الايرادات'                           gauge 14.97  statement 14.97
    revised the revenue line of 20 companies by 3%, same year, same period
--- the revised database: 653 tickers
    vintage basis: {'period': 6237, 'inputs': 293}
    gauges the vintage check withholds: 20  {'net_margin': 20}
      2010_KSE net_margin: computed from 'الايرادات' = 23.64 while the statements now carry 24.35 for the same fiscal year 2025: the figure was revised after the gauge stage las
      2012_KSE net_margin: computed from 'الايرادات' = 0.19 while the statements now carry 0.20 for the same fiscal year 2025: the figure was revised after the gauge stage last 
      202_KSE net_margin: computed from 'الايرادات' = 14.97 while the statements now carry 15.42 for the same fiscal year 2025: the figure was revised after the gauge stage las
      205_KSE net_margin: computed from 'الايرادات' = 1,485.06 while the statements now carry 1,529.61 for the same fiscal year 2025: the figure was revised after the gauge sta
      235_KSE net_margin: computed from 'الايرادات' = 3.07 while the statements now carry 3.16 for the same fiscal year 2025: the figure was revised after the gauge stage last 
    peer classes: {'bank': 204, 'non_bank': 408, 'insurance': 41}
    sector ranks: 196 withheld, 1758 kept
    expected 20, caught 20

3. THE SAME, ON THE POST-PATCH GAUGE OUTPUT (every row stamped with its fiscal year)
--- the three demonstration companies, repaired and re-gauged: 6 tickers
    vintage basis: {'period': 28, 'inputs': 32}
    gauges the vintage check withholds: 0
    peer classes: {'bank': 1, 'non_bank': 4, 'insurance': 1}
    sector ranks: 0 withheld, 0 kept

4. DERIVED EPS: WHICH BASIS, AND WHAT IS WITHHELD
--- the published database: 653 tickers
    given    source's own average-share column           382
    withheld no net income, or a zero count              268
    withheld no share count at all                         3
--- the repaired parse: 6 tickers
    given    unchanged position                            5
    given    source's own average-share column             1

5. WHAT THE PEER-GROUP RULE COSTS, AND WHAT IT PROTECTS
    scored rows: 1758 kept, 196 withheld (10.0%)
      bank        kept     0   withheld   196
      insurance   kept    85   withheld     0
      non_bank    kept  1673   withheld     0
    (the 492 rows the corrected classification MOVES are measured in contamination.out; every one of them is inside the withheld set or moves by less than 4.7 points)
```

---

## 5. What P9 costs a debate

```
THE ROOM AS CONFIGURED (app/settings.py, untouched by this work)
  advisors seated          6  buffett, lynch, dalio, marks, alwaleed, alrumayyan
  advisor model            deepseek/deepseek-v4-pro
  chair model              anthropic/claude-sonnet-5.5
  debate rounds            1 (clamped to 1..2 -> 1)
  stages                   brief, openings, faultlines, debate x1, final, verdict
  model calls per debate   21 = chair 3 + advisors 6x(2+1)=18
  the pack is in EVERY call's system prompt (engine.Room.system) and the debate path does
  no prompt caching, so the pack is paid for once per call.

WHAT P9 ADDS TO ONE CALL'S PROMPT, exactly
ticker           P1-P8 chars  P9 chars    total    +%  P1-P8 bytes  P9 bytes    total
2222_TADAWUL          17,473    10,917   29,062   66%       17,588    10,919   29,179
1120_TADAWUL          20,043    14,937   35,660   78%       20,172    14,941   35,793
2010_TADAWUL          18,421     9,617   28,725   56%       18,654     9,619   28,960
4061_TADAWUL          18,123     8,142   26,878   48%       18,751     8,144   27,508
4190_TADAWUL          18,325     8,248   27,225   49%       18,639     8,250   27,541

PER CALL, mean of the five
  characters   18,477 -> 29,510   (+10,372, +56%)
  UTF-8 bytes  18,761 -> 29,796   (+10,375, +55%)

PER DEBATE, 21 calls
  characters added   217,816
  UTF-8 bytes added  217,867  <- a CEILING on the added input tokens:
                        no byte-level BPE tokenizer emits more tokens than bytes
  chars/4 would say  54,454  <- the old assumption, not a measurement
  so the added input tokens per debate are between about 54,454 and 217,867.
  The true figure is the provider's reported prompt_tokens and needs a paid run.

THE HARD BOUND, independent of any ticker
  P9's declared budget is 16,000 characters and Pack.prompt() truncates at it,
  so one call can never carry more than 16,000 characters of P9 and a debate never more than 336,000.

DOES THE PACK'S TRUNCATION EVER FIRE? (it must not: it cuts mid-row)
  fit() drops whole statement rows while over budget and never a calculation, a limitation
  or a row a calculation divides by; Pack.prompt()'s [:budget] is the backstop behind it.
  653 tickers: 0 over the 16,000-character budget; largest 10,776 (QNBK_QSE)
  limitations intact after fit(): 653 of 653
  headroom at the largest: 5,224 characters
```

---

## 6. The three cases

The pack is built by the module the advisors read through (`api/app/evidence.py`), so this is the
pack and not a description of one. Nothing is truncated: a limitation cut short is the part that
matters cut off. The `rank` column is empty in the demonstration because stages 3 and 4 need a
universe to rank inside and these scratch databases hold three companies; the rank behaviour is
measured over all 653 tickers in section 4.

```
========================================================================================================
2222_TADAWUL  Saudi Aramco
========================================================================================================

--- BEFORE (today's parser, the pages as they are served): 4,243 characters of a 16,000 budget  (fits: True), sector=non_bank, peer class recorded by the pipeline=non_bank
    Balance Sheet       None@None  34 rows (+8 omitted)  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings  NO VALUE
        no net income line in the income statement
      eps_derived  NO VALUE
        no net income line
      roe_on_period_end_common_equity  NO VALUE
        no net income line
      payout_cash  NO VALUE
        there is no income statement, so there is no earnings window to match dividends to and no payout
          ratio can be computed
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is
        not, because the source serves a rolling five-quarter grid. Year-on-year revenue or earnings
        cannot be compared from this dataset; the single quarters are the history there is.
      - A SECTOR PERCENTILE IN P2 IS A RANK INSIDE THE PIPELINE'S OWN `non_bank` PEER CLASS, not inside
        the sector the exchange publishes. On 2026-10-29 that class was short the 140 tickers the
        pipeline had misfiled as banks; adding them back moves these ranks by at most 4.7 percentile
        points.

--- AFTER (the repaired parser, same pages, patched gauge stage): 10,843 characters of a 16,000 budget  (fits: True), sector=non_bank, peer class recorded by the pipeline=non_bank
    Income Statement    TTM@2026-06  18 rows (+0 omitted)  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        'Shares Outstanding (Million)' is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  34 rows (+8 omitted)  aggregation=quarter_end_snapshot
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
      extraordinary_share_of_earnings                -8.9453 %
        denominator: the absolute value of reported net income, so the share reads the same for a profit
          and a loss
        check: reported minus before-unusual is -36,530.00 and the statement's extraordinary line is
          -36,530.00: they agree, so the split is the statement's own
        check: per share the same split is 1.69 reported against 1.83 before unusual items
      eps_derived                                     1.6875 currency units per share
        denominator: 'Shares Outstanding (Million)', a position at 2026-06, unchanged through every
          quarter of the window, so it equals the window's mean
        check: the statement's own 'Earning Per Share (Riyal)' is 1.6900 against 1.6875 derived: within
          2%, so both are on this share count
      eps_unit_confirmation                     408,980.0000 millions of the reporting currency
        check: 1.6900 x 242,000 = 408,980.00 against reported 408,371.00: the per-share figure is in the
          statement's own unit
      roe_on_period_end_common_equity                26.0199 %
        denominator: 'Total Shareholders' Equity' at 2026-06: period-end common equity, NOT an average
          of opening and closing equity. 'Total Owners Equity' (1,795,831.00) is NOT the denominator: it
          carries minority interest, which reported net income is already net of.
        check: earnings cover twelve months to 2026-06 and equity is struck at 2026-06: one point in
          time
        check: on average equity (2025-12 and 2026-06, mean 1,530,727.00) the same earnings give 26.68%
      payout_cash                                    79.4351 %
        denominator: net income over twelve months to 2026-06, the same window the dividends are matched
          to
        check: 4 dividend(s) with a pay date in 2025-07-01..2026-06-30 total 324,390.00 against net
          income 408,371.00
        check: amounts are company totals from the dividend history, not a per-share figure multiplied
          by a share count
      payout_declared                                79.4351 %
        denominator: net income over twelve months to 2026-06, the same window the dividends are matched
          to
        check: 4 dividend(s) with a announce date in 2025-07-01..2026-06-30 total 324,390.00 against net
          income 408,371.00
        check: amounts are company totals from the dividend history, not a per-share figure multiplied
          by a share count
      dps_window                                      1.3400 currency units per share
        check: 4 ex-date(s) inside 2025-07-01..2026-06-30
        check: against the share count the earnings use (242,000) that is 324,280.00 in total
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income
        statement is not, because the source serves a rolling five-quarter grid. Year-on-year revenue or
        earnings cannot be compared from this dataset; the single quarters are the history there is.
      - A SECTOR PERCENTILE IN P2 IS A RANK INSIDE THE PIPELINE'S OWN `non_bank` PEER CLASS, not inside
        the sector the exchange publishes. On 2026-10-29 that class was short the 140 tickers the
        pipeline had misfiled as banks; adding them back moves these ranks by at most 4.7 percentile
        points.

    the fundamentals strip (ranks kept):
      gauge                      value          status    rank  vintage  note
      ev_ebitda                      -       na_sector       -  period  
      ps                        3.5169              ok       -  inputs  
      roic                     23.9022              ok       -  inputs  
      net_margin               22.3951              ok       -  inputs  
      gross_margin             51.3471              ok       -  inputs  
      debt_equity               0.1893              ok       -  inputs  
      current_ratio             2.0032              ok       -  period  
      interest_coverage        81.6968              ok       -  inputs  
      fcf_yield                      -       na_sector       -  period  
      payout                         -  missing_inputs       -  period  

========================================================================================================
1120_TADAWUL  Al Rajhi Bank
========================================================================================================

--- BEFORE (today's parser, the pages as they are served): 7,215 characters of a 16,000 budget  (fits: True), sector=bank, peer class recorded by the pipeline=bank
    Balance Sheet       None@None  32 rows (+0 omitted)  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings  NO VALUE
        no net income line in the income statement
      eps_derived  NO VALUE
        no net income line
      roe_on_period_end_common_equity  NO VALUE
        no net income line
      net_financing_margin  NO VALUE
        net financing income or the earning-asset lines are absent
      cost_to_income  NO VALUE
        no operating expense or operating income line
      cost_of_risk  NO VALUE
        no provisions line or no financing-investment balance
      npl_ratio                                       0.7478 %
        denominator: gross financing investments, before the loss provision
      npl_coverage                                  152.4860 %
        denominator: non-performing financing at the balance-sheet date
      equity_to_assets                               11.0091 %
        denominator: total assets at the balance-sheet date. A leverage measure, NOT a regulatory
          capital ratio: not risk-weighted, not comparable with CET1.
      financing_to_deposits                         112.8089 %
        denominator: customer deposits only, excluding due to banks and term sukuk: the measure is about
          deposit funding
      payout_cash  NO VALUE
        there is no income statement, so there is no earnings window to match dividends to and no payout
          ratio can be computed
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is
        not, because the source serves a rolling five-quarter grid. Year-on-year revenue or earnings
        cannot be compared from this dataset; the single quarters are the history there is.
      - BANK: revenue, gross margin, net margin on sales, price to sales, current ratio, interest
        coverage, return on invested capital, EV/EBITDA and free cash flow yield are not defined for
        this company and are not supplied. What it is read on is in `calculations`. Equity to assets
        there is leverage, not regulatory capital.
      - NO SECTOR RANKINGS FOR THIS COMPANY: the pipeline ranks its gauges inside the `bank` peer class,
        which on 2026-10-29 held 204 tickers of which 53 are banks. A rank in that class is not a rank
        against banks, so P2 carries the values with no percentiles. The peer LIST in P5 is unaffected -
        it comes from the exchange's own sector classification, not from this detection.

--- AFTER (the repaired parser, same pages, patched gauge stage): 14,863 characters of a 16,000 budget  (fits: True), sector=bank, peer class recorded by the pipeline=bank
    Income Statement    TTM@2026-06  24 rows (+0 omitted)  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        'Shares Outstanding (Million)' is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  32 rows (+0 omitted)  aggregation=quarter_end_snapshot
        source columns: ['2026-06']
    quarters: ['label', '2025-09', '2025-12', '2026-03', '2026-06', '2026-09']
        Operating Income                           9,881.8  10,409.2  10,528.5  10,884.5  11,115.0
        Operating Expenses                         -2,216.3  -2,679.6  -2,457.3  -2,394.5  -2,357.0
        Net Profit Before Unusual Items            6,360.2  6,374.5  6,751.6  7,012.1  7,106.0
        Extraordinary income/expense               0.0  0.0  0.0  0.0  0.0
        Net Income                                 6,360.2  6,374.5  6,751.6  7,012.1  7,106.0
        Earning Per Share (Riyal)                  1.1  1.1  1.1  1.2  1.2
    calculations:
      extraordinary_share_of_earnings                 0.0000 %
        denominator: the absolute value of reported net income, so the share reads the same for a profit
          and a loss
        check: reported minus before-unusual is 0.00 and the statement's extraordinary line is 0.00:
          they agree, so the split is the statement's own
        check: per share the same split is 4.42 reported against 4.42 before unusual items
      eps_derived                                     4.4164 currency units per share
        denominator: 'Shares Outstanding (Million)', a position at 2026-06, unchanged through every
          quarter of the window, so it equals the window's mean
        check: the statement's own 'Earning Per Share (Riyal)' is 4.4200 against 4.4164 derived: within
          2%, so both are on this share count
      eps_unit_confirmation                      26,520.0000 millions of the reporting currency
        check: 4.4200 x 6,000 = 26,520.00 against reported 26,498.39: the per-share figure is in the
          statement's own unit
      roe_on_period_end_common_equity                21.9588 %
        denominator: 'Total Shareholders' Equity' at 2026-06: period-end common equity, NOT an average
          of opening and closing equity. 'Total Owners' Equity' (152,566.00) is NOT the denominator: it
          carries minority interest and equity sukuk, which reported net income is already net of.
        check: earnings cover twelve months to 2026-06 and equity is struck at 2026-06: one point in
          time
        check: on average equity (2025-12 and 2026-06, mean 117,763.71) the same earnings give 22.50%
      net_financing_margin                            3.4314 %
        denominator: earning assets taken as investments plus net financing investments. Due from banks
          (29,548.10) is excluded: it is a short-term interbank position, not an asset the bank sets its
          margin on.
        check: earning assets = 174,998.62 + 762,096.10
      cost_to_income                                 23.3736 %
        denominator: operating income, a bank's revenue analogue — the line a price-to-sales ratio needs
          and does not find
      cost_of_risk                                    0.3576 %
        denominator: net financing investments at the balance-sheet date
      npl_ratio                                       0.7432 %
        denominator: gross financing investments, before the loss provision
      npl_coverage                                  153.2247 %
        denominator: non-performing financing at the balance-sheet date
      equity_to_assets                               11.4407 %
        denominator: total assets at the balance-sheet date. A leverage measure, NOT a regulatory
          capital ratio: not risk-weighted, not comparable with CET1.
      financing_to_deposits                         110.7119 %
        denominator: customer deposits only, excluding due to banks and term sukuk: the measure is about
          deposit funding
      net_income_to_operating_income                 63.5393 %
        denominator: operating income, a bank's revenue analogue. Comparable with other banks only,
          never with a net margin on sales.
      payout_cash                                    37.7381 %
        denominator: net income over twelve months to 2026-06, the same window the dividends are matched
          to
        check: 2 dividend(s) with a pay date in 2025-07-01..2026-06-30 total 10,000.00 against net
          income 26,498.39
        check: amounts are company totals from the dividend history, not a per-share figure multiplied
          by a share count
      payout_declared                                37.7381 %
        denominator: net income over twelve months to 2026-06, the same window the dividends are matched
          to
        check: 2 dividend(s) with a announce date in 2025-07-01..2026-06-30 total 10,000.00 against net
          income 26,498.39
        check: amounts are company totals from the dividend history, not a per-share figure multiplied
          by a share count
      dps_window                                      1.6700 currency units per share
        check: 2 ex-date(s) inside 2025-07-01..2026-06-30
        check: against the share count the earnings use (6,000) that is 10,020.00 in total
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income
        statement is not, because the source serves a rolling five-quarter grid. Year-on-year revenue or
        earnings cannot be compared from this dataset; the single quarters are the history there is.
      - BANK: revenue, gross margin, net margin on sales, price to sales, current ratio, interest
        coverage, return on invested capital, EV/EBITDA and free cash flow yield are not defined for
        this company and are not supplied. What it is read on is in `calculations`. Equity to assets
        there is leverage, not regulatory capital.
      - NO SECTOR RANKINGS FOR THIS COMPANY: the pipeline ranks its gauges inside the `bank` peer class,
        which on 2026-10-29 held 204 tickers of which 53 are banks. A rank in that class is not a rank
        against banks, so P2 carries the values with no percentiles. The peer LIST in P5 is unaffected -
        it comes from the exchange's own sector classification, not from this detection.

    the fundamentals strip (ranks withheld):
      gauge                      value          status    rank  vintage  note
      ev_ebitda                      -  not_meaningful       -  period  
      ps                             -  not_meaningful       -  period  
      roic                           -  not_meaningful       -  inputs  
      net_margin                     -  not_meaningful       -  period  
      gross_margin                   -  not_meaningful       -  period  
      debt_equity               1.5090              ok       -  inputs  rank withheld: disputed peer class
      current_ratio                  -  not_meaningful       -  period  
      interest_coverage              -  not_meaningful       -  period  
      fcf_yield                      -  not_meaningful       -  period  
      payout                         -  missing_inputs       -  period  

========================================================================================================
2010_TADAWUL  SABIC
========================================================================================================

--- BEFORE (today's parser, the pages as they are served): 4,198 characters of a 16,000 budget  (fits: True), sector=non_bank, peer class recorded by the pipeline=non_bank
    Balance Sheet       None@None  34 rows (+24 omitted)  aggregation=None
    quarters: none
    calculations:
      extraordinary_share_of_earnings  NO VALUE
        no net income line in the income statement
      eps_derived  NO VALUE
        no net income line
      roe_on_period_end_common_equity  NO VALUE
        no net income line
      payout_cash  NO VALUE
        there is no income statement, so there is no earnings window to match dividends to and no payout
          ratio can be computed
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: one window is available and the prior year's income statement is
        not, because the source serves a rolling five-quarter grid. Year-on-year revenue or earnings
        cannot be compared from this dataset; the single quarters are the history there is.
      - A SECTOR PERCENTILE IN P2 IS A RANK INSIDE THE PIPELINE'S OWN `non_bank` PEER CLASS, not inside
        the sector the exchange publishes. On 2026-10-29 that class was short the 140 tickers the
        pipeline had misfiled as banks; adding them back moves these ranks by at most 4.7 percentile
        points.

--- AFTER (the repaired parser, same pages, patched gauge stage): 9,543 characters of a 16,000 budget  (fits: True), sector=non_bank, peer class recorded by the pipeline=non_bank
    Income Statement    TTM@2026-06  15 rows (+0 omitted)  aggregation=sum_quarters
        source columns: ['2025-09', '2025-12', '2026-03', '2026-06']
        'Shares Outstanding (Million)' is aggregated as end_quarter_position, not as the section's rule
    Balance Sheet       Q@2026-06  34 rows (+24 omitted)  aggregation=quarter_end_snapshot
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
      extraordinary_share_of_earnings               -78.8496 %
        denominator: the absolute value of reported net income, so the share reads the same for a profit
          and a loss
        check: reported minus before-unusual is -16,812.35 and the statement's extraordinary line is
          -16,812.35: they agree, so the split is the statement's own
        check: per share the same split is -7.11 reported against -1.51 before unusual items
      eps_derived                                    -7.1074 currency units per share
        denominator: 'Shares Outstanding (Million)', a position at 2026-06, unchanged through every
          quarter of the window, so it equals the window's mean
        check: the statement's own 'Earning Per Share (Riyal)' is -7.1100 against -7.1074 derived:
          within 2%, so both are on this share count
      eps_unit_confirmation                     -21,330.0000 millions of the reporting currency
        check: -7.1100 x 3,000 = -21,330.00 against reported -21,322.06: the per-share figure is in the
          statement's own unit
      roe_on_period_end_common_equity               -17.2605 %
        denominator: 'Total Shareholders' Equity' at 2026-06: period-end common equity, NOT an average
          of opening and closing equity. 'Total Owners Equity' (148,707.14) is NOT the denominator: it
          carries minority interest, which reported net income is already net of.
        check: earnings cover twelve months to 2026-06 and equity is struck at 2026-06: one point in
          time
        check: on average equity (2025-12 and 2026-06, mean 126,124.71) the same earnings give -16.91%
      payout_cash  NO VALUE
        net income over the window is not positive, so a payout ratio is not meaningful
      payout_declared  NO VALUE
        net income over the window is not positive, so a payout ratio is not meaningful
      dps_window                                      3.0000 currency units per share
        check: 2 ex-date(s) inside 2025-07-01..2026-06-30
        check: against the share count the earnings use (3,000) that is 9,000.00 in total
    limitations:
      - NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
        balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
        cannot be computed from anything here, and dividend cover can be tested against earnings only,
        never against cash.
      - ONE INCOME-STATEMENT WINDOW: twelve months to 2026-06 is available and the prior year's income
        statement is not, because the source serves a rolling five-quarter grid. Year-on-year revenue or
        earnings cannot be compared from this dataset; the single quarters are the history there is.
      - A SECTOR PERCENTILE IN P2 IS A RANK INSIDE THE PIPELINE'S OWN `non_bank` PEER CLASS, not inside
        the sector the exchange publishes. On 2026-10-29 that class was short the 140 tickers the
        pipeline had misfiled as banks; adding them back moves these ranks by at most 4.7 percentile
        points.

    the fundamentals strip (ranks kept):
      gauge                      value          status    rank  vintage  note
      ev_ebitda                 9.7802              ok       -  inputs  
      ps                        1.3392              ok       -  inputs  
      roic                     -0.6210              ok       -  inputs  
      net_margin              -18.8289              ok       -  inputs  
      gross_margin             17.1822              ok       -  inputs  
      debt_equity               0.3685              ok       -  inputs  
      current_ratio             2.4297              ok       -  period  
      interest_coverage         0.1371              ok       -  inputs  
      fcf_yield                      -       na_sector       -  period  
      payout                         -  missing_inputs       -  period  

```
