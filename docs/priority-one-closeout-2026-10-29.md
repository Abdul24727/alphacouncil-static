# Priority One, closed out: financial evidence and data intelligence

2026-10-29. Branch `rebuild`. Nothing pushed, nothing deployed, no paid model call made.

This finishes the prepared ingestion repair and delivers the Council evidence update, demonstrated
on Aramco (2222), Al Rajhi (1120) and SABIC (2010). Models, roster and debate rounds are
unchanged; no provider was added and no benchmark redesigned.

Raw outputs for everything claimed here: `docs/verification/priority-one-closeout-2026-10-29.md`.

---

## 0. What I found that changes the picture

Three measurements made today that were not in the earlier rounds, each from the live server
rather than from a sample.

**The production database, read today, is worse than the sample suggested.** A read-only copy of
`/opt/alphacouncil/backend/llm-council/det_out/screening.sqlite` says:

| exchange | tickers | income statements | balance sheets | cash-flow statements |
|---|---|---|---|---|
| TADAWUL | 243 | **0** | 243 | 0 |
| KSE | 121 | 120 | 121 | 0 |
| ADX | 88 | 88 | 88 | 0 |
| DFM | 60 | 60 | 60 | 0 |
| QSE | 53 | 53 | 53 | 0 |
| MSM | 51 | 51 | 51 | 0 |
| BSE | 37 | 37 | 37 | 0 |

Every Saudi company's income statement is absent, as diagnosed. And **no company in the universe
has a cash-flow statement at all** — 0 of 653. I had been describing that as a limitation of the
Tadawul pages; it is a limitation of every page the pipeline reads. So free cash flow, operating
cash flow, capital expenditure, cash conversion and dividend cover against cash are not available
for any company, and `fcf_yield`'s gauge note says "UAE: no cash-flow statement published", which
is the wrong reason for a Saudi ticker and the right verdict.

**The pipeline already computes a bank scorecard, and it writes nothing.** `ingest_bank_metrics.py`
is step 17 of the nightly run. It defines six of the seven measures I built, with the same
formulas, into a `bank_metrics` table that exists in the live database and holds **zero rows**.
The nightly log reads:

```
bank_metrics: wrote 0/58 banks
  rows[screening.sqlite:bank_metrics] - -> 0
[OK step 17] ingest_bank_metrics (0.2s)
```

58 banks are labelled and found; 0.2 seconds is not long enough to open 58 HTML files, so it is
failing to locate the statement file and skipping every bank — and the step exits 0, so the
pipeline calls it a success every night. Bank evidence was never missing because nobody built it.
It was built, it runs, it produces nothing, and nothing notices.

This is why the Council update computes bank measures from the **parsed line items** instead of
from raw HTML: that route is fixed by the repair, is covered by tests, and does not depend on a
stage that has been quietly empty. `bank_metrics` is now dead weight — repair or retire it as a
separate scoped change; this delivery does not touch it and does not need it.

**`score` is written by `compute_gauge_scores.py`, not by `compute_sector_averages.py`.** My
2026-10-29 pre-application record named the wrong script, and said the ranking "does not
self-heal". The correction: stage 4 begins with `UPDATE fundamentals_gauges SET score = NULL` and
then writes only the scorable rows, so a ranking cannot survive a run of that stage. What remains
true, and is what the guard below is for, is that running the gauge stage **alone** leaves a
refreshed value beside its old ranking.

---

## 1. The repair, finalised

### Quarterly flows are standalone, not cumulative — confirmed two ways

The whole repair rests on this. If the provider's quarterly columns were year-to-date, the fourth
column would already *be* the fiscal year and summing four would overstate it by about two and a
half times.

**Test A, internal.** Read the columns as if cumulative and look at the quarters that reading
implies — the first differences inside one fiscal year. Across the five tickers parsed, **40 flow
rows give an impossible result**. Aramco's revenue is the clearest:

```
Sales       2025-06=407,142   2025-09=418,160   2025-12=416,290
implies                11,018            -1,870     <- negative revenue
```

A company cannot bill minus 1.87 billion riyals in a quarter. The same refutation appears in
Al Rajhi, SABIC, Anaam and Jarir.

**Test B, external.** The provider's own `eps_ttm` comes from a different page (the ratios scrape)
and is not downstream of this parser. Standalone and cumulative readings predict figures several
times apart, and only one of them lands:

