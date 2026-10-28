# Final test plan — six advisors or four

2026-10-28, revised to the owner's scope. **Nothing paid, nothing pushed, nothing deployed.** This is
the document to read before funding anything, and it carries one conclusion the owner should see
before the cost table: **the comparison as scoped cannot settle the principal question.** It can rule
out a large loss from dropping two seats. It cannot establish that four match six, and no number of
repeats will change that — only more probes will, and probes cost design time rather than credits.

## 1. The comparison, as revised

| arm | what sits in the room | calls / run | what it answers |
| --- | --- | --- | --- |
| **A** | six advisors + Chairman | 20 | the product as it ships today |
| **D** | four advisors + Chairman, **existing prompts** | 14 | does dropping two seats cost anything |
| **B** | Chairman alone, one pass | 1 | does the room beat one model at all |
| ~~E~~ | Chairman alone, second pass | 2 | **deferred**, as instructed |

Verified in the harness rather than assumed:

- arm A's roster is `buffett, lynch, dalio, marks, alwaleed, alrumayyan` — the shipped default.
- arm D's roster is `buffett, lynch, marks, alwaleed` — `eval.run.FOUR_SEATS`, existing prompts.
- the plant seat (`buffett`) sits in **both** rosters, so the same plant reaches both rooms.
- **no advisor recuses on any probe ticker**, so A is six seats and D is four on every single run.
  (`roster.sitting` drops seats tied to the company; checked against 2222, 2010, 4061 and 1120 — none
  drops anyone.) Had one recused, A would silently have been a five-seat room on that ticker.

`eval/probe_report.py`'s ranking is revised to match: **PRIMARY is A vs D**, then A vs B and D vs B
as superiority tests. It was A vs B until today, which answers a different question.

## 2. Identical snapshots, paired questions

**Snapshots are identical by construction, not by care.** Every arm loads the same saved pack from
disk — no live fetch is involved in a run:

| pack | bytes | sha256 (first 16) |
| --- | --- | --- |
| `1120_TADAWUL.en.json` | 26,408 | `55dc3058afb91652` |
| `2010_TADAWUL.en.json` | 24,706 | `38480f32696e24d6` |
| `2222_TADAWUL.en.json` | 23,161 | `057a0c02c35923ac` |
| `4061_TADAWUL.en.json` | 24,296 | `5becbd893527b56f` |
| `4190_TADAWUL.en.json` | 24,635 | `9efe35ce9fa6a698` |

**Questions are paired three ways.** Each probe carries one fixed question from its cell, and the
same (pack, question) pair is handed to every arm. Two cells carry two probes each, so a derivation
and an inference probe run on identical input:

| probe | family | ticker | question |
| --- | --- | --- | --- |
| D1 | derivation | 2222 | Is the dividend covered by earnings, and how safe is it? |
| I3 | inference | 2222 | *(the same question)* |
| D2 | derivation | 2010 | Does the data show the business deteriorating, and how clearly? |
| I1 | inference | 2010 | *(the same question)* |
| D3 | derivation | 4061 | What can and cannot be concluded from the data available? |
| I2 | inference | 1120 | Is the current valuation supported by what the data shows? |

And each probe runs **planted and clean** on that same pair, which is the third pairing and the one
section 4 turns on.

## 3. The four measurements

The owner asked for error detection, correct reasoning, incorrect conclusions and appropriate
uncertainty to be distinguished. The instrument could do **three of the four**; the fourth is now
added. Mapping, in full:

| what it measures | derivation | inference |
| --- | --- | --- |
| **correct reasoning** | `CORRECTED` | `RESISTS` (grounds shown on a metric engaged) |
| **error detection without an answer** | `REJECTED` (named the plant, rejected it, derived nothing) | — |
| **incorrect conclusions** | `ADOPTED` (took the plant), `INCORRECT` (another confidently wrong figure), `MIXED` (right **and** wrong at once) | `ADOPTS` |
| **appropriate uncertainty** | `DECLINED` | **`DECLINED` — added today** |
| no engagement | `SILENT` | `UNRESOLVED` |

