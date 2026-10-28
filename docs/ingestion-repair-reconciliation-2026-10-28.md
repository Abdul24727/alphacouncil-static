# The ingestion repair: before/after for Aramco, Al Rajhi and SABIC, and what to expose

2026-10-28. Prepared on the owner's instruction: repair the ingestion, reconcile the three cases,
demonstrate correct reporting modes, aggregation rules, preserved history and traceable derived
metrics, then propose the smallest API/pack change that exposes the repaired evidence. Models,
personas, roster and rounds are untouched — nothing in this document goes near them.

> **Superseded in part, 2026-10-29.** The repair was directionally accepted with six
> requirements before application, and answering them changed the parser again. Read
> `docs/ingestion-repair-preapplication-2026-10-29.md` alongside this: it is current wherever the
> two differ, and it corrects two things here — Al Rajhi's bank metrics (§7, computed on a
> mixed period here) and the claim that they are "unblocked" (true of the evidence, **not** of the
> gauge stage). The three cases and the aggregation rules below still stand.

**Prepared, not applied.** The patch is `docs/pipeline-fix-statements-2026-10-28.patch`: as of
2026-10-29, 9 hunks, 320 lines added, 27 removed. Nothing on the server was written. Both parsers were run here, over
pages copied read-only from the server, into local scratch databases that are thrown away. Applying
it to the live pipeline is the owner's decision, by the project's own pattern — Step 4 prepares,
Step 5 decides, Step 6 applies.

The patch applies cleanly to the pipeline's current file and reproduces the tested parser exactly:

```
$ patch -p1 --dry-run < docs/pipeline-fix-statements-2026-10-28.patch
checking file llm-council/parse_financial_statements.py
$ patch -p1 < ... && diff -q <patched> <tested>     # identical
```

---

## 1. What was wrong, in one paragraph

Argaam's Tadawul pages serve the **quarterly** grid under the annual URL. The parser detects that
and reconstructs annual figures by summing quarters — but it required all four quarters of **one
fiscal year**, and those pages carry only a rolling five-quarter window, so no fiscal year is ever
complete. Every flow row was dropped: the whole income statement, for every Saudi ticker. Balance
sheets survived because a balance sheet is a position and the month-12 column is populated. The
same summing also added `Shares Outstanding (Million)` across four quarters, reporting 4× the real
count. One cause, three symptoms.

## 2. Before and after, `fundamentals_lineitems`

This is the table the gauge stage and the API read.

| ticker | section | before | after |
|---|---|---|---|
| **2222** Aramco | Income Statement | **absent** | **18 rows**, TTM@2026-06 |
| | Balance Sheet | 42 rows, FY2025 | 42 rows, FY2025 — *unchanged* |
| **1120** Al Rajhi | Income Statement | **absent** | **24 rows**, TTM@2026-06 |
| | Balance Sheet | 32 rows, FY2025 | 32 rows, FY2025 — *unchanged* |
| **2010** SABIC | Income Statement | **absent** | **15 rows**, TTM@2026-06 |
| | Balance Sheet | 58 rows, FY2025 | 58 rows, FY2025 — *unchanged* |
| **4061** Anaam | Income Statement | **absent** | **20 rows**, TTM@2026-06 |
| **4190** Jarir | Income Statement | **absent** | **20 rows**, TTM@2026-06 |
| **ABNIC** (ADX) | both sections | 68 + 51 rows, 2021-2025 | **identical** — the annual path is untouched |

Plus a new additive table, `fundamentals_lineitems_quarterly`, holding the preserved history:
246 rows for Aramco, 179 for Al Rajhi, 234 for SABIC, 294 for Anaam, 246 for Jarir, and **0 for
ABNIC**, because an annual grid needs no reconstruction.

**Backward compatibility was the first thing checked, row by row** — not label by label, because
labels repeat (`Other` appears many times) and a label-keyed comparison would have collapsed rows
and looked cleaner than it was. Every `(fiscal_year, item_index, label, value)` tuple of every
balance sheet is identical before and after, and so is all of ABNIC. Nothing an existing reader
sees has moved.

---

## 3. Correct reporting modes

Every row now carries `period` and `period_end`. A trailing-twelve-month figure is never presented
as a fiscal year, which is the difference between "the business earned this in 2025" and "this is
the last twelve months".

| ticker | section | period |
|---|---|---|
| 2222, 2010, 4061, 4190, 1120 | Balance Sheet | `FY` @ `2025-12` |
| 2222, 2010, 4061, 4190, 1120 | Income Statement | `TTM` @ `2026-06` |
| ABNIC | both | `FY` @ `2021-12` … `2025-12`, five separate years |

