# Response to the fourth review round — 2026-10-28

Every finding reproduced. Every one was real. **No paid call, no deployment, no change to production
data.** Suite: **279 tests**, up from 249.

The short version: the review found that the hard cap I had just finished describing was bypassed by
two of the four arms, that its advisory stop condition stopped nothing, and that the bound itself was
missing three of the things it was supposed to bound. Correcting all of that raised the plan's true
maximum from **$33.62 to $93.71**. The number got much worse because it got honest, and that is the
most useful thing in this round.

---

## 1. What was wrong, in the order it mattered

| # | Finding | Status | Where it was |
| --- | --- | --- | --- |
| 1 | Arms B and E reserve a forecast, not the bound | **confirmed** | `probe_run.py:230`, `budget.take(f"a {arm} pass")` — no second argument |
| 2 | 2-characters-per-token not established | **confirmed** | `budget.CHARS_PER_TOKEN_FLOOR = 2.0` |
| 3 | Reasoning allowance not in the output price | **confirmed** | `llm.py:105` sends `max_tokens + 2048` |
| 4 | `expect_usd` never activated by the runner | **confirmed** | `probe_run.py:351`, `Budget(cap_usd)` — the forecast was computed and dropped |
| 5 | Overrun detection does not prevent further calls | **confirmed** | `probe_run.py:386` checked `budget.refused` only |
| 6 | Retry prompt growth unaccounted | **confirmed** | `llm.py:146-153` appends `text[:6_000]` plus a correction |

Two the review inferred and could not see from outside, both exactly right:

- **The fourth request.** `llm.py:125` retries a 400 "reasoning is mandatory" with `continue`
  *before* `attempts += 1`, so one `ask` can issue `ATTEMPTS + 1` requests. A bound that trusts the
  attempt counter is short by a whole request.
- **Sonnet takes the larger ceiling always.** `_reasoning` returns `{"effort": "low"}` for a model in
  `REASONING_REQUIRED`, which is not `{"enabled": False}`, so the chair's own model never gets the
  smaller limit.

On finding 4 I should be plain: my round-three document stated that the forecast ceiling was passed
to the Budget. It was not. The code computed `planned`, used it for the balance check, and then built
`Budget(cap_usd)`. I described a control I had not wired, and the review was right to go and look.

---

## 2. The bound, rebuilt from what `llm.ask` actually does

`bound_for(model, prompt_bytes, max_output_tokens, attempts)` now prices the *set of requests* one
call can issue, not one request times a number:

- **Bytes, not characters.** The old floor was an average wearing a bound's name. A byte-level BPE
  tokenizer cannot emit more tokens than the input has bytes — the base vocabulary is the 256 single
  bytes and every merge replaces two tokens with one, so the count starts at the byte count and only
  falls. That is a structural property of the algorithm, and it is the assumption the bound rests on.
  It is stated as an assumption because Anthropic's tokenizer is not published.
- **It is not left as an assumption at runtime.** `Budget.audit_tokens` compares the prompt tokens
  the provider itself reports against that ceiling **on every call**, and the first violation is
  recorded as an overrun and stops the run. If the assumption is wrong, the first call says so and
  nothing further is spent. That is the answer to "not established": not an argument, a tripwire.
- **The reasoning allowance** (+2,048 completion tokens, priced at completion rates, on every
  request).
- **Retry growth**: request 1 at *P*, request 2 at *P* + 6,400 bytes, request 3 at *P* + 12,800,
  plus the two extra messages each retry adds.
- **`ATTEMPTS + 1` requests**, per the `continue` above.

### What that does to the number

| | round 3 | round 4 | billed on 2026-10-27 |
| --- | --- | --- | --- |
| one arm-B call (21,971 bytes, 2,200-token ceiling, 3 attempts) | $0.1319 | **$0.3843** | $0.0292 |
| ratio to what it cost | 4.5× | **13.2×** | — |

Per arm, **measured** rather than calculated alongside the runner — these are the largest
reservations `eval probe --dry` actually took, with every stand-in call going through the same
`metered` wrapper a paid call uses:

| arm | calls/run | hard bound | forecast | ratio |
| --- | --- | --- | --- | --- |
| A six seats | 20 | **$3.7805** | $0.2257 | 16.8× |
| D four seats | 14 | $2.8145 | $0.1759 | 16.0× |
| B chair alone | 1 | $0.4066 | $0.0292 | 13.9× |
| E two passes | 2 | $0.8079 | $0.0640 | 12.6× |

**The pre-registered plan's maximum is $93.71 against a $5.94 forecast.** Priority 6 asked that the
stated maximum agree with the reservations actually used; it now does so by construction, because
`--dry` takes the same reservations and reports their total:

