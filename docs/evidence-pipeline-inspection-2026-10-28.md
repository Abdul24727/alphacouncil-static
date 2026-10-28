# The financial evidence pipeline: inventory, three reconciled cases, and the smallest fixes

2026-10-28. Written on the owner's instruction, quoted verbatim from the review that asked for it:

> "Inspect and document the current financial evidence pipeline and available-but-excluded data.
> Reconcile these three cases. Propose the smallest fixes; do not change models, personas, roster
> or debate stages yet."

**Nothing was changed.** No model call, no commit to the pipeline, no deployment, no production
write. Everything below was read: the repository, the five committed data packs under
`docs/eval/packs/`, a 2026-08-02 offbox copy of `screening.sqlite`, and the **beta** API over a
read-only SSH tunnel on 2026-10-28. Models, personas, roster and debate stages are untouched.

Two reads were refused and one route around them was used. `python3` against the server's live
`screening.sqlite` was refused by the auto-mode classifier, as it was on 2026-10-24; the server
has no `sqlite3` binary. Every live fact below therefore comes from beta's own HTTP API, which is
the same route the 2026-10-24 check used. Where a figure could only be had from the 2026-08-02
copy, it is dated in the text.

---

## 1. The finding that matters most

**No Saudi company has an income statement in the live database.** Of 238 tickers sampled across
the universe, every one of the 90 Tadawul names lacks an `Income Statement` section, while 135 of
the 148 names on the six other exchanges have one:

| exchange | sampled | has Income Statement | has Balance Sheet |
|---|---:|---:|---:|
| TADAWUL | 90 | **0 (0%)** | 80 |
| ADX | 34 | 30 (88%) | 30 |
| BSE | 13 | 13 (100%) | 13 |
| DFM | 21 | 20 (95%) | 20 |
| KSE | 43 | 39 (91%) | 39 |
| MSM | 19 | 15 (79%) | 15 |
| QSE | 18 | 18 (100%) | 18 |
| **all** | **238** | **135 (57%)** | **215** |

It is a regression, not a gap that was always there. In the 2026-08-02 copy of `screening.sqlite`,
Saudi Aramco had 18 income-statement rows and SABIC 15, with FY2025 revenue, cost of sales, gross
income, operating income, zakat, net income and EPS. Both are gone today.

The data is still being collected. The 2026-10-23 full harvest wrote
`.../2222_TADAWUL/harvest_runs/run_20261023_002357/financial_statements_annual.html`, 1.72 MB,
containing `Net Income` 19 times, `Cost of Sales` 19 times and `Gross Income` 7 times. **The loss
is between the harvest and the database**, in the parse or load stage, not in the scrape. Two
files carry that stage (`parse_financial_statements.py`, `compute_fundamental_gauges.py`); which
one is at fault is not established here, because PROJECT.md section 4 forbids touching the old
pipeline's code before Step 5's checkpoint, and this brief says propose, not change.

One supporting observation, offered as a lead rather than a conclusion: the 2026-10-28 gauge log
carries hundreds of label-search warnings for ADX, DFM, MSM, BSE and KSE tickers and **not one for
any Tadawul ticker**. Whatever stage would report a Saudi statement problem is silent about Saudi
companies.

### What that costs the room, in figures

Everything derived from an income statement is `missing_inputs` for every Saudi name. These are
Aramco's own gauge values from the 2026-08-02 copy, computed, status `ok`, each with a sector
percentile, beside what the room was handed in the 2026-10-27 pack:

| gauge | 2026-08-02 value | percentile | in the 2026-10-27 pack |
|---|---:|---:|---|
| net_margin | 20.83 % | 72.6 | `missing_inputs` |
| gross_margin | 50.16 % | 81.6 | `na_sector` |
| roic | 21.58 % | 88.0 | `missing_inputs` |
| interest_coverage | 66.65 x | 96.4 | `missing_inputs` |
| **payout** | **92.64 %** | 15.9 | `missing_inputs` |
| ps | 3.83 x | 25.1 | `missing_inputs` |

Six of Aramco's ten computed gauges. The room is told they are missing. They were computed, and
the inputs they were computed from are recorded.

---

## 2. Where every material input comes from

The pack each seat reads is built once per session by `api/app/debate/pack.py`. It calls eight
Copilot database tools and tags each result `P1`-`P8`. Nothing in the pack computes a market
figure; the only transformation is returns being multiplied by 100 into percents.

