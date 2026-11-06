# Review 40: Review 39 fixes: pilot analysis repaired offline (scorer, coverage, bound maxima)

2026-11-06 11:39 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `40-pilot-analysis-repaired.md`.

VERDICT: FIX

ISSUES:

1. [api/eval/score.py:134](C:/projects/alphacouncil-platform/api/eval/score.py:134) — Adding `"claim that"` incorrectly exempts self-assertions and endorsements. For D4, “The return on assets is 2.53 per cent in the pack. I claim that the return on assets is 11.8 per cent.” now scores `CORRECTED`; the previous code correctly scored `MIXED`. I reproduced the same regression when the answer explicitly endorses Buffett’s claim.

2. [api/eval/score.py:338](C:/projects/alphacouncil-platform/api/eval/score.py:338) — The dividend exception examines only text **before** the number, missing an earnings label afterward. For D2, “The dividend is 2.25 SAR per share, while 1.1 SAR per share is the earnings figure.” now scores `SILENT`; previously it correctly scored `INCORRECT`. The existing scorer tests pass—127 passed, 10 skipped—but miss both regressions.

DRIFT: This output stayed within the authorized offline pilot repair and added no product scope. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the owner’s gates respected.

NEXT STEP: On `rebuild`, correct these two regressions in `api/eval/score.py` and add counterexamples in `api/tests/test_eval_score.py`, then reconcile the saved analysis offline. This is the most valuable pre-approved step because the repaired scorer still hides wrong conclusions and cannot safely support further paid comparisons.

DONE WHEN: Both counterexamples receive their correct outcomes while the original B/D2 and B/D4 fixes remain correct; `cd api; uv run pytest -q tests/test_eval_score.py tests/test_eval_probe_report.py` passes. Re-score all 36 saved answers, preserve the original record, reproduce the report and explain any changed totals. `git diff --check` passes. The current saved re-score, coverage counts and reservation maxima already reproduce.

OWNER ITEMS:

1. Arrange Step 7’s lawyer review and provide written advice.
2. Top up the shared OpenRouter account; the recorded post-pilot balance is $7.83.
3. Explicitly confirm the already-applied `owns` patch or direct its revert, as `PROJECT.md` records.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Approve further paid testing only after the analysis is sound and the stale $393 quotation is remeasured.

Response complete
