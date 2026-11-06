# Review 61: Reviews 59 and 60 fixed: credit dated; private page a recorded departure; cost brief rebuilt from the record

2026-11-06 16:14 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `54-reviews-59-60-fixed.md`.

VERDICT: ACCEPT

ISSUES: none.

DRIFT: These corrections support the unchanged goal: alphacouncil.tech finished, published and polished under `PROJECT.md`, without adding product scope. The earlier private-page publication remains a recorded departure; acknowledging it does not supply authorization.

NEXT STEP: On `rebuild`, extend the existing comparison harness in `api/eval/probe_run.py` to retain every displayed turn, its model/token/cost usage, and elapsed time to the first displayable turn. Its `save()` currently discards usage and its event callback discards timing; closing this evidence gap is the most valuable prerequisite to evaluating the owner’s analyst-and-presenter option.

DONE WHEN: Focused offline tests prove complete transcript retention, correct cost accounting—including failed and scripted turns—and first-turn timing. A stand-in run produces the records without model calls, preserves the historical pilot JSONL, and clearly labels simulated measurements. Run `uv run pytest tests/test_eval_probe_run.py tests/test_eval_budget.py` from `api/`, plus `git diff --check`.

OWNER ITEMS:

1. Send the corrected repository lawyer pack for evaluation of the live site; return written advice for `docs/legal-advisors-<date>.md`.
2. After the prototype and budget are reviewable, approve the necessary paid A-versus-option-2 comparison and each release separately. Show the changed mechanism and wording to the lawyer before release.
3. Any further publication or update of the private artifact requires explicit approval.
4. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