| tag | tool | router | underlying store |
|---|---|---|---|
| P1 | `get_ticker_overview` | `routers/ticker.get_ticker` | `briefs` + `scraped_ratios` + `stocks` via `app/ratios.py`; price from the ticker's `price_history_10y.csv`; technicals from `ticker_tech_snapshot` |
| P2 | `get_fundamentals` | `ticker_research.get_fundamentals` | `fundamentals_gauges`, plus the same published ratios |
| P3 | `get_dividends` | `ticker_research.get_corporate` | `dividends`, `capital_changes` |
| P4 | `get_council` | `ticker_research.get_council` | `briefs`, `app/ratios.py`, `news_ai` |
| P5 | `get_peers` | `ticker.get_peers` | `briefs`, for same-sector names |
| P6 | `get_news` | `ticker.get_news` | `items` + `news_ai` in `evidence.sqlite` |
| P7/P8 | `get_price_summary` 1Y / 5Y | `copilot/tools.price_summary` | the price CSV |

Four SQLite files, written by the old pipeline and opened read-only by explicit path
(`briefs_index`, `screening`, `evidence`, `market_indices`), plus one CSV per ticker.

**The pack already uses every Copilot database tool that takes a ticker.** There is no unused tool
to switch on. Widening what the room sees means either adding a tool or adding a field, which is
section 5.

**One ratio layer, three source tables.** `app/ratios.py` resolves P/E, P/B, dividend yield, ROE
and ROA from `stocks`, then `scraped_ratios`, then `briefs`, so one ticker shows one number on
every screen. It nulls a ratio that is not meaningful: P/E on non-positive earnings, P/B and ROE
on negative book value. That design is sound, and it is the reason section 4 finds what it finds.

---

## 3. Which periods are comparable: they are not

One pack, fetched 2026-10-27, carries nine different as-of dates. Taking Aramco's:

| what | as of | age at fetch |
|---|---|---:|
| price, day change, volume (`quote`) | 2026-10-13 | 14 d |
| 1Y and 5Y price windows (P7, P8) | end 2026-10-13 | 14 d |
| **`quote.freshness`, prices** | **2026-10-13** | 14 d |
| **`freshness[prices]`, same dataset** | **2026-08-11** | **77 d** |
| technicals: RSI, SMA 50/200, 52-week distances | 2026-08-11 | 77 d |
| fundamentals gauges (P2) | 2026-08-12 | 76 d, `stale: false` |
| council votes (P4) | 2026-08-07 | 81 d |
| peers, every price and P/E (P5) | 2026-08-07 | 81 d |
| news (P6) | 2026-08-04 | 84 d (SABIC: 2026-01-07, **293 d**) |
| disclosures | 2026-03-09 | 232 d |
| statements, where they exist | FY2025 only | one year |

Three consequences, in order of how badly they mislead.

**(a) Every valuation ratio is priced off a price the pack does not show.** The ratios are
internally consistent with each other and with a price that is not `last_price`:

| | P/E x EPS | P/B x book | market cap / shares | `last_price` | gap |
|---|---:|---:|---:|---:|---:|
| Aramco | 26.62 | 26.61 | 26.50 | 25.78 | **+3.3 %** |
| Al Rajhi | 64.13 | 64.15 | 64.55 | 62.10 | **+3.3 %** |
| SABIC | - | 51.06 | 50.55 | 45.32 | **+12.7 %** |

Three independent cross-products agree to within 0.4 % in each row, which makes the stale block
*more* convincing to a reader, not less. A seat asked whether SABIC is cheap at 1.24x book is
reading a multiple struck at about 50.80. At 45.32 against the same book value it is 1.10.

**(b) The subject's price is newer than every peer's.** P5's peers are priced 2026-08-07, the
subject 2026-10-13. A relative-value question answered from prices is wrong by construction;
answered from P/E ratios it is accidentally consistent, because the subject's P/E is August too.
Nothing in the pack distinguishes the two.

**(c) P1 contradicts itself about the price date.** `quote.freshness.as_of` says 2026-10-13 and
`freshness[prices].as_of` says 2026-08-11, 63 days apart, in the same dataset. The cause is real
and worth stating plainly: the price files are refreshed nightly, the analytic pipeline last
completed on 2026-08-12, and `freshness` reports the pipeline while `quote` reports the file. The
`asof` probe in the benchmark asks a room to spot exactly this; the honest answer is itself
ambiguous.