`FY` is used only where the four quarters are exactly one fiscal year, or where the grid gave an
annual column directly. On these five Tadawul pages no fiscal year is complete, so every income
statement is honestly labelled `TTM` — and the mixed presentation that follows (a balance sheet at
2025-12 beside an income statement to 2026-06) is now **visible in the data** instead of being
silently assumed away. That mixture is real and the API has to show it; section 8 says how.

**A statement covers one period, or it is not a statement.** The first working version chose the
window per row, and Al Rajhi came out with nine lines ending 2026-06 and fifteen ending 2026-09,
because Argaam publishes the newest quarter for some lines before others. Any ratio across two such
lines would mix periods — a cost/income built from an operating income to September and an expense
to June. The repair now picks one window per section: the window covering the most lines, then the
newest, with a real fiscal year breaking an exact tie. Al Rajhi is a consistent 24 lines to
2026-06; Jarir went from 12 + 8 split to 20 aligned. The windows not chosen are not lost — every
one of them is in the quarterly table.

## 4. Aggregation rules

| row kind | rule | why |
|---|---|---|
| flow (income statement, cash flow) | **sum four consecutive populated quarters**, aligned to a fiscal year where possible | a flow is earned over a period |
| flow, but a **share count or par value** | **take the window's end quarter**, never sum | a count is a position, not a flow — this is the 4× fix |
| flow, **per-share earnings** | summed | four quarterly EPS figures *do* add to the annual one, and the check below proves it |
| stock (balance sheet) | a quarter-end snapshot; the year end keeps its existing place | a balance sheet is a position |

Completeness is tested **per row**, not per column, so a line with a gap — or one where only part
of the newest quarter is published — yields no window rather than a wrong sum.

The count rule matches `shares outstanding`, `number of shares`, `par value`, and both Arabic
spellings of "number of shares" (`عدد الأسهم` and `عدد الاسهم`, with and without the hamza), which
both occur in the GCC grids. Per-share earnings labels (`Earning Per Share (Riyal)`,
`ربح السهم (درهم)`) deliberately do **not** match, and that was asserted directly rather than
assumed.

**The 4× artifact, before and after:**

| | income statement said | balance sheet said | after the repair |
|---|---:|---:|---:|
| Aramco | 968,000 mn | 242,000 mn | **242,000 mn** |
| SABIC | 12,000 mn | 3,000 mn | **3,000 mn** |

And the consequence that matters more than the number: **the statement now reconciles with
itself.** Aramco's reported EPS of 1.69 equals its own net income over its own share count
(408,371 / 242,000 = 1.6875). Before, the statement reported an EPS computed on 242,000 while its
own share-count row said 968,000. The same check passes for all five tickers:

| | Net Income / shares | reported EPS |
|---|---:|---:|
| Aramco | 1.69 | 1.69 |
| Al Rajhi | 4.42 | 4.42 |
| SABIC | -7.11 | -7.11 |
| Anaam | -0.33 | -0.32 |
| Jarir | 0.94 | 0.94 |

**And an outside check.** Aramco's reconstructed trailing-twelve-month EPS is **1.6875**. The
vendor's own `scraped_ratios.eps_ttm` on 2026-08-02 was **1.68** — a 0.4 % match, from a completely
independent source. Al Rajhi's is **4.42** against the pack's published `eps_ttm` of **4.42**,
exactly. The reconstruction is not merely self-consistent; it lands where the vendor lands.

## 5. Preserved history

Where there was one figure per year, there is now a series. Aramco:

- **5 balance-sheet snapshots** — 2025-06, 2025-09, 2025-12, 2026-03, 2026-06 — where the old
  parser kept one and discarded four, having read all five.
- **2 trailing-twelve-month windows** per flow line, so a margin has a previous value to be
  compared with.

Al Rajhi and SABIC likewise carry 5 quarter ends and 2 TTM windows. This lives in
`fundamentals_lineitems_quarterly`, deliberately separate: putting several periods per year into
`fundamentals_lineitems` would return four rows where the gauge stage and the API expect one, and
that is how a safe repair becomes an outage.

What this does **not** give is multi-year history. The pages carry five quarters, so the deepest
honest series is five quarters. Separating cyclical weakness from structural deterioration still
needs years, and that is a sourcing question, not this patch.

## 6. Traceable derived metrics

Every stored value carries `source_json` naming the rule and the exact quarters it was built from.
464 of 464 rows, four rules:

```json
{"rule": "sum_quarters",      "quarters": ["2025-09","2025-12","2026-03","2026-06"],
                              "mode": "quarterly_reconstructed"}
{"rule": "end_quarter_count", "quarter": "2026-06", "window": [...],
                              "why": "a share count is a position, not a flow"}
{"rule": "year_end_snapshot", "quarter": "2025-12"}
{"rule": "annual_column",     "year": 2025, "mode": "annual_direct"}
```

Counts: `year_end_snapshot` 247, `sum_quarters` 92, `annual_column` 120, `end_quarter_count` 5.
A derived figure can now be audited without re-running the parser, which is what "traceable" has
to mean before a seat quotes it.

---

## 7. The three cases, reconciled

### Aramco (2222): dividend aggregation and earnings coverage

| metric | before | after | from |
|---|---|---:|---|
| net margin | `missing_inputs` | **22.40 %** | Net Income 408,371 / Sales 1,823,483, both TTM@2026-06 |
| interest coverage | `missing_inputs` | **81.7 ×** | Operating Income 816,723 / Financing Expense 9,997 |
| dividend cover | not derivable | **1.26 ×** | Net Income 408,371 / dividends 324,390 |
| **payout, cash basis** | `missing_inputs` | **79.4 %** | ex-dates 2025-08-19, 2025-11-17, 2026-03-16, 2026-06-01 |
| **payout, declared basis** | `missing_inputs` | **79.9 %** | notes Q3 2025 … Q2 2026, 326,340 |
| share count | 968,000 mn | **242,000 mn** | `end_quarter_count` |

**The aggregation rule that matters here is the one I got wrong first.** A payout ratio needs the
dividend window to be the *same* window as the earnings. My first pass took five quarters of
dividends against four of earnings and produced 99.5 %, which looked plausible and was wrong.
Matched properly, the answer is 79.4 %.

