# F-10, F-11 and a paired test of the Council — design for approval

**Nothing here is implemented.** This is the design the owner asked for on 2026-10-27: fix the two
defects, then run one minimal test that answers a single falsifiable question with a pass or a fail,
before anyone changes the Council's architecture.

## 0. Where the stopped bench left things

The exploratory bench ran 15 of its planned runs before being stopped. All five cells, one repeat,
three arms — so **n = 1 per (arm, cell), 5 observations per arm**. Too small to conclude from, and
it was never the test that decides anything. It is reported because it is measured.

| arm | runs | seconds | cost $ | words | unverified figures | gaps named |
| --- | --- | --- | --- | --- | --- | --- |
| A — the room as it ships | 5 | 47.6 (40.2–53.2) | **0.2226** | 280 | 0 (0–4) | 3 |
| B — the Chair's model alone | 5 | **8.6** (7.6–9.1) | **0.0295** | 299 | **0 (0–0)** | **4** |
| C — six seats over three models | 5 | 41.6 (39.6–58.5) | 0.4327 | 295 | 0 (0–2) | 3 |

Unverified figures by cell: arm A in **2 of 5** cells (dividend 4, thin 1), arm C in **1 of 5**
(dividend 2), arm B in **none**. Arm A costs **7.5×** arm B; arm C costs **14.7×**.

Read it as a prompt for the real test, not as a verdict: it measures cost, length and figure
hygiene, none of which is the Council's claimed advantage.

## 1. F-10 — a billing refusal reaching members as a network failure

**Cause, established.** OpenRouter answers **HTTP 402** when the account cannot cover a request.
`llm.ask` catches `openai.APIStatusError` and, unless it is the reasoning refusal, raises
`SeatError("unreachable")`. The member is then told *"the AI service could not be reached"*
(`web/messages/en.json`, `debate.errors.unreachable`). 401 and 429 are already classified correctly
as `credentials` and `busy`; 402 is the gap.

**Proposed fix, three parts.**

1. **Classify it.** In `llm.ask`'s `APIStatusError` branch, before the generic raise: `402` →
   `SeatError("no_credit", usage)`. Nothing else changes; the reasoning-refusal branch stays.
2. **Word it.** Add `debate.errors.no_credit` to both catalogues. The member does not need our
   billing state, but must not be told the network failed: *"the room has run out of capacity for
   now"* / the Arabic equivalent. The **operator** gets the truth — log the provider's own message
   at ERROR, so the journal says `402 … add credits` rather than `unreachable`.
3. **Prevent it.** Add one line to `scripts/prod-monitor.py` reading `/api/v1/credits` and alerting
   below a threshold — the measured median session is $0.2226, so a $10 floor is about 45 sessions
   of warning. **This is the part that stops a member ever seeing it.**

**Deliberately not doing: a retry on 402.** Retrying an unaffordable request fails three times
instead of once. F-10 was on the list as "add a transport retry"; that would have been wrong.

**Tests.** A fake 402 raises `no_credit`; and every code `llm`/`engine` can raise has a string in
**both** catalogues — a check that does not exist today.

**Note for Goal 4:** the monitor goes from 14 lines to 15, which touches the "monitor at 14 of 14"
wording in Goal 4's done-when and Step 18.

## 2. F-11 — a new HTTP client per model call, never closed

**Cause, established.** `copilot/openai_compat.make_client()` returns a **new**
`openai.AsyncOpenAI` on every call, each with its own httpx pool; `llm.ask` calls it on every call and
never closes it. About 21 pools per session. Demonstrated: three sessions in one process ran
normally (51.5 s, 9.1 s, 50.4 s), the fourth never finished, and the same cell in a fresh process
took 43.5 s.

**Options.**

| | Approach | Why not / why |
| --- | --- | --- |
| a | One module-level client | Simplest, but an httpx client binds to the loop that made it; breaks tests that call `asyncio.run` repeatedly |
| b | **Cache one client per running event loop** | Fixes the server, the tests and the bench; a few lines; **recommended** |
| c | One client per session, threaded through `ask` | Most explicit, but changes the engine's signature for no extra benefit |

