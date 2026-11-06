# Review 65: Review 64 fixes: presenter fallbacks, no merged costs, plan saved; dry comparison repeated

2026-11-06 21:07 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `58-presenter-fixes.md`.

VERDICT: FIX

ISSUES:

1. [api/eval/probe_run.py:392](/C:/projects/alphacouncil-platform/api/eval/probe_run.py:392) gives P’s analyst the raw planted opening; [presenter.py:123](/C:/projects/alphacouncil-platform/api/app/debate/presenter.py:123) inserts it without the engine’s citation processing. A’s Chair receives the processed version. Reproduced on I1: A sees `[P1]` and `[P2]` citations; P’s analyst sees none. Citation differences affect 14 of 15 active probes and can bias the quality comparison. The existing equivalence test covers A/B, not P. Fix this before requesting paid-run approval.

DRIFT: The output stays within the owner’s room-cost direction and adds no product scope. The goal remains alphacouncil.tech finished, published and polished under `PROJECT.md`, with the existing presentation preserved.

NEXT STEP: On `rebuild`, correct the A/P planted-input mismatch in `probe_run.py` and `presenter.py`, extending the existing equivalence regression in `test_eval_probe_run.py`. This is the most valuable pre-approved step because it prevents paying for a comparison influenced by different evidence presentation.

DONE WHEN: Captured prompts prove equivalent planted text, citations and seat attribution across A/P for all 15 active probes; focused pytest checks and `git diff --check` pass. Repeat the isolated 60-session dry comparison, updating reservations and preserving historical records. This review confirmed the four requested repairs, 32 passing tests and the saved dry totals; three writing tests were excluded, and the full-suite/lint claims were not independently rerun.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for evaluation of the live site; return advice for `docs/legal-advisors-<date>.md`.
2. After the comparison correction is reviewed, approve the necessary paid A/P run and its updated cap. Any release needs separate approval, with changed mechanics and wording shown to the lawyer first.
3. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
