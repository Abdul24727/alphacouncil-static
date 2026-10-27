# The paired test, as it was actually run — 2026-10-27

The design is `docs/council-test-design-2026-10-27.md`. This file records what the run did, what
changed between design and execution, and what it measured. It is written to be read by someone who
was not there.

**Status: complete.** 60 runs, $9.00 spent, nothing failed. The pre-registered result is a FAIL, and
the reason is a ceiling effect rather than anything about the Council — see "The result" below.

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

**45 planted runs, all 45 `ok`, no absences, no failed turns. $6.56 for the phase and $9.00 for all
60 runs, against a $13.74 starting balance and an $8.00 cap. Balance after: $4.84.**

### The pre-registered answer: FAIL

```
PROPAGATION OF THE PLANTED ERROR (lower is better)
  A: 13/15 propagated, 15/15 contested in the challenges
  B: 15/15 propagated
  D: 12/15 propagated, 15/15 contested in the challenges

  PRIMARY: A 13/15 vs B 15/15  Fisher p = 0.4828  -> FAIL
  secondary: D 12/15 vs A 13/15  Fisher p = 1.0000
  secondary: D 12/15 vs B 15/15  Fisher p = 0.2241
```

That is the result of record. The rule said no measurable difference is a FAIL, not an
inconclusive, and it stands.

### And the metric is invalid, which was written down before the run

The limit recorded above — that a string match cannot tell *repeating* a wrong figure from *naming*
it in order to reject it — turned out not to be a caveat here. It is the whole measurement.

**Every one of the 45 answers was read. Not one adopted the planted claim.** Classified
mechanically as well, with a rejection marker required in the figure's own sentence or the one
after it:

| arm | runs | rejects the figure in words | never states it | adopts it |
| --- | --- | --- | --- | --- |
| A six seats | 15 | 13 | 2 | **0** |
| B Chair alone | 15 | 15 | 0 | **0** |
| D four seats | 15 | 12 | 3 | **0** |

The five answers that never state the figure were read in full: all five give the pack's correct
value and reach the correct conclusion. The figure appears in the other 40 for the same reason every
time — the answer is explaining what it rejected:

> *"Buffett opened with a return on equity of 18.9 per cent and read no deterioration. Every other
> advisor pointed out that this figure is not in the pack."* (A, deterioration)

> *"The analyst's note cites a return on equity of 18.9 per cent. The pack does not say that."*
> (B, deterioration)

So the pre-registered test reports FAIL for a reason that has nothing to do with the Council: **the
baseline is already perfect.** The Chair alone caught the error 15 times out of 15. There was no
shortfall for six seats to cover, so no test built this way could have shown one. **This is a
ceiling effect. The Council's error-catching advantage is not demonstrated, and it is not
disproven — this test could not have detected it either way.**

### Why the task turned out to be too easy, which is the reusable lesson

The data pack is in the prompt. Every plant contradicted a figure sitting in the same context
window — `pe` 14.51, `roe_pct` −15.37, `return_12m_pct` +33.78 — so catching it took one lookup and
one comparison, which a strong model does reliably on its own. Four of the five plants were errors
of **fact against a published field**, and those cannot discriminate.

A probe only tests reasoning where the pack does not already hold the answer.

### The one place the arms did diverge — and it runs against the hypothesis

The `dividend` cell is the only one whose answer is **not** in the pack: `P2` marks the payout ratio
as missing inputs, so the right answer has to be built from `P3`'s dividend rows against `P1`'s
`eps_ttm` — 1.35 / 1.84, about 73 per cent.

| arm | derived a payout ratio | what it told the member |
| --- | --- | --- |
| A six seats | **4 of 4** runs: 73–74% | "Trailing earnings cover the dividend and the balance sheet looks strong" |
| D four seats | **4 of 4** runs: 72–74% | "Earnings appear to cover the dividend with a modest cushion" |
| B Chair alone | **0 of 4** runs | "Dividend coverage **cannot be confirmed** from this data" (2 of its 3 planted runs) |

Scored as a figure in the 70–76 band within about 130 characters of "payout" or "cover". The rooms
did the arithmetic across two datasets, got it right, and told the member the dividend is covered
with about a quarter of earnings retained. The single model **declined the question** and listed the
missing payout field as a gap. Both arms were honest; only one was useful.

Two scoring notes, because the first cut of this was wrong. The regex counted the "75" inside an ROE
of 26.75 as a payout ratio and credited arm B with 3 of 3; it does not. And the rooms' arithmetic was
checked independently — 1.35 / 1.84 is 73.4 per cent, so 73–74 is right, and the planted 97.4 is
wrong by 24 points.

**This is n = 4 per arm, on one cell, and it is post hoc.** It decides nothing. It is reported
because it is the only measured difference in 60 runs, and because it points at what a test with
discriminating power would have to plant: not a figure that contradicts the pack, but a derivation
the pack does not contain.

### Everything else that was measured

| arm | runs | seconds | $ / run | words | unverified figures | phase total |
| --- | --- | --- | --- | --- | --- | --- |
| A six seats | 15 | 59.1 (43.6–73.6) | 0.2257 (0.2092–0.2785) | 278 (236–346) | 1 (0–5) | $3.4528 |
| D four seats | 15 | 49.8 (43.2–60.2) | **0.1759** (0.1572–0.2031) | 284 (255–322) | 2 (0–4) | $2.6616 |
| B Chair alone | 15 | **8.1** (7.1–9.8) | **0.0292** (0.0271–0.0316) | 310 (278–350) | 1 (1–2) | $0.4434 |

The room costs **7.7×** the single model and takes **7.3×** as long. Four seats cost **22% less**
than six and run 16% faster.

### What this says about the four-seat proposal

Arm D existed to separate the two changes the proposal bundles — fewer seats, and rewritten
philosophies — by changing only the count. On the count alone:

- **Catching the planted error: no difference.** Both rooms caught it in 15 of 15. Neither this test
  nor a larger version of it can separate them on a task the baseline also passes.
- **Cost: four seats are 22% cheaper** and measurably faster, and the modelled $0.2193 was
  pessimistic — the real figure is $0.1759, because four seats make a shorter transcript.
- **Against that, four seats left more unverified figures**: a median of 2 against 1 in the planted
  phase, and 3 of 5 runs against 1 of 5 in the clean controls. Small samples, and figure hygiene is
  not what this test measures — but it is the one signal pointing away from cutting the count, and it
  is the signal the numbers-game worry predicted.

So the count is **not** shown to be the variable that matters, in either direction. Nothing here
argues for rewriting the philosophies, and nothing here argues against it.

### What would have to change to answer the original question

The question — *does the Council catch material financial errors the Chair alone misses?* — is still
open, and this run says why: it was asked with errors a single model catches on its own. A test with
power would plant what the pack cannot settle by lookup:

1. **A wrong derivation whose inputs are all in the pack and whose output is not** — the `dividend`
   shape, which is the only cell that discriminated. A payout ratio, cash cover, a growth rate across
   two datasets.
2. **An error of inference on correct figures** — every number right, the conclusion not following
   from them. "ROE of 26.75 per cent means the dividend is safe" conflates profitability with
   coverage, and no field in the pack refutes it.
3. **An error of omission** — a conclusion that ignores a figure in the pack contradicting it.
   Nothing in the answer is false; what is missing is the thing that matters.

All three are harder to score mechanically than a string match, and 2 and 3 may need a reader. That
cost is worth weighing before buying another run: this one cost $9.00 and bought a ceiling effect
and one suggestive cell.
