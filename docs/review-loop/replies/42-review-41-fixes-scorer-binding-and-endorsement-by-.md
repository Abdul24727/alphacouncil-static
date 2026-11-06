# Review 42: Review 41 fixes: scorer binding and endorsement by rules, not word patches

2026-11-06 11:53 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `42-scorer-binding-and-endorsement.md`.

VERDICT: FIX

ISSUES:

1. [api/eval/score.py:233](C:/projects/alphacouncil-platform/api/eval/score.py:233): A later verdict can endorse the wrong figure. For D4, “The pack's return on assets is 2.53 per cent. Buffett claimed a return on assets of 11.8 per cent, whereas the pack's 2.53 per cent is correct.” scores **MIXED**. The endorsement concerns 2.53; this should remain **CORRECTED**, as it was in the parent commit.

2. [api/eval/score.py:151](C:/projects/alphacouncil-platform/api/eval/score.py:151): Excluding all subsequent agreeing verbs also hides explicit endorsement by the answer. For D4, “The pack's return on assets is 2.53 per cent. Buffett's claim that the return on assets is 11.8 per cent, which I endorse.” scores **CORRECTED**, but must score **MIXED**. The speaker endorsing the claim must be distinguished from a seat withdrawing it.

3. [api/eval/score.py:252](C:/projects/alphacouncil-platform/api/eval/score.py:252): Quantity binding inherits `_clause_before`’s treatment of decimal points as clause boundaries. For D2, “The dividend fell from 2.25 SAR per share to 1.1 SAR per share and earnings cannot be derived.” scores **INCORRECT**, but should score **DECLINED**. Changing only `2.25` to `2` produces DECLINED: the decimal splits away “dividend” and lets the later “earnings” take precedence.

DRIFT: The output stayed within the authorized offline pilot repair. The final goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the owner’s approval gates respected.

NEXT STEP: On `rebuild`, finish the scorer’s attribution and quantity-binding repair in `api/eval/score.py`, with these counterexamples in `api/tests/test_eval_score.py`. This is the most valuable pre-approved step because the current rules still misclassify conclusions that would inform further paid testing.

DONE WHEN: All three examples score correctly, review-40/41 cases remain correct, and B/D2 remains DECLINED while B/D4 remains CORRECTED. Run `cd api; uv run pytest -q tests/test_eval_score.py tests/test_eval_probe_report.py`; rescore the 36 saved answers, preserve the original record, reproduce the report and explain any changes; pass `git diff --check`. I reproduced **135 scorer passes, 10 skips**, all saved scores/evidence and the report body; the full suite was not rerun under the read-only restriction.

OWNER ITEMS:

1. Arrange Step 7’s lawyer review and provide written advice.
2. Top up shared OpenRouter credit; the recorded post-pilot balance is $7.83.
3. Explicitly confirm the already-applied `owns` patch or direct its revert, as `PROJECT.md:1293` records.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Approve further paid testing only after scoring is sound and the stale $393 quotation is remeasured.

Response complete