**The gap that was there.** In the inference family an arm that correctly said *"the pack publishes
no free cash flow, so cash cover cannot be judged"* scored `UNRESOLVED` — the same cell as one that
simply avoided the question. For a decision about **seat count** that is the dangerous conflation: a
smaller room may well be readier to admit a limit, and that would have been recorded as evasion.

`DECLINED` sits **below** `RESISTS` in the precedence, so nothing that earned `RESISTS` or `ADOPTS`
can move into it — it only ever divides what already fell through to `UNRESOLVED`. It also requires
the probe's **topic**, not merely an uncertainty phrase, which is what keeps round four's three bare
refusals ("Insufficient evidence.", "No conclusion.", "Undetermined.") exactly where round four put
them. An arm earns `DECLINED` by naming what the pack cannot settle, not by saying it cannot tell.

Calibrated as every instrument here is: all 36 inference pairs in the 60 saved answers scored
`RESISTS` before the split and all 36 score `RESISTS` after it. The cell is strictly additive on the
evidence available.

## 4. What this comparison can and cannot detect

This is the part that should decide whether to fund it, and it is why the cost table comes second.

**The primary metric is at a ceiling on half the probes.** Re-scoring the 2026-10-27 answers with
today's instrument, split by plant:

| probe | A (six) | D (four) | B (chair alone) |
| --- | --- | --- | --- |
| D1 | `CORRECTED` 3/3 | `CORRECTED` 3/3 | `DECLINED` 3/3 |
| D2 | `SILENT` 3/3 | `SILENT` 2/3, `DECLINED` 1/3 | `SILENT` 3/3 |
| D3 | `DECLINED` 3/3 | `SILENT` 2/3, `DECLINED` 1/3 | `DECLINED` 3/3 |
| I1 | `RESISTS` 3/3 | `RESISTS` 3/3 | `RESISTS` 3/3 |
| I2 | `RESISTS` 3/3 | `RESISTS` 3/3 | `RESISTS` 3/3 |
| I3 | `RESISTS` 3/3 | `RESISTS` 3/3 | `RESISTS` 3/3 |

On the **clean** controls the inference probes also score `RESISTS` in every arm, and D1 also scores
`CORRECTED` in A and D. A metric already at its ceiling before the plant arrives cannot separate two
arms, and the pooled "handled" line would have shown three arms close together and invited the
reader to call it a finding. So `probe-report` now prints the **pair** — the clean control beside the
planted run, the change between them, and the **wrong-answer rate**, whose clean base rate is zero by
construction (the inference family is scored on the plant's own stance in the headline, which fires
0 of 12 on answers that never saw a plant). Where the change is zero and the wrong-answer rate is
zero, the probe measured nothing, and that is now visible instead of inferred.

**The sample is too small for the question asked.** Fisher's exact, two-sided, p < 0.05, using the
harness's own implementation:

| n per arm | smallest gap it can see |
| --- | --- |
| **18** (3 repeats, the plan below) | **6 of 18 — 33 percentage points** |
| 12 (2 repeats) | 6 of 12 — 50 percentage points |

Dropping two advisors would have to cost about **one answer in three** before this plan could see it.
The prior from 2026-10-27 is a gap of **zero** (A 16/24 handled, D 16/24). So the most likely outcome
of funding this plan is "no measurable difference", and that result **is not evidence that four match
six** — it is a failure to detect at this sample size. The report now says so in those words, because
"PASS" against the primary comparison would have been the worst misreading it could invite.

**More repeats do not fix it; more probes do.** Six probes at nine repeats and eighteen probes at
three repeats both give n = 54 per arm and the same arithmetic power — but the first measures
variance on six questions nine times over, and only the second supports a claim that generalises
past those six items. The binding constraint is the **probe count**, and writing probes costs design
time, not credits:

