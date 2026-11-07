# Review 87: P9 fix released to production (ea51de796c)

2026-11-07 19:59 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `81-p9-production-release.md`.

VERDICT: ACCEPT

ISSUES:

1. P9's production behavior is not yet proven — non-blocking for release acceptance. docs/release-production-p9-2026-11-07.md, lines 87–98. The evidence establishes that production runs ea51de796c, both services restarted from that release, and all 3,566 manifest-listed files match. The four changed-file hashes also match the supplied beta manifest. However, production's Pro-only statement notes were not read, and no paid advisor session tested whether fabricated statement figures have stopped. Beta's 76 changed notes and 638 unchanged notes support the fix, but production has its own database. Action: record deployment as complete; retain P9 behavioral verification as outstanding until an owner-authorized paid test. Do not claim the behavior is proven.

2. Transient connection failure remains unexplained — non-blocking. launch-check/run.txt, check-data-fixes-attempt1.txt and pages-attempt1.txt show two failures around 19:39 UTC. rerun.txt confirms both subsequently passed unchanged. connection-drop.txt shows zero recorded nginx errors, zero 5xx responses, no fail2ban action, active services and successful server-local monitoring. Those observations do not establish external availability during the interruption. Action: retain the incident record; investigate if the symptom recurs. The successful reruns do not justify rollback.

3. Source-verification boundary. The deployment script, underlying web/scripts/check-*.mjs scripts, page-shot script and live Git repository are not attached. Therefore their complete behavior cannot be independently audited here. The attached wrappers, preflight, command output and logs support the reported results, including the reviewed-script comparison and exact-commit guard. This is an evidence limitation, not an identified release defect.

DRIFT: No material drift. The release follows the approved fix-only path, retains today's advisors' room, introduces no prototype or additional features, and shows no unauthorized push or paid model call. The production deployment is complete; the remaining legal and functional-verification items remain open under the original plan.

NEXT STEP: On rebuild, perform a read-only final handoff check for Step 7 (lawyer review). Open docs/lawyer-review-pack-2026-11-06.md, verify that its public URLs and descriptions still correspond to the live ea51de796c site, and prepare a concise owner-ready handoff identifying the pack, live URL, current release and any discrepancy requiring correction. This is the highest-value pre-approved work because the lawyer's written advice is the principal outstanding launch dependency, and the published site is ready for evaluation. Do not send the pack, change legal wording, deploy, push or incur paid model costs.

DONE WHEN: Claude provides a dated check under docs/ showing:

The handoff references https://alphacouncil.tech and production release ea51de796c.

Every public URL referenced by the lawyer pack was checked using read-only HTTP requests, with its actual status or redirect recorded.

The pack's description of the existing advisors' room was checked against the current site's public wording.

Any discrepancies are identified explicitly; otherwise, the record states that none were found.

git status --short and git diff --check confirm that the only local changes are the intended documentation, with no release, push or external communication.

OWNER ITEMS:

1. Highest priority — Step 7: Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the published website. Obtain written advice for docs/legal-advisors-<date>.md. Claude may subsequently implement required changes under the existing approval rules.

2. P9 functional verification: Authorize a specifically scoped, paid production session if the owner wants direct evidence that the advisors no longer invent financial-statement figures. No paid run is authorized by this review.

3. Step 18, item 4: Await and verify a genuine customer renewal. A successful renewal-job check is not proof of a completed renewal payment.

4. Repository protection: Separately authorize any proposed push of rebuild to the public remote. The claimed 76 unpushed commits cannot be independently counted from these attachments; verify the ahead count before requesting approval.

5. Optional, non-blocking: F-12 duplicate webhook cleanup in Moyasar and optional server hardening remain owner-controlled. Neither is required to accept this P9 release.

Response complete