**Caveat that must be in the release note:** the Copilot uses `make_client` too, so this gives it a
shared pool across requests as well. That is the normal pattern and the intended outcome, but it is
a behaviour change on a hot path — beta first, watched, then production.

**Tests.** Two `ask` calls on one loop use the same client object; and N sequential sessions do not
grow the client count.

## 3. The paired test

**The one question:** *does the Council catch material financial errors that the Chair alone
misses?* That is the Council's only claimed advantage that can be measured without judgement.

### Design

A **case** is one (pack, question, planted error). Each case runs a 2×2: {Council, Chair alone} ×
{clean, planted}. Identical pack bytes, identical question, identical error text. The Council gets
the error as one seat's round-one answer; the Chair alone gets it as an analyst's note.

**The errors must be material** — each inverts the conclusion — and **falsifiable from the pack**:

| # | Planted claim | What the pack supports |
| --- | --- | --- |
| 1 | payout ratio 97.4% | ~70-73% (P3 dividend rows against P1 eps_ttm) |
| 2 | P/E 4.2 | ~14.5 (P1) |
| 3 | debt to equity 2.9 | 0.20 (P2) |
| 4 | dividend yield 11.8% | ~5.2% (P1) |
| 5 | 12-month return −38% | positive (P1) |

### Scoring rubric — computed, no judge

Primary outcome per run, after `checks.normalize_digits` on the final answer:

- **PROPAGATED** — the planted number appears in the final answer.
- **NOT PROPAGATED** — it does not.

Secondary, Council only: **CONTESTED** — the planted number appears in any round-two challenge turn.
This separates "the room argued it down" from "the Chair happened not to mention it".

**Validity gate, pre-registered.** A case counts only if its *clean* run shows the arm engages with
that figure at all — the correct value or the metric's name appears in the clean answer. A case
failing this is **VOID** and dropped **before** the result is read. Without this gate, an arm earns
credit for never raising the subject.

### Pass or fail, fixed before anything runs

- **n = 5 cases × 3 repeats = 15 planted runs per arm.**
- Build the 2×2 table of propagations: Council *x*/15 against Chair *y*/15.
- **PASS** if and only if Fisher's exact test gives **p < 0.05** *and* the Council's propagation rate
  is the lower one.
- **FAIL** otherwise — and "no measurable difference" is a fail, not an inconclusive.
- **Calibration, computed with the implementation itself, not estimated.** My earlier figures were
  wrong: I wrote that 2/15 vs 8/15 gives p ≈ 0.046 and passes. It gives **p = 0.0502 and fails.**
  What n = 15 per arm can actually detect:

  | Council | Chair | p | |
  | --- | --- | --- | --- |
  | 0/15 | 5/15 | 0.0421 | PASS |
  | 1/15 | 7/15 | 0.0352 | PASS |
  | 1/15 | 6/15 | 0.0801 | fail |
  | 2/15 | 9/15 | 0.0209 | PASS |
  | 2/15 | 8/15 | 0.0502 | fail |
  | 4/15 | 10/15 | 0.0656 | fail |

  **So this test can only find a large effect.** The Council has to catch roughly five or six more
  errors out of fifteen than the Chair alone. A real but modest advantage will be recorded as a
  FAIL at this sample size, and that is a limit of the test, not a finding about the Council — the
  report says so in those words. Buying the power to detect a smaller effect means more runs and
  more money; at n = 30 per arm the same 2 vs 8 separation would clear it comfortably.
- The table, both rates and p get reported whichever way it goes.

### Spending limit — enforced, not promised

Measured: Council **$0.2226**/run, Chair **$0.0295**/run.

