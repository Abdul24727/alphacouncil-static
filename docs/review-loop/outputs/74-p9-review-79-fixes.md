# Output 74: P9, review 79's fixes

**Commits on `rebuild`:** `5cf387c` (the revision, tests and record) and `f11f8f2` (the patches saved without
lone-space lines; both still apply). Nothing was paid for, pushed or released.

**Review 79's issues:**
1. **Quarterly-only data:**
   - **The change:** `limitations_of` now receives the `quarters` the dataset carries (`dataset_of` builds them first).
   - **No statement figure and no quarter:** "NO FINANCIAL STATEMENTS".
   - **Single quarters only:** "NO ANNUAL STATEMENTS". The quarters "are the only reported figures here: quote each
     with the quarter it covers", and nothing says quarterly results are missing.
   - **The pack:** `no_statements_note` has a quarters-only form too ("NO ANNUAL FINANCIAL STATEMENTS IN THIS PACK
     … The quarters in [P9] `quarters` are reported").
2. **All-null statement rows:**
   - **The rule:** "held" means a reported number. Statement sections are counted from rows whose value is not null.
     The pack uses `has_figure` (a non-bool number after the label) on `statements` and `quarters`.
   - **The window count:** it uses only years with a number, which matches what `statements` shows, since
     `bounded_statements` already drops years without one.
   - **The result:** an all-null P9 gets NO FINANCIAL STATEMENTS and the pack note. There is no window line, no
     cash-flow line and no "tested against earnings".
3. **Advisory, not a guarantee:** the record now says so.
   - **What it is:** a missing-data instruction plus the existing unverified-figure detection.
   - **What the detection misses:** it marks a figure found in no dataset but does not remove it, and a made-up
     figure equal to a number elsewhere is not caught.
   - **What would measure the effect:** only a model evaluation, which is paid.
   - **No further enforcement was added.**
4. **Evidence limits:** the raw sweep JSON and all five frozen packs are now attached. The test files are attached in
   full.

**Review 79's DONE WHEN** (`p9-after.txt` from `p9-after.py`; `tests.txt`):
- **Empty P9:** NO FINANCIAL STATEMENTS and the pack note. 0 of 7 calculations have a value.
- **Quarterly-only P9:** the quarter stays (`[['Net Income', 77.0]]`) under NO ANNUAL STATEMENTS, and the pack note
  says to quote it with its quarter.
- **All-null rows:** no assertion of earnings or dividend cover, and the pack note appears.
- **A balance sheet only:** "NO INCOME STATEMENT", and "dividend cover cannot be tested against earnings or cash".
- **Normal (an income statement and a balance sheet, two years):** the old text word for word, and no pack note.
- **No P9, or a P9 error:** the pack note is line 2, and the data starts at line 3.
- **The tests:**
  - **The P9 tests:** 9 pass (8 new, 1 extended).
  - **`test_evidence.py`, `test_debate.py` and `test_copilot.py`:** 137 passed.
  - **The whole suite:** 604 passed, 10 skipped (596 before P9).
  - **ruff:** the same findings at `73d7140` and now.
- **The exact diffs:**
  - `p9-fix.patch` is the whole change since `73d7140`.
  - `p9-fix-review-79.patch` is this revision.
  - Both reverse-apply cleanly to the current tree, and `git diff --check 73d7140 HEAD` exits 0.

**The question for the review:** is P9's fix now correct? If so, the next step is a fix-only release candidate from
production's `026699b906` for the owner's decision, built and checked as the sector-standing candidate was.
