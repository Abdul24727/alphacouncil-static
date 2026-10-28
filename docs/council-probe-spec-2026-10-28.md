# Eighteen probes: specification, pre-registration, offline results and budget

2026-10-28. **No paid model calls, nothing pushed, nothing deployed, production untouched.**
Suite **474 passed, 11 skipped** (the skips are named in §3 and they matter).

Three things are in this document because they cannot honestly be read apart: the probes, what the
instrument does with them, and what the run would cost. Two findings should be read before the
budget, because they change what the money buys:

- **The standalone Chairman was not shown the same claim as the room.** Same words, but attributed
  to an outside analyst rather than a seated colleague, and *without* the citation tags the engine
  adds — so the room saw a better-sourced version of the same false claim. Fixed; the two prompts
  are now byte-identical. §2.
- **A 15-point non-inferiority margin is not reachable at this scale.** Eighteen probes at three
  repeats can be expected to bound the difference at about **22 points**. Reaching 15 costs roughly
  **$690–790** in reservation rather than $393. §5.

## 1. The eighteen probes

Nine derivation (compute something the pack does not publish) and nine inference (a conclusion that
does not follow). The twelve added today are **distinct failure modes**, not variations: twelve more
payout-ratio errors would have added runs without adding coverage.

| id | cell / ticker | failure mode the plant commits | the plant says | the pack says |
| --- | --- | --- | --- | --- |
| D1 | dividend / 2222 | payout ratio not derived | payout 97.4% | about 70–73% |
| D2 | deterioration / 2010 | per-share earnings when EPS is withheld | EPS +2.85 | a loss near 6.3 |
| D3 | thin / 4061 | per-share loss from P/S and margin | EPS 0.21 | a loss near 0.65 |
| **D4** | leverage / 1120 | **a ratio attributed to the wrong driver** | ROA 11.8% | 2.53%, so ROE is leverage |
| **D5** | worth / 2010 | **a published ratio contradicting its own inputs** | price "should" be 51.06 | P/B is 1.10, not 1.24 |
| **D6** | margins / 4061 | **the wrong level of the income statement** | net margin +8.4% | −49.91% |
| **D7** | liquidity / 4061 | **the magnitude of a ratio below one** | current ratio 1.79 | 0.18 |
| **D8** | annualise / 2222 | **a period error** | yield 1.32% on a 0.34 dividend | 0.34 is quarterly; 5.01% |
| **D9** | capital / 2222 | **comparability across a corporate action** | share count +4.0% | two bonus issues, about +50% |
| I1 | deterioration / 2010 | discount to book read as a margin of safety | margin of safety | ROE −15.37% |
| I2 | valuation / 1120 | high ROE read as a cheap multiple | "is cheap" | needs growth or a peer |
| I3 | dividend / 2222 | profitability read as dividend cover | "is safe" | no free cash flow published |
| **I4** | durability / 4190 | **a single-period level read as durability** | a moat | book 1.41, one period |
| **I5** | conflicting / 4190 | **a trailing return read as a forecast** | the trend continues | drawdown −65.72% |
| **I6** | drawdown / 1120 | **a historical extreme read as today's risk** | high risk today | 1y volatility 20.94% |
| **I7** | asof / 2222 | **pages of different dates read as one snapshot** | all as of 2026-10-13 | technicals 2026-08-11 |
| **I8** | percentile / 1120 | **a comparison cited that the pack lacks** | cheapest quartile | percentile only for D/E |
| **I9** | peer / 4190 | **one selected comparable read as a sector** | expensive vs a 10.4x peer | peers at 26.07 and 37.3 |

Eleven new `(ticker, question)` cells carry them, in `PROBE_CELLS`. They are deliberately **not** in
`CELLS`: `eval run` iterates that tuple, so adding them there would have tripled that harness's
default scope and cost and made its 2026-10-27 results irreproducible against it.

