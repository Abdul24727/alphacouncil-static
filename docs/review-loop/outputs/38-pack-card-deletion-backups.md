# Output 38: review 37's two fixes to the lawyer's pack

Both are in `docs/lawyer-review-pack-2026-11-06.md`; `git diff --check` is clean.

**1. The saved card** (§5.1, "Four steps decide what happens to the token", with the code named for each):
- **Cancel:** keeps the token so the member can resume, and a cancelled plan is not charged again (`cancel_renewal`,
  `resume_renewal`, and `run_renewals`' `renewing` test).
- **The end of a plan is applied by the hourly billing job**, not at the end time itself. On its first run after a
  cancelled plan's period ends, or after the third failed renewal (retried daily), `_end` clears the token and asks
  Moyasar to delete it.
- **A refund** clears the token and ends Pro **only if the refunded payment paid the current period**
  (`_refunded`). A refund of an older payment marks that payment refunded and leaves the plan and the token as they
  are.
- **Account deletion:** `forget_card` tries to delete the card and logs a failure.
- **What the records can and cannot show:** the old conclusion ("never keeps a card it can charge…") is gone. The
  site's records show when it stopped holding a token, not that Moyasar deleted its copy.

**2. What outlives account deletion** (§3 step 6, and §5.1):
- **Payment records.**
- **Rate-limit rows (IP and email).** They have no user link (`rate_hits`) and go by age, a day, on the next counted
  attempt.
- **Backups.** They keep their own schedule:
  - server `daily/` 14 and `weekly/` 8;
  - the owner's computer, 60 days daily and 400 days weekly;
  - the dumps include card-token ids.

  The backup paragraph is now one block, with its source (`docs/production.md`, "Backups").

**The pilot is still running.** Its result will be output 39.

**The question for the review:** is this sound, and what is the single next pre-approved step?
