# Output 03: review 02's step, a label sweep that cannot certify what it did not check

Commits `7154aa4` and `b63b86c`. The record is `docs/arabic-statement-labels-2026-11-03.md`, "Review 02's
fixes to the sweep".

**Issue 1, the sweep** (`web/scripts/check-data-fixes.mjs` line ~202 in review 02):
- The logic now lives in `web/scripts/lib/label-sweep.mjs`. `check-data-fixes.mjs` `SWEEP=1` calls it.
- **Verdicts:**
  - `pass` only when every listed company was read and every shown line has English.
  - `fail` on any of these:
    - a line left in Arabic, named;
    - any non-200 or network error (that company was not checked);
    - Pro-only after some companies were read (coverage incomplete, findings kept);
    - an empty run.
  - `unavailable` (an INFO line, neither pass nor fail) only when statements are Pro-only from the first
    company.
- Why fail on any non-200: the API answers 200 with an empty list for a company with no statements, and
  only 503 (data unavailable) or 404 (unknown ref) otherwise. So no listed company has a legitimate
  non-200.
- **Regression tests** in `web/scripts/lib/label-sweep.test.mjs`, 11 of them:
  - pass;
  - Arabic left;
  - unshown statement ignored;
  - HTTP 500, 503, 429 and 404 each fail;
  - a network error fails;
  - gated from the start is unavailable;
  - gated after reading is a fail that keeps its finding;
  - an empty run fails.
- `npm test`: 58/58. Lint clean.
- **Real runs:**
  - Production signed out gives `unavailable`: 0 of 5 read, gated at the first company (1010).
  - Beta through the new code: 714 of 714 companies, 40,278 lines, no request failed. The one FAIL is
    F-16's 18 cash-flow labels in 8 companies, which the 05:00 UTC publish removes
    (`docs/screenshots/gulf-english-labels-2026-11-06-sweep-failclosed.txt`).

**Issue 2, the counts:** corrected in the record, with a note.
- 29 new English keys: 27 plus the 2 composed bank sub-lines. All are unused by Saudi lines, so Arabic pages
  are unchanged.
- 4 new label tests (43 → 47).

**Also:** the review script now writes LF line endings.

**Still pending:**
- F-16's check after the 05:00 UTC publish, and the sweep re-run then.
- Nothing is released or pushed. These need the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next step?
