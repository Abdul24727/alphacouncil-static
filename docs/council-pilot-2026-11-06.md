# The $66 validation pilot, 2026-11-06

**Asked for by the owner in chat** (2026-11-06): "Retire D1/D3/D6, run it".

**What it was for:** the test plan says the pilot exists to prove the harness, the scoring and the cost model
against live models. It was not meant to answer six seats against four, and it does not
(`docs/council-test-plan-final-2026-10-28.md` §5).

*Corrected after review 39:* the first version of this report read two scorer defects as results, misread the
coverage measure, and quoted median reservations where the maxima are the bound. All are corrected below, and the
figures as first reported are kept beside the corrected ones.

**The record:**
- `docs/eval/probe-results.jsonl`: all 36 runs, **as run**, unaltered;
- `docs/eval/pilot-2026-11-06/probe-results-rescored.jsonl`: the same 36 answers re-scored by the fixed scorer.
  - **Changed rows:** each keeps `outcome_as_run` and `evidence_as_run`.
  - **Every row:** says how it was re-scored. No model was called.
- `docs/eval/pilot-2026-11-06/pilot.log`: the run's log;
- `pilot-report.txt`: the report as printed at the time;
- `pilot-report-rescored.txt`: the report over the re-scored record, with the corrected coverage section.

## What ran

