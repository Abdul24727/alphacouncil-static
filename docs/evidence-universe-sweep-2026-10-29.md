# The evidence module over the whole universe: four findings and two fixes

2026-10-29, after the Priority One closeout. Branch `rebuild`. Nothing pushed or deployed.

The tests cover fixtures and the three cases cover three companies. Neither can answer the
question this sweep asks: **does the new evidence module hold up on all 653 tickers the pipeline
actually carries** — the Kuwaiti real-estate companies, the Omani shells, the Bahraini banks, the
41 insurers that were never part of any case?

Run read-only against a copy of the published database. Raw output in
`docs/verification/priority-one-closeout-2026-10-29.md`, section 10.

**Nothing broke**: 0 exceptions and 0 non-finite values across 653 tickers, and 0 datasets over
the budget. What the sweep found instead was four things no test would have caught.

---

## 1. The label groups were Tadawul-shaped, and resolved almost nothing elsewhere

Measured per group, as the count of tickers whose statements carry any label in it:

| group | before | after | reaches |
|---|---|---|---|
| NET_INCOME_BEFORE_UNUSUAL | **0** | 385 | every exchange |
| EXTRAORDINARY | **0** | 407 | every exchange |
| AVERAGE_SHARES | **0** | 408 | every exchange |
| EPS_BEFORE_UNUSUAL | **0** | 406 | every exchange |
| EPS_REPORTED | 100 | 406 | every exchange |
| EQUITY_COMMON | 218 | 626 | every exchange |
| TOTAL_ASSETS | 243 | **653** | every exchange |
| TCA | 208 | 377 | every exchange |
| BANK_DEPOSITS | 3 | 64 | every exchange |
| BANK_FINANCING | 3 | 42 | every exchange |
| BANK_INVESTMENTS | 35 | 230 | every exchange |

Outside Saudi the statements are in Arabic, and the Arabic templates spell the same line several
ways — `إجمالي حقوق المساهمين` and `إجمالى حقوق المساهمين` are one line on 101 tickers between
them. Worse for exact matching, the per-share lines carry their unit inside the label: `(فلس)`,
`(درهم)`, `(ريال قطري)`, `(بيسة)`.

So two changes, both small. Labels are compared after normalisation — whitespace collapsed,
English case folded, the alef and ya forms unified — and a group entry may begin with `~` to mean
"any label starting with this", which is how one entry covers a per-share line in every currency
in the region without listing them.

Every alias added was read off the database with a count of the tickers carrying it. None was
guessed.

**What this changed end to end**: return on equity, derived EPS and the extraordinary split went
from **0 companies to 382–384**. They were resolving for nobody: Tadawul has no income statement
until the repair lands, and the labels for everyone else did not match.

**It also makes the `mean` share-count rule real.** The pre-application record said that rule was
"implemented and untestable on current data" because no Tadawul grid carries an average-share row.
It was looking in the wrong section of the wrong market: **408 tickers carry one**, in the balance
sheet of the Arabic grids. That correction is mine to make.

---

## 2. `Total Common Equity` is not common equity

The conventional Saudi bank template carries a line called `Total Common Equity`, which looks
exactly like the denominator a return on common equity needs.

It is not. On 1180 it is 203,827.25, which is shareholders' equity (185,625.83) plus minority
interest (548.74) plus equity sukuk (17,652.68), to the halala. The same holds on 1010. Reading it
as common equity would have understated every conventional Saudi bank's return on equity by about
a tenth, and nothing on the face of it says so.

It is in `EQUITY_ALL`, with the arithmetic in a comment. Checking a label's meaning against its own
components caught what the name hid.

---

## 3. The pipeline calls 204 tickers banks. 53 of them are banks.

The sweep's bank measures came back with a median equity-to-assets of **40.28%** across 177
companies. No population of banks looks like that; banks run at 8 to 16.

The cause is not in the measures. The pipeline detects a bank by an **absence** — no gross income
line and no current-asset split — and the Arabic templates carry neither line for ordinary
companies either. Against the sectors the site shows:

| the pipeline's 204 "banks" | count |
|---|---|
| Financial Services | 56 |
| **Banks** | **53** |
| Insurance | 27 |
| Real Estate | 20 |
| Industrials | 13 |
| Consumer Discretionary | 12 |
| Consumer Staples, Energy, other | 23 |

Kuwaiti real-estate companies and Omani industrials were being handed a bank's evidence and told
that revenue, margins and the current ratio are "not defined for this company".

**The fix is a positive test.** A bank claim — from the pipeline or from the fallback — is honoured
only where the balance sheet corroborates it with a customer-deposit line or a lending balance. On
this data that leaves **64**: all 53 of the site's banks, 10 financing companies and one
unlabelled. **Not one company the site calls a bank is dropped by it.** A bank claim the statements
do not corroborate yields `unknown`, which suppresses nothing.