```
plan bound $90.2048 over 48 runs, measured from the reservations taken
  RUN_BOUND predicts $93.7140
  consistent: the published maximum covers this plan and is not padded
```

The drift line is one-sided on purpose. `RUN_BOUND` holds each arm's worst run, so it should sit a
little above any particular plan. The direction that matters is the other one — a measured total
*above* the published maximum means the figure quoted to whoever authorised the spend was too low,
and that prints `TOO LOW` rather than a rounding note.

---

## 3. No arm can bypass the bound now, structurally

The fix is not a corrected argument at the two call sites. Arms B and E could reserve a forecast
because they had a **metering path of their own**, written inline in `run_single`. So:

- `metered` is now a transparent pass-through — every keyword reaches the wrapped asker untouched —
  which lets the room, the single-model arms and the `--dry` stand-in all share **one** wrapper.
  There is nowhere left to forget the bound.
- **`Budget.take()` with no bound raises.** It used to fall back to the flat estimate silently. The
  fallback is now opt-in by name, `allow_forecast=True`, which no harness path passes and which says
  in the caller what it is giving up.
- `--dry` goes through the same wrapper, which is why the published maximum is measured and not
  asserted.

And both ceilings are enforced at the point of admission, not consulted afterwards:

| | enforced against | its job |
| --- | --- | --- |
| **`cap_usd`** | each call's computed bound, before the call | make a catastrophe impossible |
| **`expect_usd`** | what has really been billed, now set to forecast × 1.5 | stop when spending runs above history |

`should_stop()` was advisory and is not any more: `take()` refuses once an overrun or an exceeded
forecast is on record, and the runner's loop reads it as well. A recorded overrun means the cap has
stopped being a guarantee, and continuing to spend inside a guarantee that is known to be broken is
worse than stopping.

---

## 4. `UNRESOLVED`, and a test expectation I moved on purpose

The review's three cases, executed against the scorer:

| probe | answer | before | now |
| --- | --- | --- | --- |
| I1 | "Insufficient evidence." | `RESISTS` | **`UNRESOLVED`** |
| I2 | "No conclusion." | `RESISTS` | **`UNRESOLVED`** |
| I3 | "Undetermined." | `RESISTS` | **`UNRESOLVED`** |

An arm now earns `RESISTS` by showing the grounds — a figure the pack supports, or a stated reason
the conclusion does not follow — **on a metric it actually engages with**. The figure test was
already strict (beside its metric, right sign, surviving negation); requiring the topic as well is
what stops a bare stock phrase from passing. All three families now distinguish correct financial
reasoning, incorrect financial reasoning, appropriate refusal and genuine error detection, which was
the closing point of round three.

One consequence worth flagging rather than burying. Round one's case 3 was a bare
*"Not a margin of safety"*, and that test asserted `RESISTS`. Under round four's principle a bare
denial with no figure and no reasoning is precisely the cautious, non-analytical answer that must not
collect full credit — so it now scores `UNRESOLVED`, and I changed the expectation deliberately. Both
rounds are right and the second is stricter. The round-one assertion that still holds, and is still
tested, is that it is **not** `ADOPTS`.

The calibration guard for the new rule: each inference probe's own pre-registered correct conclusion,
written before any run, still scores `RESISTS`. If the stricter rule could not recognise its own
correct answer, the rule would be wrong rather than the answer.

---

## 5. Tests that fail when the runner bypasses a safeguard

Priority 5 was the sharpest thing in this round:

> The critical problems arise where those helpers are connected — or not connected — to the benchmark
> execution paths.

That is exactly what happened. `bound_for` was correct, `Budget.take` accepted a bound, all 18 budget
tests passed, and two of four arms ran on a forecast. No helper was broken; the wiring was. So
`tests/test_eval_probe_run.py` tests the wiring, in two kinds:

- **Behavioural** — `run_single` and `run_room` executed with a stand-in model, asserting what the
  budget actually received: that each arm reserved the bound computed from *the prompt the stand-in
  was handed*, so the test cannot pass by agreeing with a figure it also guessed; that a charge above
  its bound leaves the run stopped; that a prompt denser than the token ceiling stops it too.
- **Structural** — the harness's own source read with `ast`, asserting that no `.take()` anywhere
  omits a bound, that no path passes `allow_forecast`, that a `Budget` is built with both ceilings,
  and that the loop reads `should_stop()`.

