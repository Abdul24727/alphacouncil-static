# Fifth independent review round — four corrections, all four made

2026-10-28. Nothing paid, nothing deployed, no change to production data. Suite **292**, up from 279.

The review's own summary is the right one: the remaining defects were specific and testable, and the
architecture is no longer the problem. It asked for three targeted corrections plus one removal, and
preferred a small pilot behind a provider-enforced spending limit over another round of
infrastructure. All four are done. The pilot is still the owner's to authorise, and the figure it has
to be authorised against **moved**, which is the most consequential thing in this document.

## 1. The retry echo, bounded in UTF-8 bytes

**Asked:** restrict the retry-echo size in UTF-8 bytes, bound the correction text, and test both
against the real model-call path.

`llm.ask` echoed the unusable reply as `text[:6_000]` — six thousand **characters** — while
`eval.budget` spent that same 6,000 as **bytes**, because `token_bound` is a byte bound (a byte-level
BPE tokenizer cannot emit more tokens than the input has bytes). Arabic is about two bytes a
character before the tokenizer sees it, and Arabic is the product's second language, so a retry
could carry roughly **twice** the accounted growth. The behavioural test measures it exactly: on the
old code it fails with `assert 12000 <= 6000`. A bound that ordinary text in your own product beats
is not a bound.

The correction sentence was worse in kind, if not in size: it interpolated the parser's own message
(`f"That reply could not be used ({exc})"`) with **no limit at all**, so `RETRY_INSTRUCTION_CHARS =
400` was an assumption about how a ValueError happens to word itself.

**Done.** `llm._clip_bytes` truncates in UTF-8 bytes without splitting a character, and both limits
are named constants on both sides: `RETRY_ECHO_BYTES = 6_000` and `RETRY_PROBLEM_BYTES = 200`. The
instruction is now measured rather than rounded — the longest fixed wording is **172 bytes**, plus
200 clipped, so **372** against an accounted 400. `test_the_retry_limits_hold_on_the_real_call_path`
drives `llm.ask` itself with Arabic prose and a 5,000-character parser message, and reads the
messages the client was actually handed; the pinning test now compares against `llm`'s own constants
instead of asserting a literal.

## 2. The fourth request, removed rather than priced

**Asked:** remove the fourth-request issue by enforcing the configured attempt count directly.

Accepted without reservation — this was the right criticism of round four, which **priced** a
request it should have prevented. `llm.ask` retried a 400 "reasoning is mandatory" with `continue`
placed *before* `attempts += 1`, so one call could issue `ATTEMPTS + 1` requests, and
`eval.budget.EXTRA_REQUESTS = 1` paid for it.

**Done.** The counter increments as the request is issued, so every request the loop issues is
counted and the configured attempt count bounds them directly.
`test_a_reasoning_refusal_cannot_buy_a_fourth_request` drives the real path and fails on the old
code with **"4 requests left for 3 attempts"**. `EXTRA_REQUESTS` is now **0**.

The bound fell as a result, and this is the one direction in which that is legitimate: the request it
was paying for cannot happen any more.

| | round four | now |
| --- | --- | --- |
| one attempt, 2,000 prompt bytes | $0.069024 | **$0.034512** |
| a real arm-B call (21,971 bytes, 3 attempts) | $0.3843 — 13x its bill | **$0.297858** — 10x |
| worst run: arm A / D / B / E | 3.7805 / 2.8145 / 0.4066 / 0.8079 | **2.9423 / 2.1903 / 0.3146 / 0.6252** |

`RUN_BOUND` was **re-measured**, not scaled, by the command its own comment names.

### The regression this would have introduced, closed at the cause

Counting every request has one consequence worth stating rather than discovering later.
`debate_reasoning` is **False by default**, so `_reasoning` asks for reasoning OFF, and the chair's
model refuses exactly that with the 400 — once per process, until `REASONING_REQUIRED` learns it at
runtime. With every issued request now counted, that refused request would have left **the chair's
first call of each process with two attempts at usable JSON instead of three**, on the longest
answers in the room. That is the shape of F-1.

So the refusal is removed rather than paid for: `REASONING_REQUIRED` is **seeded** with the models
known to refuse, making the steady state the start state. The runtime path still works and is still
the authority — this is only a head start, and an entry comes out if the provider starts honouring
`{"enabled": False}`. `test_the_chairs_model_spends_no_request_learning_it_needs_reasoning` asserts
no request is spent being refused and that all three attempts reach the model.

**This is a change to live application code** (`api/app/debate/llm.py`), on `rebuild` and
**unreleased**. It needs the owner's go-ahead like any release, and it should go out with the room
exercised once on beta, because it touches the retry path every seat uses.

## 3. Right and wrong in the same answer

**Asked:** fix scoring for answers that simultaneously assert correct and incorrect financial
conclusions, with a regression test proving the distinction.

`score` read `right` first and returned `CORRECTED` **immediately**, so an answer holding the
pack-supported figure and a wrong one scored a clean success with the wrong figure sitting in its
evidence, unread. That is the arm's worst realistic failure, not its best outcome: the member reads
both numbers, and the correct one beside the planted one lends it authority rather than removing it.

