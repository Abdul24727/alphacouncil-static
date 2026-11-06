# Review 37: Review 36 fixes: lawyer pack retention table from code; owns approval recorded exactly

2026-11-06 10:59 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `37-pack-retention-and-owns-approval.md`.

VERDICT: FIX

ISSUES:

1. The saved-card claims remain too broad. [The pack’s refund statement and conclusion](/C:/projects/alphacouncil-platform/docs/lawyer-review-pack-2026-11-06.md:142) omit that `_refunded` clears the token **only when the refunded payment covers the current subscription period** ([billing.py:377](/C:/projects/alphacouncil-platform/api/app/billing.py:377)). Also, period expiry does not immediately clear it: the renewal job must execute `_end`. Replace “never keeps a card … after a plan ends” with the actual cleanup triggers.
2. [The deletion walkthrough](/C:/projects/alphacouncil-platform/docs/lawyer-review-pack-2026-11-06.md:71) still promises everything disappears except payments. Account deletion removes the user and cascading records, but `rate_hits` has no user foreign key ([appdb.py:237](/C:/projects/alphacouncil-platform/api/app/appdb.py:237)); its email/IP entries survive until age-based cleanup. Backup copies also follow their separate retention schedule.

DRIFT: This output stays within finishing, publishing and polishing the existing site, without adding scope. The earlier `owns` approval departure remains unresolved; accurately recording it does not supply the missing approval.

NEXT STEP: On `rebuild`, correct these remaining retention statements in §§3 and 5.1 of `docs/lawyer-review-pack-2026-11-06.md`. This pre-approved documentation correction makes the handoff reliable for Step 7, the principal remaining launch dependency.

DONE WHEN: The pack distinguishes current-period refunds from older refunds, expiry from cleanup execution, and account-record deletion from retained rate-limit entries and backups, with implementing code references. `git diff --check` passes; the current committed correction already passes that check.

OWNER ITEMS:

1. Arrange the lawyer’s review and provide written advice in `docs/legal-advisors-<date>.md`.
2. Top up the shared OpenRouter balance.
3. Explicitly confirm the applied `owns` patch or direct its revert.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Approve the next public push after its exact-range audit.
6. Decide on the full paid run after the pilot report and updated cost bound; the old $393 quotation needs remeasurement.

Response complete
