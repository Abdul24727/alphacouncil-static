# Review 88: Lawyer pack checked against the live site

2026-11-07 20:18 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `82-lawyer-pack-check.md`.

VERDICT: FIX

ISSUES:

1. Live AI model providers are presented as verified facts when only their configured defaults were checked.

File: docs/lawyer-review-pack-2026-11-06.md, lines 215–218.

The pack states that DeepSeek serves the Copilot and six advisors, while Anthropic's Claude serves the Chair.

However, docs/lawyer-pack-check-2026-11-07.md explicitly acknowledges that production's model settings were not read because they reside in a file containing credentials.

The Copilot's live model is confirmed by /api/v1/copilot/status, but the six advisors' and Chair's actual production models are not independently confirmed.

Fix: Distinguish verified live configuration from documented defaults. Identify the production model providers as unverified until the owner confirms them. Do not expose credentials. This matters to the lawyer's assessment of third-party processing and international data transfers.

2. The assertion that production and beta use identical market data is stronger than the available evidence.

Files: docs/lawyer-review-pack-2026-11-06.md, lines 87–89; docs/release-production-p9-2026-11-07.md, lines 89–101.

scripts/deploy-production.sh, lines 80–83, confirms that production's market-data configuration was copied from beta during initial setup.

The P9 production record explicitly states that the current configuration was not re-read.

Thus, identical released code is established, but continued equivalence of the live market-data configuration is not independently established.

Fix: Say that production and beta were configured to use the same market-data sources at setup, with current configuration equivalence not independently reverified. Retain the already documented limitation on signed-out production checks.

3. A legacy contact-page discrepancy was missed in the lawyer handoff.

Evidence: docs/screenshots/lawyer-pack-check-2026-11-07/page-text/legal-terms.en.txt and legal-cookies.en.txt, with the same contact reference appearing in Arabic.

The legal documents describe https://alphacouncil.tech/contact.html as the contact page. The live URL redirects to /legal, rather than a dedicated contact page.
AlphaCouncil

The check reviewed legal-document addresses, but did not report this discrepancy within their contents.

Fix: Add this as a known legacy-document issue under question (e) for the lawyer. Do not rewrite the published legal texts before receiving legal advice.

4. Changes to the controlling plan documents cannot be audited from the attachments.

File: docs/lawyer-pack-check-2026-11-07.md, final section, “The repository after this check”.

The record says PROJECT.md and docs/review-loop/MASTER-PLAN.md were changed.

Neither file nor its modification diff is included in the attached archives.

The master plan in the review prompt is available, but that does not establish what was changed in the repository.

Fix: Verify the actual diffs against their preceding versions and record that they contain status updates only, without changing project objectives, authorization rules, or settled decisions. Any unsupported change must be reverted.

DRIFT:

The work remains aligned with Step 7: preparing the existing live site for legal review without introducing features, deployments, or paid calls. The four identified corrections and evidence gaps concern handoff accuracy, not scope expansion. The unprovided plan-file diffs prevent complete verification of the reported repository changes.

NEXT STEP:

Claude should complete one targeted, documentation-only correction pass on branch rebuild, updating docs/lawyer-review-pack-2026-11-06.md and docs/lawyer-pack-check-2026-11-07.md, adding the legacy contact-link issue for the lawyer, and verifying the plan-file diffs.

Preserve the already supported corrections: /legal#merchant, the distinction between the rule-based council and the AI advisors' room, release ea51de796c, the VAT disclosure, and the implemented renewal-reminder logic.

No additional production deployment, paid model session, new tool, or legal-text rewrite is necessary.

This is the highest-value pre-approved step because the remaining major launch dependency is the owner's legal review. Completing an accurate, qualified handoff enables that review without reopening completed engineering work.

DONE WHEN:

Claude provides:

A revised lawyer pack that clearly distinguishes verified live facts, configured defaults, and owner-confirmation items.

An updated check record documenting all corrections and the contact-link discrepancy.

Evidence that changes to PROJECT.md and MASTER-PLAN.md did not alter the controlling plan or approvals.

A successful git diff --check, together with a reviewed diff limited to the authorized documentation and status changes.

A final handoff identifying exactly the two documents the owner should give the lawyer and the facts still awaiting owner confirmation.

No push, release, payment, or external communication should occur.

OWNER ITEMS:

Confirm the handoff facts: four accounts, one refunded owner payment, no paying customers, the hosting provider and hosting country, and the actual live AI providers if available. The account/payment counts are historical as of November 6, not independently refreshed.

Send the corrected legal pack together with docs/legal-questions-2026-10-27.md to the lawyer. Supply access to the live site and the beta password privately. Only the owner authorizes any real payment and refund involved in testing.

Obtain the lawyer's written findings on questions (a)–(i), especially CMA authorization, commercial market-data rights, the named advisors' likenesses, Moyasar disclosures, Saudi data-protection obligations, and recurring billing. Record the resulting advice in docs/legal-advisors-<date>.md; subsequent releases remain subject to separate owner authorization.

Response complete
