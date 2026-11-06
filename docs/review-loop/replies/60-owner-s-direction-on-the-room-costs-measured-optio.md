# Review 60: Owner's direction on the room: costs measured, options, is a paid comparison necessary

2026-11-06 16:09 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `53-owner-direction-room-cost.md`.

VERDICT: FIX

ISSUES:

1. **The 77% advisor-cost split is unsupported.** [Cost report:23](/C:/projects/alphacouncil-platform/docs/council-cost-options-2026-11-06.md:23) divides A−D by six, but removing seats also changes the transcript supplied to the remaining advisors and Chair (`api/app/debate/engine.py:201,250`). Those totals cannot isolate advisor costs. The pilot averaged **17.5 paid advisor calls plus 3 Chair calls**, not 18 plus 2.5: planted runs replace one advisor opening with a free scripted answer (`api/eval/probe_run.py:211`). The JSONL also covers **three companies**, not the five claimed at line 31. Correct the repeated split in `PROJECT.md:275`.
2. **The proposed comparison is underpriced.** [Output 53:50](/C:/projects/alphacouncil-platform/docs/review-loop/outputs/53-owner-direction-room-cost.md:50) specifies 15 probes × two arms × planted/clean = **60 sessions**. Using its own estimates gives **$9.03–$9.63**, not $5–6; A alone is approximately $7.53. Option 2’s actual cost remains unmeasured.
3. **Option 2’s accuracy is a hypothesis.** [Cost report:55](/C:/projects/alphacouncil-platform/docs/council-cost-options-2026-11-06.md:55) assumes roughly B’s accuracy, although its presenter rewrites the analysis and Chair’s answer. The existing harness retains the final answer and summary flags (`api/eval/probe_run.py:285`), so it does not establish correctness throughout the displayed discussion. Define acceptance criteria and audit the actual presented output; one repeat must not be presented as proof of equivalent performance.
4. **The lawyer’s status is misstated.** [Cost report:75](/C:/projects/alphacouncil-platform/docs/council-cost-options-2026-11-06.md:75) says the lawyer is evaluating the site now. `PROJECT.md:1016` and the master plan say **NOT STARTED**. The site is ready for review; the review has not been recorded as underway.

DRIFT: The proposed internal cost reduction follows the owner’s direction and preserves the existing room; it adds no product scope. The destination remains the finished, published, polished site, with the lawyer’s advice applied and the remaining launch checks completed.

NEXT STEP: On `rebuild`, correct and complete the option-2 cost/comparison brief in `docs/council-cost-options-2026-11-06.md`, reconciling its repeated claims in `PROJECT.md` and Output 53. This is the most valuable immediate step because implementation and spending should follow an accurate comparison: a paid A-versus-option-2 check is necessary before adoption, but an A-versus-D run is unnecessary for this decision.

DONE WHEN: A read-only recalculation of `docs/eval/probe-results.jsonl` reproduces the averages, call counts and three-company coverage; the brief counts all 60 proposed sessions, separates estimates from measurements, defines comparison criteria and full-output auditing, and leaves the cap pending prototype-based calculation. Lawyer status is accurate and `git diff --check` passes.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for review of the existing live site; this need not wait for option 2.
2. Later, approve the specific beta release and paid comparison separately, after reviewing the prototype and corrected budget. Show the changed mechanism and wording to the lawyer before release.
3. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
