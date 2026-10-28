# The ingestion repair: pre-application record

2026-10-29. The repair was directionally accepted on 2026-10-28 with six requirements before
application. This document answers them. It supersedes parts of
`docs/ingestion-repair-reconciliation-2026-10-28.md`, which remains the record of the three cases;
where a figure here differs from that one, this one is current and says why.

**Acceptance gate, as set by the owner:** financial reconciliation, not compatibility with the old
probe bands. Nothing below treats D3 or D6 as a blocker. P9 (the `get_statements` Copilot tool) and
the bank revenue mapping are held as subsequent scoped changes, and §8d of the earlier report now
matters more than it did — see §5.

Still prepared, not applied. The patch is `docs/pipeline-fix-statements-2026-10-28.patch`, now
**9 hunks, 320 lines added, 27 removed**, and it still applies cleanly to the pipeline's current
file and reproduces the tested parser byte for byte. Nothing on the server has been written.

---

## 0. What changed in the parser since the 10-28 preparation

Four changes for the requirements, and two faults of my own that re-running the reconciliation
caught:

| | change |
|---|---|
| §1 | every populated quarter of a flow row is kept, so a row with fewer than four consecutive quarters is no longer dropped entirely |
| §2 | three aggregations instead of two — `sum`, `end` (a position) and **`mean`** (a period average), so a share-count row and an average-share-count row are not treated alike |
| §4 | the balance-sheet snapshot matching the chosen flow window is also emitted under that window's fiscal year, **without which the repair would have broken the gauge stage** |
| — | the aligned balance sheet uses **one** snapshot date for the whole section, and prefers the date matching the flow window |

**Two faults I introduced and then caught.** Adding the standalone quarters made them candidates
for the main table, and since every row has a newest quarter they won on coverage — so Aramco's
income statement came back as `Q@2026-06`, a single quarter's revenue where a year's belongs. Only
`FY` and `TTM` windows may reach `fundamentals_lineitems` now. And the aligned balance sheet first
fell back per row to "the newest snapshot at or before the window", which put 37 of SABIC's lines
at 2026-06 and 21 at 2025-12 inside one balance sheet. A balance sheet is a position; two dates
inside one do not foot. Both were found by re-running the reconciliation rather than by inspection,
which is the argument for re-running it after every change.

---

## 1. Standalone-quarter handling

`quarter_windows` returns only runs of four consecutive quarters. Before this round, a row that
produced no window produced **nothing at all** — no annual figure and no quarterly row — so a
company with three quarters of history lost its income statement in the same way the original bug
lost everyone's, only more quietly.

| quarters available | windows | classified as |
|---|---:|---|
| one | 0 | — |
| two | 0 | — |
| three | 0 | — |
| four, one fiscal year | 1 | `FY@2025-12` |
| four, straddling two years | 1 | `TTM@2026-06` |
| five consecutive | 2 | `TTM@2026-03`, `TTM@2026-06` |
| four with a gap | 0 | — |

Every populated quarter is now kept as a `Q` row in `fundamentals_lineitems_quarterly` regardless.
**This is not hypothetical** — on the six tickers in this run, flow lines that reached no window at
all and would have been lost entirely:

| ticker | lines kept that would have vanished |
|---|---:|
| SABIC (2010) | **28** |
| Anaam (4061) | 6 |
| Jarir (4190) | 3 |
| Al Rajhi (1120) | 2 |

These are lines the issuer publishes in some quarters and not others — a sub-line of cost of sales,
an EBITDA row — and the old rule's all-or-nothing test deleted them without a trace.

The main table still takes only a full window, so nothing quarterly is passed off as annual.

## 2. EPS share denominators

Three aggregations inside a flow section, and the **order of the tests matters**: "Average number
of shares (Million)" contains "number of shares", so an average row must be recognised before the
position markers or it would take the end quarter.