A smaller note: `fundamentals` is marked `stale: false` at 76 days because its budget is 100 days.
That is the configured intent, not a defect, but "not stale" and "current" are not the same claim.

---

## 4. Which calculations are trustworthy

**The gauges are computed carefully and the room cannot check any of them.** Every row of
`fundamentals_gauges` carries an `inputs_json` recording exactly what went in. Aramco's
`debt_equity`:

```json
{"total_debt": 299323.0,
 "debt_parts": {"Short-term Debt": 43165.0, "Long-Term Debt": 256158.0},
 "equity": 1491996.0, "equity_label": "Total Shareholders' Equity", "sector": "non_bank"}
```

`get_fundamentals` selects `gauge_key, value, status, score`. **It does not select `inputs_json`.**
The audit trail exists, in the same row, and is dropped one line before the room.

This is not academic. Al Rajhi's `debt_equity` reaches the room as **1.72**, while its balance
sheet shows total liabilities of 900,356 against equity of 114,854, a ratio of **7.84**. A seat
will either call 1.72 implausible and be wrong, or reason about bank leverage from it and be
wrong. The `inputs_json` settles it in one line: `{"debt_parts": {"Term Sukuk": 79866.63, "Due to
Banks": 117283.80}, "equity": 114854.17, "sector": "bank"}` - it is wholesale funding to equity,
deliberately excluding customer deposits, a sensible measure carrying a misleading name. I had it
down as a non-bank template misapplied to a bank until I read the inputs. That is the point.

**The status vocabulary collapses three different facts into one word.** `GaugeMetric.status`
admits `ok`, `missing_inputs`, `na_sector`, `undefined_nonpositive` and `published`. The database
uses all of them. The pack flattens them:

- *not meaningful for this kind of company* - correct and useful (`current_ratio` and `roic` are
  `na_sector` for Al Rajhi, because a bank has no current split).
- *the input line was never harvested* - `missing_inputs`.
- *the quantity is undefined because the denominator is not positive* - should be
  `undefined_nonpositive`, and for the published ratios it is not. **SABIC's P/E arrives as
  `missing_inputs`.** There is no `pe` gauge row, so `get_fundamentals` falls through to the
  published ratio, which `ratios.py` correctly nulled because earnings are negative, and the
  fallback writes `"published" if v is not None else "missing_inputs"`. A company that lost
  SAR 25.8 bn is reported identically to a company whose data never arrived. Same for P/B and ROE
  on negative equity.

**Two sector labels are miscalibrated, in opposite directions.** `fcf_yield` is `na_sector` for
all three, and its recorded reason for a Saudi company is
`"note": "UAE: no cash-flow statement published"`. `gross_margin` is `na_sector` in the pack for
SABIC, a petrochemical whose gross margin is both meaningful and, in August, computed at 15.29 %.

**"Sector percentile" means one of three buckets.** `sector_averages` holds exactly three
`sector_key` values: `bank`, `insurance`, `non_bank`. So Aramco's `debt_equity` at the 53.8th
percentile and `current_ratio` at the 68.7th are percentiles among **all 378-382 non-financial
GCC equities**, not among Energy. And the dataset whose title is "Fundamentals with sector
percentiles" delivers a percentile for **2 of its 15 metrics**, both of them balance-sheet gauges.

**A share-count contradiction the data states about itself.** Income-statement share counts are
exactly 4x the balance-sheet counts, on both tickers that have both statements: Aramco 968,000 vs
242,000, SABIC 12,000 vs 3,000. In both cases the EPS in the same statement is computed on the
balance-sheet count (Aramco 348,042 / 242,000 = 1.4382 against a stated 1.44; SABIC
-25,779.24 / 3,000 = -8.5931 against a stated -8.59), so the balance-sheet count is the usable
one and the income statement's own figure is an artifact. This is consistent with PROJECT.md's
standing note that the provider's share-count definition is unestablished, and it is checkable
without the provider: EPS x shares must equal net income.

---

## 5. Available but excluded

The honest inventory separates two very different things: data that exists and is not shown, and
schema that exists and was never filled.

### Exists, has rows, never reaches the room