| ticker | published eps_ttm | standalone | cumulative | standalone/published | cumulative/published |
|---|---|---|---|---|---|
| 1120 | 4.42 | 4.541 | 1.062 | **1.03x** | 0.24x |
| 2222 | 1.84 | 1.687 | 0.287 | **0.92x** | 0.16x |
| 4190 | 0.94 | 0.977 | 0.258 | **1.04x** | 0.27x |

SABIC and Anaam publish no `eps_ttm` (`unit_unconfirmed`), so they have no anchor on this test and
rest on Test A.

Both tests are in the dataset the advisors receive, not only in this document: P9 carries the
annual figure, the four quarters it is the sum of, and the note "each column is one quarter as
reported, standalone and not cumulative".

### The ROE denominator is named, every time

The published ROE cannot say what it divided by, and that is the finding. The fundamentals strip
now carries, against `roe`:

> **NOT DISCLOSED by the source**: neither the equity date nor whether it is period-end or average
> equity is stated, so this figure cannot be reproduced or checked.

Beside it, a derived ROE that can be: `roe_on_period_end_common_equity`, whose denominator reads
*"'Total Shareholders' Equity' at 2026-06: period-end common equity, NOT an average of opening
and closing equity. 'Total Owners Equity' (1,795,831.00) is NOT the denominator: it carries
minority interest, which reported net income is already net of."* For a bank the same note adds
equity sukuk. The checks state what the alternative denominator would give, so the choice is
visible rather than assumed:

| | published | derived, named denominator | on average equity |
|---|---|---|---|
| Aramco | 26.75 % | **26.02 %** | stated in `checks` |
| Al Rajhi | 23.49 % | **21.96 %** | stated in `checks` |
| SABIC | -15.37 % | **-17.26 %** | stated in `checks` |

The derived figures are reproducible from two rows of the statements beside them. The published
ones are not reproducible at all.

### Derived EPS is withheld where the share-count treatment is unsupported

A share count is a position, so a window's figure is the count at its end; an average-share row is
a mean over the window. They differ exactly when the count moved, and the difference is invisible
in the result — on a window where the count goes 1,000 to 1,200 the two rules give 0.3333 and
0.3636, both plausible.

So: an average-share row is the denominator when one exists (and the test for it runs *before* the
position markers, because "Average number of shares" contains "number of shares"). A position is
the denominator only when the count did not move across the window's quarters, and the note says
so. When the count moved and only a position exists, `eps_derived` returns **no value** and names
what is missing, with the counts it saw:

> the only share count is 'Shares Outstanding (Million)', an end-of-period position, and it moved
> inside the window (2025-09=100, 2025-12=100, 2026-03=120, 2026-06=120): a flow over a closing
> count is not a supported earnings per share, and there is no average-share line

On today's data no share count moves in any of the five windows, so the withholding path is
exercised by a test rather than observed in the wild. That is stated rather than glossed.

### Two bounded pipeline patches, both reversible

| patch | file | size | applies | reverses |
|---|---|---|---|---|
| `docs/pipeline-fix-statements-2026-10-28.patch` | `parse_financial_statements.py` | 9 hunks, 320 added, 27 removed | clean, reproduces the tested parser byte for byte | `patch -R` restores the original byte for byte |
| `docs/pipeline-fix-gauges-2026-10-29.patch` | `compute_fundamental_gauges.py` | 6 hunks, 44 added, 2 removed | clean, reproduces the tested file byte for byte | `patch -R` restores the original byte for byte |

The gauge patch does two things and nothing else:

**Provenance.** Every gauge row's `inputs_json` gains the fiscal year, the flow window's period
and end, the balance-sheet date behind its position operands, the detected sector and the time it
was computed — on every row, including `missing_inputs` and `na_sector` ones, because a missing
input is evidence too and the sector is what decides whether a gauge was ever applicable.

**Ranking.** The upsert keeps a ranking only while the value is unchanged:

```sql
score = CASE WHEN excluded.value IS value THEN score ELSE NULL END
```

guarded by a `PRAGMA table_info` check, because `score` is added by stage 4 and a fresh database
has not got the column.

**Measured on the whole live universe**, both gauge stages run over copies of the same database:

```
original: DONE: 6530 gauge rows. status: {'missing_inputs': 2325, 'na_sector': 2500, 'ok': 1679, 'undefined_nonpositive': 26}
patched:  DONE: 6530 gauge rows. status: {'missing_inputs': 2325, 'na_sector': 2500, 'ok': 1679, 'undefined_nonpositive': 26}

rows only in one: 0 / 0
rows whose (value, status) differ: 0
6,530/6,530 rows carry a fiscal year; 6,530/6,530 carry a sector
sectors seen: {'bank': 2040, 'non_bank': 4080, 'insurance': 410}
```

Not one value or status moves on any of 653 tickers. (My local run computes 1,679 `ok` where the
server has 1,954: all 277 differences are `payout`, because I hold 33 tickers' dividend CSVs
locally rather than all 714. It is the same shortfall in both runs, which is why the comparison is
still exact.)

### A stale gauge or ranking cannot accompany a refreshed statement

Two mechanisms, and the second is the one that makes it a guarantee rather than a procedure.

**The data cannot hide it.** Every gauge row now says which fiscal year and window it was computed
from, and the API compares that with the statements it is about to sit beside. A mismatch sets
status `stale`, and the value *and* the ranking are withheld:

```
computed from fiscal year 2025 while the statements now carry 2026: the gauge stage has not run
since the statements were refreshed
```

A gauge from a database with no stamp cannot be dated, and is left alone rather than called stale
on a guess.

**The ranking cannot outlive the value it ranked.** Tested on the live universe: refresh one line
item, run the gauge stage **alone**, and look for a new number under an old rank.

```
2222_TADAWUL before: current_ratio=1.999/rank 68.8, debt_equity=0.201/rank 53.6
a line item was refreshed and the GAUGE STAGE ALONE was re-run:
   current_ratio          1.999 ->      2.498   ranking cleared

values holding a NEW number under an OLD ranking: 0
after stages 3 and 4, 2222_TADAWUL gauges with status ok and no ranking: 0
whole universe: 0 ok gauges without a ranking
```

An idempotent re-run on unchanged statements keeps every ranking (10/10 on Aramco), so the guard
costs nothing when nothing moved.

### Publication order, and rollback

1. **Named safety copies first.** `publish_dbs.sh` copies the live file to
   `/opt/alphacouncil/backups/dbpublish-<stamp>/` and keeps five — observed as one per day, so the
   automatic window is a five-day rotation, not an archive. A named copy outside it comes first.
2. `git apply` both patches in `/opt/alphacouncil/backend` (`-p1`), each file backed up as
   `.bak-<date>` first, per the project's standing rule.
3. One pass against `det_out`: `parse_financial_statements` → `compute_fundamental_gauges` →
   `compute_sector_averages` → `compute_gauge_scores`. **Stage 4 must run**: without it the guard
   leaves every changed gauge unranked, which is safe but shows no percentiles.
4. Check before publishing: Tadawul income statements present, gauge statuses, `ok` rows all
   ranked.
5. Ship the API change to beta **before** publishing the database — see §2's note on `periods`.
6. Publish.

Rollback: restore the named copy, and `patch -R` the two files (proven byte for byte). The added
columns are nullable and SQLite cannot drop them; restoring the database file makes that moot.
**What rollback cannot undo is anything read while it was live**, so no paid benchmark run between
application and the post-publish check.

The API degrades on either schema by design (`period_aware` reads it off `PRAGMA table_info`), so
the two can be deployed in either order — but see the next section for why one order is better.

---

## 2. The Council evidence update

The smallest version of what was asked: one new dataset, fields on two existing endpoints, one new
module. No new provider, no model change, no roster or round change.

### P9: bounded financial statements

A new Copilot tool `get_financial_statements` and endpoint `/v1/tickers/{ref}/evidence`, added to
the pack as **P9**. It carries, for one company:

- **`statements`** — the income statement and balance sheet, as reported, each section with its
  `period` (FY, TTM or Q), `period_end`, the `aggregation` rule that produced it, and
  `source_columns`: the quarter-end columns that were added together. Rows are
  `[label, 2026, 2025]`, with `row_rules` naming any row aggregated differently from its section —
  which is how `Shares Outstanding (Million)` announces itself as `end_quarter_position` inside a
  summed income statement.