| rule | rows | why |
|---|---|---|
| `sum` | Sales, Net Income, `Earning Per Share (Riyal)`, `ربح السهم (درهم)` | a flow is earned over the period, and four quarterly EPS figures do add to the annual one |
| `end` | `Shares Outstanding (Million)`, `Par Value (Riyal)` | a **position**: true at an instant. Summing these is what reported 4× the real share count |
| `mean` | `Average number of shares`, `Weighted average…`, `متوسط عدد الأسهم (مليون)` (both hamza spellings) | already an average over its own quarter, so a four-quarter window takes the **mean** |

**Why the distinction is not cosmetic.** A window where the count moves — a bonus issue between
Q2 and Q3 — with quarterly net income of 100 each quarter:

| | shares | EPS |
|---|---:|---:|
| position rule (end quarter) | 1,200 | 0.3333 |
| average rule (mean of four) | 1,100 | 0.3636 |

An 8.3 % difference, and invisible: both are plausible numbers. Taking the end quarter for an
average-shares row understates EPS by exactly that much.

**On today's data the `mean` rule does not fire on the quarterly path**, and that is worth saying
rather than hiding. Tadawul grids carry `Shares Outstanding (Million)`, a position; the
average-share rows appear on the GCC Arabic grids, which parse as `annual_direct` and need no
window arithmetic at all. The rule is defensive and was exercised directly against the function,
not left to chance.

**The reconciliation that does run on today's data** — summed quarterly EPS against net income over
the window's own share count:

| ticker | EPS summed | NI / shares | shares | denominator rule |
|---|---:|---:|---:|---|
| Aramco | 1.6900 | 1.6875 | 242,000 | `end_quarter_position` |
| Al Rajhi | 4.4200 | 4.4164 | 6,000 | `end_quarter_position` |
| SABIC | −7.1100 | −7.1074 | 3,000 | `end_quarter_position` |
| Anaam | −0.3200 | −0.3254 | 32 | `end_quarter_position` |
| Jarir | 0.9400 | 0.9365 | 1,200 | `end_quarter_position` |

They agree **because no share count moved in these windows** — that is the only reason summing EPS
and dividing net income land in the same place. The repair records which rule produced the
denominator, so a window where the two diverge can be told apart from one where they do not.

## 3. Dividend and bank-metric formulas

Written down because every one of them has a wrong version that looks right. Notation: a flow of
period *P* ending *E*; a position at *E*. The grid stores expenses and provisions **negative**, so
the formulas negate where a positive ratio is wanted.

### Dividends

```
window(E)        = the four quarters ending E
DPS_ttm          = Σ dps      over window(E)          ex-date basis
Dividends_mn     = Σ amount_mn over window(E)          ex-date basis
payout_cash      = Dividends_mn / NetIncome_P
payout_declared  = Σ amount_mn where `note` names a quarter in window(E)  / NetIncome_P
payout_per_share = DPS_ttm / EPS_P
dividend_cover   = NetIncome_P / Dividends_mn          = 1 / payout_cash
yield            = DPS_ttm / price_at(E)
base_dividend    = dps − (performance_linked_mn / shares)   from the `note` text
```

Rules, each of which exists because the obvious alternative is wrong:

1. **The dividend window must be the same window as the earnings.** My first pass took five
   quarters of dividends against four of earnings and produced a payout of 99.5 % — plausible and
   wrong. Matched, it is 79.4 %.
2. **`amount_mn` is a company total; `dps` is per share.** They sit in the same row and must never
   be added or divided into each other.
3. **Never sum every row in P3.** Ten rows is two and a half years; summing them gives Aramco a
   14.66 % yield.
