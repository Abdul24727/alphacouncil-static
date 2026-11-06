# The $66 validation pilot, 2026-11-06

**Asked for by the owner in chat** (2026-11-06): "Retire D1/D3/D6, run it".

**What it was for:** the test plan says the pilot exists to prove the harness, the scoring and the cost model
against live models. It was not meant to answer six seats against four, and it does not
(`docs/council-test-plan-final-2026-10-28.md` §5).

**The record:**
- `docs/eval/probe-results.jsonl`: all 36 runs, the harness's own record;
- `docs/eval/pilot-2026-11-06/pilot.log`: the run's log;
- `docs/eval/pilot-2026-11-06/pilot-report.txt`: the full `eval probe-report` output.

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
| OpenRouter balance | $13.47 before, **$7.83 after** |
| Validity gate | 6 of 6 probes count |

## What the pilot proves, which is its job

- **The harness ran end to end on live models**, both phases under one budget, with no error and no retry storm.
- **The scorer produced every outcome class** on live answers:
  - ADOPTED, CORRECTED, DECLINED, INCORRECT (with its out-of-band reason), MIXED and SILENT for derivation;
  - RESISTS for inference.
- **The cost model held:** 9 % over its forecast, from history measured on 2026-10-27.
- **The room's own instruments read live numbers** for both rooms, and UNAVAILABLE, not 0, for the single model, as
  designed.

## What it measured (descriptive; n = 6 probes, one repeat)

| Arm | handled, planted | handled, clean | false pos | refused wrongly | incorrect | $ / run | × B |
|---|---|---|---|---|---|---|---|
| A, six + Chair | 4/6 | 4/6 | 0/6 | 0/6 | 1/6 | 0.2453 | 7.5× |
| B, one model | 4/6 | 4/6 | 0/6 | 0/6 | 2/6 | 0.0328 | 1.0× |
| D, four + Chair | 4/6 | 4/6 | 0/6 | 1/6 | 1/6 | 0.1821 | 5.6× |

- **Inference is at a ceiling.** I1–I3 score RESISTS in every arm, planted and clean, so they cannot separate the
  arms. The report predicted this and says to read `incorrect` there instead.
- **Derivation:** each arm handled 1 of 3. A and D handled D4; B missed D4 and handled D5.
  - **D2:** A and D declined, and B gave an out-of-band figure.
  - **D5:** A took the plant's figure (ADOPTED), B corrected it, and D was MIXED.
- **D2 and D5's clean controls are SILENT** (once DECLINED) in every arm. With nothing planted, the question does not
  draw the calculation out, so "handled, clean" is 0 there by design and their planted results are read on
  `incorrect`.
  - **The inputs are still there:** checked on the server against today's packs, every banded probe's registered
    inputs are present (D1–D6, D8). That check covers whether an input exists, not its value: D1, D3 and D6 were
    retired because their values moved.
- **Six against four:** the paired difference is 0.0 points, and the report prints "NON-INFERIOR" against the
  15-point margin. On six probes, one repeat and three of them at a ceiling, that line carries no weight. The report's
  own power table needs about 18 probes × 6 repeats to see 15 points.
- **Priority Two, mandate coverage:**
  - **Openings citing none of the seat's own datasets:** A 42 of 72, D 26 of 48.
  - **Datasets owned by a seat and never cited by it:**
    - in A: P2, P5, P6, P7, P8, P9;
    - in D: P2, P7, P8, P9.

  On these packs, more than half of the opening statements did not draw on the evidence the seat is answerable
  for. The pilot is too small to say more than that.
- **Priority Three:** 0 rulings with no grounds in either room.

## What it found that changes the next run

1. **The published hard bound is stale.** Per-run reservations measured on live calls are A $3.80, D $2.65 and B
   $0.32. The dry run reserved A $3.02 and D $2.26, and `RUN_BOUND` holds $2.94, $2.19 and $0.31. Live calls retry,
   and the repaired packs are larger.
   - **The effect:** the $393 decision-grade quotation is out of date. `RUN_BOUND` has to be re-measured from these
     live runs before any figure is put to the owner.
   - **The cap still did its job.** Spending is checked per call, which is why $81 of reservations added up over 432
     calls while $5.64 was spent.
2. **The inference probes cannot separate the arms on the planted metric.** The decision-grade run should read
   them on `incorrect` and the paired block, as the report says, or replace them.
3. **The probe set is 6 derivation and 9 inference since the retirement.** The decision-grade run should restore
   the balance or say why not (recorded in `test_there_are_eighteen_probes_evenly_split`).
4. **The account cannot fund a decision-grade run:** $7.83 is left, and the live site draws on the same account.

## What is the owner's

- Top up OpenRouter before anything else: the live Copilot, the advisors' room and the nightly news step share the
  $7.83.
- Whether to fund the decision-grade run, and at what cap once `RUN_BOUND` is re-measured.
- What to do about Priority Two's coverage finding: re-prompt the seats, or leave it and measure it properly first.
