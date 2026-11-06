# Review 25: Unit captions for unconfirmed currency; candidate de19095 (review 24 step)

2026-11-06 05:54 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `25-unit-captions.md`.

VERDICT: FIX

ISSUES:

1. `docs/release-readiness-2026-11-06.md:36` says Arabic changes only through rows 2, 3 and 6. The new caption also changes Arabic (row 5), and phone tables are now row 7. Correct this release-impact summary.
2. `research-panels.tsx:644` changes `CapitalPanel`, but `14-unit-captions.txt:1–16` and its screenshots cover only income and balance statements. The second changed panel lacks rendered verification. The statement fix is supported: screenshots look correct, 68 tests pass independently, and the inventory and eight-listing count match.

DRIFT: The output stayed within polishing existing panels, without guessing currencies or changing figures. The destination remains finished, published and polished alphacouncil.tech under PROJECT.md, preserving the owner’s decisions and approval gates.

NEXT STEP: On `rebuild`, complete the caption change’s verification for the existing capital-changes panel. Save evidence under `docs/screenshots/release-candidate-de19095/` and correct the readiness summary during that closeout. This finishes validation of the changed surface before the owner considers releasing it.

DONE WHEN: English and Arabic screenshots at 1440 and 390 px show complete capital-panel captions, with displayed figures matching the API. Cover confirmed and unconfirmed currency where database rows exist; explicitly document any unavailable case without inventing data. The readiness report accurately includes the Arabic caption change, and `git diff --stat de19095..HEAD -- web/src api deploy web/messages web/public` remains empty if only evidence and records change.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Address disk pressure and F-14’s rejected pipeline key.
3. After verification, separately authorize beta release, production release and public push.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot before deciding on the $393 run.
5. Decide on the explicitly gated `owns` patch.

Response complete
