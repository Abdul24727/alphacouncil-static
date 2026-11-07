# Review 76: Exact-commit deploy guard

2026-11-07 01:34 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High, with the attached files.
Output reviewed: `70-exact-commit-guard.md`.

VERDICT: ACCEPT

The exact-commit deployment safeguard satisfies review 75's requirements. The beta-only release of 026699b906ea3a513b4f2dbfc37672fa68ee9d42 may now be presented to the owner for authorization.

No deployment, production release, push, or paid action is authorized by this verdict.

ISSUES:

1. Non-blocking documentation discrepancy. docs/release-request-sector-standing-2026-11-07.md, lines 34–35, describes both scripts' --check output as reporting the archive and both environments' running revisions. In fact, scripts/deploy-staging.sh, lines 36–59, reports archive details and beta status, whereas scripts/deploy-production.sh, lines 40–65, reports beta and production status but no archive details. Correct the wording during the next routine documentation edit. This does not affect deployment safety.

2. Evidence limitation, not a blocker. The original candidate's complete eight-file diff, application tests, build log, and screenshots from review 74 are not attached. Their results cannot be independently reconfirmed here. Review 74 already accepted that candidate, and review 75 explicitly ruled out repeating the full application suite without an application-code change.

3. Git and server provenance limitation. 70-git-checks.txt reports four successful git show --check commands, and deploy-preflight.txt, lines 147–152, reports unchanged server revisions and four active services. The underlying repository and server are not directly accessible in this review. These are consistent supporting transcripts, not independently observed production state.

The deployment safeguards themselves passed examination:

Both attached scripts independently pass bash -n.

The supplied script diff reverse-applies cleanly to the attached versions.

Both scripts require a full 40-character SHA for non-default branches and compare it against the checkout's actual commit.

git archive uses the verified commit rather than resolving mutable HEAD again.

Missing, shortened, incorrect, and advanced-HEAD cases are rejected.

An independent local Git simulation reproduced the principal acceptance and refusal behavior.

Production's --check correctly returns nonzero when beta is running a different revision.

The documented beta preflight preserves b5655a5064 for rollback and identifies 2e44ee6fbf for pruning.

DRIFT:

No material drift. The work remains confined to safe deployment of the already-reviewed sector-standing correction, without introducing the rejected presenter prototype, additional product features, market-data changes, or paid activity.

NEXT STEP:

Claude should present the existing beta-only authorization request from docs/release-request-sector-standing-2026-11-07.md to the owner, after one final read-only confirmation from C:/AlphaCouncil-Staging/deploy-026699b.

This is the most valuable next step because the exact-commit safeguard is now verified and the remaining gate to making the correction available on beta is the owner's explicit authorization. No further application development or repeated full test suite is needed for this release.

DONE WHEN:

Claude demonstrates the following:

git -C /c/projects/alphacouncil-platform diff --quiet c3bcff6 -- scripts/deploy-staging.sh exits 0.

The exact-SHA staging --check command in the release request exits 0, identifies commit 026699b906ea3a513b4f2dbfc37672fa68ee9d42, and confirms rollback b5655a5064 is retained.

The owner receives one precise beta-only approval request explaining the release contents, expected pruning, rollback, and separate production gate.

No deployment or other owner-restricted action occurs before authorization.

OWNER ITEMS:

1. Legal review — highest overall launch priority. Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the already published site. Written advice and any required live changes remain outstanding.

2. Beta deployment authorization — immediate release decision. Approve or decline deploying exactly 026699b906ea3a513b4f2dbfc37672fa68ee9d42 to beta, acknowledging the removal of 2e44ee6fbf and retention of b5655a5064 for rollback. Production requires separate authorization after successful beta checks.

3. Step 18, item 4 — genuine renewal. The real customer subscription-renewal verification remains outstanding and cannot be replaced by a simulation.

Response complete
