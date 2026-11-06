# Output 46: review 45's step. The cost bound is recalibrated and the decision-grade run re-quoted.

**Measured, with no model calls.** The full decision-grade plan was dry-run on the server from `rebuild` HEAD:
- **The plan:** 15 active probes, arms A, B and D three times each, plus one clean control per arm and probe: 180
  runs.
- **Reserved:** $331.30, against the old `RUN_BOUND`'s $326.85. That is TOO LOW.
- **Dry per-run maxima:** A 3.154860, D 2.377631, B 0.330336.
- **The pilot's live per-run maxima:** A 3.971305, D 2.792840, B 0.330336. Live calls retry; stand-ins never do.

**`api/eval/probe_run.py`:**
- **`RUN_BOUND`:** A 3.9714, D 2.7929, B 0.3304. Each is the larger of the two measurements, rounded up as before.
  E is unchanged and not re-measured; it is in no planned run.
- **`RUN_COST`:** A 0.2511, D 0.1870, B 0.0318, the pilot's live means.
- **The comments** record both measurements and the previous values.
- **The re-run dry plan** prints "RUN_BOUND predicts $425.68 … loose by 28%", which is expected: the dry run cannot see
  live retries.
- **The record:** `docs/eval/dry-probe-results.jsonl` is replaced by the 180-row record; the old one had 216 rows for
  18 probes.

**The quote:**

| | |
|---|---|
| Forecast | **$28.19** (60 runs an arm × the live means) |
| Reservation | **$425.68** |
| Cap | **$426** |
| Smallest visible gap | about 20 points, read between the plan's 12- and 18-probe rows, not simulated |

Dated notes beside each $393: the test plan (§4's table and its "fund the decision-grade run" step),
`docs/council-pilot-2026-11-06.md` item 1, and `PROJECT.md` §9 and Next Up item 4. The registered probes and the
paid record are unchanged.

**Checks:**
- `uv run pytest -q`: 560 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings;
- `git diff --check` is clean.

**The owner's, before that run:**
- top up OpenRouter: the forecast is about $28, and the live site shares the account;
- settle D5's markers;
- approve the $426 cap.

**The question for the review:** is this sound, and what is the single next pre-approved step?