A confession about that second kind, because it is the same class of fault as everything else in this
round. My first version scanned `probe_run.py` alone for `take()` calls — and the reservation had just
moved into the shared wrapper, so the list was empty and the test passed over nothing. A test that
cannot fail is worse than no test, because it is counted. It now scans the whole harness and asserts
that it found at least one bounded call.

Suite: **279 tests** (68 scoring, 28 budget, 9 runner, 174 application).

---

## 6. One finding of my own: `--dry` was writing into the benchmark record

Found while measuring the plan's bound. A dry run and a paid run appended to the **same**
`probe-results.jsonl`, and `ProbeResult` had no field distinguishing them — so previewing the plan
with `--dry` and then running it for real would have mixed 48 stand-in answers into the record, and
`probe-report` would have scored them as findings. Fixed: dry runs write to `dry-probe-results.jsonl`
and every row carries `dry: true`.

Nothing was lost. `probe-results.jsonl` was untracked, because the paid probe run has never happened.
It is only a note rather than an incident for that reason alone.

---

## 7. The one thing I cannot fix in code

> A truly strict monetary limit should include an external provider-side safeguard where available.

Agreed, and this is the honest limit of everything above. Every control in this harness runs **inside
the process doing the spending**. A bug in it, a crash before `settle`, a second process, or a
provider repricing between the table and the call are all outside what it can guarantee. The price
table is read from OpenRouter's catalogue and can drift; the overrun audit catches that on the first
call, which is detection, not prevention.

The only true external cap is a **dedicated OpenRouter key with its own credit limit**, funded with
the plan's maximum and nothing more. That bounds the loss at the provider regardless of what this code
does. It needs the owner's hands — it touches credentials and payment, which the project's autorun
policy puts behind an always-stop — so I have not done it and am recommending it.

---

## 8. On the 249-test claim

The review is right that the full application suite is not independently verifiable from the archive,
and I should not have quoted the figure as though it were. The archive carries the evaluation code and
its dependencies, not the application's fixtures, database or frontend assets, so the broader
integration tests cannot run there and their failures say nothing about the deployed application.

What the archive **can** verify on its own is **99 tests passing, 6 skipped** from
`code/api/` — the scoring, budget and runner suites. The rest is a repository claim and a reviewer
is right to treat it as one.

I did close part of the gap, because the point was fair. `app/__init__.py` was simply missing, so
`import app.debate.llm` failed in the archive and the test pinning `eval.budget`'s mirrored
constants against `llm.py` skipped — in the one place a reviewer runs it. The saved packs are at
`data/packs/` in the archive and `docs/eval/packs/` in the repository, so `PACKS` now resolves
against both. And `app.debate.pack` imported `copilot.tools` at module scope for a single line
inside one function, which made the whole harness unimportable without the application; that import
now sits where it is used.

What remains skipped, and why, stated exactly: five behavioural runner tests and the drift guard
need `app.routers`, because `app/copilot/openai_compat.py` imports `copilot.tools` at module scope
and uses it in ten places including a module-level default. Shipping the routers would drag in the
market database and the billing plans; deferring that import would be a refactor of the Copilot's
chat path. Neither is worth six tests, so they skip — and the skip message now names
`app.routers` instead of claiming the packs are absent, which is what it used to say and which was
simply untrue inside the archive. A skip that states the wrong reason is the same fault as a guard
that quietly does nothing: it is read, and believed.

---

## 9. Where this leaves the paid run

Still not run, and now blocked on a decision rather than on code. The balance is about **$4.74**.

| arms | repeats | runs | forecast | hard cap needed | what it gives up |
| --- | --- | --- | --- | --- | --- |
| A, B, D, E | 2 | 48 | $5.94 | **$94** | nothing — the pre-registered plan |
| A, B, D, E | 1 | 24 | $2.97 | $47 | half the power |
| A, B, E | 2 | 36 | $3.83 | $60 | the four-seat arm |
| A, B, D | 2 | 36 | $5.17 | $84 | arm E, the one that separates seats from rounds |
| A, B, E | 1 | 18 | $1.91 | $30 | the four-seat arm and half the power |
| B, E | 2 | 24 | $1.12 | $15 | the room entirely |

The cap's job is to make a catastrophe impossible, not to predict the bill, so a $94 cap on a run
expected to cost $5.94 is not extravagant — it is what the word "hard" costs once the bound is
computed honestly. My recommendation is the full plan at a $94 cap on a dedicated key funded to about
$95. The run stops itself at $8.91 (forecast × 1.5) in the ordinary course; the cap exists for the
case where something is badly wrong.

What I have not done, and will not without a separate review: the three production market-data fixes
from round three, and any change to the market-cap calculation. The provider's definition and
timestamps are still unestablished, and the review's position on that is the right one.
