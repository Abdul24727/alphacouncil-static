# Output 65: review 70's fixes to the comparison audit

**Review 70** was the first review run in ChatGPT in the owner's browser, on GPT-6 with thinking effort High, as
the owner's rule of 2026-11-07 now requires. Its fixes are in commit `3d6fa15` on `rebuild`. No paid call was made.

**1. The I8 clean Buffett claim is out of the count (issue 1).**
- **The quote:** "sits well above the sector without peer book multiples to compare it to".
- **Why it is out:** it says itself that the pack holds no peer P/B, so it neither implies data the pack lacks nor is
  false on the pack.
- **Consistency:** option 2's like line in the same probe (Buffett, I8 P clean: P/B "high for a bank") was marked as
  an unsupported addition and never counted. Counting one and not the other would apply two rules.
- **Where it is kept:** `excluded-claims.json`, with the reason. It stays in `audit.md` as a contradiction of the
  Chair's ruling 3.
- **The new totals:**
  - **Wrong claims:** 209 against 55 (A planted 98, clean 111).
  - **Inventions:** 47 against 2. Today's room has 23 invented figures and 24 invented statements; option 2 has 0
    and 2.
  - **Checked quotes:** 264, with 0 missing.
- **Unchanged:** figures absent from the data (121 against 0) and the cost (62.4 %).

**2. `RESULT.md` now draws the same distinction as `audit.md` (issue 2).**
- **The invented figures:** 22 of the 23 are statement data that the advisors' briefs place in P9, whatever tag the
  turn cites. The 23rd is the I6 leverage threshold, cited to [P6].
- **The invented statements:** they also cover notes and peer comparisons (peer returns on equity, a sector rank for
  ROE) that no pack holds.
- **`audit.md` §2:** it says the same, and records the exclusion with its review.

**3. The evidence that could not be checked last time is attached (issue 3).**
- **The plan files:** `PROJECT.md` and `MASTER-PLAN.md` as they stand at `3d6fa15`.
- **The diff:** `65-diff-1184414-3d6fa15.diff`, the repository diff of the audit package and the plan files since the
  browser-review commit.
- **The checks:** `65-checks.txt`, the transcript of `classify_flags.py`, `verify_quotes.py`, `tally.py` and the
  record check at `3d6fa15`.
  - **The flag file** regenerates identically.
  - **The quotes:** 264 checked against their stated turns, 0 missing.
  - **The records:** `git diff --quiet 24f94d7 HEAD` passes on the historical records, the comparison's
    `probe-results.jsonl` and `flag-classifications.json`.
  - **The run record:** last changed in `154c56d`, the commit that saved it.
- **Not attachable:** the frozen data packs. The pack facts each claim turns on are quoted in its `why` field and in
  `audit.md`.

**The question for the review:** may the audit package now stand?
