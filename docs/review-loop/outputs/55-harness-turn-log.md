# Output 55: review 61's step. The harness keeps every displayed turn, its cost and the time to the first one.

**`api/eval/probe_run.py`:**
- **`TurnLog`:** the engine's own two callbacks, kept rather than discarded.
  - `save(turn, usage)` stores every turn as saved, with a `usage` record: model, prompt and completion tokens,
    cost, seconds, and two flags.
    - **`scripted`:** the plant's opening, which costs nothing.
    - **`simulated`:** a dry run, whose costs are not real.
  - A `None` usage is recorded as zeros, not a blank.
  - Absent seats are kept with the usage of their failed attempts (F-7).
  - `emit(event)` stamps `first_turn_seconds` at the first turn a visitor sees. Stage events and absent seats don't
    stop the clock.
- **Two new `ProbeResult` fields:** `turns` and `first_turn_seconds`.
  - **The room runner** (A, D) records both.
  - **The single-model runner** (B, E) has no turns. Its whole output is the answer, so `first_turn_seconds` is the
    run's own seconds.

**Tests** (`api/tests/test_eval_probe_run.py`, all offline, no model calls):
1. **Usage per turn,** with a billed failed turn, a free scripted turn and a `None` usage, summing exactly. The turn
   passed in is not mutated.
2. **First-turn timing:** it skips stage events and absent seats, and later turns don't move it.
3. **Reconciliation on a fake paid room.** It runs through the real metering path (`metered`) with a Budget:
   - one seat fails its opening, billed $0.004;
   - the plant's opening is scripted;
   - every other call costs $0.01.

   The checks:
   - all turns are kept: one each of brief, fault lines and verdict, and an opening for every seat;
   - exactly one scripted turn;
   - the absent turn carries $0.004;
   - **the turns' costs equal the run's `cost_usd`;**
   - `first_turn_seconds` ≤ `seconds`.
4. **Stand-in runs:**
   - **room:** 21 turns, every one labelled `simulated`, with a first-turn time;
   - **single model:** no turns, and its first-turn time is its run time.

**Checks:**
- `uv run pytest tests/test_eval_probe_run.py tests/test_eval_budget.py`: 53 passed;
- the whole suite: 564 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings;
- `git diff --check` is clean.
- **The record:** `docs/eval/probe-results.jsonl` and `docs/eval/pilot-2026-11-06/` are unchanged. New fields
  appear only in new runs, and the report reads old rows as before.
- **Not run:** a full `eval probe --dry` was not run. It would overwrite the committed 180-row dry record, and the
  stand-in tests cover the records without it.

**The question for the review:** is this sound, and what is the single next pre-approved step?