| | runs | cost |
| --- | --- | --- |
| Planted, Council | 15 | $3.34 |
| Planted, Chair | 15 | $0.44 |
| Clean, validity gate | 5 + 5 | $1.26 |
| | | **$5.04** |

**Hard cap $6.00**, enforced in the loop: before each run the harness reads `/api/v1/credits` and
**aborts** if the spend so far plus one more run would breach the cap, plus a hard run-count cap.
Current balance is **$6.07** — it fits, but with no margin, so topping up first is advisable so the
cap is what stops the run rather than the balance.

### Arm D — four seats, existing prompts (added 2026-10-27 on the owner's decision)

`DEBATE_ADVISORS=buffett,lynch,marks,alwaleed`. **No code change:** `roster.MIN_ADVISORS` is 2, so a
four-seat room is configuration. The philosophy specifications are **held** until this reports.

The point of arm D is to separate two changes the proposal bundles: **fewer seats** and **rewritten
philosophies**. Run together, neither can be credited. Arm D keeps today's prompts and changes only the
count, so it isolates the count. If four seats catch errors as well as six, the specifications are worth
writing and the count is not the variable. If they do not, the specifications start with a deficit to
overcome — which is worth knowing before writing them, not after.

**Why the count might matter on this metric:** catching a planted claim is partly a numbers game. Six seats
give five possible challengers; four give three. Arm D could score worse with better reasoning per seat.

**Comparability, checked:** no seat recuses itself on any of the five cells under either roster, so both
rooms run at full strength and seat count is the only difference between A and D.

**A bug this surfaced, which would have voided arm D silently.** `PLANT_SEAT` is `dalio`, and dalio is not
in the four-seat roster. `with_plant` intercepts on `seat.id == PLANT_SEAT`, so in arm D nothing would have
been planted at all — and every run would still have been recorded `planted=True`. Arm D would have looked
like a room that never propagates an error, because it was never given one. Two requirements follow:

1. **The plant moves to `buffett`**, who sits in both rosters. It is also the harder test: the most
   authoritative seat is the one the room has most reason to defer to.
2. **The harness asserts the plant seat is seated** and fails loudly if not. A silently clean "planted" run
   is the same family of fault as F-4 (an absence counted as an answer) and F-9 (a crash instead of a
   result): the harness believing its own happy path.

### Comparisons: one primary, the rest secondary

Three arms make three pairwise tests, and testing all three at p < 0.05 inflates the chance of a false
positive. So the comparisons are ranked **before** running:

- **PRIMARY, and the only one carrying the pass/fail: A (six seats) vs B (Chair alone).** This is the
  question "does the Council catch material errors the Chair alone misses". Fisher exact, p < 0.05, Council
  lower.
- **SECONDARY, reported with p but no pass/fail: D vs A** (does cutting to four hurt?) and **D vs B** (does a
  four-seat room beat the baseline?). These inform the next decision; they do not decide this one.

### Revised budget

| | runs | cost |
| --- | --- | --- |
| Planted, A six seats | 15 | $3.34 |
| Planted, D four seats | 15 | $3.29 |
| Planted, B Chair alone | 15 | $0.44 |
| Clean controls, 5 cases x 3 arms | 15 | $2.36 |
| | **60** | **~$9.43** |

**Hard cap $10.00**, enforced against the live balance before each run as before. Arm D's $0.2193 is a
modelled figure that holds the Chair's prompt size constant; the real cost is a little lower, because four
seats make a shorter transcript. Balance at the time of writing is **$6.07**, so this needs a top-up of
about $5 before it can run.

### Sequencing

**F-11 before the test, not after.** It now matters more: three arms and 60 runs, not 40. The test needs runs back to back, and the client leak is
precisely what broke the last two attempts. F-10 next, so a refusal is legible. Then the test.

### What this test cannot tell you

Whether the Council is "better" in any general sense; whether its prose is more useful; whether six
models beat three. It answers one falsifiable question. If it fails, the honest reading is that the
Council's error-catching advantage is unproven at this sample size — not that it is disproven.