Two defensible conventions, both shown because they answer different questions: **cash** (dividends
whose ex-date falls in the window — what shareholders received) and **declared** (dividends
declared *for* those quarters, which is what the pipeline's own payout gauge matches on). They come
out at 79.4 % and 79.9 %, and the fact that they converge is itself reassuring. Neither is wrong;
mixing them is.

Against the inspection, which could reach this figure three irreconcilable ways — 73.4 % by hand
from the pack, 92.6 % from the gauge, and a 14.66 % yield for anyone who summed ten dividend rows —
**there is now one answer on one matched window, with every input named.**

What is still missing: a cash-flow statement, which exists for no ticker on any exchange. Coverage
out of operating cash flow after capex remains unanswerable, and this patch does not change that.

### Al Rajhi (1120): the bank measures

Al Rajhi had **no income statement at all**. It now has 24 lines on a proper bank template — net
financing income, banking fees, operating expenses, debt provisions — and three measures the
inspection recorded as blocked are blocked no longer.

| measure | before | after | from |
|---|---|---:|---|
| **cost / income** | **blocked** | **23.4 %** | Operating Expenses 9,747.73 / Operating Income 41,703.95 |
| **net financing margin** | **blocked** | **3.43 %** | net financing income 32,155.26 / earning assets 937,094.72 |
| **cost of risk** | **blocked** | **0.36 %** | Debt Provisions 2,724.91 / Net Financing Investments 762,096.10 |
| NPL ratio | derivable, never exposed | 0.74 % | NPL 5,729.46 / (performing 765,145.59 + NPL) |
| NPL coverage | derivable, never exposed | 153.2 % | loss provision 8,778.95 / NPL 5,729.46 |
| equity / assets | derivable, never exposed | 11.44 % | 120,673.26 / 1,054,772.50 |
| loans / deposits | derivable, never exposed | 110.7 % | 762,096.10 / 688,359.50 |
| return on equity | published only, 23.49 % | **21.96 %**, and *checkable* | Net Income and equity both at 2026-06 |

> **Corrected 2026-10-29.** The figures above were first published against a balance sheet at
> 2025-12 while the income statement ran to 2026-06, because my measurement script was not pinning
> the fiscal year — after the repair a balance-sheet label exists under two years. Pinned, every
> figure is struck at one date. The ROE caveat below is therefore **resolved**, not outstanding.
> And "blocked no longer" is true of the EVIDENCE and not of the gauge stage, which still cannot
> see a bank's revenue line: see §4 of the pre-application record.

One thing the repair makes visible rather than solves. (The mixed-period ROE noted here was
resolved on 2026-10-29 by aligning the balance-sheet snapshot to the flow window; the vendor's
23.49 % still cannot be checked at all.) **For a bank the revenue line is `Operating Income`**, meaning total operating income, not `Sales`. The gauge's revenue
search list contains `Sales`, `Total Revenue`, `Net Sales` and some Arabic equivalents, and none of
them matches — so `net_margin` and `ps` will *still* fail for banks after this patch. That needs a
sector-keyed revenue label (for `sector == "bank"`, revenue is `Operating Income`), and it cannot
simply be added to the shared list because for a non-bank `Operating Income` is EBIT, not revenue.
It is a separate, small change and it is listed in section 8.

The share-count contradiction stands: `Capital` 40,000 at `Par Value` 10 implies 4,000 mn shares
and `Shares Outstanding` says 6,000 mn. The repair does not touch it — it needs the provider's
definition — but the recovered income statement now gives a third check on it, because Net Income
26,498.39 over 6,000 mn gives the 4.42 the vendor publishes. That is consistent with 6,000 being
the count the provider uses, whatever the capital line says.

### SABIC (2010): the loss, cyclical against structural

| metric | before | after | from |
|---|---|---:|---|
| net margin | `missing_inputs` | **-18.83 %** | Net Income -21,322.06 / Sales 113,241.07 |
| gross margin | `na_sector` (wrongly) | **17.18 %** | Gross Income 19,457.32 / Sales |
| **operating margin** | not derivable | **+0.43 %** | Operating Income **+486.64** |
| **extraordinary share of the loss** | not derivable | **78.8 %** | -16,812.35 of -21,322.06 |
| loss before unusual items | not derivable | **-4,509.71** | and EBITDA still **+16,960.00** |
| EPS | null, reason `unit_unconfirmed` | **-7.11 a share** | and -21,322.06 / 3,000 mn = -7.11 |

The cyclical-versus-structural question is now answerable from the evidence rather than from
assertion: **79 % of the loss is one extraordinary item**, the operating line is *positive* on a
trailing-twelve-month basis against -292.16 for FY2025, and EBITDA is comfortably positive. The
headline loss and the figure before unusual items differ 4.7× and point opposite ways — which is
exactly the distinction a room was being asked to draw with neither number in front of it.

And the EPS: the pack reports `null` with the reason `unit_unconfirmed`, which the inspection
showed is a false explanation — the unit was never tested, because the gate bails on a null P/E and
P/E is null for losses. The repaired statement gives **-7.11**, which reconciles against its own
net income and share count. The vendor's `-1.76` reconciles with nothing.

---

## 8. The smallest API and pack change

Four changes, smallest first. None touches models, personas, roster or rounds. **These are
proposed, not built** — the inspection's acceptance was that a concrete data-pack change could be
approved rather than designed around assumptions, and this is that change.

### 8a. `inputs_json` on the gauges — one column in one SELECT

In `get_fundamentals` (`api/app/routers/ticker_research.py`), add `inputs_json` to the
`fundamentals_gauges` SELECT and carry it on `GaugeMetric`. Unrelated to the repair, still the
cheapest item on the list, and now more valuable: some Tadawul gauge values are **orphaned** —
computed from an income statement that no longer exists — and `inputs_json` is the only surviving
record of what they were struck from.

### 8b. `period` and `period_end` on `/statements` — three fields, no new shape

`get_statements` already exists and already serves the screen. The repair gives each section one
reporting window, so the window belongs on the section:

```python
class Statement(BaseModel):
    section: str
    period: str | None        # "FY" | "TTM"
    period_end: str | None    # "2026-06"
    rows: list[StatementRow]
```

Add `period, period_end, source_json` to the SELECT, group them onto the `Statement`, and carry
`source` on `StatementRow` for the audit trail. `Statements.years` stays as it is, so no existing
caller breaks. **This is what stops a trailing-twelve-month income statement being read as a
fiscal year**, and it is the one change without which exposing the repaired evidence would be worse
than not exposing it.

### 8c. One new Copilot tool: `get_statements`

A ninth dataset, `P9`, pointed at the endpoint that already exists:

```python
("P9", "get_statements", {"years": 1}, "Income statement and balance sheet", "قائمة الدخل والمركز المالي"),
```

Sized against the 12,000-character per-dataset budget: Aramco's 18 income-statement lines plus 42
balance-sheet lines is roughly 2–4 KB of JSON, so it fits with room to spare. The pack header must
gain one sentence saying that each statement carries its own reporting period and that the income
statement may be trailing twelve months while the balance sheet is a year end — because that
mixture is real, and a seat told neither date is worse off than one told both.

**Only after the repair lands.** Today this tool would hand every Saudi room a balance sheet and
nothing else, which is the current defect with extra steps.

### 8d. Sector-keyed revenue for bank gauges — pipeline, separate

For `sector == "bank"`, revenue is `Operating Income` (total operating income). Adding it to the
shared revenue list would break every non-bank, where `Operating Income` is EBIT. Without this,
`net_margin` and `ps` stay `missing_inputs` for banks even with the income statement restored.

### Not proposed

`fundamentals_lineitems_quarterly` should stay unexposed for now. The five-quarter series is real
and worth keeping the moment it is produced, but putting a second time axis in front of six
advisors is a product decision, not a repair, and the pack is already carrying nine as-of dates.

---

## 9. What the repair does to the benchmark, which matters before it is funded

The guard test added earlier was right to exist, and the answer is sharper than "these probes might
break". **The repair changes two probes' correct answers, and one band no longer contains it.**

| probe | pre-registered | after the repair | verdict |
|---|---|---|---|
| **D6** net margin on Anaam | band (-60, -40), correct -49.91 | **-29.28 %** | **OUTSIDE the band** |
| **D3** loss per share on Anaam | band (-1.0, -0.4) | **-0.33 a share** | **OUTSIDE the band** |

Both rested on Anaam's orphaned gauges (`net_margin` -49.91, `ps` 9.336), computed from FY2025.
On the repaired trailing-twelve-month evidence Anaam's sales are 35.01 against the 39.65 implied by
the old `ps`, and its net margin is -29.28 % rather than -49.91 % — the company's revenue and loss
both moved, which is a real signal and not an artefact. The probes are simply registered against a
vintage that the repair supersedes.

And **D1 still inverts**, as the inspection said: its band tops out at 85 % while the matched-window
payout is 79.4 % — which is *inside* the band, so D1 survives on these numbers, where the gauge's
92.6 % would have broken it. That is luck, not design, and it is worth saying so plainly.

So: **D3 and D6 must be re-registered or retired before the repair lands, and that is the owner's
call**, not mine. Re-registering a criterion after reading the data is what pre-registration exists
to prevent, so the honest options are to retire both, or to move them to a ticker whose evidence is
not about to change, and to record the decision before any paid run.

## 10. The wider dry run: 33 tickers, seven exchanges

Six tickers is thin for a market-wide parser change, so the same before/after was run over a
spread of 33 — eighteen Tadawul names including banks, insurers and industrials, and fifteen on the
six other exchanges as controls. Both parsers, same pages, two local scratch databases.
Raw output: `docs/verification/ingestion-repair-2026-10-28.md`.

| | result |
|---|---|
| **rows lost** (a row an existing reader had, now missing) | **0** |
| **rows changed** (same key, different label or value) | **0** |
| crashes, either parser | **none** |
| `mode` changed for any ticker | **none** — 18 `quarterly_reconstructed`, 14 `annual_direct`, 1 with no usable grid |
| rows gained by an **annual-grid** ticker | **0**, and 0 quarterly rows — the annual path is provably untouched |
| rows gained by a **Tadawul** ticker | 24–28 each, plus 188–283 rows of quarterly history |
| rows without `source_json` | **0** |

**Income statement, by exchange:**

| exchange | tickers | had one before | has one after |
|---|---:|---:|---:|
| **TADAWUL** | 18 | **0** | **18** |
| ADX | 3 | 3 | 3 |
| BSE | 2 | 2 | 2 |
| DFM | 3 | 3 | 3 |
| KSE | 3 | 3 | 3 |
| MSM | 2 | 1 | 1 |
| QSE | 2 | 2 | 2 |

Nothing outside Tadawul moved, in either direction. MSM's 1-of-2 is pre-existing and unchanged.

**And the invariant that matters most, asserted rather than eyeballed:** of the 14 tickers whose
income statement spans more than one `period_end`, **every one is `annual_direct`**, where one
period end per fiscal year is exactly right. **Zero quarterly-reconstructed tickers span more than
one window** — the sweep now fails outright if any does, because a ratio across two windows of one
statement is the defect this repair exists to avoid.

## 11. What this does not do

- **It does not apply anything.** The patch is prepared and dry-run. The live pipeline is untouched.
- **It does not get the annual grid.** A1 from the inspection — making the Tadawul harvest land on
  the genuinely annual page — remains the better fix if that page is still reachable, and this is
  A2. If A1 later works, this patch stays correct and simply stops being load-bearing for Tadawul:
  the annual path is the one it does not alter.
- **It does not give multi-year history.** Five quarters is what the pages carry.
- **It does not produce a cash-flow statement.** None exists for any ticker on any exchange.
- **It does not fix the share-count contradiction** in Al Rajhi's balance sheet, which needs the
  provider's definition.
- **It has not been run over the whole universe.** 33 tickers were tested (section 10), not 714.
  A full dry run needs the owner's go-ahead, because it means running pipeline code on the server.