- **`quarters`** — the five single quarters behind the annual figures, for the lines worth a trend,
  with the note that each column is standalone and not cumulative.
- **`calculations`** — see below.
- **`limitations`** — what this company's data cannot answer at all.
- **`currency`, `unit`, `basis`, `source`, `sector`**.

**The bound is enforced, not hoped for.** `fit()` encodes the dataset and, while it is over budget,
drops statement sub-detail from the end of the longest section — never a row any calculation
divides by, and never a calculation or a limitation. The alternative is the prompt truncating the
JSON mid-row, which cuts a figure in half and changes it without saying so.

The row cap takes the protected lines first and fills the rest in the statement's own order. That
matters: on a Tadawul balance sheet the share count is the *last* row, so taking the first N would
have dropped the denominator of every per-share measure in the same dataset. A test asserts it
cannot.

P9's budget is **16,000 characters**, its own rather than the uniform 12,000. Measured: a bank's
statements plus the measures a bank is read on come to 14,490 characters, and holding that to
12,000 meant cutting the income statement to 10 rows to pay for the prose explaining it — the
wrong way round. The budget is one constant (`evidence.DATASET_BUDGET`, mirrored in
`pack.DATASET_CHARS_BY_TAG`) and lowering it degrades gracefully in the order above.

### Gauge definitions and operands