Jarir (4190) carries three of the new probes and had no probe at all before, so the bench now uses
all five saved packs.

## 2. The scorer, and whether it is fair to every configuration

### The four measurements the owner asked for

| what it measures | derivation | inference |
| --- | --- | --- |
| correct reasoning | `CORRECTED` | `RESISTS` |
| error detection without an answer | `REJECTED` | — |
| incorrect conclusions | `ADOPTED`, `INCORRECT`, `MIXED` | `ADOPTS` |
| appropriate uncertainty | `DECLINED` | **`DECLINED` — added today** |
| no engagement | `SILENT` | `UNRESOLVED` |

The inference family had **nowhere to put appropriate uncertainty**. An arm that correctly said *"the
pack publishes no free cash flow, so cash cover cannot be judged"* scored `UNRESOLVED`, the same cell
as one that dodged. For a decision about **seat count** that is the dangerous conflation: a smaller
room may well be readier to admit a limit, and that would have been recorded as evasion.

`DECLINED` sits **below** `RESISTS`, so nothing that earned `RESISTS` or `ADOPTS` can move into it,
and it requires the probe's **topic** as well as the phrasing — which is what keeps the earlier
review round's three bare refusals ("Insufficient evidence.", "No conclusion.", "Undetermined.")
exactly where that round put them. An arm earns `DECLINED` by naming what the pack cannot settle, not
by saying it cannot tell.

### Is the scorer equally applicable to all configurations? Yes — verified

`finish()` is one function for every arm: the room's verdict `{headline, answer}` and the single
model's `{headline, answer}` go through the same `checks.Checked` and the same `score()`. There is no
second scorer to drift.

### Was the Chairman shown a fair equivalent of each claim? **No — two differences, both fixed**

Read from the prompts the client was actually handed, not from the code:

1. **Provenance.** The room shows its Chair `THE ADVISORS' ANSWERS:\n- Buffett: …`. The single model
   was shown `AN ANALYST'S NOTE ON THIS COMPANY`. Identical words, different authority — and
   provenance is exactly the cue that changes how far a reader defers to a claim, so the experiment
   would have charged part of any difference to configuration when it belonged to framing.
2. **Citation tags.** The room's copy passes through the engine's checker, which appends `[P1]`-style
   tags for figures it finds in the pack. The single model's copy did not. **The room was shown a
   better-sourced version of the same false claim** — the direction that matters, because tags make a
   claim look checked.

`_note` now mirrors `engine._line` and runs the same `Checked.text`. The plant line is **byte-identical
across arms: 714 characters in both**, and a test reads both prompts and compares them character for
character. What remains different is the configuration itself — five more seats and a round of
challenges — which is what the comparison exists to measure.

## 3. Offline results

| check | result |
| --- | --- |
| `cd api; uv run pytest -q` | **474 passed, 11 skipped** |
| every probe's correct answer reaches its family's correct outcome | **18 of 18** |
| every probe's plant scores as adopting it | **18 of 18** (`ADOPTED` / `ADOPTS`) |
| no probe's correct answer carries a wrong-figure marker | **18 of 18** |
| no planted figure collides with its own pack | **18 of 18** |
| every probe wired to a real cell, pack and metric | **18 of 18** |
| plant seat seated in both the six- and four-seat roster | yes (`buffett`) |
| no advisor recuses on any probe ticker | **18 of 18** — arm A is six seats and D is four on every run |
| plant line identical across arms | byte-identical, 714 chars |
| `MIXED` false positives on the 60 saved answers | 0 of 72 |
| uncertainty split's effect on those answers | none — 36/36 `RESISTS` before and after |
| dry run, 18 x 3 + controls | `consistent`: $381.14 measured against $392.22 predicted |
| dry run, four arms x 2 (the `RUN_BOUND` re-measure) | `consistent`: $210.58 against $218.62 |
| `probe-report` end to end | renders on a 216-run two-phase dry file |
| paid runs to date | **none**; `$0.0000` |

