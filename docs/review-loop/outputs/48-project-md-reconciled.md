# Output 48: review 47's step. PROJECT.md's current summaries reconciled with the recorded work.

**Changed** (`PROJECT.md` only, plus this output). Each edit keeps the old wording identifiable in a dated note.

- **Header:**
  - **Deployed:** now **`b5655a5064` on both tiers**, released 2026-11-06 on "Beta, then production", with rollback
    `5c18a3ae46`. A note says it named `5c18a3ae46` until then.
  - **Pushed:** `b5655a5`, already updated earlier today.
- **§6, the Gulf English-page follow-up:** "done on `rebuild` and NOT released" now reads **RELEASED on both tiers
  (`b5655a5064`)**. The evidence is beta's checks and the sweep at 714/714 and 40,811 lines. On production, the
  labels chunk `0h67wtzm9w_13.js` is byte-identical to beta's and hash-equal on the public site, and separately both
  tiers run the same release sha. *(Corrected after review 49: this said production's served code.)*
- **§6, F-14:** "the owner's, as a credential" now reads **FIXED 2026-11-06**. The app's key was copied in without
  being printed, and a two-item run wrote English headlines and both summaries.
- **§6, the superseded release note:** names `b5655a5064` as current and lists `5c18a3ae46`, `2e44ee6fbf` and
  `df83e19404` before it.
- **§6, "Not done":** keeps the lawyer, and adds what is open and what was done today.
  - **Open, all the owner's:**
    - the OpenRouter top-up (balance $7.83);
    - the `owns` confirm or revert;
    - F-12;
    - before the decision-grade run, D5's markers and the $426 cap.
  - **Done today:** the release, the push, the retention, F-14, the test accounts and the pilot.
- **§9, the roadmap heading:** now "where we are (2026-11-06; first written 2026-11-04)". It has a dated note: all
  work that can close before the lawyer is closed, and the rest is the owner's.
- **§9, Claude's list:** the pilot is done, and the decision-grade run with its hand audit is about a day and a half
  once funded.
- **§9, "How much longer":** the paid line now names the run's preconditions.
- **§9, the 2026-11-04 follow-up note:** now **RELEASED (`b5655a5064`)**.
- **Item 3's F-13 entry:** gains "released the same day in `2e44ee6fbf`".

**Already consistent, and checked:**
- §9's go-ahead list: struck with outcomes earlier today;
- F-16 verified live;
- the pilot entry, with the audit, 31 of 36;
- the re-quote.

`git diff --check` is clean. No code changed.

**The question for the review:** is this sound, and what is the single next pre-approved step?

*Review 48's correction:* F-7's paragraph in §6 now names `b5655a5064` as live and `5c18a3ae46` as its rollback.