| source | scale | what it holds | why it never arrives |
|---|---|---|---|
| `fundamentals_lineitems` via `GET /v1/tickers/{ref}/statements` | 123,413 rows, 649 tickers (2026-08-02) | balance sheet and, outside Tadawul, income statement | the endpoint exists and is served to the screen; **no Copilot tool exposes it**, so the pack cannot reach it |
| `ticker_insights` via `GET /v1/tickers/{ref}/insights` | 700 rows, 1 per ticker | performance, seasonality, ownership, analyst coverage | same: served to the screen, no tool |
| `fundamentals_gauges.inputs_json` | one per gauge per ticker | the inputs and labels behind every computed gauge | the column is not in `get_fundamentals`'s SELECT |
| `sector_averages` | 30 rows | mean, median, n and stdev per bucket per gauge | not read by the API at all |

### Schema only, no rows anywhere (2026-08-02)

| table | columns it would hold | market-wide rows |
|---|---|---:|
| **`bank_metrics`** | `cost_income`, `net_margin_bank`, `cost_of_risk`, `npl_ratio`, `npl_coverage`, `equity_assets`, `loans_deposits` | **0** |
| `fundamentals_cagr` | per-metric CAGR with window, start and end year | **0** |
| `fundamentals_history` | per-year value of any metric | **0** |
| `fundamentals_segments` | revenue and profit by business segment | **0** |
| `company_kpis` | per-company KPI decks | **0** |
| `mna_history` | deal history | 2 (none for our three) |
| `negotiated_deals` | off-market blocks and premiums | 39 (none for our three) |

And nowhere, for any ticker on any exchange: **a cash-flow statement**.
`fundamentals_lineitems` has three sections market-wide - `Balance Sheet`, `Income Statement` and
`(none)` (61 rows, 48 tickers). There is no cash-flow section, which is why `fcf_yield` is
`na_sector` for all 653 tickers that carry the gauge.

---

## 6. Aramco (2222): dividend aggregation, earnings coverage, cash-flow evidence

### Dividend aggregation

P3 gives ten dividend rows, newest ex-date 2026-08-19, and **no window marker and no TTM total**.
Four defensible aggregations, from the same ten rows:

| method | result | yield at `last_price` 25.78 |
|---|---:|---:|
| sum `dps` over the last 12 months of ex-dates | 1.35 | 5.24 % |
| sum `dps` over all ten rows (the obvious error) | 3.78 | **14.66 %** |
| sum `amount_mn` over the last 12 months, over market cap | 326,340 | 5.09 % |
| the pack's published `dividend_yield_pct` | - | **5.01 %** |

The published 5.01 % implies a DPS of 1.3337 at the ratio price of 26.62. No seat can reproduce it
from the pack, because the window, the price and the treatment of performance-linked dividends are
all invisible. And `amount_mn` is a company total, not a per-share figure, sitting in the same row
as `dps` with nothing to stop the two being added.

**The aggregation trap that changes the investment answer.** DPS runs 0.48, 0.48, 0.48, 0.33,
0.33, 0.33, 0.33, 0.34, 0.34, 0.34 - read as a series, a 29 % cut. The `note` field says why: the
2024 rows include "performance-linked dividends SAR 40390 million", the 2025 rows "SAR 820
million", and the 2026 rows none. Net of the top-up the base dividend went 0.313, 0.327, 0.34 -
**it rose**. The correct reading is recoverable only from free text in a `note`, and the
performance-linked component has no field of its own.

Aramco's history also crosses two bonus issues (2022-05, +25 %; 2023-05, +20 %) and a 2024
secondary offering. All ten rows sit after the bonus issues, so this window is comparable - but
nothing in the pack says that, and the next ticker's may not be.

### Earnings coverage

The pack says `payout: missing_inputs`. Three answers are available and they are far apart:

| route | payout |
|---|---:|
| by hand from the pack: TTM DPS 1.35 / EPS 1.84 | **73.4 %** |
| the pipeline's own gauge, 2026-08-02 | **92.6 %** |
| FY2025 dividends 322,420 / FY2025 net income 348,042 | **92.6 %** |

The gauge recorded its work: `{"dividends": 322420.0, "net_income": 348042.0,
"dividend_rows_matched": 4, "dividend_matched_rows": [...]}`, naming each quarter it matched. **The
pipeline already does this aggregation correctly, already computes coverage, and the room is told
the inputs are missing.** A seat doing it by hand lands on 73 %, which is a materially more
comfortable company than 93 %.

### And a comparability problem specific to Aramco

