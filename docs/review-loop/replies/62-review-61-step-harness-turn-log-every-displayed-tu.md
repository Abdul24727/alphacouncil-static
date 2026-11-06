# Review 62: Review 61 step: harness turn log (every displayed turn, per-turn cost, first-turn time)

2026-11-06 16:22 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `55-harness-turn-log.md`.

VERDICT: FIX

ISSUES:

1. `api/eval/probe_run.py:339–344` loses billed Chair-failure usage: `api/app/debate/engine.py:457–459` rethrows before saving a turn. Offline reproduction: a failed brief costs $0.004 with no recorded turns; a failed verdict costs $0.204 while recorded turns total $0.200. The new reconciliation test covers only an advisor failure.
2. `api/eval/probe_run.py:243` converts an unknown provider cost into zero. `Usage.cost_usd` is optional (`api/app/debate/llm.py:54–64`). A paid-model usage record containing tokens but no reported cost becomes `cost_usd: 0.0`, with both `scripted` and `simulated` false—incorrectly presenting unknown spending as free.

DRIFT: The output stayed within the requested harness work and the owner’s room-cost direction. The goal remains alphacouncil.tech finished, published and polished, preserving the existing presentation without adding product scope.

NEXT STEP: On `rebuild`, finish usage accounting in `api/eval/probe_run.py` and its existing tests: retain billed Chair failures separately from displayed turns and distinguish unknown cost from confirmed zero. This closes the evidence gap before the architecture comparison relies on it.

DONE WHEN: Offline tests cover failures at brief, fault lines and verdict; recorded usage reconciles with known run costs; unknown costs remain explicitly unknown; scripted turns remain free. Run `uv run pytest tests/test_eval_probe_run.py tests/test_eval_budget.py` and `git diff --check`, preserving historical JSONL records. My read-only run passed 51 focused tests; two requiring temporary files were excluded.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for review of the live site; return written advice for `docs/legal-advisors-<date>.md`.
2. Once the prototype and cap are reviewable, approve each necessary paid comparison and release separately; show mechanism and wording changes to the lawyer before release.
3. Step 18 item 4 awaits a real customer’s renewal.

Response complete
