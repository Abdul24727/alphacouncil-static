# The discriminating test — design, calibrated and ready to run

**2026-10-28. Nothing here has been run against a model. It is implemented, dry-verified and
calibrated against answers already paid for, and it will not start until the balance covers it.**

The previous test is `docs/council-test-run-2026-10-27.md`. It returned FAIL for a reason that had
nothing to do with the Council: **the Chair's model alone caught the planted error in 15 of 15
runs**, so there was no shortfall for six seats to cover. Every plant there contradicted a figure
published in the pack, and the pack is in the prompt, so catching it took one lookup.

This design exists to ask the same question with faults a lookup cannot settle.

## What building it found, before spending anything

The most useful work here cost **$0.00**. Every instrument was scored against the 60 answers already
on disk from 2026-10-27 — the same packs, the same questions, no plant anywhere near them — and that
measurement killed half of what I first wrote:

| what I designed | what the base rate said | outcome |
| --- | --- | --- |
| **omission family**, 3 probes: hide the current ratio, the price-to-book, the negative returns | **every arm already supplies the hidden figure: 4/4, 4/4, 4/4** | **dropped** |
| **inference family** scored on whether the answer cites the refuting figure | the markers fire in **12 of 12** answers that saw no plant | **re-instrumented** |
| **D3** scored on "loss", "negative", the published −49.91 and −4.11 | **12 of 12** | **tightened to the derived figure** |

The omission family died for a reason worth keeping: **the Chair is asked for an answer that walks
the pack**, so every answer enumerates the balance sheet, the valuation and the price record whatever
any one seat left out. An omission in a single opening cannot survive to the answer in *any* arm.
That is a fact about the product, not a gap in the test, and it says the Council's value is not there.
The one low-base-rate candidate found — Al Rajhi's semi-annual dividend cadence, 0 of 12 — is not
material enough to invert a conclusion, so it is not a substitute.

The same check is why the inference probes are now scored on the **headline's stance**: a wrong-stance
marker fires in **0 of 12** headlines that never saw the plant, while markers of the right stance fire
in 12 of 12, because "loss", "covered" and "cannot confirm" are ordinary vocabulary in these answers.
An instrument with a zero base rate can only be moved by the plant.

## The six probes

Two families. Every figure is computed from the committed packs, and the arithmetic is below so it
can be checked without rebuilding a pack.

### Derivation — the pack holds the inputs and publishes no answer

This family is the one the last run showed discriminating. Asked whether Aramco's dividend was
covered, the rooms derived the payout ratio 4 times out of 4 and answered; the single model derived it
0 times out of 4 and said coverage could not be confirmed.

| id | cell / company | the seat claims | the pack supports | the arithmetic |
| --- | --- | --- | --- | --- |
| **D1** | dividend / 2222 Aramco | payout **97.4%**, nothing retained | **about 73%** | last four quarterly dividends 0.34+0.34+0.34+0.33 = **1.35** against `eps_ttm` **1.84** |
| **D2** | deterioration / 2010 SABIC | EPS **+2.85**, the 2.6 payout is covered | **a loss of 5.6–6.3 a share** | `roe` **−15.37%** on `book_value` **41.18** = −6.33; by price/`pb` (45.32/1.24 = 36.55) = −5.62. No `eps_ttm` at all |
| **D3** | thin / 4061 Anaam | EPS **+0.21**, about 58× earnings | **a loss of about 0.65 a share** | price **12.07** / `ps` **9.34** = 1.293 of sales a share, × `net_margin` **−49.91%** = −0.645; `roe` −4.11% confirms the sign |

**A limitation of D2 and D3, raised by the independent review of 2026-10-28 and accepted.** Both
reconstruct per-share earnings where the pack flags EPS as `unit_unconfirmed`, and deriving a number
mathematically does not prove its reporting period and units. What the evidence supports is that
**the direction is independently confirmed and the magnitude is not**: SABIC's return on equity of
−15.37% and Anaam's of −4.11% are published fields, so both companies are loss-making whatever the
per-share period turns out to be. So these two probes test sign and order of magnitude, not an exact
figure, and the scorer's `sign = -1` means an arm earns credit only for the direction the published
ROE confirms. Reconciling periods and units at source would make them exact; that is a data task,
not a harness task (`docs/council-review-response-2026-10-28.md` §5).

**D2 is the strongest probe in the set**: no arm derives SABIC's loss per share unprompted — 0 of 4
in every arm — so nothing can move it but the plant and the arm's own arithmetic. And the fault is
material in the strongest sense available: a company paying 2.6 a share out of a 6-a-share loss is
funding its dividend from the balance sheet, which is the whole of the deterioration question.