The proof it worked is the distribution, not the count: equity to assets across the 64 moves to a
median of **10.89%**, and the other three bank ratios land where bank ratios land — net financing
margin 1.64 to 5.35% (median 2.59), cost to income median 43.51%, financing to deposits median
96.07%, non-performing 0.75 to 2.53%. Four independent measures in their textbook ranges is
stronger evidence that the formulas and denominators are right than any single reconciliation.

**This is a finding about the pipeline, not only about the API.** `compute_sector_averages.py`
buckets by that same detection, so 140 non-banks sit in the bank peer class — which means the
sector percentile on every gauge, for the real banks and for the mislabelled companies alike, is a
rank inside a peer group that is not the peer group. The API now refuses to present bank evidence
on an uncorroborated claim; the percentiles are the pipeline's to fix, and are not touched here.

---

## 4. A return on negative equity is not a return — a real bug in my code

WDAM_QSE: a loss of 125.17 over shareholders' equity of **−18.99** gave a return on equity of
**+659.14%**. A loss divided by negative equity comes back positive and large, and reads as a
spectacular return.

`ratios.py` has guarded the published ratio against exactly this since before today — *"ROE over
negative equity reads as a high positive return: not meaningful"* — and my derived ROE did not.
Fixed: a non-positive equity denominator withholds the figure and says what the equity was. Eight
companies move from a confident wrong number to a stated reason.

The other tails were checked and are arithmetic, not errors: ORIENT_DFM's EPS of 164.20 is the
source's own figure on 5 million shares; MANAZEL_ADX's extraordinary share of 1,586% is a reported
profit of 14.40 sitting on an underlying loss of 214.06, which is the kind of thing a seat should
see; SHPS_MSM earns 16.78 on 3.23 of book equity and its balance sheet foots.

---

## What the sweep says is still missing, and whose it is to fix

- **No cash-flow statement anywhere**: 653 of 653. Not a label gap — the source does not publish
  one on the pages the pipeline reads.
- **Dividends cover Tadawul only**: 230 tickers, all Saudi. So payout and dividend yield cannot be
  computed for any GCC company, whatever the repair does. The three Saudi cases work; the rest wait
  on dividend collection.
- **Asset quality is absent for GCC banks at source.** The Arabic bank template carries net loans
  and customer deposits but no performing/non-performing split and no provision stock, so the
  non-performing ratio and provision coverage resolve for 10 Saudi banks and nobody else. The
  measures come back with `missing` naming the line, which is the right answer.
- **No gross income line on the Arabic grids**, so gross margin is a Saudi-only measure.

Suite: **531 passed, 11 skipped**.

---

## Addendum: the same sweep against a repaired parse

The sweep above ran on the published database, where `period_aware` is false — so the
period-aware half of the module was never exercised at scale. Repeated over the 32 tickers of the
33-ticker dry run, parsed by the repaired parser and gauged by the patched gauge stage, which is
the state the owner will have after applying both patches:

```
32 tickers from the repaired parse; period_aware=True
exceptions: 0
budget 16,000: over it 0; median 8,188  largest 12,769
sectors {'bank': 16, 'non_bank': 12, 'unknown': 3, 'insurance': 1}
datasets carrying a quarterly series: 18 of 32
sections carrying the source columns they were summed from: 27

reporting modes seen, by section        aggregation rules recorded
   Balance Sheet FY          14            annual_column               28
   Balance Sheet Q           16            sum_quarters                18
   Income Statement FY       14            quarter_end_snapshot        16
   Income Statement TTM      18            row:end_quarter_position     9
                                           row:mean_of_quarters         2
```

Both statement shapes appear and are labelled as what they are: the GCC annual grids give a real
fiscal year, the repaired Tadawul grids a trailing twelve months over a quarter-end balance sheet.
27 of 32 sections carry the quarter ends they were summed from. The per-row exceptions are
recorded where a row is aggregated differently from its section — nine share counts held at the
end quarter, and **two averaged over the window**.

**That second one settles a claim I had hedged twice.** The pre-application record said the `mean`
share-count rule was "implemented and untestable on current data". It is exercised in a real
repaired parse, and 408 tickers in the live database carry an average-share row. Both halves of
that statement were wrong, in the same direction: I had looked for the row in the income statement
of the Saudi grids, and it lives in the balance sheet of the Arabic ones.

The measures on the 16 banks land where they should: equity to assets median **11.46%**,
non-performing **0.93%**, provision coverage **160.30%**, cost of risk **0.30%**, financing to
deposits **102.88%**, net financing margin **2.99%**. Return on equity across the 29 companies that
support one has a median of **12.18%**. Every one of the 16 banks' per-share figures is confirmed
against its own net income.

Two things this run does not show: `payout` resolves nowhere, because the scratch database has no
dividend history seeded (the three cases cover that path with the real history); and the largest
dataset is 12,769 characters, which is the measurement behind P9 having its own budget rather than
the uniform 12,000.

**The three cases were re-run after every fix in this document and are byte-for-byte identical**,
so every figure in `docs/priority-one-closeout-2026-10-29.md` still holds.
