# Output 56: review 62's two gaps in the turn log, closed

1. **Billed Chair failures are kept.**
   - **The gap:** the engine re-raises a Chair `SeatError` before saving any turn (`engine.py`, `turn`), so its
     attempts' cost never reached `save`.
   - **The fix:** `TurnLog.observe` wraps the asker and keeps those calls in a new `ProbeResult.failed_calls`, each
     with `stage`, `error` and `usage`. They are billed but are not displayed turns.
   - **Advisor failures** are not duplicated there: the engine already saves them as absent turns with their usage.
2. **An unknown cost stays unknown.** `usage_record` keeps `cost_usd: None` when the provider reported none, or when
   there is no usage at all.
   - **The one confirmed zero:** the plant's scripted opening, where no model was called.
   - **No longer possible:** a paid call with tokens but no cost recorded as `0.0` with both flags false.

**Tests** (`tests/test_eval_probe_run.py`, offline):
- **The unit test:** extended with a `None` usage and with a paid usage that has tokens but no cost. Both are `None`,
  and the known costs still sum.
- **The fake paid room:** now a helper. The advisor-failure test checks `failed_calls == []` and reconciles turns
  plus failed calls to `cost_usd`.
- **New, at each Chair stage:** brief, fault lines and verdict. In each case:
  - the run fails;
  - `failed_calls` holds exactly that stage at $0.004;
  - no displayed turn exists for it;
  - **the recorded known costs equal the run's `cost_usd`.**

**Checks:**
- `uv run pytest tests/test_eval_probe_run.py tests/test_eval_budget.py`: 56 passed;
- the whole suite: 567 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings;
- `git diff --check` is clean;
- the pilot's records are unchanged.

**The question for the review:** is this sound, and what is the single next pre-approved step?
