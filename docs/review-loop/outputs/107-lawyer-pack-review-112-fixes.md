# Output 107: review 112's five fixes to the lawyer pack's facts

**Review 112 said FIX** on five overstatements. It kept the verified facts: Hostinger in Paris, two refunded owner
test payments, the provider names, the account settings, and the stale links' removal.

**What was done** (commit `3355437` on `rebuild`, local only; `pack-107.diff`):

1. **The processing location.**
   - **§5.2 now says:** "it may be processed outside the Kingdom; the actual locations are **not verified**".
   - **The top note says:** "Not verified: where the requests were processed".
   - **(h) says:** "Not verified: where any request was processed. Requests may be processed outside the Kingdom."
   - **On the two companies:** a new line says "Where a company is based does not show where a request was
     processed."
2. **Account-wide, not site-specific.**
   - **§5.2:** "These are observations on a shared account, not traced site requests". The list is headed "Providers
     observed on the account for the site's three configured models. No site request was traced to a provider".
   - **The "Not read" line:** it now says the Copilot's code allows fallbacks whenever it names hosts. That "was not
     established for every production request, so the companies above are the ones observed on the account, not
     confirmed recipients of the site's visitors' data."
   - **(h):** "Observed on the owner's shared OpenRouter account … The account also carries other work, and no site
     request was traced to a provider."
   - **The facts file:** the same distinction throughout.
3. **The shared key.** "So the key appears to serve other work too". The traffic "is not separated by source", and the
   evaluation runs are "most likely on it as well".
4. **The August payment.** "2026-08-12: 79 SAR, refunded. The owner confirms it was a test. Its description suggests
   an earlier version of the site, which is not verified."
5. **The handoff note.** The obsolete three-fact table and the separate status list are replaced by one current table:
   - 1a payments: done;
   - 1b accounts: the owner's;
   - 2 hosting: done;
   - 3 the AI services: "Recorded; location not verified".

   The opening line now says the pack was corrected on 2026-11-08.
6. **The status lines:** the check record's 2026-11-08 update and `PROJECT.md` use the same "observed on the shared
   account" wording.
7. **Checks** (`git-state-107.txt`):
   - A scan of the four documents for the overstated phrases finds none.
   - `git diff --check` is clean.
   - `rebuild` is `[ahead 8]`; the only uncommitted file is this output.
   - The remote is still at `7b32e2d`.
   - Nothing was pushed, sent or changed in any account.

**The question for the review:**
- Are the five fixes right and complete?
- Once the owner gives the account count (and §2 is corrected if it is not four), is the pack ready to send?
