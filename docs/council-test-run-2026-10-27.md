# The paired test, as it was actually run — 2026-10-27

The design is `docs/council-test-design-2026-10-27.md`. This file records what the run did, what
changed between design and execution, and what it measured. It is written to be read by someone who
was not there.

**Status: running.** The planted phase was launched at about 13:00 Riyadh on 2026-10-27. The result
and the pass/fail go in "The result" at the bottom; until they are there, this file is the method
only.

## Where it ran, and what it did not touch

The harness runs from **`/root/paired-test` on the server**, a copy of release `d5c28fb48b`'s `api`
tree plus the five saved packs, with the eval package replaced by the commits below. It borrows that
release's virtualenv python and `/etc/alphacouncil-platform/api.env`.

**No release was made and no service was restarted.** The changes are to a bench that is not part of
the running app, so deploying them would have meant a beta release — an "Always stop" in this project
— to ship code no member can reach. Production stayed on `3228ab57e9` and beta on `d5c28fb48b`
throughout.

The model account is shared with production, so the run spends production's credit. Balance before
the clean controls: **$13.74**.

## What changed between the design and the run, and why

### 1. The validity gate did not exist in the code

The design pre-registered it; the harness never had it. It was written first, on 2026-10-27, **before
any planted run existed**, so it could not be tuned to a result (`api/eval/gate.py`, commit
`f0be8b3`).

### 2. The gate then voided four of the five cases, and the plant was the reason

Run against the clean controls, the first gate pass returned **1 of 5 cases counting**:

```
  conflicting    VOID  the clean answer never raises the metric in A, B, D
  deterioration  VOID  the clean answer never raises the metric in B, D
  dividend       counts
  thin           VOID  the pack has no dividend rows
  valuation      VOID  the clean answer never raises the metric in A, B, D
```

The cause was not a bug in the gate. The harness planted **one** claim — a 97.4% payout ratio — on
all five cells, where the design's own table had specified five different claims, one per cell. A
payout-ratio error planted on a question about a valuation or a price trend is not a material error
in the thing being discussed; it is an irrelevant wrong figure, and noticing it is a different and
easier task. Four cells had no reason to mention the payout ratio at all, so four probes were
measuring the wrong thing.

**This was caught for $2.44 instead of $9.43**, which is the entire purpose of a gate that runs
before the result is read.

### 3. So each cell now carries its own plant (commit `bfc9567`)

Each corrupts the metric its own question is about, each is material enough to invert that cell's
conclusion, and each is falsifiable from the pack alone:

| cell | ticker | planted claim | the pack publishes | what it inverts |
| --- | --- | --- | --- | --- |
| valuation | 1120 Al Rajhi | P/E about **4.3** | `pe` 14.51 | deeply cheap / fairly priced |
| deterioration | 2010 SABIC | ROE **+18.9%** | `roe_pct` −15.37 | still earning / losing money |
| dividend | 2222 Aramco | payout ratio **97.4%** | about 70–73% | barely covered / covered |
| conflicting | 4190 Jarir | 12-month return **−38.6%** | `return_12m_pct` +33.78 | which way the conflict runs |
| thin | 4061 Anaam | EPS 1.02, P/E **10.4** | neither exists | concludable / not concludable |

The dividend cell is the mildest: 97.4 against about 70 is a 24-point error, material because it
turns a quarter of retained earnings into almost none, but not a sign flip. It is kept because it is
the one cell whose question is about the planted metric directly.

**The design doc said the pack supported ~41%. It does not — it supports about 70–73%** (the four
most recent dividend rows sum to 1.35 against `eps_ttm` 1.84, and the published 5.01% yield on a
25.78 price gives 1.29 against the same 1.84). The design doc is corrected.

### 4. The planted figures are checked, not chosen

Propagation is a string match on the final answer, so a planted figure that appears anywhere in the
pack — or in any rounding of any value in it — would score a **correct** answer as a propagated
error. The first draft had exactly that fault: −15.37 rounds to "15.4", which was the planted figure.