`/fundamentals` now carries, per metric: the `formula`, the `denominator` (named, or "NOT
DISCLOSED" where the source will not say), the `source` (computed from statements, or published),
the `operands` the pipeline actually divided — read back from its own `inputs_json` audit — and
`as_of`, the window and date behind them. Where a gauge has no value, a `note` says what was
missing, how many labels were searched and how many the section does hold.

### Validated calculations, or exactly what is missing

Every entry carries its formula, its operands with the window each came from, and a check that
proves it — or no value and a `missing` list. A test asserts the exclusive-or across all three
companies: `(value is None) == bool(missing)`, always.

The checks are not decoration. `eps_unit_confirmation` multiplies the reported per-share figure by
the share count and compares it with reported net income — which confirms the unit for a
loss-making company, where the pipeline's own check (EPS x P/E against the price) cannot work
because there is no meaningful P/E. SABIC: `-7.1100 x 3,000 = -21,330.00` against reported
`-21,322.06`, 0.04 % apart.

### Banks get bank evidence, not a forced number

For a company the pipeline detects as a bank, the generic ratios come back `not_meaningful` with a
reason instead of `missing_inputs`:

> `ps`: a bank has no sales line; price to revenue is not a measure banks are valued on. The
> measures this company is read on are in the financial-evidence dataset.

This is deliberately *not* the bank revenue mapping that was held as a subsequent change. Mapping
`Operating Income` into the revenue slot would make a price-to-sales ratio and a net margin on
financing income appear beside industrial companies' and get compared with them. "Missing" reads
as a gap to be filled and invites exactly that fix. The eight measures a bank is actually read on
are supplied instead, each a ratio of lines a bank's statement carries, each with its denominator
spelled out — including that equity to assets is leverage and **not** a regulatory capital ratio.

### Reported, derived and rule-based stay apart

The pack header now says it in the seats' own reading order:

> THREE KINDS OF THING ARE IN THIS PACK AND THEY ARE NOT INTERCHANGEABLE. Reported: figures the
> source published, in [P9] under `statements` and `quarters`, each with the period it covers and
> the date it was struck. Derived: figures computed from those, in [P9] under `calculations` and in
> [P2] where a metric carries a `formula` and `operands` — quote the formula when you use one, and
> where a calculation carries `missing` instead of a value, there is no number to use. Opinion:
> [P4] is rule-based votes from fixed thresholds, not measurements; it is not evidence for or
> against anything, and a seat must not cite it as a figure. [P9] `limitations` says what this
> company's data cannot answer at all.

### `periods` is a precondition, and here is why

`StatementRow.values` is keyed by fiscal year. After the repair one balance-sheet row carries a
December 2025 figure beside a June 2026 one, labelled only "2025" and "2026" — two positions six
months apart presented as a year-on-year comparison, which is worse than today's defect. The field
is per section per year, because a section now holds a real fiscal year beside a quarter-end
snapshot:

```
Balance Sheet  periods: {"2026": {period: "Q",  period_end: "2026-06", aggregation: "quarter_end_snapshot"},
                         "2025": {period: "FY", period_end: "2025-12", aggregation: "year_end_snapshot"}}
```

So the API change ships to beta before the database is published, even though the code works
against either schema.

### What it costs

The pack goes into each seat's system prompt, per call, and the debate path does no prompt
caching, so pack growth multiplies by the number of calls:

| ticker | P1–P8 today | + P9 | new total | change |
|---|---|---|---|---|
| 2222 | 17,473 | 10,553 | 28,772 | +65 % |
| 1120 | 20,043 | 14,490 | 35,287 | +76 % |
| 2010 | 18,421 | 9,253 | 28,435 | +54 % |
| 4061 | 18,123 | 7,778 | 26,588 | +47 % |
| 4190 | 18,325 | 7,884 | 26,935 | +47 % |

Mean 18,477 → 29,203 characters, roughly 4,600 → 7,300 input tokens per call. With 8 seats over
three stages that is on the order of **+60,000 input tokens per debate**. This is the price of the
Council having financial statements at all, where before it had none — but it is the owner's call,
and the single constant that sets it is named above.

---

## 3. The three companies, end to end

Both columns are real: *before* is the current parser's output from the live pages, *after* is the
repaired parser's, each run through the same new API module. The packs themselves are in the
verification log.

### Aramco 2222 — dividend window, payout, and what the cash-flow gap forbids

**Before**: a balance sheet to FY2025 and nothing else. The dataset returns no payout, no EPS, no
ROE and no margin, each with its reason — *"there is no income statement, so there is no earnings
window to match dividends to"*.

**After**: an income statement at `TTM@2026-06`, built from `['2025-09', '2025-12', '2026-03',
'2026-06']`, and a balance sheet at `Q@2026-06`.

The dividend window is the point of this case. The earnings window runs 2025-07-01 to 2026-06-30,
derived from the reporting mode and never from the fiscal-year label. Four dividends have a pay
date inside it, totalling 324,390 against net income of 408,371:

| basis | matched | total | payout |
|---|---|---|---|
| cash (pay date in the window) | 4 | 324,390 | **79.44 %** |
| declared (announce date in the window) | 4 | 324,390 | **79.44 %** |

The fifth dividend — ex-date 2026-08-19, for Q2 2026 — is *outside* the window. Including it, as
a fiscal-year-label match does, gives **99.5 %**: the difference between a company paying out four
fifths of its earnings and one paying out essentially all of them. A test asserts that dividend
cannot be counted.

**The cash-flow limitation is stated, not left to be noticed:**

> NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a
> balance sheet only. Operating cash flow, capital expenditure, free cash flow and cash conversion
> cannot be computed from anything here, and dividend cover can be tested against earnings only,
> never against cash.

So a seat can say Aramco paid 79 % of reported earnings and **cannot** say whether it paid them out
of cash flow. That distinction was previously unavailable in either direction.

Also visible, and new: 8.9 % of the trailing result is extraordinary (`Net Profit Before Unusual
Items` 444,901 against `Net Income` 408,371, the gap agreeing with the statement's own
`Extraordinary income/expense` of -36,530), and the five quarters show revenue rising 407,142 →
521,797 while net income moved 85,632 → 121,506.

### Al Rajhi 1120 — aligned statements and defined bank measures

**Before**: a balance sheet to FY2025. Four bank measures computed from it, three blocked for want
of an income statement.

**After**: income statement `TTM@2026-06` and balance sheet `Q@2026-06` — the same date, so the
ratios are struck at one point in time, which is what "aligned" has to mean. All eight measures,
each with its denominator named:

| measure | value | denominator as stated |
|---|---|---|
| net financing margin | **3.4314 %** | investments + net financing investments; due from banks excluded as a short-term interbank position |
| cost to income | **23.3736 %** | operating income, a bank's revenue analogue |
| cost of risk | **0.3576 %** | net financing investments at the balance-sheet date |
| NPL ratio | **0.7432 %** | gross financing investments, before the loss provision |
| provision coverage | **153.2247 %** | non-performing financing at the balance-sheet date |
| equity to assets | **11.4407 %** | total assets; leverage, NOT a regulatory capital ratio |
| financing to deposits | **110.7119 %** | customer deposits only, excluding due to banks and term sukuk |
| net income to operating income | **63.5393 %** | operating income; comparable with other banks only |
| return on equity | **21.9588 %** | period-end common equity, excluding minority interest and equity sukuk |

Payout 37.74 %, from two dividends inside the window against earnings of 26,498.39.

These correct the figures in the 2026-10-28 report, which were computed against a 2025-12 balance
sheet while the income ran to 2026-06. They match the corrected set in the 10-29 record.

### SABIC 2010 — a loss, a verified unit, and the one-off separated from the trend

**After**, from one dataset:

- **Negative earnings handled, not hidden.** `payout_cash` and `payout_declared` return no value:
  *"net income over the window is not positive, so a payout ratio is not meaningful"* — while
  `dps_window` still reports **3.00 a share** of dividends paid. A seat sees a company paying 3.00
  a share while losing 7.11 a share, which is the tension, rather than a ratio with no meaning.
- **Units verified without a P/E.** `-7.1100 x 3,000 = -21,330.00` against reported `-21,322.06`.
  The pipeline publishes no `eps_ttm` for SABIC (`unit_unconfirmed`) precisely because a
  loss-making company has no meaningful P/E to check against.
- **Reported separated from extraordinary.** `Net Profit Before Unusual Items` -4,509.71,
  `Extraordinary income/expense` -16,812.35, `Net Income` -21,322.06 — and the check confirms the
  first two sum to the third, so the split is the statement's own and not an inference.
  **-78.85 % of the reported result is extraordinary.** Per share the same split is -7.11 reported
  against -1.51 before unusual items.
- **Cyclical or structural, as evidence rather than opinion.** The quarters say it:

```
Sales              30,227.9  34,332.5  27,950.0  26,151.9  24,806.6
Gross Income        6,224.4   6,105.7   3,870.0   5,128.2   4,353.4
Operating Income    2,242.6   1,430.5  -2,304.2   1,254.9     105.4
Net Income         -4,066.1     435.5 -20,937.8      13.2    -832.9
```

Revenue down 18 % across five quarters and operating income down to 105 is the cyclical part; the
-20,937.8 quarter is one -15,980.2 charge. The data now supports the distinction instead of
leaving a seat to guess which it is looking at.

---

## 4. What is not done

- **Nothing is applied.** Both patches are prepared and reversible; application, publication,
  pushing and deployment remain the owner's, per the standing rule.
- **A full 714-ticker parse** cannot be run here: it needs the harvest pages on the server. The
  gauge, sector-average and ranking stages *were* run over the whole live universe (653 tickers
  with line items), with zero value or status changes.
- **`bank_metrics` is left dead.** Repairing or retiring step 17 is a separate scoped change. The
  delivery does not depend on it.
- **The bank revenue mapping is not done, and §2 argues it should not be.** Exposing bank evidence
  is the better answer to the same problem; if the mapping is ever wanted, it is for comparability
  inside the bank peer group, not for putting banks into price-to-sales.
- **The `mean` share-count rule is tested, not observed.** No share count moves in the current
  windows, so the withholding path has no live example.
- **No prompt caching on the debate path**, which is why P9's size multiplies by the number of
  calls. Out of scope here; worth knowing before the pack grows again.
- **D3/D6 probe bands** are untouched: financial reconciliation was the acceptance gate.

## 5. Files

| file | what |
|---|---|
| `api/app/evidence.py` | new. Reported statements, derived calculations, withholding rules, bank measures, staleness, the bounded dataset and its enforced budget |
| `api/app/routers/ticker_research.py` | `/statements` gains `periods` and `rules`; `/fundamentals` gains definitions, operands, `as_of`, staleness and bank handling; new `/evidence` |
| `api/app/copilot/tools.py` | new `get_financial_statements` tool |
| `api/app/debate/pack.py` | P9, its own budget, and the reported/derived/opinion header |
| `api/tests/test_evidence.py` | new. 32 tests |
| `api/openapi.json`, `web/src/lib/api/schema.d.ts` | regenerated; web typechecks |
| `docs/pipeline-fix-gauges-2026-10-29.patch` | new. Provenance on every gauge, and a ranking that cannot outlive its value |
| `docs/pipeline-fix-statements-2026-10-28.patch` | unchanged, re-verified today |

Suite: **515 passed, 11 skipped** (483 before this work).
