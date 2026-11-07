# Review 89: Lawyer pack: review 88's fixes

2026-11-07 20:32 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `83-lawyer-pack-review-88-fixes.md`.

VERDICT: FIX

ISSUES:

Review 88's four requested corrections are substantially present. I checked the lawyer pack, check record, contact evidence, merchant JSON files, routing code and plan diff. The contact-page and Arabic privacy-email discrepancies are correctly documented, and the plan diff contains status updates rather than changes to the objective, approvals or settled decisions.

Two remaining factual qualifications should be fixed before the owner sends the pack.

1. AI processing location and routing are still presented as confirmed facts.

File: docs/lawyer-review-pack-2026-11-06.md, lines 225–237 and 314–316.

The pack states that questions and company data go to language models outside Saudi Arabia and that OpenRouter chooses the serving host.

Checked: api/app/settings.py, lines 34–54, permits different providers and OpenAI-compatible endpoints. api/app/copilot/openai_compat.py, lines 113–126, applies OpenRouter routing settings conditionally. The live API evidence confirms the Copilot's configured model, not its actual serving host or processing jurisdiction.

Fix: Distinguish the released code's default routing from production-confirmed routing. State that data may be processed outside Saudi Arabia, but the actual serving providers, processing countries and production routing settings were not verified. Qualify question (h) accordingly. Do not assert a particular jurisdiction without evidence.

2. The historical beta-to-production data-copy claim exceeds the attached proof.

Files: docs/lawyer-review-pack-2026-11-06.md, lines 93–99; docs/lawyer-pack-check-2026-11-07.md, lines 167–173; docs/release-production-p9-2026-11-07.md, lines 96–101.

Checked: scripts/deploy-production.sh, lines 79–99, copies market-data settings from staging only when the production environment file does not already exist.

The script demonstrates the intended first-setup behavior, but the attachments do not include the original setup execution evidence or current production environment values.

Fix: Say that the deployment script is configured to copy staging's market-data settings when first creating production's environment file. Whether that copy executed, and whether the production and beta settings currently match, are not established by this evidence. Preserve the existing qualification that identical P9 notes on production remain unverified.

No new site feature, legal document or production change is needed for either correction. The inherited billing and signed-in behavior claims rely partly on files not included in these bundles; this review does not independently reverify them.

DRIFT:

No scope drift. The work remains within the original launch plan's Step 7 legal handoff. The established room design, live release ea51de796c, legal texts, approval gates and owner's decisions remain unchanged.

NEXT STEP:

On branch rebuild, perform one final documentation-only factual correction to the two claims above in the lawyer pack, the check record and the P9 production record.

This is the highest-value pre-approved step because it removes the remaining unsupported statements from material the lawyer will use to assess data protection and regulatory obligations. Do not change the site's legal texts, deploy, push, send documents or make paid calls.

DONE WHEN:

Claude provides the precise documentation diff showing both corrections and confirms:

git diff --check passes.

git diff -- PROJECT.md docs/review-loop/MASTER-PLAN.md shows no new changes to the master plan.

The lawyer pack no longer asserts unverified production routing, processing jurisdiction or executed environment-copy behavior as fact.

The existing contact-page issue, Arabic privacy-email issue, model defaults, production release and renewal facts remain intact.

No application code or production files changed.

OWNER ITEMS:

Confirm the lawyer pack's outstanding facts: the account/payment counts, production hosting provider and country, and the actual production models used by the six advisors and Chair. Confirm AI routing and processing jurisdiction where evidence is available; otherwise keep them explicitly unverified for the lawyer.

Send the two documents to the lawyer: docs/lawyer-review-pack-2026-11-06.md and docs/legal-questions-2026-10-27.md, after the final corrections and confirmations. Provide beta access privately. The lawyer must review the running site and address questions (a)–(i).

Record the lawyer's written advice in docs/legal-advisors-<date>.md and authorize any resulting changes that require an owner checkpoint.

Step 18, item 4: await and verify a real customer's first renewal. The optional duplicate Moyasar webhook and server hardening remain owner-controlled but are not prerequisites for sending the lawyer pack.

Response complete
