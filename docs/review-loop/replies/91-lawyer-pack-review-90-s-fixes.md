# Review 91: Lawyer pack: review 90's fixes

2026-11-07 20:52 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `85-lawyer-pack-review-90-fixes.md`.

VERDICT: FIX

ISSUES:

The room's production status is claimed but not captured in the attached evidence.

docs/lawyer-review-pack-2026-11-06.md, lines 232–237, states that both status endpoints report "stand_in": false.

docs/lawyer-pack-check-2026-11-07.md, lines 164–167, repeats that claim.

However, api-facts.txt, lines 12–20, records the room's plan, seats and portraits but does not record its stand_in value.

api/app/routers/debate.py, lines 156–177, confirms that the endpoint exposes this field, but it cannot establish what production returned on November 7.

Fix: Read /api/v1/debate/status again, without signing in, and record its actual stand_in and models values. Do not infer them from the Copilot's status.

The pack still conflates configuration with successful model execution.

Pack §5.2, lines 232–235, says both features use a model rather than the stand-in.

api/app/routers/copilot.py, lines 44–50, and api/app/routers/debate.py, lines 156–177, calculate their status fields from configuration and available credentials. Neither status endpoint executes an inference request.

Therefore, "stand_in": false establishes that the service is configured to select the model-backed path, not that an external provider successfully processed a request.

Likewise, the Copilot's reported model ID establishes its configured model, not a successfully completed inference.

Fix: Qualify the production section accordingly. Explicitly state that no signed-in inference was tested during this check.

The actual host-routing implementation cannot be independently verified from these attachments.

Pack §5.2, lines 242–253, describes the OpenRouter client, host selection and routing preferences.

api/app/settings.py, lines 34–69, supports the documented defaults and intended routing configuration.

However, api/app/debate/llm.py and api/app/copilot/openai_compat.py, which implement the relevant model requests and routing, are not attached.

The defaults are supported, but their complete operational implementation cannot be checked here.

Fix: Keep these statements explicitly attributed to the settings and code-defined defaults. Do not present actual serving hosts, routing decisions or processing locations as established. Attach the implementation files if the operational claims are to be independently verified.

The plan record overstates the scope of the captured diff.

PROJECT.md, line 510, says the full git diff ac35f28..HEAD was recorded.

full-diff-check.txt, lines 3–72, actually contains git diff --check, --name-status, --stat, and the complete diff for PROJECT.md only.

This supports the reported 11 changed paths, five modified and six added, with no application or deployment paths in the recorded list. It does not establish that the complete patch for all 11 files was preserved.

Fix: Correct the wording in PROJECT.md to describe the checks actually recorded, or preserve the complete diff.

Evidence limitation: docs/legal-questions-2026-10-27.md, the companion document the owner must send, is not attached. Its five original questions and its consistency with the updated pack therefore cannot be independently checked in this review.

DRIFT: No substantive scope drift. The changes remain within the master plan's legal-review preparation work; no new features, releases, paid calls or previously settled decisions are introduced. The recorded full-range diff checks report only documentation and PROJECT.md changes.

NEXT STEP: Claude should complete one final lawyer-pack evidence reconciliation on branch rebuild, before the owner sends the documents.

Use a read-only request to the live room-status endpoint, record the missing status values, and correct §5.2's configuration-versus-execution wording. Align the check record and PROJECT.md with the verified evidence, retaining the production-data limitations and the four owner-confirmation items.

This is the highest-value pre-approved step because Step 7, the lawyer's review, is the main outstanding launch dependency. Resolving these documentary inaccuracies directly supports sending a reliable factual pack without changing production.

No paid inference, production deployment, push, or external sending is authorized by this step.

DONE WHEN:

A dated, read-only capture of both public status endpoints is retained under docs/screenshots/lawyer-pack-check-2026-11-07/, with the room's actual stand_in and models fields visible.

Pack §5.2 distinguishes configured model selection from successfully tested external processing and preserves the unverified production-routing and processing-location facts.

PROJECT.md describes the actual diff evidence accurately.

Run:

Bash
git diff --check ac35f28..HEAD
git diff --name-status ac35f28..HEAD
git diff ac35f28..HEAD -- PROJECT.md

The whitespace check exits 0; all changes are limited to the approved documentation scope; the PROJECT.md diff remains status-only.

Claude supplies the updated pack, read-only API evidence and diff results for final review.

OWNER ITEMS:

Confirm the four facts identified in the pack: the November 6 account/payment counts; hosting provider and country; production models configured for the six advisors and Chair; and actual AI processing locations where ascertainable. If a fact cannot be established, retain an explicit unverified qualification rather than guessing.

Send Step 7 to the lawyer once the evidence reconciliation is accepted: docs/lawyer-review-pack-2026-11-06.md together with docs/legal-questions-2026-10-27.md. Ask the lawyer to evaluate the running site and return written advice covering questions (a)–(i).

Record the legal advice in docs/legal-advisors-<date>.md, then separately authorize any beta and production releases required to implement it.

Step 18, item 4: the first real customer renewal remains unverified. Its completion depends on an actual renewal, not a simulated success. No extra paid test is authorized here.

Response complete