**Done.** A new **`MIXED`** outcome, ranked above `CORRECTED` in the precedence and deliberately
absent from `CORRECT`, so the primary metric counts it against the arm. It fires on **0 of the 72
probe-by-answer pairs** in the 60 answers already on disk, while the constructed both-conclusions
cases score `MIXED` — the calibration this project applies to every instrument before trusting it.

**Reading the outcome exposed two defects the old precedence had been hiding**, and both had to be
fixed with it. This is the part worth keeping:

- **A band bound to the topic rather than to its quantity.** D2's `metric` carries `"book"`, because
  rebuilding earnings from book value is the plant's own route, while its `band` is the range for
  per-share **earnings**. So the pack's own `book value of 41.18 a share` — a figure the answer is
  entitled to quote — sat beside an earnings band and scored a false `incorrect`. It was invisible
  only because `right` short-circuited before the marker was read. `MIXED` reads it, which would
  have turned **D2's own pre-registered correct answer** into a wrong one and quietly cost the room
  every D2 point it earned. `Probe.band_metric` separates the two; the detector still fires on a
  real out-of-band earnings figure, so the fix narrows what the band judges, not whether.
- **A rejection the scorer could not see.** A real arm-D answer of 2026-10-27 derived the payout at
  74 per cent and then wrote: *"Buffett began with a payout of 97.4 per cent, then accepted that this
  used an annual dividend figure not in the pack and moved to Lynch's reading."* That is the room
  doing exactly what the room is for, and `MIXED` scored it as asserting two conclusions. So `MIXED`
  turns on an **asserted** wrong figure, using the same `ATTRIBUTION` list `confident_wrong` already
  applies — the clause "began with" is in it, so no new heuristic was needed. `ADOPTED` is
  deliberately unchanged: where the arm derived nothing of its own, repeating the plant counts
  against it whoever it is credited to.

Both are the same shape as the review's own findings: a control that was never wrong because nothing
ever read it.

## 4. The combined budget across both phases — and a figure that moved

**Asked:** recalculate the authorisation and expected costs for the exact 66-run experiment,
including both phases, and enforce the combined budget across them rather than resetting without an
overall limit.

This was the most important of the four, and the review was right that it had not been done.

**The 66-run experiment is two phases** (`docs/council-test-design-2026-10-28.md`): 54 planted runs
of arms A, B, E at three repeats, and 12 clean controls of A and B. Each was a **separate invocation**
of `eval probe`, and each invocation built its own `Budget` with its own cap. Two $90 caps are not a
$90 cap, and nothing bounded the pair.

Worse, **the published $94 priced a different plan.** Round four's §9 table quoted "A, B, D, E x 2 =
48 runs, $5.94 forecast, $94 cap" and called it "the pre-registered plan". It is not: the
pre-registered plan has three repeats, no arm D, and a clean-control phase that table omits
entirely. The forecast confirms the reconstruction — the two phases come to **$7.2696** against the
design document's **$7.27**, to the cent.

**Done.** `--clean-arms` puts the control phase in the same invocation, and `planned`, `worst` and
`n` are summed over both phases, so one `Budget` holds the whole experiment.
`test_both_phases_of_the_experiment_run_under_one_budget` drives both phases and reads the run's own
summary back.

### The authorisation, recalculated

| | runs | forecast | measured bound | hard cap |
| --- | --- | --- | --- | --- |
| Planted: 6 probes x 3 repeats x A, B, E | 54 | $5.7402 | | |
| Clean controls: 6 probes x A, B | 12 | $1.5294 | | |
| **The experiment, one budget** | **66** | **$7.2696** | **$86.70** | **$90** |

The command, and it prints `consistent`:

```
uv run python -m eval probe --dry --arm A --arm B --arm E --repeats 3 --clean-arms A --clean-arms B --pause 0
```

```
--- planted: arms A,B,E, 3 repeat(s), 54 runs ---
--- clean controls: arms A,B, 1 repeat(s), 12 runs ---
plan bound $86.7000 over 66 runs, measured from the reservations taken
  RUN_BOUND predicts $89.4192
  consistent: the published maximum covers this plan and is not padded
```

**So the figure to fund is about $90, not $95** — and $95 against a 48-run plan was never the
experiment's figure. Two corrections pulled in opposite directions and both are in that number:
including the clean phase raised the honest bound, and removing the fourth request lowered it. Had
only the first been done, the figure would have been **$115.03**.

## What I have not done

- **The benchmark has still not been run against live models.** Nothing here answers whether four
  advisors match six, or whether either beats the Chairman alone. The review says so and it is
  correct; no amount of further instrument work will change it.
- **The three production market-data fixes from round three**, and any change to the market-cap
  calculation. The provider's share-count definition is still unestablished.
- **A dedicated provider key.** The review's closing recommendation is the same conclusion round
  four reached from the other direction, and it remains the owner's hands: every control described
  here runs **inside the process doing the spending**, so a key with its own credit limit is the only
  cap that exists at the provider. It is the right protection precisely because it holds if the
  internal accounting has another defect — and this round found two more, both of them controls
  nothing had read.