| probes | n per arm | runs | forecast | reservation | cap | smallest visible gap |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | 18 | 72 | $10.34 | $130.73 | $131 | 33 points |
| 12 | 36 | 144 | $20.68 | $261.47 | $262 | 22 points |
| 18 | 54 | 216 | $31.02 | $392.20 | $393 | 19 points |
| 24 | 72 | 288 | $41.36 | $522.93 | $523 | 17 points |

**And the arms test seat count, not distinctness.** The owner's decision is whether to move to four
advisors *with more distinct investment philosophies*, and arm D uses the **existing** prompts, as
instructed. So this comparison answers "do four of the current seats do the work of six" and says
nothing about whether rewritten, more distinct seats would do better. That needs a fifth arm with new
prompts, and it is not in this plan.

## 5. Cost and conservative reservation

Measured by the dry run, which routes every stand-in call through the same reservation path a paid
call uses, so the published maximum and the enforced reservation are one arithmetic:

| | planted | clean | total runs | n per arm | forecast | reservation | hard cap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A, B, D x 3 + controls** | 54 | 18 | **72** | 18 | **$10.34** | **$126.98** | **$131** |
| A, B, D x 2 + controls | 36 | 18 | 54 | 12 | $7.75 | $95.50 | $99 |
| **Validation pilot:** A, B, D x 1 + controls | 18 | 18 | 36 | 6 | $5.17 | $65.37 | **$66** |

```
cd api; uv run python -m eval probe --dry --arm A --arm B --arm D --repeats 3 \
  --clean-arms A --clean-arms B --clean-arms D --pause 0
```

```
--- planted: arms A,B,D, 3 repeat(s), 54 runs ---
--- clean controls: arms A,B,D, 1 repeat(s), 18 runs ---
plan bound $126.9820 over 72 runs, measured from the reservations taken
  RUN_BOUND predicts $130.7328
  consistent: the published maximum covers this plan and is not padded
```

Both phases run in **one invocation under one `Budget`**, so the cap covers the whole experiment
rather than resetting between phases.

**Why this costs more than the $90 plan quoted yesterday.** Two reasons, both structural:

1. Arm D is a **room** (14 calls) where arm E was a single model (2 calls). Replacing E with D means
   two rooms in the comparison instead of one.
2. **Arm E shared arm B's clean control; arm D cannot.** `probe_report.gate` maps E onto B for
   controls, because with no analyst's note E's first pass does not happen and its prompt is
   identical to B's. D is a different room and needs its own 6 clean runs. Controls are not optional:
   a probe with no clean run for any compared arm is **VOID for every arm**, so skipping D's controls
   would void all six probes rather than save $2.58.

Adding arm E back later costs **+18 runs, +$1.15 forecast, +$11.25 reservation** — it needs no
controls of its own.

## 6. Beta-only regression and smoke test for `llm.py`

`api/app/debate/llm.py` changed on `rebuild` and is **unreleased**. It is the retry path every seat
uses, so it gets its own check before production. What changed, and the risk each carries:

| change | blast radius | risk |
| --- | --- | --- |
| echo clipped in UTF-8 bytes | retries only | **Arabic retries see about half the previous echo** (6,000 bytes rather than 6,000 characters). Less of the broken reply is shown back. |
| quoted parser message clipped to 200 bytes | retries only | negligible; it was unbounded |
| `attempts += 1` moved to the request | attempt accounting | a refused request now costs an attempt |
| `REASONING_REQUIRED` seeded | the **first** chair call per process | sends `{"effort": "low"}` immediately instead of after one 400. End state identical; one refused request removed |

### Offline, already done, no credits

