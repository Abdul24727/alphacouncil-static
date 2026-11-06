# Output 13: review 12's step, the phone evidence the release check lacked

Commit `bbf60d0`.

**Rendered at 390:** local web against beta's API, the same code as candidate `509d7bf`. These are the 11
panels the 2026-11-04 label set had only at 1440:
- English income and balance for 301, 821, BKIC.BH and EAND;
- Arabic income and balance for 8010;
- Arabic income for 1211.

`1211`'s Arabic balance sheet at 390 already had evidence in the real-estate check.

**What each panel checks** (`docs/screenshots/release-candidate-509d7bf/7-phone-gap.txt`):
- the row count equals the API's;
- the column count equals the columns `statementColumns()` makes from the API (newest first);
- **every cell in every column** equals the API's value, formatted as the panel formats it;
- the newest column is in view on load;
- the oldest column comes into view after the box scrolls to its far end (negative `scrollLeft` in RTL).

Per page, the 2026-11-04 set's expected labels show.

**Result: PASS 11/11, 0 cells differing.** Examples:
- 821: 29 rows × 5 years in each statement;
- EAND's balance sheet: 65 rows × 5 years;
- 8010: "12 شهرًا حتى يونيو 2026" for the income statement, "يونيو 2026, 2025" for the balance sheet;
- expected labels 3/3, 12/12, 1/1, 1/1, 1/1, 1/1.

Screenshots on load, plus `-scrolled` where the table scrolls, are in `phone-gap/`. I inspected 821's
income statement and 8010's scrolled balance sheet by eye.

**Recorded in the readiness report and `PROJECT.md`:**
- check 7 is added to the table;
- the review cleanup list now leaves only the busy check in the superseded harvest script.

Two observations, not figure defects, are left for review:
1. 821 shows Argaam's own lowercase "income from investments & Other operating income". That is the same
   kind of case as the real-estate label.
2. Scrolled to the oldest year, a phone table scrolls the line labels out of view. A label column that stays
   in place would read better.

`git diff --check` is clean.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
