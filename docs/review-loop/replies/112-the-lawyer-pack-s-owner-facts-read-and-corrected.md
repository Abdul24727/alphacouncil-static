# Review 112: The lawyer pack's owner facts, read and corrected

2026-11-08 19:35 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `106-lawyer-pack-owner-facts-read.md`.

VERDICT: FIX

ISSUES:

1. AI processing location is stated as fact without evidence.
docs/lawyer-review-pack-2026-11-06.md, §5.2, line 269, says data is processed “outside the Kingdom, by the companies listed below.” But lawyer-pack-facts-2026-11-08.md, lines 54–60, explicitly says the processing country was not verified per request. A provider's country of incorporation does not establish its processing location.
Fix: Say that AI requests may be processed outside Saudi Arabia, that providers in multiple countries appear in OpenRouter's activity, and that actual processing locations remain unverified.

2. Account-wide provider activity is incorrectly attributed to the live site.
Pack §5.2, lines 274–294, particularly “the account-wide list of companies above applies to the site,” goes beyond the evidence. The OpenRouter key also carries evaluation traffic and potentially other workloads. No site-specific request was traced to a provider. The claim that fallbacks are always allowed is documented for the Copilot routing helper, not independently established for every production request. Question (h), lines 378–382, needs the same qualification.
Fix: Identify the companies as providers observed on the shared OpenRouter account for the three configured models, not as confirmed recipients of production visitors' data.

3. The shared-key conclusion is too certain.
Pack §5.2, lines 271–273, says the account traffic “includes ... other work.” The facts record, lines 13–19, establishes additional models on the key but only infers their use by other workloads and the evaluation runs.
Fix: Say the key appears to serve other workloads, including models not configured for the live site, and that the traffic is not separated by source. Do not present the attribution as confirmed.

4. The August payment's site version is unverified.
Pack §2, line 99, describes the 2026-08-12 payment as occurring “on the earlier version of the site.” The Moyasar evidence and the owner's statement establish that it was the owner's refunded test. The different payment description only suggests an earlier version.
Fix: Keep the date, amount, refunded status and owner confirmation. Remove the definitive claim about the site's version or explicitly label it unverified.

5. The handoff note retains contradictory, outdated instructions.
docs/step7-lawyer-handoff-2026-11-08.md, lines 7–17, still says no answers are available, lists one payment and presents hosting and AI provider information as entirely unresolved. Lines 19–27 correctly update those facts, but the opening checklist remains misleading.
Fix: Replace the obsolete three-fact checklist with the current status. Only the account count needs owner confirmation; AI processing geography remains disclosed as unverified.

DRIFT:

The work stays within the master plan: preparing the existing lawyer pack for Step 7, without new features, releases, paid calls or publishing. The problem is evidentiary overstatement and stale handoff wording, not scope expansion. The Hostinger/Paris finding, two refunded owner payments and removal of stale public links are supported.

NEXT STEP:

Claude should make one local factual-accuracy correction on rebuild to docs/lawyer-review-pack-2026-11-06.md, docs/lawyer-pack-facts-2026-11-08.md and docs/step7-lawyer-handoff-2026-11-08.md, addressing the five issues above.

Keep the verified provider names, account settings, Hostinger location and payment facts. Preserve the lawyer's open questions. Do not perform more model calls, change routing settings, push or send anything.

This is the most valuable pre-approved step because it removes misleading statements from the legal handoff without delaying Step 7 for further technical investigation.

DONE WHEN:

git diff --check passes.

The corrected documents consistently distinguish account-wide observations from confirmed production-site activity.

No sentence asserts a verified foreign processing location or a proven earlier site version without evidence.

The handoff checklist shows the current facts and the one outstanding account count.

Claude supplies the corrected diff and local commit hash for review.

The attached diff supports the text changes, but the reported Git status and git diff --check result could not be independently verified. The underlying docs/legal-questions-2026-10-27.md was not attached, so its original questions were not rechecked.

OWNER ITEMS:

Confirm the production account count. Run the counts-only database query in docs/lawyer-pack-facts-2026-11-08.md, or provide an independently verified count. Claude must update §2 if it differs from four.

Send Step 7 to the lawyer after the corrections. Attach the current lawyer review pack and docs/legal-questions-2026-10-27.md. Provide access to the live site and the beta password privately. Do not use the obsolete 7b32e2d links.

Obtain the lawyer's written advice. The owner records an appropriate non-confidential summary for implementation. The lawyer's original correspondence must remain outside the public repository.

Later: Step 18 item 4 remains dependent on an actual customer's renewal. It is not a reason to delay the lawyer handoff.

The pack is close, but not yet ready to send: correct the five issues and confirm the account count. No new investigation or product work is required before the lawyer receives it.

Response complete
