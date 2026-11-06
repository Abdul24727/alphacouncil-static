# Output 37: review 36's three fixes

**1. The `owns` approval, recorded exactly.**
- **What the owner said:** the owner's message answered a list that named "the `owns` patch" with "finish every thing
  first".
- **What it did not cover:** the four-question confirmation that followed did not name the patch, and the plan asks
  for an explicit go-ahead.
- **Where it is recorded:** the §9 line and the changelog entry in `PROJECT.md` now say this in those words.
- **What happens next:** it is put to the owner to confirm, or to have reverted with `git revert 5a46b8b`. That
  commit changes the check script only.

**2 and 3. The lawyer's pack §5.1, rewritten from the code** (`docs/lawyer-review-pack-2026-11-06.md`). The table now
has separate columns for how long a token **works** and when its **record is deleted**, with the implementing code
named for each row.
- **Sessions:** 30 days (`SESSION_DAYS`), and an expired one is refused. The record is deleted at sign-out, at a
  password reset, or with the account; otherwise an expired session stays until then.
- **Reset links:** they work for one hour, once (`RESET_MINUTES`). Expired ones are deleted the next time any reset
  is requested (`forgot_password`).
- **Verification links:** they work for **48 hours** (`VERIFY_HOURS`); the pack had said one hour.
  - An unused link is replaced when a new one is sent (`issue_verification`).
  - A used one stays until the account is deleted.
- **Rate-limit rows:** rows older than a day are deleted the next time any attempt is counted (`DbRateLimit.hit`).
- **The saved card** now has its own step-by-step note:
  - **Cancelling** keeps the token, so the member can resume (`cancel_renewal`, `resume_renewal`).
  - **When the plan ends** (`_end`) **and on a refund** (`_refunded`), the token is cleared and its deletion asked of
    Moyasar, without checking the answer.
  - **When the account is deleted** (`forget_card`), the card's deletion is attempted first, and a failure is only
    logged.
  - **Brand and last four** stay until the account is deleted.
  - **The conclusion is stated plainly:** the site never keeps a card it can charge after a plan ends or an account
    is deleted. It does not confirm that Moyasar deleted its copy.
- **Two rows added:** the subscription row, and payment records, which are never deleted.

`git diff --check` is clean.

**The pilot is still running.** Its result will be output 38.

**The question for the review:** is this sound, and what is the single next pre-approved step?
