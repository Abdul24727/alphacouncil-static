# Output 78: P9, review 83's fixes

**Commit on `rebuild`:** `2ee892a`. Nothing was paid for, pushed or released.

**Review 83's issues:**
1. **A whole year hidden by the cap:**
   - **The cap (`bounded_statements`):** after the usual selection, any year column with a figure at the source but
     none kept gets the first line with a figure for that year added. So the cap can run over by at most one line a
     year, and a selection that already covers every year is unchanged.
   - **The trim:** `fit`'s `droppable` never removes the last figure in any year column.
   - **The effect:** the years P9 shows match the years the source reports (for the loaded years), and
     `period_end`, the latest year's period, always describes a column that shows figures.
   - **Your reproduction** (`p9-review83-repro.py`):
     - **Before** (`p9-review83-before.txt`): column 2025 showed 0 figures, `rows_omitted` was 1, `period_end` was
       2025-12, and the note said "the prior year's income statement is not".
     - **After** (`p9-review83-after.txt`): both columns show figures (Zakat & Tax 555 for 2025), `rows_omitted` is 0,
       and there is no one-window note.
2. **A quarter outside the carried series:**
   - **The wording:** `limitations_of` now knows whether the source reports any income-statement quarter. A note
     that names quarterly results as absent (NO FINANCIAL STATEMENTS, NO INCOME STATEMENT) says "this dataset
     carries no …" when it does.
   - **The series:** not widened.
   - **The pack note:** it now reads "… IN THIS PACK (…): it holds no income statement, balance sheet, cash flow
     statement or quarterly results for this company". It describes the pack.
   - **Your reproduction:**
     - **Before:** "the source holds no … quarterly result".
     - **After:** "this dataset carries no … quarterly result".
3. **The verification boundary:**
   - **The bytes:** the zip again holds both commits' copies of the four files under `baseline/`.
   - **The patch on production:** `p9-fix.patch` was applied with `git apply` to a fresh copy of production's four
     files (from `git archive 026699b906`). After CRLF to LF (git apply on Windows outside a repository writes CRLF),
     each file's blob equals `rebuild`'s (`tests.txt`).

**Review 83's DONE WHEN:**
- **The reproductions:** both fail before and pass after (the two files above).
- **The table** (`test_p9_says_exactly_what_it_holds`, 14 cases):
  - **The two new cases:** "two years, one hidden by the cap" and "a quarter on a line P9 does not carry", both word
    for word.
  - **The twelve earlier cases:** they pass with the same expected text. The empty and all-null cases' pack note
    has "it holds no …".
  - **New checks in every case:** every year column shown carries a figure, and the source is never said to have no
    quarterly result when it reports one.
- **The trim test** (`test_the_budget_trim_never_empties_a_year`): a tight budget trims 23 of 24 lines and stops at
  the last line with a 2025 figure, which the earlier rule would have dropped.
- **The commands** (`tests.txt`):
  - **The P9 tests:** 25 pass.
  - **`tests/test_evidence.py tests/test_debate.py tests/test_copilot.py`:** 153 passed.
  - **The whole suite:** 620 passed, 10 skipped.
  - **ruff:** the same findings at `73d7140` and now.
  - **Whitespace:** `git diff --check 73d7140 HEAD` exits 0.
- **The scope:** outside `docs/` and `PROJECT.md`, only the four P9 files changed.
- **The diffs:**
  - `p9-fix.patch` is the whole change.
  - `p9-fix-review-83.patch` is this revision.
  - Both reverse-apply cleanly.

**Attachments:** this prompt and one zip, laid out by repository path, including `baseline/`.

**The question for the review:** is P9's fix now correct, so that a fix-only release candidate can be built from
production's `026699b906`?
