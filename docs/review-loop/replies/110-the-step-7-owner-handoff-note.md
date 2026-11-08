# Review 110: The Step 7 owner handoff note

2026-11-08 14:39 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `104-step7-owner-handoff-note.md`.

VERDICT: FIX

ISSUES:

1. Incorrect handling of confidential legal advice — docs/step7-lawyer-handoff-2026-11-08.md, line 40. The note instructs the owner to save the lawyer's written advice directly into docs/legal-advisors-<date>.md, or give it to Claude to save. This conflicts with the accepted lawyer pack, §7, lines 364–370, and legal-questions-2026-10-27.md, lines 174–179. Those require an owner-written summary of the advice, excluding client names, personal data and fee details. The repository is public. Fix: Replace line 40 with an instruction for the owner to record only the advice, decisions and required changes in a sanitized summary. Do not commit the lawyer's original correspondence.

2. Pinned links become outdated if the pack changes — handoff note, lines 17 and 24–27. Line 17 correctly requires correcting the pack if the owner's confirmed facts differ. However, lines 24–27 offer links permanently pinned to 7b32e2d. Those links would still show the old facts. Fix: State explicitly that, following a correction, the owner must send the corrected document as an attachment, or authorize a new public push and use the newly verified commit-pinned link. Never send the old link as the corrected version.

3. Git verification claims lack independent evidence — Output 104, items 2, 6 and 7. The attached documents establish the handoff note's wording and consistency with the accepted pack. They do not establish commit 2a2a0dd, the reported clean tree, plan-file status-only changes, or the SHA-256 equality of published files. No Git logs, diffs or hash-check output were attached. These claims remain unverified, not disproven.

DRIFT:

The output stays within the master plan: no new features, no reopened decisions, no unauthorized publishing, payments or releases. The two handoff defects concern accuracy and confidentiality, not scope expansion. The final goal remains a finished, published and polished AlphaCouncil site, with Step 7 legal advice implemented and Step 18's real renewal verified.

NEXT STEP:

Claude should make one documentation-only correction to docs/step7-lawyer-handoff-2026-11-08.md on rebuild, fixing Issues 1 and 2.

Preserve the accepted lawyer pack and its two-document handoff. Do not alter either source document, contact the lawyer, push, deploy or make paid calls.

This is the highest-value pre-approved action because it removes the remaining defects from the instructions the owner needs to start Step 7 safely.

DONE WHEN:

Claude provides:

git diff --check — passes.

git diff -- docs/step7-lawyer-handoff-2026-11-08.md — shows only the two corrections.

A read-back confirming that the note requires an owner-written, sanitized advice summary and prevents outdated pinned links being sent after corrections.

git status -sb and the local commit SHA, demonstrating the work remains local without an unauthorized push.

No additional review pack or new tooling is needed.

OWNER ITEMS:

1. Highest priority — confirm the three facts: account/payment/refund counts, Hostinger and the VPS data-centre country, and AI processing locations if ascertainable. Unknown AI locations may remain explicitly unverified; they must not delay the lawyer handoff.

2. Start Step 7: send the corrected, accepted docs/lawyer-review-pack-2026-11-06.md and docs/legal-questions-2026-10-27.md to the lawyer. Provide access to the live site and the beta password privately. The lawyer must assess the live product and answer questions (a)–(i).

3. On receiving legal advice: record a sanitized owner summary in docs/legal-advisors-<date>.md. Claude may prepare the required changes, but beta and production releases each require separate owner approval.

4. Step 18, item 4: verify the first genuine customer renewal when it occurs. Do not simulate one.

5. Optional, lower priority: complete the Argaam username exact-value check only if the value is obtainable without signing in. Never commit the username.

Response complete
