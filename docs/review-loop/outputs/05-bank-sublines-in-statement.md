# Output 05: review 04's step, bank income sub-lines read within their statement

Commit `3071c91`. Record: `docs/arabic-statement-labels-2026-11-03.md`, "Bank income sub-lines, read
within their statement".

**What the source establishes:** a read-only scan of every harvested income statement found 39 (32 Gulf in
Arabic, 7 Saudi in English).
- "الاستثمارات"/"Investments" (tr23), "أرصدة لدى البنوك والمؤسسات المالية"/"Due from Banks & Other FI's"
  (tr24) and "قروض و سلف"/"Loans and Advances" (tr25) occur ONLY as children of "دخل العمولات الخاصة"/"Special
  Commission Income".
- "ارصدة للبنوك و المؤسسات المالية"/"Due to Banks" (tr27) and "ودائع العملاء"/"Customer Deposits" (tr28) occur
  ONLY under "مصاريف العمولات الخاصة"/"Special Commission Expense".
- No other use of those texts occurs in any income statement.

**The change:**
- `web/src/content/data-labels.json` gets `in_statement` → `"Income Statement"`: 5 entries, each with
  `match` (the stored text in both languages) plus `en` and `ar`. Example: "Special commission income from
  investments" / "دخل العمولات الخاصة من الاستثمارات". Argaam's parent wording is joined to the child's. A
  `_in_statement_about` note says why. `pairs` and `aliases` are byte-unchanged.
- `web/src/lib/data-labels-core.ts` (new, no imports): `makeDataLabel(data)` returns
  `dataLabel(text, locale, statement?)`. An `in_statement` match for that statement wins; otherwise the
  previous logic runs unchanged.
- `web/src/lib/data-labels.ts`: `export const dataLabel = makeDataLabel(data)`. Same import path for all
  callers.
- `web/src/components/stock/research-panels.tsx`: only the statement table passes `section`. Holders,
  events, capital changes and templates do not.

**Tests:** `web/src/lib/data-labels-core.test.ts`, 4 tests on the real dictionary through the real function.
- All 5 entries, from both stored languages, in both page languages.
- The balance-sheet meaning is kept for the same words.
- No statement passed: identical to before, aliases included.
- Other income lines are unaffected.

Suite 63/63. `tsc --noEmit` exits 0; lint and `npm run build` (93/93) pass.

**Rendered** (local web against beta's API): ADCB (Gulf, Arabic-stored) and 1010 (Riyad Bank, English-stored),
income and balance, English and Arabic, at 1440 and 390. 16/16 PASS. Per panel:
- the labels that must show do;
- no bare sub-line is left in an income statement;
- the balance sheet keeps its words. ADCB uses "ودائع العملاء" in both statements: expense in the income
  statement, "Customer Deposits" in the balance sheet;
- every newest-column value equals the API's row by row.

The first run failed twice on my own expectation: ADCB's balance sheet spells "إستثمارات", not "الاستثمارات".
I checked that against the API and corrected the expectation, not the code.

Evidence: `docs/screenshots/bank-sublines-2026-11-06/` and `.txt`.

**Still pending:**
- F-16's check after the 05:00 UTC publish, and the sweep re-run.
- Nothing is released or pushed. That is the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next step?