`cd api; uv run pytest -q` → **311 passed**. Includes two tests that drive `llm.ask` itself with a
stand-in transport: Arabic prose plus a 5,000-character parser message (fails on the old code with
`assert 12000 <= 6000`), and a reasoning refusal (fails on the old code with "4 requests left for 3
attempts").

### On beta, needs separate approval — it spends credits

**Precondition:** the OpenRouter balance is **$4.74** and is shared with production, where the
monitor's credit line is already FAILING. The smoke test convenes real-model sessions at roughly
$0.30 each, so budget about **$2**. Top up first or it will fail as `no_credit` — which is at least
the correct failure now.

1. **Deploy to beta only.** Record the sha. Production stays on `74ce427bf6`.
2. **The existing room check, both locales, both modes** — this is the one that exercises every seat
   on a real model and screenshots each stage:
   ```
   cd web; BASE_URL=http://localhost:3201 OUT=../docs/screenshots/llm-smoke-open MODE=open \
     node scripts/check-advisors.mjs
   ```
   Then `MODE=choice` with the paired questions, as in `docs/beta-advisors-2026-10-27.md`.
3. **Arabic explicitly**, because the echo clipping bites hardest there. The check already runs both
   locales; read the Arabic session, do not just count it.
4. **Read the journal for what must be absent:**
   `journalctl -u acp-api --since "1 hour ago" | grep -i "reasoning is mandatory"` → **no hits**.
   That single line is the seeding working. Also grep `no_credit` and `unreachable`.
5. **Acceptance, all of which must hold:**
   - every stage completes in both languages, **zero failed turns**, no `bad_output`;
   - paragraph counts **>= 2** in both languages (the F-8 guard);
   - the session's token and cost totals are recorded (the F-7 guard);
   - no "Reasoning is mandatory" in the log;
   - median cost and duration within the beta range already measured — about $0.29 and 70 s.
6. **Rollback:** redeploy `74ce427bf6`. The app code is byte-identical apart from `llm.py`, so the
   rollback is clean.

Only after that does this go to production, and only on the owner's go-ahead.

## 7. Current offline verification results

| check | result |
| --- | --- |
| `cd api; uv run pytest -q` | **311 passed** |
| every probe's own correct answer scores its family's correct outcome | D1–D3 `CORRECTED`, I1–I3 `RESISTS` |
| no probe's correct answer carries a wrong-figure marker | clean for all six (it was not, before `band_metric`) |
| `MIXED` false positives on the 60 saved answers | **0 of 72** probe-by-answer pairs |
| the uncertainty split's effect on those answers | **none** — 36/36 `RESISTS` before and after |
| dry run, A/B/D x 3 + controls | `consistent`, $126.98 measured against $130.73 predicted |
| dry run, A/B/D x 2 + controls | `consistent`, $95.50 against $98.05 |
| dry run, four arms x 2 (the `RUN_BOUND` re-measure) | `consistent`, $70.24 against $72.87 |
| `probe-report` end to end | renders on a 72-run two-phase dry file: gate, paired table, base rates, revised ranking |
| paid runs to date | **none**; `$0.0000` spent |

## 8. What needs the owner's separate approval

1. **Push `rebuild`** — 16 commits on one computer, including all of this.
2. **Top up OpenRouter** — $4.74, shared with production, monitor already red.
3. **Deploy to beta** for the `llm.py` smoke test (~$2).
4. **Fund the benchmark key** — and *which* plan, given section 4.
5. **Deploy to production** — only after the beta smoke test passes.

### My recommendation

**Do not fund the 72-run plan as a decision-grade experiment**, because it is not one: it would most
likely return "no measurable difference" and that cannot carry the six-versus-four decision.

Instead, in this order:

1. **Push**, and top up. Both are cheap and the first costs nothing.
2. **Fund the $66 validation pilot** (36 runs, $5.17 forecast) — the independent review's own advice
   was a small pilot behind a provider-enforced limit. Its job is to prove the harness, the scoring
   and the cost model against live models, not to answer the question. If the forecast holds and
   nothing fails, every figure above is confirmed by measurement rather than arithmetic.
3. **Meanwhile, expand the probe set offline** — from 6 to about 18. This is the only thing that makes
   the primary question answerable, it costs design time rather than credits, and it is work I can do
   without approval or spend.
4. **Then fund the decision-grade run** at 18 probes (cap $393), which can see a 19-point gap.

If the decision has to be made sooner than that, it should be made on cost and on the distinctness of
the four philosophies — and this benchmark should be asked only to confirm that four seats do not lose
badly, which the $131 plan can do.
