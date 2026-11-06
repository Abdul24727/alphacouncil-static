# Output 58: review 64's four fixes to the prototype, and the dry comparison repeated

1. **Malformed advisor values fall back for that seat alone.**
   - **The fix:** `_advisor_turn` turns a non-object value into an empty slice, which the engine refuses, so that
     seat falls back. `_serve` catches any refusal, not a named few.
   - **When a whole round fails:** for any exception, every seat falls back, and the round's failed attempts are
     billed once.
   - **Test:** a string-valued opening for one advisor gives 1 fallback and 0 round failures; the session completes
     and every known charge is recorded exactly once.
2. **No merged costs.**
   - **Removed:** `combine()`.
   - **The rule now:** a fallback turn carries only the fallback's usage. The call it superseded, or a failed
     round's attempts, goes to `PresenterAsker.extra` and from there to `ProbeResult.extra_calls`, as `{stage, role,
     usage}`.
   - **Test:** an unreported fallback cost stays `None` on its turn, while the superseded presenter charge stays
     known in `extra_calls`.
   - **Reconciliation:** across turns, failed calls and extra calls, it equals the run's cost in every arm-P test.
3. **The analyst's plan is saved** (`ProbeResult.analyst_plan`).
   - **Test:** the plan has brief, seats, fault lines and verdict, and its seats match the displayed openings.
4. **The brief is corrected** (`docs/council-cost-options-2026-11-06.md`):
   - option 2 is built as a prototype, off by default;
   - turns, plans and extra calls are recorded;
   - P's provisional $0.1036 is **41.3 %**, **above** the 40 % criterion;
   - a release item: the app's session total must also count superseded calls before the app may use this engine.
     Today it sums displayed turns only.

**Checks:**
- `uv run pytest -q`: 577 passed, 10 skipped;
- `presenter.py` is lint-clean;
- `git diff --check` is clean.

**The 60-session dry comparison, repeated** in a fresh staging copy (`/root/presenter-20261106b`):
- **All ran:** 30 A at 20–21 calls each, and 30 P at 4 calls each, with 0 fallbacks.
- **Reserved:** $127.32 in all, unchanged.
- **Plans:** all 30 P runs saved their analyst plan.
- **Every turn** is `simulated`.
- **`RUN_BOUND` predicts $166.82,** "loose by 31 %" as expected from the live scaling.
- **The record:** `docs/eval/presenter-comparison/` is replaced by this run. The historical records are unchanged.

**The questions for the review:** is this sound, is the comparison ready to put to the owner, and what is the
single next pre-approved step?
