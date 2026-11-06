# Review 16: Pipeline tooling count corrected (review 15 fix)

2026-11-06 01:08 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `16-count-corrected.md`.

VERDICT: ACCEPT

ISSUES: none.

DRIFT: The correction stayed on plan: Git confirms five pipeline files, 25 + 307 + 28 = 360, clean whitespace checks, and no candidate-to-HEAD app changes. The goal remains the finished, published, polished existing site in both languages at 1440 and 390 px, with owner approval gates intact.

NEXT STEP: On `rebuild`, correct the existing label “income from investments & Other operating income” to “Income from investments & other operating income” in `web/src/content/data-labels.json:413`, preserving the source spelling through the existing alias mechanism. Recorded at `docs/release-readiness-2026-11-06.md:126`, this is a concrete visitor-facing polish item Claude can finish now; F-16’s verification must wait until the publish, still ahead at this review’s 01:08 UTC.

DONE WHEN: `npm test` passes in `web`; local screenshots of ticker 821’s income statement in English and Arabic at 1440 and 390 px show the corrected English label, preserved Arabic, and figures matching the API. Update the readiness report to identify the new candidate and its evidence, since its app code will differ from `307d2fc`.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Give separate go-aheads for beta release, production release, and public push.
3. Address recorded disk pressure and F-14’s rejected pipeline key.
4. Retire or re-register D1/D3/D6 and authorize the $66 pilot; decide on the $393 run afterward.
5. Decide on the explicitly gated `owns` patch.

Response complete