- **Code:** `rebuild` `f7b7de3`, staged on the server at `/root/pilot-20261106`. It ran with beta's release environment
  (`b5655a5064`'s venv, `/etc/alphacouncil-platform/api.env`): the same OpenRouter account and models as production.
- **Run as:** a server-side job (`acp-pilot-20261106`), so a dropped connection could not cut it short.
- **The command:**
  `eval probe --arm A --arm B --arm D --repeats 1 --clean-arms A --clean-arms B --clean-arms D --only D2,D4,D5,I1,I2,I3 --cap-usd 66`.
- **Arms:**
  - A: the six advisors and the Chair;
  - B: the Chair's model alone, one pass;
  - D: four advisors and the Chair.
- **Probes:** the first design's three derivation and three inference probes.
  - D1 and D3 were retired before the run, so D4 and D5 replaced them. They are the next derivation probes in
    registration order.
  - I1, I2 and I3 are unchanged.
- **Runs:** one planted run and one clean control per arm and probe, 36 in all.

## Accounted for

| | |
|---|---|
| Runs planned / finished / failed / stopped | 36 / 36 / 0 / 0 |
| Model calls | 432 (A 246, D 174, B 12) |
| **Spent** | **$5.64** (A $3.01, D $2.24, B $0.38); the forecast was $5.17, so 9 % over |
| Cap | $66, enforced per call; never approached |
| OpenRouter balance | $13.47 before, **$7.83 after** (read from OpenRouter's credits endpoint) |
| Validity gate | 6 of 6 probes count |

## What the pilot proves, which is its job

- **The harness ran end to end on live models**, both phases under one budget, with no error and no retry storm.
- **The cost model held:** 9 % over its forecast, from history measured on 2026-10-27.
- **The room's own instruments read live numbers** for both rooms, and UNAVAILABLE, not 0, for the single model, as
  designed.
- **The scoring was exercised only in part, and two defects showed up:**
  - **Seen live:**
    - derivation answers scored ADOPTED, CORRECTED, DECLINED, MIXED and SILENT;
    - INCORRECT once as run, and that one was a defect (below);
    - inference answers scored RESISTS only.
  - **Never seen live:** REJECTED for derivation, and ADOPTS, DECLINED and UNRESOLVED for inference. The pilot
    validates none of those paths.
  - **Two defects, found by review 39 and fixed** in `eval/score.py`, with regression tests in
    `tests/test_eval_score.py`:
    1. **Arm B on D2** named a dividend, "from 2.25 SAR per share … to 1.1 SAR per share". The per-share
       **earnings** band bound that dividend through the unit "per share" alone and scored INCORRECT.
       - **The fix:** a unit is not a metric. A figure bound only by the unit belongs to the per-share quantity
         named nearest to it: in its own clause (before it, then after it), else in the clauses before it in the
         same sentence, and never in a later clause (`_quantity_kind`). It is judged against the band unless that
         quantity is another one: dividend, distribution, DPS, book value or payout.
         - **Still judged:** "1.1 SAR per share is the earnings figure" (review 40).
         - **Not judged:** "…to 1.1 SAR per share, while earnings cannot be derived" (review 41).
       - **Re-scored:** DECLINED. The answer said the earnings question could not be settled.
    2. **Arm B on D4** derived the pack's 2.53 and ruled against "Buffett's claim that the return on assets is
       11.8 per cent". The attribution list lacked the noun form, so 11.8 counted as asserted and the run read
       MIXED.
       - **The fix:** add the possessive "'s claim" (`_attributed`). A bare "claim that" also matched the answer's
         own voice.
         - **What makes the figure the answer's own again:** a credit that the answer endorses. That means an
           un-negated agreeing word in the clause before ("I agree with Buffett's claim…"), matched as whole words
           so "disagree" and "incorrectly" do not count, or a verdict after the figure ("…is correct").
         - **What does not:** a verb of agreeing after the figure, whose subject is usually the seat withdrawing
           ("…then accepted that…").
         - **Read where:** a verdict is read in the figure's own clause, so "…whereas the pack's 2.53 is correct"
           endorses 2.53, not 11.8. The answer's first-person agreement ("…, which I endorse") is read to the end
           of the sentence.
         - **Found by:** reviews 40–42 and a calibration test on the 2026-10-27 answers.
       - **Re-scored:** CORRECTED, with the figure kept in evidence as attributed.
    3. **Clause boundaries** (review 42): a decimal point or a thousands comma between digits no longer counts as
       one (`_is_boundary`). "2.25" used to split its own clause.
  - **Re-scoring all 36 answers moves exactly the two outcomes above.** A test pins that, so any later rule change
    that moves another live answer has to say so.
  - **All 36 answers were then audited by hand,** successes included, against each probe's registered truth
    (`docs/eval/pilot-2026-11-06/audit.md`: the scorer's outcome, the human verdict, an excerpt and a note for
    every one).
    - **Agreement:** the human reading agrees with the re-scored outcome on 31 of 36 (review 44 corrected this from
      32).
    - **The other 5 are all on D5.** Its registered markers take the right answer as 1.10, 1.1 or five phrases, and
      the plant as 51.06 or 51.1. They cannot see an answer that states the pack's inconsistent figures **agree**,
      and cannot tell a 1.10 the room overruled from one it asserted.
      - **Every clean D5 answer** said the figures agree. A and B said so in words: B's headline says "disagree",
        but its body rules that they agree. D derived 1.24 from price and book.
      - **Both rooms' planted answers** said so too, while rejecting the plant's discount. The scorer read them as
        ADOPTED (A) and MIXED (D). D's MIXED came from markers firing on Lynch's 1.10, which the room overruled.
    - **What happens to them:** the scorer is left as registered, and the human verdicts are what this report
      uses.

## What it measured (descriptive; n = 6 probes, one repeat; the hand audit)

| Arm | handled, planted | handled, clean | wrong answer, planted | false positive, clean | refused wrongly | $ / run | × B per handled |
|---|---|---|---|---|---|---|---|
| A, six + Chair | 4/6 | 4/6 | 1/6 | 1/6 | 0/6 | 0.2453 | 9.4× |
| B, one model | 5/6 | 4/6 | 0/6 | 1/6 | 0/6 | 0.0328 | 1.0× |
| D, four + Chair | 4/6 | 4/6 | 1/6 | 1/6 | 1/6 | 0.1821 | 6.9× |

**How this differs from the scorer:**
- **The scorer as run** gave B 4/6 handled and 2/6 incorrect: the two defects above.
- **The re-scored figures** match this table on handled. They miss all three clean false positives and label both
  rooms' planted D5 answers wrongly: ADOPTED (A) and MIXED (D), where each rejects the plant and states a false
  consistency (`audit.md`).

**Inference is at a ceiling.** I1–I3 resist in every arm, planted and clean, so they cannot separate the arms. B's
two I2 answers are borderline ("supported by returns"), but neither calls the stock cheap.

**Derivation, planted (the audit's verdicts):**

| Probe | A, six + Chair | B, one model | D, four + Chair |
|---|---|---|---|
| D2 | DECLINED | DECLINED | DECLINED |
| D4 | CORRECTED | CORRECTED | CORRECTED |
| D5 | rejects the plant, but says the figures are consistent | CORRECTED: "those three figures do not agree" | rejects the plant, but says the figures agree; overruled Lynch's right 1.10 |

**D5 is the probe that separates answers, and it runs against the rooms.** The pack's price (45.32), book value
(41.18) and price-to-book (1.24) do not agree: 45.32 ÷ 41.18 is 1.10.
- **No arm saw it unprompted.** In the clean controls, A, B and D each stated or derived that the figures agree.
- **With the plant in front of it, only the single model** said the three figures do not agree. Both rooms missed
  it.

**The other derivation probes:**
- **D2** is declined in every arm.
- **D4** is corrected in every arm, planted and clean.
- **D2's clean controls** are silent in A and B, and D refused a derivation the pack supports.

**The inputs are still there:** checked on the server against today's packs, every banded probe's registered inputs
are present (D1–D6, D8). That check covers whether an input exists, not its value: D1, D3 and D6 were retired because
their values moved.

**Six against four:** the paired difference is 0.0 points, and the report prints "NON-INFERIOR" against the
15-point margin. On six probes, one repeat and three of them at a ceiling, that line carries no weight. The
report's own power table needs about 18 probes × 6 repeats to see 15 points.

**A room against one model:** B handled 5 of 6 planted runs against the rooms' 4 of 6, with p = 1.0 in both
comparisons. At this size nothing separates them on accuracy. The cost per handled answer does: 9.4× B's for six
seats, 6.9× for four.

**Priority Two, mandate coverage,** in openings the models wrote. The planted seat's scripted opening is left out,
as the report now does.

| | six + Chair | four + Chair |
|---|---|---|
| Openings | 66 | 42 |
| Missing at least one of the seat's own datasets | 36 | 20 |
| Citing none of them | **1** | **1** |
| Datasets left uncited at least once | P5, P6, P7, P8, P9 | P7, P8, P9 |

- **As first reported:** "42 of 72 / 26 of 48 openings citing none". That was wrong twice over.
  - The engine's flag lists every owned dataset left uncited, so those counts were openings missing **one or
    more**.
  - They included the six scripted plant openings in each room.
- **The corrected reading:** a seat almost always draws on some of its evidence, and often not all of it.

**Priority Three:** 0 rulings with no grounds in either room.

## What it found that changes the next run

1. **The published hard bound is stale.** Live calls retry, and the repaired packs are larger.

   | Per-run reservation | A | D | B |
   |---|---|---|---|
   | Live, maximum (the bound) | **$3.97** | **$2.79** | **$0.33** |
   | Live, median | $3.81 | $2.66 | $0.32 |
   | Dry run | $3.02 | $2.26 | $0.32 |
   | `RUN_BOUND` | $2.94 | $2.19 | $0.31 |

   - **The effect:** the $393 decision-grade quotation is out of date. `RUN_BOUND` has to be re-measured from these
     maxima before any figure is put to the owner.
   - **Done the same day (review 45):** `RUN_BOUND` is now A 3.9714, D 2.7929 and B 0.3304, the larger of the live
     and dry maxima, rounded up. `RUN_COST` is the pilot's live means: A 0.2511, D 0.1870, B 0.0318.
     - **The decision-grade plan,** dry-run in full on the server: 180 runs, $331.30 reserved, and the harness
       calls the new bound "loose by 28%", because a dry run cannot see live retries.
     - **The quote:** forecast **$28.19**, cap **$426**. The dry record is `docs/eval/dry-probe-results.jsonl`.
   - **The cap still did its job.** Spending is checked per call, which is why $81.20 of reservations added up over
     432 calls while $5.64 was spent.
2. **The inference probes cannot separate the arms on the planted metric.** The decision-grade run should read them
   on `incorrect` and the paired block, or replace them. Their ADOPTS, DECLINED and UNRESOLVED paths have never been
   seen live.
3. **The probe set is 6 derivation and 9 inference since the retirement.** The decision-grade run should restore the
   balance or say why not (recorded in `test_there_are_eighteen_probes_evenly_split`).
4. **The account cannot fund a decision-grade run:** $7.83 is left, and the live site draws on the same account.
5. **The scorer reads words, so it will always have another constructed counterexample.** Reviews 39–42 found
   five rounds of them, each now a test.
   - **What makes a result trustworthy:** the audit of every answer, done here for all 36 (`audit.md`). The
     decision-grade run is reported only after the same audit:
     - **every** answer, planted and clean, successes included, because a false success inflates the result just
       as surely (review 43);
     - each with the human verdict against the registered truth, a supporting excerpt, and the scorer's outcome
       beside it;
     - disagreements resolved before the result is reported. Where a disagreement is a scorer defect it becomes a
       test, as these did. Where it is a gap in a probe's registered markers, like D5's here, the human verdict
       stands and the gap is recorded.
   - **The cost of that:** about 180 answers to read for a 15-probe run. It is the price of a result that can be
     trusted.
6. **D5's registered markers need a decision before the next run.** They cannot see a stated "the figures agree",
   which is the wrong answer every arm gave unprompted. Extending them now would be choosing markers after reading
   answers. So it is the owner's call: extend them, or keep D5 as registered and rely on the audit.

## What is the owner's

- Top up OpenRouter before anything else: the live Copilot, the advisors' room and the nightly news step share the
  $7.83.
- Whether to fund the decision-grade run, and at what cap once `RUN_BOUND` is re-measured.
