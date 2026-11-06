# Review 20: F-16 after-publish check as a script (review 19 step)

2026-11-06 01:40 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `20-f16-check-script.md`.

VERDICT: FIX

ISSUES:

1. `scripts/pipeline-checks/f16_after_publish.py:76–86` can approve missing balance sheets: an empty query passes `not left`, and AMLAK’s zero rows pass `< 50`. I executed its data-check block against in-memory SQLite fixtures: all four data checks passed even with all nine balance sheets absent, provided the eight cash-flow statements existed.
2. `docs/review-loop/outputs/20-f16-check-script.md:32` misclassifies the results. The script has **eight** night/publish checks and **four** data checks. The reported ninth PASS is ADNIC’s data check; nine total passes and three failures remain consistent.

DRIFT: No scope drift: this implements the previously requested F-16 verification and correctly leaves production verification pending. The goal remains completing `PROJECT.md`: the existing site finished, published and polished in both languages at 1440 and 390 px, with the owner’s decisions and approval gates preserved.

NEXT STEP: On `rebuild`, fix the existing F-16 checker to require balance-sheet rows for all nine companies and `0 < amlak < 50`; reconcile the documentation’s counts. This is the most valuable pre-approved work before the publish because the current check can mistake missing data for a successful repair.

DONE WHEN: In-memory regression checks demonstrate that a missing balance sheet for any of the nine fails, AMLAK’s zero-row case fails, the fixed-data control passes, and the original misplaced-cash-flow case fails. Record the command and results under `docs/` and commit on `rebuild`; keep live verification pending until the actual publish check and 714/714 English-label sweep pass.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Give separate go-aheads for beta release, production release and public push when verification is complete.
3. Address disk pressure and F-14’s rejected pipeline key.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot; decide on the $393 run afterward.
5. Decide whether to apply the explicitly gated `owns` patch.

Response complete
