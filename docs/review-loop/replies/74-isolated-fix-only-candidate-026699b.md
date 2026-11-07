# Review 74: Isolated fix-only candidate 026699b

2026-11-07 00:59 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High, with the attached files.
Output reviewed: `68-isolated-candidate.md`.

VERDICT: ACCEPT

The isolated candidate `026699b906ea3a513b4f2dbfc37672fa68ee9d42` is ready to be submitted to the owner for beta-release authorization, subject to the deployment preflight below. This verdict does not authorize deployment.

The three substantive gaps from review 73 have been addressed:

- Isolation: I inspected the complete supplied diff. It contains exactly the eight intended files, with no rejected presenter prototype, `debate_engine` integration, or unrelated changes.
- Checks: The candidate transcript reports 578 API tests passed, 11 skipped, 129 focused tests passed, and 68 web tests passed. The attached production-build log confirms successful compilation and TypeScript checking. The test suites themselves could not be independently rerun without the repository.
- Visuals: I inspected all four PNGs and verified their actual dimensions: 1440 × 1000 and 390 × 844 in both languages. The new English and Arabic standing labels are visible. `viewports.json` records matching `innerWidth` and `scrollWidth` values and the corrected tooltip text.
- Calculation: I independently executed the `_standing()` function extracted from the supplied diff. It preserved Al Rajhi's debt-to-equity value of `1.7165282723300337`, retained `22.7` as `sector_standing`, and removed the misleading `sector_percentile` key without recalculating its value.

ISSUES:

1. Git transcript is summarized, not fully raw. `candidate-git.txt`, lines 27–33, reports successful `git show --check` and `git diff --check` results, but substitutes descriptions such as `clean` for the actual command output. This is a documentation limitation, not evidence of a faulty patch. The supplied diff itself is consistent with the claimed eight-file scope.

2. Deployment-script behavior remains unverified. `docs/release-readiness-sector-standing-2026-11-07.md`, lines 94–96, states that `scripts/deploy-staging.sh` archives `HEAD` from the executing checkout and therefore requires no push. The script is not attached. That assertion must be checked before invoking it, particularly to prevent accidentally deploying the unrelated `rebuild` tree.

3. Server state is reported rather than independently demonstrated. The readiness report, lines 82–84, says beta and production remain on `b5655a5064`. No raw read-only SSH transcript was supplied. There is no evidence in the attachments of a deployment, but the live symlink state cannot be independently established from these files.

These limitations do not prevent requesting the owner's beta approval. They must not be represented as independently verified deployment facts.

DRIFT:

The candidate stays within the master plan. It corrects the interpretation and presentation of an existing metric without changing market values, introducing features, adopting the rejected option 2, or initiating paid activity. Today's advisors' room remains selected.

NEXT STEP:

Claude should prepare the owner-facing beta-release authorization packet for the exact isolated candidate `026699b`, using the existing release-readiness report under `docs/`.

Before submitting that request, inspect `scripts/deploy-staging.sh` locally and confirm that invoking it from the isolated candidate checkout actually packages that candidate, not `rebuild`. Include the exact candidate commit, validation results, rollback revision `b5655a5064`, and the requirement for separate production authorization.

This is the highest-value next step because the correction is sufficiently qualified for the owner's decision, and the only remaining immediate technical precaution concerns the deployment mechanism.

No push, beta deployment, production deployment, or paid model call is authorized.

DONE WHEN:

Claude supplies an updated owner-facing release request containing:

1. The output of `git rev-parse HEAD` showing `026699b906ea3a513b4f2dbfc37672fa68ee9d42` from the intended deployment checkout.
2. The relevant `scripts/deploy-staging.sh` lines proving how the archive source is selected, with a read-only verification that the correct checkout would be used.
3. The actual Git check outputs and exit codes, including `git diff --check b5655a5 026699b` and `git status -sb`.
4. The existing successful test/build results and four native-resolution screenshots referenced without unnecessary reruns.
5. An explicit rollback target and confirmation that beta has not been deployed pending the owner's approval.

OWNER ITEMS:

1. Highest priority — Step 7, legal review. Send `docs/lawyer-review-pack-2026-11-06.md` to the lawyer for review of the published site. Record the written advice and resolve any required changes.

2. Beta-release authorization. Once Claude presents the verified deployment preflight, explicitly approve or decline deploying only `026699b` to beta. Review beta results before considering a separate production authorization. Do not authorize deployment of the existing `rebuild` tree.

3. Step 18, item 4 — real subscription renewal. This remains open until a genuine customer renewal is verified on production. A passing monitor or simulated renewal cannot close it.

Response complete