4. **Two conventions, never mixed.** *Cash* (ex-date in the window — what shareholders received)
   and *declared* (the quarter the `note` names — what the period earned out, which is what the
   pipeline's own payout gauge matches). For Aramco they give 79.4 % and 79.9 %; they converge,
   which is reassuring, but a figure must say which it is.
5. **The yield's price must be the price at the window end**, not `last_price` from another date.
6. **Cross a capital change and per-share figures stop comparing.** Aramco's history crosses bonus
   issues in 2022-05 (+25 %) and 2023-05 (+20 %); the present window is after both.

### Bank metrics (`sector == "bank"`)

All flows TTM to *E*, all positions at *E*. Al Rajhi at `E = 2026-06`:

```
cost_income          = −OperatingExpenses_TTM / OperatingIncome_TTM            23.4 %
net_financing_margin =  NetFinancingIncome_TTM / (NetFinancingInvestments_E
                                                  + Investments_E)              3.43 %
cost_of_risk         = −DebtProvisions_TTM / NetFinancingInvestments_E          0.36 %
npl_ratio            =  NPL_E / (PerformingFinancing_E + NPL_E)                 0.74 %
npl_coverage         = −FinancingLossProvision_E / NPL_E                      153.2 %
equity_assets        =  TotalShareholdersEquity_E / TotalAssets_E              11.44 %
loans_deposits       =  NetFinancingInvestments_E / CustomerDeposits_E        110.7 %
roe                  =  NetIncome_TTM / TotalShareholdersEquity_E              21.96 %
```

**For a bank the revenue line is `Operating Income`** — meaning total operating income — **not
`Sales`.** A bank's grid has no Sales row at all. This is why §5 matters: the gauge stage's revenue
label list does not contain it, so `net_margin` and `ps` stay `missing_inputs` for banks even after
the repair.

These figures differ from the 10-28 report (3.47 %, 0.75 %, 152.5 %, 11.01 %, 112.8 %, 23.07 %)
because that version read the balance sheet at 2025-12 while setting it against income to 2026-06.
**My measurement script was not pinning the fiscal year**, and after the repair a balance-sheet
label exists under both its own year and the aligned window's year, so an unpinned query returned
whichever row the planner reached first. Pinned, every figure above is struck at one date — and
**ROE is no longer a mixed-period ratio**, which the earlier report listed as a limitation. The
alignment resolved it.

## 4. TTM semantics in the existing consumers

Three consumers read `fundamentals_lineitems`. I ran the first rather than reading it.

### `compute_fundamental_gauges.py` — this is where the repair would have broken things

```python
yr = conn.execute("SELECT MAX(fiscal_year) FROM fundamentals_lineitems WHERE ticker_key=?", ...)
year = yr[0]
```

Every input is then looked up `WHERE fiscal_year = year`: net income, operating income, gross
income, **total current assets, total current liabilities, equity, cash**, taxes, finance expense,
EBITDA — and the sector test `is_bank = (gross_income is None and tca is None)`, where `tca` is a
**balance-sheet** row.

As first prepared, a Tadawul ticker would have had its income statement under 2026 and its balance
sheet under 2025. `MAX` is 2026, so the gauge stage would have read a year holding an income
statement and **no balance sheet**: `debt_equity`, `current_ratio` and `ev_ebitda` would have gone
from `ok` to `missing_inputs` for every Saudi ticker, and any non-bank without a Gross Income line
would have been **misdetected as a bank**, mis-bucketing sector averages market-wide. The repair
would have traded one regression for another.

Hence the aligned snapshot. The pipeline's own gauge stage, run over both scratch databases:

| gauge | Aramco before → after | SABIC before → after |
|---|---|---|
| `net_margin` | `missing_inputs` → **22.395 / ok** | `missing_inputs` → **−18.829 / ok** |
| `gross_margin` | `na_sector` → **51.347 / ok** | `na_sector` → **17.182 / ok** |
| `roic` | `missing_inputs` → **23.902 / ok** | `missing_inputs` → **−0.621 / ok** |
| `interest_coverage` | `missing_inputs` → **81.697 / ok** | `missing_inputs` → **0.137 / ok** |
| `ps` | `missing_inputs` → **3.517 / ok** | `missing_inputs` → **1.339 / ok** |
| `ev_ebitda` | `na_sector` → `na_sector` | `na_sector` → **9.780 / ok** |
| `current_ratio` | 1.999 / ok → **2.003 / ok** | 1.801 / ok → **2.430 / ok** |
| `debt_equity` | 0.201 / ok → **0.189 / ok** | 0.261 / ok → **0.368 / ok** |

**Nothing breaks. Five or six gauges per ticker come back.** And two things the owner should know
before application:

- **Currently published gauge values move**, because they are now read from a June position rather
  than a December one. SABIC's `current_ratio` goes 1.801 → 2.430, a 35 % change. That is a fresher
  balance sheet, not a recalculation error, and `period_end` now records which date it is. It will
  be visible on the screen.
- **Bank gauges stay blocked.** Al Rajhi's `net_margin`, `ps` and `interest_coverage` remain
  `missing_inputs` after the repair, because the gauge stage looks for `Sales`/`Total Revenue` and
  a bank's revenue line is `Operating Income`. The *data* is there — §3 computes cost/income at
  23.4 % by hand — but the gauge stage cannot see it. The 10-28 report said these measures were
  "unblocked"; that was true of the evidence and **not** of the gauge stage, and the distinction is
  mine to correct.

**Sector detection**, checked on the same two databases, is correct before and after — and strictly
more robust after, because Aramco and SABIC go from `gross_income=None, tca=present` to
`gross_income=present, tca=present`, so the bank test has two independent signals instead of
leaning on `tca` alone. No ticker changes sector.

### `get_statements` (the API) — must not ship without §8b

`SELECT DISTINCT fiscal_year … ORDER BY fiscal_year DESC LIMIT years`, and each row's values are a
dict keyed by year. After the repair a Tadawul ticker has years `[2025, 2026]`, so **one
`StatementRow` would carry a December 2025 balance-sheet figure and a June 2026 one in the same
dict, labelled only "2025" and "2026"** — two positions six months apart presented as a year-on-year
comparison. That is worse than today's defect.

This changes the §8b proposal from the earlier report. `period` is **not** a property of a section:
after the repair a section has several years with different periods (a Tadawul balance sheet is
`FY@2025-12` for 2025 and `Q@2026-06` for 2026; an ADX one is `FY` for five years). So:

```python
class Statement(BaseModel):
    section: str
    periods: dict[str, dict]     # "2026" -> {"period": "TTM", "period_end": "2026-06"}
    rows: list[StatementRow]
```

**§8b is a precondition for application, not an accompaniment.**

### `run_rebuild_pipeline.py` — no effect

It references the table only as `count_tables=[(screening, "fundamentals_lineitems")]`, which logs
a row count. Counts rise; nothing gates on them.

## 5. Invalidation, recomputation and rollback

### The dependency chain

```
parse_financial_statements.py   ->  fundamentals_lineitems  (+ …_quarterly, new)
compute_fundamental_gauges.py   ->  fundamentals_gauges     (value, status, inputs_json)
compute_sector_averages.py      ->  sector_averages, and fundamentals_gauges.score
publish_dbs.sh                  ->  /var/lib/alphacouncil/screening.sqlite   (what the API reads)
```

### Invalidation

`fundamentals_gauges` upserts on `(ticker_key, gauge_key)` and the stage iterates
`SELECT DISTINCT ticker_key FROM fundamentals_lineitems`, computing the whole fixed gauge set per
ticker. **So every gauge value, status and `inputs_json` is overwritten by a full recompute — the
gauges self-heal and no explicit invalidation is needed.** That includes the **orphaned** values
(Anaam's `net_margin` of −49.91, computed from an income statement that no longer existed), which
is what clears them: it recomputes to −29.277.

**One thing does not self-heal.** `score` — the sector percentile — is written by
`compute_sector_averages.py`, **not** by the gauge insert, whose column list is
`(ticker_key, gauge_key, value, status, inputs_json)`. So a gauge whose value is recomputed while
the averages step is skipped keeps a percentile from the previous vintage: a correct number beside
a stale ranking. **`compute_sector_averages.py` must run after the gauge step, in the same run.**
This matters more than usual here, because the repair moves values on every Saudi ticker at once,
so the percentile distributions themselves change.

### Order of application

1. Take the named safety copies in the rollback step below. **Do this first.**
2. Apply the patch: `patch -p1 < docs/pipeline-fix-statements-2026-10-28.patch` in
   `/opt/alphacouncil/backend/`, which leaves `parse_financial_statements.py.orig`.
3. Run, in order and in one run: `parse_financial_statements.py` →
   `compute_fundamental_gauges.py` → `compute_sector_averages.py`, all against
   `det_out/screening.sqlite`. **Do not publish yet.**
4. Check `det_out/screening.sqlite` before publishing: Tadawul tickers have an `Income Statement`
   section; `MAX(fiscal_year)` holds both sections at one `period_end`; no quarterly-reconstructed
   ticker has a flow section spanning more than one `period_end`; `fundamentals_gauges` has no
   ticker whose gauge count fell.
5. Ship §8b (`periods` on `Statement`) to beta **before** the first publish, or the screen shows
   two balance-sheet dates as a year-on-year comparison.
6. Publish: `publish_dbs.sh`.

### Rollback

The publish script already backs up the live file before installing — `cp -a` of
`briefs_index`, `screening` and `evidence` into `/opt/alphacouncil/backups/dbpublish-$STAMP/` —
and keeps the five most recent. Observed on 2026-10-29: five directories, one per day at
`05:00:01Z`, covering 2026-10-24 to 2026-10-28, 8.2 GB in total. **So the automatic window is about
five days, and it is a rotation, not an archive** — five more publishes evict it.

That is why step 1 is a named copy outside the rotation:

```
cp -a /opt/alphacouncil/backend/llm-council/det_out/screening.sqlite \
      /opt/alphacouncil/backups/prestatementrepair-det_out-screening.sqlite
cp -a /var/lib/alphacouncil/screening.sqlite \
      /opt/alphacouncil/backups/prestatementrepair-live-screening.sqlite
```

To roll back:

1. `patch -R -p1 < docs/pipeline-fix-statements-2026-10-28.patch` — the parser is restored exactly;
   the patch has been proven reversible against a fresh copy.
2. Restore `det_out/screening.sqlite` from the named copy, so the next nightly run starts from the
   pre-repair state rather than re-deriving it.
3. Restore `/var/lib/alphacouncil/screening.sqlite` from the named live copy (or from the newest
   `dbpublish-*` predating the repair), then re-run `/healthz/deep`.
4. Leave `fundamentals_lineitems_quarterly` in place or `DROP` it — nothing reads it, so either is
   safe; dropping it is cleaner if the repair is abandoned.
5. The three added columns on `fundamentals_lineitems` are additive and nullable. SQLite cannot drop
   a column in the version this pipeline uses, and nothing requires it: the pre-repair code never
   names them. **Restoring the database file makes the question moot**, which is the reason step 1
   exists.

**What rollback cannot undo:** anything a user or a Council session read while the repair was live.
A paid benchmark run must not be funded between application and the post-publish check.

## 6. What is still not done

- **Not applied.** Steps 1–6 above are the owner's to authorise.
- **Not run over all 714 tickers.** 33 tickers over seven exchanges, with zero rows lost and zero
  changed; the full dry run needs the server.
- **P9 and the bank revenue mapping** are held as subsequent scoped changes, as instructed — with
  §4 now showing that the bank mapping is what actually unblocks bank gauges, so it is worth
  scheduling rather than shelving.
- **Multi-year history, a cash-flow statement, and Al Rajhi's capital-versus-shares
  contradiction** are all unchanged and all out of this patch's reach.
- **D3 and D6** still need re-registering or retiring, and on the owner's instruction that is not a
  gate on this repair. D6's correct answer is now **−29.277** from the gauge stage itself, against a
  pre-registered band of (−60, −40).