P5 gives Aramco five Energy peers: National Shipping (market cap 27,907), Petro Rabigh (26,937),
ADES (19,973), Arabian Drilling (7,271) and Saudi Arabian Refineries (732) - against Aramco's
6,413,000. **The largest peer is 0.44 % of Aramco's market cap**, Aramco is over 99 % of its own
sector by capitalisation, and two of the five have no P/E at all, leaving a median of 12.5 drawn
from a shipping line and two drillers. "Aramco's P/E of 14.47 against its sector" is not a
valuation comparison, and nothing in the pack signals that.

### Cash-flow evidence

None, and provably so rather than by omission. No cash-flow statement exists for any ticker. For
Aramco specifically the room has no operating cash flow, no capex (`Capital work in Progress`
404,970 is a balance, not a flow), no net income and no payout ratio. The one thing the balance
sheet does support, and which the room cannot see today: FY2025 cash and equivalents of 243,099
plus short-term investments of 45,272 come to 288,371 against 322,420 of dividends declared for
the year - **the annual dividend exceeds cash and short-term investments by 12 %**. That is the
kind of statement the Aramco question needs, and it is one balance-sheet read away.

---

## 7. Al Rajhi (1120): valuation comparability, bank-specific resilience

### Valuation comparability

Al Rajhi has **no income statement at all** - 32 rows, every one balance sheet - and four gauge
rows confirm the pipeline looked and found nothing: `"expected_section": "Income Statement",
"available_in_section": []`. So no revenue, no net income, no finance cost, and therefore no net
margin, no payout, no P/S and no interest coverage, for any bank.

Worse, the balance sheet contradicts itself on the share count, and the valuation turns on it:

| field | value |
|---|---:|
| `Capital` | 40,000 |
| `Par Value (Riyal)` | 10.0 |
| capital / par, implied shares | **4,000 mn** |
| `Shares Outstanding (Million)` | **6,000 mn** |

Those cannot all be true. Book value per share is 19.14 on 6,000 shares and **28.71** on 4,000.
P/B at `last_price` 62.10 is 3.24 or **2.16** - a 50 % difference in the headline valuation measure
of the subject company. The pack reports `pb: 3.19` and `book_value: 20.11` from the vendor feed,
a third pair of figures, matching neither. The same check passes cleanly for SABIC (30,000 / 10 =
3,000 shares, stated 3,000) and cannot be run for Aramco, whose balance sheet has no `Par Value`
row. I am not asserting which count is right; the provider's definition is still unestablished.
I am asserting that the data states a contradiction about itself and nothing checks it.

Peers are comparable in one respect and not in another: all eight are Tadawul banks, priced
2026-08-07, the same vintage as Al Rajhi's own P/E, so P/E against peers is sound, while
`last_price` against peers' `last_price` is two months out.

### Bank-specific resilience

`bank_metrics` has exactly the right seven columns and **zero rows, market-wide**. But four of the
seven are computable today from balance-sheet lines already in the database:

| measure | from | Al Rajhi, FY2025 |
|---|---|---:|
| NPL ratio | 5,694.22 / (755,748.52 + 5,694.22) | **0.75 %** |
| NPL coverage | 8,682.89 / 5,694.22 | **152.5 %** |
| equity / assets | 114,854.17 / 1,043,268.30 | **11.0 %** |
| loans / deposits | 752,759.85 / 667,287.50 | **112.8 %** |

The other three - cost/income, net interest margin, cost of risk - need the income statement and
cannot be computed for any bank today.

So the answer to "are bank-specific resilience measures available" is: **four of seven are one
arithmetic step from data already in the database; three are blocked behind the same missing income
statement as everything else; none of the seven is exposed.**

---

## 8. SABIC (2010): loss-making earnings, unit confirmation, cyclical vs structural

### The loss, and how the pack reports it

| what the room is told | what the data says (2026-08-02) |
|---|---|
| `pe: null, status: missing_inputs` | P/E is undefined because earnings are negative |
| `eps_ttm: null, reason: "unit_unconfirmed"` | `scraped_ratios.eps_ttm` = **-1.76** |
| `payout: missing_inputs` | gauge status was `undefined_nonpositive`, net income -25,779.24 |
| `net_margin: missing_inputs` | **-20.28 %**, computed, percentile 7.9 |
| `gross_margin: na_sector` | **15.29 %**, computed, percentile 21.1 |
| `roe: -15.37`, `roa: -8.24` | these do arrive, so the loss is visible in the ratios |

