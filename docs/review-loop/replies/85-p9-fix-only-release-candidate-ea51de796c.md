# Review 85: P9 fix-only release candidate ea51de796c

2026-11-07 13:47 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `79-p9-release-candidate.md`.

VERDICT: ACCEPT

ISSUES:

1. No blocking defect in the release candidate. I independently verified that candidate-ea51de796c.patch applies cleanly to the four supplied production files and reproduces all four candidate files byte for byte. All eight supplied file hashes match candidate-checks.txt lines 25–28. The patch changes exactly the four P9 files, with no additional paths. All four candidate Python files pass syntax parsing.

2. Non-blocking evidence limitation — test and reproduction logs. candidate-checks.txt lines 43–55 report 21 + 4 selected P9 tests passing, 153 related tests passing, and 602 passing with 11 skipped for the full API suite. However, the complete repository, dependencies, reproduction scripts, and reference outputs are not attached, so I cannot independently rerun those checks. The supplied harness and output are consistent. In candidate-checks-harness.sh lines 44–48, Ruff compares diagnostic counts rather than individual findings; identical findings are therefore not independently established, although the reported counts are unchanged.

3. Non-blocking evidence limitation — deployment preflight. staging-preflight.txt lines 8–20 records a successful exact-commit --check, including the candidate SHA, rollback target and proposed pruning. The actual scripts/deploy-staging.sh is not attached, so its current implementation cannot be independently inspected. The captured preflight supports readiness to request beta approval, not authorization to deploy.

The supplied evidence establishes no release-blocking contradiction. The report correctly distinguishes deterministic checks from unproven model behavior: the fix does not guarantee that advisors will stop inventing figures. That requires a paid session to measure.

DRIFT:

No drift. The candidate retains today's advisors' room, contains only the previously accepted P9 correction, excludes the rejected presenter prototype, and makes no web, pipeline, payment or feature change. Nothing has been pushed or deployed.

NEXT STEP:

Claude should now present the owner with a single, explicit request for permission to deploy the P9 candidate to beta only, using the already prepared release instructions in docs/release-readiness-p9-2026-11-07.md, lines 36–47.

The request must identify:

Exact commit: ea51de796cf3bbdbea21a45f35682335eab5a2f8

Branch: release/p9-no-statements

Destination: beta only

Rollback: 026699b906

Expected pruning: 5c18a3ae46

Evidence: successful exact-SHA preflight and candidate checks

This is the shortest remaining path to exercising the accepted correction on a running environment. Claude must not deploy, push, or make paid model calls without the applicable owner's approval.

DONE WHEN:

Claude has placed the exact beta-only approval request before the owner, citing the existing report and preflight evidence, with a clear yes/no decision requested.

Until approval, confirm that both environments remain on 026699b906 using the previously demonstrated read-only readlink -f checks. No further implementation or review round is needed before requesting authorization.

OWNER ITEMS:

Beta deployment authorization — immediate. Explicitly approve or reject deployment of commit ea51de796c to beta only.

Lawyer review — outstanding launch requirement. Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the published site. Step 7 has not started.

Production deployment authorization — later. A separate go-ahead is required after the beta release and its checks are reviewed.

Real renewal verification — later. Step 18 item 4 remains dependent on an actual customer renewal; it cannot be simulated as completed.

Response complete