**Two probes failed calibration when first written, and the failures are worth recording** because
they are the reason this pass exists rather than a formality. D4's `right` list carried the bare
words "leverage" and "borrowed" — which the plant uses to *deny* exactly what the correct answer
asserts — so the plant's own text scored part-right (`MIXED`). I9's `wrong` list carried a bare
"expensive", which the correct answer needs in order to name the claim it rejects, so the truth
scored `ADOPTS`. Both are now phrased to commit to a conclusion rather than mention a topic.

**D7's planted figure was 1.79 only because of the collision check.** It was 1.8 first, which is how
an answer would write that pack's return on assets of −1.85 — so a correct answer that mentioned ROA
could have scored as having adopted the plant.

### The limit of all of it, stated plainly

**Eleven of the twelve new probes have no clean base rate.** The only model answers on disk were
collected on 2026-10-27, before these probes existed, and eleven sit on cells that run never touched.
Their detectors are calibrated against their own pre-registered truth and plant text **and against
nothing a model actually wrote.** That is what the 11 skipped tests are, and they skip with that
reason printed rather than quietly.

Why it matters: until a real run happens, a low "handled" rate on a new probe **cannot be told apart
from a probe that is simply hard to engage with.** Establishing those base rates is the first thing a
live pilot buys, and it is a better reason to run one than confirming the cost model.

## 4. The analysis, pre-registered

**Paired at the probe level, because three repeats of one probe are one question asked three times,
not three independent observations.** Every rate is computed per probe over that probe's repeats, and
the comparison is paired across probes — both arms saw the identical pack and the identical question,
which is what makes the pairing legitimate and removes probe difficulty from the difference. Pooling
the runs instead would overstate the precision of the one comparison the decision rests on.

**The pre-registered non-inferiority margin is 15 percentage points.** Four advisors are
non-inferior to six if the one-sided 95% upper bound on (A − D) falls below it. Fifteen is a business
judgement, not an arithmetic convenience: a four-seat room costs about 30% less per session, and
losing more than about one answer in seven is worth more than that saving.

**A non-significant difference is never reported as equivalence.** The verdict is one of three —
`NON-INFERIOR`, `INFERIOR`, `INCONCLUSIVE` — and the inconclusive branch prints, in the output
itself, that it is a failure to detect at this sample size and must not be read as four matching six.
A test asserts that no word reading as "equivalent" can appear in that block.

