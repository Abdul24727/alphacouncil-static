# Review 41: Review 40 fixes: scorer attribution and dividend-sentence regressions closed

2026-11-06 11:45 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `41-scorer-regressions-closed.md`.

VERDICT: FIX

ISSUES:

1. [api/eval/score.py:199](C:/projects/alphacouncil-platform/api/eval/score.py:199): Endorsement matching uses substrings: “disagree” matches “agree,” and “incorrectly” matches “correctly.” For D4, “The return on assets is 2.53 per cent in the pack. I disagree with Buffett's claim that the return on assets is 11.8 per cent.” now scores **MIXED**; the parent commit correctly scores **CORRECTED**. Reproduced both variants.

2. [api/eval/score.py:447](C:/projects/alphacouncil-platform/api/eval/score.py:447): Attribution examines only text before the figure, so subsequent endorsement still escapes. For D4, “The pack's return on assets is 2.53 per cent. Buffett's claim that the return on assets is 11.8 per cent is correct.” scores **CORRECTED**, but must score **MIXED**.

3. [api/eval/score.py:367](C:/projects/alphacouncil-platform/api/eval/score.py:367): Reading the whole sentence introduces another dividend regression. For D2, “The dividend fell from 2.25 SAR per share to 1.1 SAR per share, while earnings cannot be derived.” now scores **INCORRECT**; the parent correctly scores **DECLINED**. Mentioning earnings afterward does not make the dividend an earnings figure.

DRIFT: The output stayed within the authorized offline pilot repair. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the owner’s gates respected.

NEXT STEP: On `rebuild`, repair these attribution and quantity-binding failures in `api/eval/score.py`, add the counterexamples to `api/tests/test_eval_score.py`, and reconcile the saved pilot analysis offline. This completes the current authorized repair before its results inform further spending.

DONE WHEN: These counterexamples score correctly, the original review-40 cases remain correct, and B/D2 stays DECLINED while B/D4 stays CORRECTED. Run `cd api; uv run pytest -q tests/test_eval_score.py tests/test_eval_probe_report.py`; re-score all 36 saved answers without changing the original record, reproduce the report, explain any changed totals, and pass `git diff --check`. Currently, I reproduced 129 scorer passes with 10 skips, all saved scores/evidence, and the report body; I did not rerun the full suite under the read-only restriction.

OWNER ITEMS:

1. Arrange Step 7’s lawyer review and provide written advice.
2. Top up shared OpenRouter credit; the recorded post-pilot balance is $7.83.
3. Explicitly confirm the already-applied `owns` patch or direct its revert, as `PROJECT.md:1293` records.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Approve further paid testing only after scoring is sound and the stale $393 quotation is remeasured.

Response complete