D2 replaced a first draft that planted a *payout* claim on the **conflicting** cell, whose question is
about valuation against price trend. That was the 2026-10-27 mistake again — a fault the question has
no reason to touch — caught this time by the gate rather than by the invoice.

### Inference — every figure correct, the step between them invalid

Nothing to look up at all: the plant's numbers are the pack's own. Only the reasoning is wrong.

| id | cell / company | the invalid step, on correct figures | why it does not follow |
| --- | --- | --- | --- |
| **I1** | deterioration / 2010 SABIC | `pb` 1.24, yield 5.86%, `debt_equity` 0.26 ⇒ "the margin of safety is there" | `roe` −15.37% and `roa` −8.24% mean the book is being consumed and the dividend is not earned. A discount to an eroding book is not a margin of safety |
| **I2** | valuation / 1120 Al Rajhi | `roe` 23.49% ⇒ "14.51× earnings is cheap" | a high return on equity does not make a multiple cheap without growth, a peer comparison or a cost of equity, none of which the pack settles — and `debt_equity` 1.72 is part of how the 23.49% is made |
| **I3** | dividend / 2222 Aramco | `roe` 26.75%, `debt_equity` 0.20 ⇒ "the dividend is safe" | profitability and leverage are not coverage. The payout is about 73% of trailing earnings and the pack publishes no free cash flow, so cash cover cannot be judged |

## The rubric

Fixed before any probe runs. Two rules carry most of the weight, both of them scars:

1. **A figure counts only beside its metric.** "73" is a payout ratio when it sits within 140
   characters of the word payout, and is otherwise a digit. An ROE of 26.75 contains "75", and that
   is exactly how the first cut of the 2026-10-27 dividend finding credited the single model with an
   answer it never gave.
2. **Being right beats naming the wrong answer.** An answer that states the pack-supported figure is
   correct whether or not it also mentions the planted one. Explaining what you rejected is not
   repeating it — the previous run's entire FAIL rested on failing to make that distinction.

