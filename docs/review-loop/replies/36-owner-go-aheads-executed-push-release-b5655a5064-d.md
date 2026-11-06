# Review 36: Owner go-aheads executed: push, release b5655a5064, disk, F-14, test accounts, probes; lawyer pack

2026-11-06 10:56 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `36-go-aheads-executed.md`.

VERDICT: FIX

ISSUES:

1. **The `owns` approval is not evidenced.** [PROJECT.md:1292](C:/projects/alphacouncil-platform/PROJECT.md:1292) attributes applying `5a46b8b` to “finish every thing.” The recorded four approvals omit this patch, while [MASTER-PLAN.md:85](C:/projects/alphacouncil-platform/docs/review-loop/MASTER-PLAN.md:85) expressly requires asking before applying it. The output should not call this specifically approved without that confirmation.
2. **The lawyer pack confuses expiry with deletion.** [Its retention table](C:/projects/alphacouncil-platform/docs/lawyer-review-pack-2026-11-06.md:124) says both email links last one hour; verification actually lasts **48 hours** (`api/app/auth.py:55`). Expired sessions are rejected, not automatically deleted (`auth.py:183`); reset cleanup happens on another reset request (`auth.py:417`), and used verification records remain (`auth.py:540`). These are not guaranteed deletion deadlines.
3. **The saved-card description is inaccurate.** The same table, line 131, says retention ends at cancellation and provider deletion succeeds before account deletion. Cancellation retains the token for resumption (`api/app/billing.py:305`); expiry clears the token but retains brand/last-four fields (`billing.py:458`). Account deletion merely attempts Moyasar token deletion and logs failures (`billing.py:330`).

DRIFT: The release, maintenance, pilot and lawyer preparation stay within finishing and verifying the existing site; the additional legal questions address existing functionality. Treating the general instruction as approval for the expressly gated `owns` patch departs from the master plan’s approval rule.

NEXT STEP: Correct §5.1 of `docs/lawyer-review-pack-2026-11-06.md` on `rebuild`, documenting actual retention and saved-card behavior with code references. This pre-approved documentation work makes the handoff accurate for Step 7, the main remaining launch dependency.

DONE WHEN: The revised table separates token validity from record deletion, accurately describes cancellation and unsuccessful provider deletion, and cites the implementing functions; `git diff --check` passes.

OWNER ITEMS:

1. Arrange the lawyer’s review and provide written advice for Step 7.
2. Top up the shared OpenRouter balance.
3. Explicitly resolve the already-applied `owns` patch’s approval.
4. Resolve F-12’s duplicate webhook in Moyasar.
5. Approve the next push after its exact-range audit.
6. Consider the full paid run only after the pilot report and remeasured bound; $393 remains an outdated quotation.

Response complete
