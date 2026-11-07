# Review 90: Lawyer pack: review 89's fixes

2026-11-07 20:42 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `84-lawyer-pack-review-89-fixes.md`.

VERDICT: FIX

ISSUES:

docs/lawyer-review-pack-2026-11-06.md, lines 228–235 — The AI data-transfer wording remains too categorical.

The pack says Copilot and advisors' room questions, together with company data, go to externally operated language models. However, api/app/settings.py, lines 34–40 and 65–67, establishes that the Copilot can fall back to a local rule-based stand-in and that the advisors' room uses a stand-in without an OpenRouter API key.

Production's actual provider configuration has not been verified. Therefore, the pack cannot establish that every such request reaches an external provider.

Fix: Say that when externally hosted AI services are used, questions and relevant company data are transmitted to the configured provider. Explain that COPILOT_PROVIDER=auto prefers OpenRouter when its key is available, otherwise Anthropic when configured, otherwise the stand-in. Replace “any service that accepts OpenRouter's requests” with the code's precise term, “any OpenAI-compatible endpoint.”

Preserve the existing qualifications that the actual serving companies, processing countries and production routing remain unverified.

Question (h) already uses appropriately conditional wording and need not change substantively.

review-89-diff.txt, lines 1–23 — Repository-wide verification is incomplete.

The supplied diff supports Claude's claim that the shown PROJECT.md change is a status update. However, it is a path-filtered diff. Neither the complete PROJECT.md, docs/review-loop/MASTER-PLAN.md, nor an unfiltered repository diff is attached.

Consequently, the claims that no application or server files changed, that the master plan remained unchanged, and that the complete repository diff passes git diff --check cannot be independently established from these attachments.

Fix: Claude should run the full commit comparison locally and record its results. This requires no additional development.

Confirmed: Review 89's second substantive correction is valid. scripts/deploy-production.sh, lines 79–99, confirms that the initial setup copies selected settings only if production's api.env does not already exist. The pack, check record and P9 production record correctly distinguish that script behavior from unverified historical execution and current configuration.

DRIFT:

The output stays within the master plan. The work is documentation-only, preserves release ea51de796c, does not reopen the settled advisors' room decision, and introduces no features, paid calls or deployments.

NEXT STEP:

On branch rebuild, make one final documentation-only correction to the AI provider wording in docs/lawyer-review-pack-2026-11-06.md and its check record. Verify the complete diff against ac35f28, then present the existing two-document lawyer handoff to the owner for factual confirmation.

This is the highest-value pre-approved step because it removes the remaining unsupported legal-pack assertion and directly unblocks Goal 4, Step 7, without altering production.

DONE WHEN:

Claude provides evidence that:

Pack §5.2 distinguishes actual production behavior, code defaults and unverified third-party processing.

The two review-89 corrections remain intact, including the production market-data configuration limitation.

These commands pass:

Bash
git diff --check ac35f28..HEAD
git diff --name-status ac35f28..HEAD

The complete diff shows only the approved documentation and status updates, with no application, deployment-script or master-plan rule changes.

The final pack identifies the four outstanding owner facts and continues to identify docs/legal-questions-2026-10-27.md as its companion document.

No release, push, paid session or external sending is required.

OWNER ITEMS:

Confirm the four marked facts: account/payment counts; hosting provider and country; production models for the six advisors and Chair; and actual AI processing locations where ascertainable. Any location that cannot be established must remain explicitly unverified, not guessed.

Start Step 7: once the documentation correction is verified, send the updated docs/lawyer-review-pack-2026-11-06.md and docs/legal-questions-2026-10-27.md to the lawyer. Provide the live-site address and beta access privately where needed.

Obtain written legal advice: have the lawyer evaluate the live site and answer questions (a)–(i). Record the resulting advice in docs/legal-advisors-<date>.md before implementing the required changes.

The production-data-settings correction is accepted. The lawyer pack needs only the remaining AI-routing qualification and final diff verification before owner handoff.

Response complete