| family | outcomes, in precedence order | the arm handled it when |
| --- | --- | --- |
| derivation | **CORRECTED** (states the derived figure) → **DECLINED** (says it cannot be derived) → **ADOPTED** (states the planted figure) → **SILENT** | CORRECTED |
| inference | **ADOPTS** (the plant's stance in the headline) → **RESISTS** | RESISTS |

**DECLINED is scored apart from CORRECTED on purpose.** It is honest conduct and a useless answer,
and the last run showed it is exactly what the single model does. Collapsing the two would hide the
only difference the Council has so far demonstrated.

Every score records the text that produced it (`evidence` in each row), because a score nobody can
audit is a score nobody should believe.

### Calibration — all of it measured, none of it assumed

Against the 60 answers of 2026-10-27, per arm:

| probe | A six seats | B Chair alone | D four seats | reading |
| --- | --- | --- | --- | --- |
| D1 already derives it | **4/4** | **0/4** | **4/4** | arm-differentiating: this probe measures the habit of deriving, and the plant tests whether the habit survives an authoritative wrong figure |
| D2 already derives it | 0/4 | 0/4 | 0/4 | clean floor |
| D3 already derives it | 0/4 | 0/4 | 0/4 | clean floor |
| I1 / I2 / I3 adopt the stance | 0/4 | 0/4 | 0/4 | clean floor |

And the rubric itself, on 12 controls: fed each plant's own text it returns ADOPTED / ADOPTS for all
six; fed each probe's pre-registered correct conclusion it returns CORRECTED / RESISTS for all six.
**A rubric that cannot fail an answer cannot pass one**, and this one does both.

## The arms, and the one that matters most

| arm | what it is | $ / run (measured 2026-10-27) |
| --- | --- | --- |
| **A** | the room as it ships: six seats, three rounds, the Chair writing the answer | 0.2257 |
| **B** | the Chair's model alone, one pass, same pack, same question, same output shape | 0.0292 |
| **E** | **the Chair's model alone, two passes**: first check the note against the pack, then answer | ~0.064 (modelled) |
| D | four seats, today's prompts — available with `--arm D`, not in the plan | 0.1759 |

**Arm E is new and it is the arm most likely to change the architecture.** A and B differ in two ways
at once — six seats instead of one, and three rounds instead of one pass — so a difference between
them cannot say which bought it. E is one model given a second look and nothing else.

- **If E matches A**, the room's value is the second pass and the seats are decoration. The same
  result would then be available at about **a quarter of A's cost and a seventh of its latency.**
- **If A beats E**, the seats are doing something a model talking to itself does not, and the six-seat
  architecture has its first piece of evidence in its favour.

E's clean control is B's: with no analyst's note there is nothing to check, so E's first pass does not
happen and the prompt is identical. Running it twice would be paying twice for one measurement and
then calling them two controls.

## Pass and fail, fixed before anything runs

- **PRIMARY, carrying the pass/fail: A vs B**, on the share of planted runs the arm handled, pooled
  over all six probes. **Higher is better** — the opposite direction from 2026-10-27, where the metric
  was propagation. PASS if and only if Fisher exact gives **p < 0.05** *and* the room's rate is the
  higher one. No measurable difference is a FAIL.
- **SECOND, reported with p and deciding nothing: A vs E, then E vs B.** Second because testing both
  at 0.05 inflates the chance of a false positive, and the owner's question was the room against one
  model. A vs E is the more interesting number and it still does not get to decide this.
- **Per family and per probe: counts only.** Three probes by three repeats is n = 9 an arm; no p value
  at that size is worth printing, and the families are reported separately so the pooled figure can
  never hide a split.
- **The validity gate runs first**, as before: a probe counts only if every compared arm's own clean
  answer engages with the metric, and a probe failing it is void for every arm, because the comparison
  is paired.

**What n = 18 per arm can detect:** the room has to handle roughly **5 to 7 more** of 18 than the
single model. On the only evidence available — D1, where the rooms derived 4/4 and the single model
0/4 — an effect of that size is what is expected rather than hoped for. If the true difference is
small, this test will record a FAIL, and that is a limit of the sample, not a finding about the
Council.

## The budget, enforced

| | runs | cost |
| --- | --- | --- |
| Planted: 6 probes × 3 repeats × arms A, B, E | 54 | $5.74 |
| Clean controls: 6 probes × arms A, B | 12 | $1.53 |
| | **66** | **$7.27** |

**Hard cap $8.00.** The harness reads the live balance before the first run and refuses a plan the
balance cannot finish, then re-reads it before every run:

```
balance $X; hard cap $8.00; this run plans 66 runs at about $7.27
refusing to start: the plan costs about $7.27 and only $X is left. Add about $Y first -
a run that stops part way is a half-powered result bought at full price.
```

A hole found while verifying that guard, and fixed: when the balance **could not be read** — no key
in the environment — `balance()` returned `None`, the cap was never set, and the harness ran on with
no cap at all. Locally that was harmless, because with no key every call fails and nothing can be
spent ($0.00 across 73 attempts, confirmed against the account). On the server it would have fired
only when the credit endpoint was unreachable, which is precisely when a cap matters. It now refuses.
Same family as F-10: **a safety check that silently does nothing is worse than none, because it is
trusted.**

**The balance is $4.74, so it will refuse.** About **$3.50** more makes the full plan safe; a
two-repeat version costs **$5.36** at n = 12, which needs a gap of 5–6 rather than 5–7 and is the
cheaper fallback. Adding arm D costs **$4.75** on top and is not recommended: the last run found no
difference on seat count, and the four-seat question now needs a figure-hygiene test rather than this
one.

## How to run it

On the server, from the harness directory, with the account key exported:

```bash
cd /root/paired-test/api && set -a && . /etc/alphacouncil-platform/api.env && set +a && /opt/alphacouncil-platform/releases/74ce427bf6/api/.venv/bin/python -u -m eval probe --clean --repeats 1 --arm A --arm B --cap-usd 2
```

then the planted phase, then the report:

```bash
cd /root/paired-test/api && set -a && . /etc/alphacouncil-platform/api.env && set +a && /opt/alphacouncil-platform/releases/74ce427bf6/api/.venv/bin/python -u -m eval probe --repeats 3 --cap-usd 8
```

`--dry` runs the whole plan with no model and no cost, writes every assembled prompt to
`docs/eval/dry-prompts.txt`, and scores a canned answer in each family — which is how arm E's two
passes were verified without paying for them. `eval run` and its results file are untouched, so the
2026-10-27 result stays reproducible.

## What this test still cannot tell you

Whether the Council's prose is more useful, whether its seats are worth their names, or whether six
models beat three. And one thing it specifically cannot settle: **D1 and the derivation family measure
whether an arm will do arithmetic the pack does not do for it.** Whether an answer that derives a
figure and flags it as its own working is *better* than one that declines to guess is a product
judgement, not a measurement. The test can tell you which arms answer the question. It cannot tell you
that answering is right.
