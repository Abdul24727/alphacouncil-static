# Output 76: P9, review 81's fixes

**Commits on `rebuild`:** `3ee9008` (the revision, tests, sweep and record) and `ddd03c0` (review 81's patch with two
lines of context). Nothing was paid for, pushed or released.

**Review 81's issues:**
1. **One window and no quarters:**
   - **The new wording:** `limitations_of` now says "ONE INCOME-STATEMENT WINDOW: … is available and the prior
     year's income statement is not. Year-on-year revenue or earnings cannot be compared from this dataset, and it
     holds no single quarters: this window is the only income history there is."
   - **Who gets it:** companies whose P9 shows no quarterly figure. On 2026-11-07 that was 25 companies, 8010 to 8311,
     listed by the summarizer.
   - **Unchanged:** a company with quarters keeps the old wording ("… because the source serves a rolling
     five-quarter grid … the single quarters are the history there is").
2. **The notes are read from what P9 shows:**
   - **The helpers:**
     - **`shown(statements)`:** the statements with a reported number as shown, after the 30-row cap.
     - **`shown_years`:** the year columns with a number.
     - **`quarters_note(annual)`:** the quarters' note.
   - **How `dataset_of` uses them:** it builds the statements, fits, then settles the limitations and the quarters'
     note on `ds.statements` and `ds.quarters` as they finally are, refitting if the wording changed.
   - **Why that ends:** trimming only removes rows, so the loop ends, and it is bounded at three passes.
   - **Your capped case:** 30 null protected rows plus a numbered row cut by the cap, with a quarter. It now gives
     the no-annual quarters' note, NO ANNUAL STATEMENTS, and the quarters-only pack note, all three agreeing.
3. **The all-null-row claim:**
   - **The record:** it now says what each run measured.
   - **The frozen `p9-sweep-values.json`:** it measures numbers per section and per company. Its summary now prints
     "individual all-null rows: NOT MEASURED in this file".
   - **The per-row measure:** `p9-sweep-values.py` now also counts rows with no number, and was rerun to
     `p9-sweep-rows.json`. It found 0 of 30,761 statement rows and 0 of 1,726 quarter rows without a number, and the
     same 48/2/1/663.
4. **Production's files:** `git rev-parse` gives the same blob for all four files at `73d7140` and at production's
   `026699b906` (`tests.txt`).

**Review 81's DONE WHEN:**
- **The regression tests:**
  - **`one year, no quarters`:** checked word for word, with no quarters claimed.
  - **`one year, with quarters`:** the old wording.
  - **`capped: no income figure shown`:** checked word for word.
  - **Every case:** the quarters' note equals the annual form exactly when an income-statement figure is shown, the
    pack note appears exactly when no statement figure is shown, and nothing claims quarters where none are shown.
  - **The original seven cases:** they still pass.
- **The demonstration:** `p9-after.py` was rerun. `p9-after.txt` shows cases 5c, 5d and 5e beside the earlier ones.
- **The tests:** the 19 P9 tests pass (10 table cases, 9 others); the three named files 147 passed; the whole suite
  614 passed, 10 skipped. ruff findings are the same at `73d7140` and now.
- **The summarizer:** rerun on the frozen JSON, it gives 48/2/1/663, and the record makes no per-row claim from it.
- **Whitespace and scope:** `git diff --check 73d7140 HEAD` exits 0. Outside `docs/` and `PROJECT.md`, only the four
  P9 files changed.
- **The diffs:**
  - `p9-fix.patch` is the whole change since `73d7140`.
  - `p9-fix-review-81.patch` is this revision.
  - Both reverse-apply cleanly.

**Attachments:** because of the chat's attachment limit, everything except this prompt is in one zip, laid out by
repository path.

**The question for the review:** is P9's fix now correct, so that a fix-only release candidate can be built from
production's `026699b906`?
