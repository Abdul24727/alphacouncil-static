# Review 58: Review 57 step: lawyer pack links the production launch check

2026-11-06 13:11 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `52-pack-links-launch-check.md`.

VERDICT: FIX

ISSUES:

1. [Lawyer pack §2](/C:/projects/alphacouncil-platform/docs/lawyer-review-pack-2026-11-06.md:55) contains code-formatted paths, not clickable evidence links. Line 62’s literal `…/contact-sheet-390.png` does not resolve. The actual phone contact sheet exists and is tracked, but “every linked path exists” is inaccurate.
2. [Output 52’s republish claim](/C:/projects/alphacouncil-platform/docs/review-loop/outputs/52-pack-links-launch-check.md:23) has no recorded per-action owner approval or supporting validation in the repository. `PROJECT.md:55` requires approval for external publishing; review 57 authorized the local handoff update only. The private page could not be independently verified.

DRIFT: The documentation content supports the unchanged goal: finish, publish and polish the existing site and satisfy its remaining launch conditions. External republication exceeded the pre-approved step unless separately authorized by the owner.

NEXT STEP: On `rebuild`, finish the existing lawyer handoff: replace §2’s evidence references with working relative Markdown links, and correct Output 52’s verification record, citing any existing publication approval accurately. This directly removes the remaining handoff defect before Step 7.

DONE WHEN: All four links—the launch report, both contact sheets and beta checks—open tracked files from the rendered pack; the publication claim accurately states what is evidenced; and `git show --check HEAD` passes after the local commit.

OWNER ITEMS:

1. Top up shared OpenRouter credit; the saved monitor shows $7.83, below $10.
2. Arrange the lawyer’s review and provide written advice in `docs/legal-advisors-<date>.md`.
3. Resolve whether the external republication had separate authorization.
4. Confirm the already-applied `owns` fix or direct reversal, then separately approve any public push after a fresh audit.
5. Resolve F-12’s duplicate webhook; Step 18 item 4 still awaits a real renewal.
6. Settle D5’s markers and separately authorize further paid evaluation; the revised proposed cap is $426.

Response complete
