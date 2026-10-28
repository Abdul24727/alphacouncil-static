# Provenance — exactly which code produced which result

Item 7 of the request: the commit the benchmark used, and every subsequent change to the evaluation
code. The repository is a private git repository on branch `rebuild`; short SHAs below are from it.

## The engine

**The engine in this package is byte-identical to the engine the benchmark ran.** The release the
benchmark ran on was `d5c28fb48b` (commit `d5c28fb`), and:

```
$ git diff --stat d5c28fb..HEAD -- api/app
(empty)
```

Nothing in `api/app` has changed since. So `code/api/app/debate/` is the code that produced every
answer in `results/results.jsonl`, not a later version of it.

## Where each phase ran

The benchmark ran on the **beta** host, never on production, and never from a release directory it
could modify.

| phase | runs | where | app code | eval code |
| --- | --- | --- | --- | --- |
| Clean controls | 15 | release directory `.../releases/d5c28fb48b` | `d5c28fb` | **`d5c28fb`** (the release's own) |
| Planted | 45 | a separate directory, a copy of that release's `api` tree | `d5c28fb` | **`bfc9567`** — `questions.py`, `run.py` and `gate.py` replaced |
| Gate decision and aggregate report | — | locally | — | `bfc9567` (unchanged in `report.py` through to `HEAD`) |

The planted phase deliberately ran from a copy rather than from the release, so **no release was
modified and no service was restarted** to run a bench whose code no member can reach.

## What changed in the evaluation code, and when

### During the benchmark: `d5c28fb` → `bfc9567`

Two commits, both made after the clean controls and before the planted phase, because the clean
controls are what exposed the need for them:

```
f0be8b3  The validity gate, written before there was a result to tune it to
bfc9567  One planted error per cell, matched to the metric that cell asks about

 api/eval/gate.py      |  64 ++++++++++++++
 api/eval/questions.py | 135 ++++++++++++++++++++++++++++-------
 api/eval/report.py    |  41 ++++++++--
 api/eval/run.py       |  20 ++++----
```

- **`f0be8b3`** added the validity gate. The design pre-registered one; the code had none. It was
  written before any planted run existed, so it could not be tuned to a result.
- **`bfc9567`** replaced one planted error used on all five cells with one per cell, matched to the
  metric that cell's question is about. The gate's first pass voided four of five cases, which is
  what showed the single plant was measuring whether a room notices an *irrelevant* wrong figure.
  `run.py`'s changes are the plumbing for that (`score`, `with_plant` and the challenge check take
  the cell); `report.py` gained the gate and the ungated table printed beside it.

**This means the 15 clean controls were scored by `d5c28fb`'s code and the 45 planted runs by
`bfc9567`'s.** It does not affect the comparison, because the clean controls carry no plant and the
only field the change touches is the planted-figure test. One consequence to be aware of when reading
the raw rows: **`plant_in_answer` on a clean row was computed against the old single figure "97.4"
and means nothing.** The gate reads `answer`, not that flag.

### After the benchmark: `bfc9567` → `HEAD`

```
f2784b5  The method of the paired test, written before its result        (docs only)
74ce427  The paired test: FAIL on the pre-registered metric, ceiling effect in fact
9dcc4a1  F-10 and F-11 live on production, and the monitor now reports the credit
71228f8  The discriminating test, calibrated against answers already paid for

 api/eval/probe_report.py | 170 +++++++++++++++  (new)
 api/eval/probe_run.py    | 330 +++++++++++++++++++  (new)
 api/eval/probes.py       | 301 ++++++++++++++++++  (new)
 api/eval/score.py        | 112 +++++++++++  (new)
 api/eval/run.py          |  25 +++  (two new subcommands only)
```

**Every change is additive.** `71228f8` adds the 2026-10-28 replacement test as four new modules
reached by two new subcommands (`eval probe`, `eval probe-report`). It does not touch `eval run`,
`questions.py`, `gate.py` or `report.py`, specifically so the 2026-10-27 result stays reproducible
from the code in this package. `74ce427` changed `results.jsonl` (it is where the 60 rows were
committed) and documentation; `9dcc4a1` is the production release of F-10 and F-11 plus docs.

The releases named in these commits — `74ce427bf6` on production and beta since 2026-10-27 — differ
from the benchmark's `d5c28fb48b` only in `api/eval`, `PROJECT.md` and documentation. The engine is
the same code either way, which is the diff shown at the top of this file.

## Models

| | |
| --- | --- |
| All six advisor seats | `deepseek/deepseek-v4-pro` |
| The Chair | `anthropic/claude-sonnet-5.5` |
| Arm B and arm E (single model) | the Chair's model, `anthropic/claude-sonnet-5.5` |
| Arm C (exploratory file only) | seats spread over `deepseek/deepseek-v4-pro`, `anthropic/claude-sonnet-5.5`, `openai/gpt-5.2` |
| Provider | OpenRouter, for every call |

Defaults are in `code/api/app/settings.py` lines 68–71.

## Spend

| | |
| --- | --- |
| Clean controls, 15 runs | $2.4440 |
| Planted, 45 runs | $6.5578 |
| **The paired test, 60 runs, 0 failed** | **$9.0019** |
| The exploratory bench, 15 runs (`exploratory-2026-10-27.jsonl`) | $3.4075 |
| The aborted run recovered into `planted-partial.jsonl`, 9 real rows of 12 | $1.3727 |
| Building and calibrating the 2026-10-28 replacement test | **$0.00** — every instrument was scored against answers already paid for |

Figures are OpenRouter's own per-call costs as recorded in each row, and every one above is the sum
of the rows shipped in `results/`, so they can be recomputed.

One discrepancy to note rather than quietly reconcile: the aborted run was reported at the time as
**$1.23**, measured as the fall in the account balance. The rows sum to **$1.3727**. The row figures
are the per-call costs the provider returned; the balance reading was taken immediately after the
process was killed, and the provider's account usage lags. Where the two disagree, the row sum is the
auditable number and is the one used here.