The loss reaches the room as two negative percentages and four absences. Its size, its cause and
its composition do not reach the room at all.

### Unit confirmation

`ratios.eps_in_price_unit` is a careful piece of work: EPS is shown only when `EPS x P/E` returns
the price within 20 %, after optionally dividing by the currency's sub-unit, because the vendor's
EPS is not stored in one unit across exchanges. It is also **mis-gated**. Its first line is
`if eps is None or not pe or ...: return None`. For a loss-making company `pe` is always None,
because `ratios.py` nulls P/E on non-positive earnings. So:

> **For every loss-making company, EPS is suppressed and the reason given is
> `unit_unconfirmed` - although the unit was never tested.** The pack tells the room SABIC's EPS
> unit could not be confirmed. The truth is that SABIC lost money.

That is the single worst sentence in the pack, because it is a false explanation rather than a
silence, and it lands on precisely the case where the loss is the whole question.

Two further unit facts, both real and both invisible: the database holds **two** EPS figures for
SABIC, `scraped_ratios.eps_ttm` -1.76 and the statement's FY2025 EPS -8.59, differing 4.9x; the
statement's "before unusual items" EPS is -1.39, so the vendor's -1.76 is close to a
pre-extraordinary TTM figure. The discrepancy is one of **definition, not units** - which is the
distinction the current machinery cannot draw.

### Cyclical weakness vs structural deterioration

Not separable from the pack today, and separable in two lines of the income statement that existed
in August:

| line | FY2025 |
|---|---:|
| Sales | 127,114.69 |
| Operating Income | **-292.16** |
| EBITDA | 16,950.00 |
| Net Profit Before Unusual Items | **-4,189.86** |
| Extraordinary income/expense | **-21,589.38** |
| Net Income | **-25,779.24** |

**84 % of the loss is a single extraordinary item.** The structural picture - roughly breakeven at
the operating line, EBITDA still positive at 16,950, a 4.2 bn loss before unusual items - and the
headline -25.8 bn differ by a factor of six, and they imply opposite conclusions about whether
this is a cycle or a decline. The room gets neither figure.

Trend evidence is absent independently of that: statements hold **one fiscal year**, and
`fundamentals_history` and `fundamentals_cagr` are empty. P7 and P8 give five years of *price*,
nothing of earnings. So even with the income statement restored, a single year cannot separate
cyclical from structural - which is the one place where this inspection points at new pipeline
work rather than a data-pack change.

One more comparability hazard the SABIC case exposes. Three of its eight peers (Sipchem, SIIG,
Saudi Kayan) have `pe: null` because they are also loss-making. They drop out of any sector P/E,
leaving a median of 32.47 from the survivors. **In a cyclical sector at the bottom of its cycle,
nullity biases the sector multiple upward**, and a room asked whether Materials is expensive sees
32.47 with no sign that a third of the sector has no earnings at all.

---

## 9. The smallest fixes

Ordered by value per unit of change. Nothing here touches models, personas, roster or debate
stages. The first item is the only one that is not ours to make.

### A. Restore the Saudi income statement (pipeline; the owner's call)

Everything in sections 6, 7 and 8 that reads as a data-pack problem is downstream of this. The
HTML is harvested and the load drops it. **Diagnose before changing anything**: for one Tadawul
ticker, run the existing parse over the 2026-10-23 `financial_statements_annual.html` and see
whether it emits income-statement rows. If it does, the loader is at fault; if not, the parser's
Tadawul table selector is. Section 4 of PROJECT.md holds this behind Step 5's checkpoint, so it
needs the owner's say-so, and it is the highest-value change available.

A second, independent pipeline defect visible in the same log: for GCC banks and insurers the
income-statement rows are **Arabic-labelled** and the gauge's search list is English-first with
partial Arabic, so `net_margin`, `interest_coverage` and `ps` fail on tickers that plainly have
the lines. Extending one label list fixes a whole sector's worth of gauges.

### B. Expose `inputs_json` (one column, one SELECT)

Add `inputs_json` to the `fundamentals_gauges` SELECT in `get_fundamentals` and carry it on
`GaugeMetric`. Every computed gauge becomes checkable: Al Rajhi's 1.72 stops being a puzzle, the
market cap behind P/S and EV/EBITDA becomes visible, and the matched dividend rows behind a payout
ratio become auditable. This is the cheapest change in the list and the one that most directly
answers "which calculations are trustworthy".

