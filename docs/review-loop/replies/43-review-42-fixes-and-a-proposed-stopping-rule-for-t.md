# Review 43: Review 42 fixes and a proposed stopping rule for the word-based scorer

2026-11-06 12:02 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `43-scorer-review42-and-a-stopping-rule.md`.

VERDICT: FIX

ISSUES:

1. [docs/council-pilot-2026-11-06.md:172](C:/projects/alphacouncil-platform/docs/council-pilot-2026-11-06.md:172): The stopping rule excludes `CORRECTED` and `RESISTS` from manual review—the success labels counted by `api/eval/probe_report.py:383`. This misses false successes and can inflate results. That failure is already documented in `api/tests/test_eval_score.py:391`, where a wrong answer previously scored CORRECTED. Ending open-ended counterexample hunting is reasonable; this selective audit does not justify trusting the scorer.

DRIFT: The output stayed within the authorized offline pilot work. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the launch checklist and owner approval gates respected.

NEXT STEP: On `rebuild`, finalize item 5 of `docs/council-pilot-2026-11-06.md`: require manual review of every planted and clean answer against the existing registered rubric before reporting results. Preserve automatic scores and record human verdicts with supporting excerpts and any disagreements. This provides a bounded stopping rule and makes the analysis trustworthy before further spending.

DONE WHEN: The revised protocol covers every outcome, and the report contains a traceable audit of all 36 saved answers. Original records remain unchanged; disagreements are resolved before reporting. I reproduced **138 scorer passes, 10 skips**, all 36 saved outcomes/evidence entries, exactly the two reported changes, and the saved report body; `git diff --check` passed. The full 560-test claim was not independently rerun.

OWNER ITEMS:

1. Arrange Step 7’s lawyer review and provide written advice.
2. Top up shared OpenRouter credit; the recorded post-pilot balance is $7.83.
3. Explicitly approve the already-applied `owns` fix or direct its revert, as `PROJECT.md:1293` records.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Authorize further paid testing only after the review protocol is settled and the stale $393 quotation is remeasured.

Response complete