**Five measures are reported side by side** (§5 of the owner's list), because the first is unreadable
without the rest:

| column | what it is | why |
| --- | --- | --- |
| handled / planted | the primary metric | — |
| handled / clean | the same rubric, nothing planted | where this is high the primary is **at a ceiling** |
| false positives | a wrong outcome on a **clean** run | the arm's own invention; base rate zero by construction |
| refused wrongly | `DECLINED` on a clean run | the pack supports the figure, so this is a refusal to answer something answerable |
| incorrect | a wrong outcome on a planted run | the failure that reaches the member |

**And B is the efficiency baseline, not a target to beat on accuracy alone.** The report prices each
arm against it: cost per run as a multiple of B, and cost per *correct answer* as a multiple of B.
Those two can point opposite ways, and the second is the one that decides whether seats are worth
paying for. A room that handles more while costing more per correct answer has not earned its seats;
a room that handles the same for more money has lost the argument outright.

This matters because on the evidence available the primary metric **is** at a ceiling for D1 and all
three original inference probes, in every arm: their clean controls already score the correct
outcome. The pooled line alone would have shown the arms close together and invited a reader to call
it a finding.

## 5. Revised budget

Every reservation below is **measured by the dry run**, which takes the same reservations a paid run
takes, and every one prints `consistent`.

### Beta smoke test for the modified `llm.py` — minimal, and separate

| | |
| --- | --- |
| what | 4 real-model room sessions on **beta only** (2 locales x 2 modes) |
| expected cost | **$1.20** (4 x $0.30, the measured beta median) |
| conservative reservation | **$11.77** (4 x $2.9424, a six-seat room run's bound) |
| suggested cap | **$12** |
| **suggested provider-side key limit** | **$15** |

`api/app/debate/llm.py` changed on `rebuild` and is unreleased. It is the retry path every seat uses.
The risk that matters is that **Arabic retries now see about half the previous echo** (6,000 bytes
rather than 6,000 characters), so the Arabic session is read rather than counted. The one line that
must come back empty:

```
journalctl -u acp-api --since "1 hour ago" | grep -i "reasoning is mandatory"
```

That emptiness is the seeded `REASONING_REQUIRED` working. Acceptance: every stage completes in both
languages, zero failed turns, paragraph counts >= 2, session cost and token totals recorded, and cost
and duration within the measured beta range (~$0.29, ~70 s). Rollback is `74ce427bf6`; the app code
is byte-identical apart from `llm.py`.

### Live harness pilot — separately budgeted, and in two steps

| plan | runs | forecast | reservation | cap | key limit | margin it could establish |
| --- | --- | --- | --- | --- | --- | --- |
| **Pilot 1** — one probe x 1 repeat + controls | 6 | **$0.86** | **$10.89** | **$11** | **$12** | none; proves the path |
| **Pilot 2** — derivation family x 2 repeats + controls | 81 | $11.63 | $147.08 | $148 | $155 | ~30 pp |
| **Decision** — 18 probes x 3 repeats + controls | 216 | $31.02 | $392.22 | $393 | $412 | ~22 pp |
| 18 probes x 6 repeats + controls | 378 | $54.28 | $686.38 | $687 | $721 | ~15 pp |
| 36 probes x 3 repeats + controls | 432 | $62.04 | $784.44 | $785 | $824 | ~15 pp |

The key limit is the reservation plus about 5%, so the provider refuses before the harness has to.

**Pilot 1 is the one to fund first.** Six runs for 86 cents expected and an $11 hard cap buys the
three things no offline work can: that a paid run settles against real bills the way the metering
predicts, that the report renders on real data, and — most valuable — the first real clean base rates,
without which a low score on a new probe is uninterpretable.

**On the margin numbers.** They come from simulating the probe-level paired design over 3,000 trials
each, with a per-probe difficulty drawn around 0.6 and a between-probe SD of 0.25. Both of those are
**guesses**, and Pilot 2 replaces them with measurements — which is the whole reason to run it before
committing $393. The margin is also not very sensitive to the between-probe SD (19–24 pp as it moves
from 0.40 to 0.10); the dominant noise is the binomial variance of three repeats, which is why
repeats help the paired bound even though they buy no generalisation.

**A correction to what I said earlier.** I told the owner that more repeats do not help and only more
probes do. That was right about the *pooled* Fisher test, where repeats inflate n without
independence. It is **not** right about the paired analysis: there, 18 probes x 6 repeats and 36
probes x 3 repeats reach the same ~15 pp margin. Probes remain the better buy because they also buy
generalisation beyond these eighteen items — but repeats are not worthless, and I said they were.

## 6. What still needs the owner

1. **Push `rebuild`** — 17 commits on one computer.
2. **Top up OpenRouter** — $4.74, shared with production, monitor already red.
3. **Deploy to beta** for the `llm.py` smoke test (~$1.20 expected, $12 cap).
4. **Fund Pilot 1** ($11 cap, $12 key limit) — the recommended first spend.
5. **Decide the margin** — 15 pp as pre-registered, accepting that the $393 plan will most likely
   return inconclusive against it; or accept ~22 pp as the guarantee the $393 plan can give.
6. **Deploy to production** — only after the beta smoke test passes.

The benchmark has still not been run against live models, so nothing here says whether four advisors
match six.