### C. Tell the truth about why a figure is absent

Three small, separate corrections, all in code we own:

1. In `get_fundamentals`, when a published ratio is null *because* `ratios.py` judged it not
   meaningful, emit `undefined_nonpositive`, not `missing_inputs`. SABIC's P/E then reads
   "undefined, earnings are negative" rather than "we do not have it".
2. In `routers/ticker.py`, set `eps_ttm_reason` to a distinct value, `earnings_nonpositive`, when
   EPS was suppressed because P/E is null rather than because the unit failed its check. And
   consider showing a negative EPS: the unit test is a magnitude check against P/E, so for a loss
   the honest options are to show the figure with its unit unverified or to say why it is hidden,
   not to blame the unit.
3. Correct the `fcf_yield` note, which currently tells a Saudi company's reader
   `"UAE: no cash-flow statement published"`, and re-examine `gross_margin: na_sector` for
   Materials, where the metric is meaningful and was computed.

### D. Date the valuation block

The ratios carry no date and are struck on a price the pack does not show - 12.7 % from
`last_price` for SABIC. The minimum honest fix is to carry the ratio layer's as-of date on
`Valuation` and name it in the pack header. The fuller fix, out of scope here, is for the header to
say that ratios, technicals, council and peers share one analytic date and the price does not.
Also reconcile `quote.freshness` and `freshness[prices]`, which disagree by 63 days inside one
dataset, and give the peer block its own as-of in a place a reader cannot miss.

### E. Two new fields, no new tool

- **`dps_ttm` and its window** on P3, computed the way the payout gauge already computes it, plus
  the performance-linked component as a field rather than inside a `note`. This removes the four
  irreconcilable aggregations in section 6 and the 14.66 % yield a seat reaches by summing ten
  rows.
- **A share-count consistency flag.** Three checks the data already supports: `Capital / Par Value`
  against `Shares Outstanding`; income-statement against balance-sheet share count; `EPS x shares`
  against net income. Al Rajhi fails the first, Aramco and SABIC fail the second, and the third
  identifies which count to trust. A flag is cheap and does not require resolving the provider's
  definition.

### F. One new tool: statements

A `get_statements` Copilot tool, pointed at the endpoint that already exists, is what makes
sections 6, 7 and 8 answerable rather than merely documented - but **only after A**, because today
it would hand every Saudi room a balance sheet and nothing else. Worth sizing when A lands: a
42-row balance sheet plus an 18-row income statement is roughly 2-4 KB of JSON against the
12,000-character per-dataset budget, so it fits.

### G. Four bank measures, no new table

NPL ratio, NPL coverage, equity/assets and loans/deposits are each one division over balance-sheet
lines already in the database (section 7). They do not need `bank_metrics` to be filled and they do
not need the income statement. Cost/income, net interest margin and cost of risk do, and should
wait for A.

### Not recommended now

Filling `bank_metrics`, `fundamentals_cagr`, `fundamentals_history` or `fundamentals_segments` is
pipeline work on empty tables, and `fundamentals_cagr` cannot be computed from one fiscal year
anyway. Multi-year statements are the prerequisite for the trend evidence section 8 needs, and that
is a larger piece of work than this brief covers. A cash-flow statement does not exist for any
ticker on any exchange and is a sourcing question, not a code change.

---

## 10. What this inspection does not establish

- **When the Saudi income statement disappeared.** It was present 2026-08-02 and absent
  2026-10-28. The only historical market-database copy on this computer is that 2026-08-02 offbox
  backup; the dated backups under `AlphaCouncil-Backups/` are Postgres application dumps, not the
  market SQLite files.
- **Which stage drops it.** Harvested and not loaded is established. Parser versus loader is not,
  and settling it means reading or running old-pipeline code, which section 4 gates.
- **Whether the gauge values from 2026-08-02 would recompute to the same numbers today.** They are
  used above as evidence that the inputs existed and the calculation ran, not as current figures.
- **Al Rajhi's true share count.** The internal contradiction is established; the resolution needs
  the provider's definition, which PROJECT.md records as still unestablished.
- **Whether the 13 non-Tadawul tickers in the sample that lack an income statement lack it for the
  same reason.** The Arabic-label finding is a lead, not a measured cause.
- **Any live production behaviour.** Every live read went to **beta**.
