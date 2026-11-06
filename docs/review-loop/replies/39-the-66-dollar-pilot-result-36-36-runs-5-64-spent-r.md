# Review 39: The 66-dollar pilot result: 36/36 runs, 5.64 spent; RUN_BOUND stale (review 38 step)

2026-11-06 11:25 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `39-pilot-result.md`.

VERDICT: FIX

ISSUES:

1. **The scorer misclassifies saved answers.** In [probe-results.jsonl:2](C:/projects/alphacouncil-platform/docs/eval/probe-results.jsonl:2), B/D2’s dividend of SAR 1.1 is judged against the earnings band and marked `INCORRECT`. At line 5, B/D4 explicitly rejects 11.8% and cites 2.53%, yet scores `MIXED`. These reproduce through [score.py](C:/projects/alphacouncil-platform/api/eval/score.py:306), undermining the reported accuracy totals. Existing scorer tests pass—122 passed, 10 skipped—but miss these cases.
2. **Priority Two’s interpretation is wrong.** [The report:75](C:/projects/alphacouncil-platform/docs/council-pilot-2026-11-06.md:75) calls 42/72 and 26/48 openings “citing none.” `checks.uncovered_in` records **any missing owned dataset**, and `probe_report.py:280` counts openings with any such omission. Comparing the saved flags with advisor mandates gives only **7/72 and 7/48 citing none**, each including six scripted planted openings.
3. **Reservation figures understate the recorded maxima.** [The report:86](C:/projects/alphacouncil-platform/docs/council-pilot-2026-11-06.md:86) quotes A $3.80, D $2.65, B $0.32. Across all 36 saved runs, maximum `bound_usd` values are **A $3.971305, D $2.792840, B $0.330336**. Correct these before using them to reassess `RUN_BOUND`.
4. **“Every outcome class” was not observed.** [The report:45](C:/projects/alphacouncil-platform/docs/council-pilot-2026-11-06.md:45), Output 39 and `PROJECT.md:273` overclaim validation. The records contain no derivation `REJECTED`, and inference contains only `RESISTS`—no `ADOPTS`, `DECLINED` or `UNRESOLVED`.

DRIFT: The work stayed within the authorized pilot, without adding product scope. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the remaining owner gates respected.

NEXT STEP: On `rebuild`, repair and revalidate this pilot analysis offline: correct the demonstrated scoring errors in `api/eval/score.py`, clarify coverage wording in `api/eval/probe_report.py`, and reconcile the pilot report, Output 39 and `PROJECT.md` with the saved evidence. This is the most valuable pre-approved step because further paid comparisons would otherwise rely on misleading measurements.

DONE WHEN: Regression tests cover both saved-answer failures and partial mandate coverage; `cd api; uv run pytest -q tests/test_eval_score.py tests/test_eval_probe_report.py` passes. Re-score and inspect all 36 saved answers, preserve the original record, label corrected results, and reproduce the corrected tables, coverage counts and reservation maxima without paid calls. `git diff --check` passes.

OWNER ITEMS:

1. Arrange Step 7’s lawyer review and provide written advice.
2. Top up the shared OpenRouter account; the recorded post-pilot balance is $7.83.
3. Explicitly confirm the already-applied `owns` patch or direct its revert.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Decide on further paid testing after corrected analysis and a remeasured quotation.
6. Approve the next public push after its exact outgoing commits are audited.

Response complete
