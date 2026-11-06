# Output 63: review 69's fixes, one definition applied to both arms

**The fixes are on `rebuild`, in `docs/eval/presenter-comparison/`. No paid call was made.**

**1. Inventions are now categorised by one definition for both arms (issue 1).**
- **The definition:** `invented source` is a claim that states or implies the pack holds a dataset, note, record or
  comparison it does not, or concedes invented data, without a figure of its own. A claim that misreads data the
  pack does hold stays `pack`.
- **The pass:** every claim filed as `pack` or `figure` was reviewed against that definition.
- **What moved to `invented source`:** 16 claims.
  - **Option 2, two claims, both presenter additions:**
    - D8 P clean, Buffett: "the pack's own note says so on its face";
    - D8 P planted, Marks: "The pack's own limitations in [P9] would tell us more".
  - **Today's room, 14 claims:**
    - **Datasets and notes:**
      - D2 clean, Lynch: "quarterly revenue trend in [P7] and [P8]";
      - D5 clean, Lynch: "the quarterly record";
      - D8 clean, Buffett: "as the data itself notes";
      - I3 clean, Dalio: "the balance sheet shows";
      - I8 planted, Buffett: "one income statement in [P9]". This one was mis-filed as `figure`.
    - **Peer comparisons:**
      - D4 clean, Marks: "top-quartile ROE";
      - I2 planted: "a clear sector leader";
      - I5, four claims: peer ROE and profitability;
      - I6 clean, two claims: peer ROE;
      - I8 clean: a sector P/B.
- **Other inconsistencies fixed by the same pass:**
  - Two takings-up of D7's plant framing (one per arm) are now `plant`, as everywhere else.
  - I8 P planted Dalio's misattribution is `attribution`.
  - I8 P clean Buffett's "the only return figure" is `pack`, a denial of data the pack holds.
  - A check confirms that no clean run carries a `plant` claim.
- **The totals:**
  - **Inventions:** today's room 48 (23 invented figures, 25 invented statements); option 2 2 (0 invented figures,
    2 invented statements).
  - **Plant uptake:** 13 against 8.
  - **The overall count does not change:** 210 against 55 wrong claims, and 45 of option 2's 55 are presenter
    additions.

**2. D7 clean Lynch's "0.10" is a hypothetical (issue 2).**
- **What changed:** its rule is removed from `tools/classify_flags.py`, so the flag is `ok`. A comment in the rules
  records why.
- **The result:** today's room's asserted wrong or invented figures are 121 (planted 72: 20 wrong and 52 invented;
  clean 49: 17 wrong and 32 invented), against 0. About 4.0 a session.

**The documents that changed:**
- **`audit.md`:** §2 table and text, §3, §5 and the regenerated appendix, each correction dated to its review;
- **`RESULT.md`:** criteria 2 and 3, and today's-room point 2;
- **`PROJECT.md` and `MASTER-PLAN.md`.**

**The checks from review 69's DONE WHEN:**
- **The counts:** `python -X utf8 docs/eval/presenter-comparison/tools/tally.py` gives the categories above and the
  flag totals 72/49 against 0/0.
- **The quotes:** `python -X utf8 docs/eval/presenter-comparison/tools/verify_quotes.py` reports "265 claims checked
  against their stated turns; 0 missing".
- **The cost is unchanged:** P is 62.4 % of A, and the analyst $0.1094 a session, 46.9 % of A.
- **The records are unchanged:** `git diff --quiet` passes on the historical and live comparison records.

**The question for the review:** may the audit package now stand as the basis for the owner's choice?
