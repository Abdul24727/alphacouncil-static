# Review 09: Review 08 fix; owns-case step held for the owner

2026-11-06 00:14 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `09-review-08-fix-and-gated-step.md`.

VERDICT: FIX

ISSUES:

1. The owner-only gate is unsupported by the cited repository evidence. Commit `4f787b3` adds it at [PROJECT.md:1249](C:/projects/alphacouncil-platform/PROJECT.md:1249) and attributes it to the owner at line 1773. The earlier “nobody asked for it” note records Claude’s deferral, not an owner instruction. [PROJECT.md:53](C:/projects/alphacouncil-platform/PROJECT.md:53) and the master plan explicitly pre-approve repository edits; changing a check script is not an exception.

DRIFT: The report correction and proposed normalization are sound and within scope, but adding an approval gate drifts from the master plan. The goal remains alphacouncil.tech finished, published and polished in both languages at 1440 and 390 px, preserving the recorded owner decisions.

NEXT STEP: On `rebuild`, finish the recorded case-mismatch fix in [check-advisors.mjs:51](C:/projects/alphacouncil-platform/web/scripts/check-advisors.mjs:51): apply the prepared uppercase normalization and update its status in `PROJECT.md` and the advisors README. This closes a verified reporting defect immediately while F-16 awaits publication.

DONE WHEN: The offline parser check gives identical coverage for `owns: p2, P9` and `owns: P2, P9`, preserves all seven existing advisor files’ results, and—run from `web`—`node --check scripts/check-advisors.mjs`, `npm test`, and `npm run lint` pass. I independently reproduced the parser results and confirmed `git apply --check` passes.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`; billing already opened under the recorded waiver.
2. Approve the reviewed polish’s beta/production releases and public-repository push per action.
3. Address disk pressure and F-14’s rejected pipeline key.
4. Settle D1/D3/D6 and authorize the $66 pilot; decide on the $393 run after its results.

Response complete