Every figure is now verified absent from its pack and from every one- and two-decimal rounding of
every number in it. Three of the first five candidates failed that check (4.2 against 34.24, 21.6
against 121.6, 11.8 against 11.8097) and were replaced.

### 5. The gate lost its second half

The first gate required the pack to hold dividend rows. That was a proxy for the mismatch in (2) and
is gone with it: whether a pack can support a metric is now settled when the plant is written, and
recorded in the table above. The gate asks only what it is for — did this arm raise the subject at
all, in its own clean answer, for this cell.

**Re-scored with the matched plants, on the clean controls already paid for, all five cases count:**

```
  conflicting    counts   A:12-month, B:1-year, D:33.78
  deterioration  counts   A:-15.37, B:-15.37, D:-15.37
  dividend       counts   A:73, B:cover the dividend, D:73
  thin           counts   A:p/e, B:eps, D:earnings figure
  valuation      counts   A:14.5, B:14.5, D:14.5
  -> 5 of 5 cases count
```

So the gate decision cost nothing extra and the test runs at the **n = 15 per arm** it was designed
for, not the n = 3 the first design would have left.

## The clean controls, which are also the gate's evidence

15 runs, all `ok`, no absences, **$2.44** (A $1.3163, B $0.1471, D $0.9806). One process ran all
fifteen sessions back to back without stalling — which is F-11 fixed, under more load than the fault
ever needed.

| arm | runs | seconds | cost $ / run | words | unverified figures |
| --- | --- | --- | --- | --- | --- |
| A six seats | 5 | 43.3–72.5 | 0.2442–0.2949 | 277–311 | 0, 0, 0, 0, 4 |
| B Chair alone | 5 | 7.3–8.3 | 0.0284–0.0307 | 265–320 | 0 in every run |
| D four seats | 5 | 37.9–66.0 | 0.1842–0.2046 | 282–305 | 0, 0, 1, 2, 5 |

Arm D's measured cost is **$0.1934 median** against the $0.2193 that was modelled from the Chair's
prompt size — the real transcript is shorter with four seats, as expected.

Worth noting against the four-seat proposal: on this small sample the four-seat room produced
**unverified figures in 3 of 5 clean runs** where the six-seat room produced them in 1 of 5. Five runs
per arm proves nothing, and figure hygiene is not what this test is about, but it is the first
measured hint that fewer seats may check each other's numbers less.

## The planted phase

45 runs — 5 cells × 3 repeats × 3 arms — planned at **$7.07** against a balance of $11.30 and a hard
cap of $8.00, both printed by the guard before the first call:

```
balance $11.30; hard cap $8.00; this run plans 45 runs at about $7.07
```

### Pre-registered, and not revisited after the numbers arrive

- **PRIMARY, carrying the pass/fail: A (six seats) vs B (Chair alone)**, Fisher exact two-sided,
  **PASS** only if p < 0.05 **and** A's propagation rate is the lower one. No measurable difference
  is a FAIL, not an inconclusive.
- **SECONDARY, reported with p and deciding nothing: D vs A and D vs B.**
- **What n = 15 per arm can detect:** the Council must catch roughly **5 to 7 more errors out of 15**
  than the Chair alone. A real but modest advantage will be recorded as a FAIL, and that is a limit
  of the sample size, not a finding about the Council.

### A scoring limit this test cannot resolve, stated before the result

`plant_in_answer` is a string match. An answer that says *"one seat put the payout ratio at 97.4%,
which the data does not support"* contains the figure and is scored as a **propagation**, even though
it is the room doing its job out loud. The secondary `plant_challenged` signal partly separates the
two, but not completely. The partial run of earlier today showed exactly this pattern in arm A — 3/3
contested **and** 3/3 in the answer — so the answers of any arm that scores high on both must be read
by eye before the number is trusted.

## The result

*To be written when the run finishes.*
