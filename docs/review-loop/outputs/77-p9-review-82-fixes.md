# Output 77: P9, review 82's fixes

**Commit on `rebuild`:** `0033105`. Nothing was paid for, pushed or released.

**Review 82's issues, fixed at the root:**
1. **Source absence:**
   - **The cause:** the capped fixture made P9 say "the source holds no …" because the 30-row cap let 30 all-null
     protected lines push out the section's only reported figure.
   - **The change:**
     - **`bounded_statements`:** a protected line now wins its place only if it carries a number (`numbered`).
       All-null protected lines join the ordinary lines, which `ordered` already sorts with latest-year numbers
       first.
     - **`fit`:** it now never drops a statement's last row with a number (`droppable`).
   - **The result:**
     - **What is shown:** a section with any reported figure in the loaded years always shows one. So through
       `dataset_of`, held-as-shown and held-at-source cannot differ, and "the source holds no …" is said only where
       the source has no number.
     - **The real data:** no company's P9 changes. Under the old rule an all-null protected line inside the cap would
       have been shown, and the per-row sweep found 0 such rows among 30,761 shown statement rows on 2026-11-07.
   - **The guard for other callers:**
     - **The check:** `limitations_of` also checks the source (`at_source`). Where the statements passed to it hide
       a figure the source has, `said()` turns "the source holds no" into "this dataset carries no", and the
       cash-flow note says "this dataset carries … only".
     - **Through `dataset_of`:** this cannot trigger.
     - **The test:** `test_limitations_never_say_the_source_lacks_a_statement_it_has` calls `limitations_of`
       directly to test it.
2. **The date warning:** it now needs both the income statement and the balance sheet to be shown with a number.
   - **Your scenario:** the capped income statement dated 2025-12, a balance sheet struck 2025-09, and quarters.
   - **The result:** the income figure is now shown, so both statements are present. The date warning is true and
     appears, and there is no NO ANNUAL INCOME STATEMENT.
   - **Asserted:** the whole limitations list, word for word.
   - **The guard test:** with only the balance sheet passed, the warning is withheld.
3. **Production's blobs:** the zip now carries both commits' copies of the four files (`baseline/73d7140/…` and
   `baseline/026699b906/…`), so git's blob hash, sha1 of "blob <size>\0<bytes>", can be recomputed from the bytes.
   `tests.txt` has the `git rev-parse` output.

**Review 82's DONE WHEN:**
- **The ten earlier table cases:** they pass unchanged, word for word, except the capped case. That case's claim is
  no longer valid, because the figure is now shown.
- **The capped case, replaced and extended** (12 cases in all):
  - **`capped: the figure behind null protected lines is shown`:** the source figure exists and is now in P9.
    Asserted: the statements, quarters' note, limitations and pack note word for word, and no absence claim.
  - **`capped: a figure beyond the cap`:**
    - **The setup:** a source figure exists and the cap omits it (`rows_omitted` 1, asserted).
    - **The result:** the statement still shows figures, and no limitation claims source absence.
  - **`capped, dated, with a balance sheet and quarters`:** your second scenario, asserted in full.
- **Checks in every table case:**
  - "the source holds no X" never appears where the source has a number for X;
  - a section with a figure at the source shows one;
  - the quarters' note and the pack note agree with what is shown.
- **The established behaviour:** the normal two-year case, the one-window cases with and without quarters, and
  the quarters-only cases are unchanged.
- **The commands** (`tests.txt`):
  - **The P9 tests:** 22 pass.
  - **`test_evidence.py`, `test_debate.py` and `test_copilot.py`:** 150 passed.
  - **The whole suite:** 617 passed, 10 skipped.
  - **Whitespace:** `git diff --check 73d7140 HEAD` exits 0.
  - **ruff:** the same findings at `73d7140` and now.
- **The scope:** outside `docs/` and `PROJECT.md`, only the four P9 files changed since `73d7140`.
- **The diffs:**
  - `p9-fix.patch` is the whole change.
  - `p9-fix-review-82.patch` is this revision.
  - Both reverse-apply cleanly.

**Attachments:** this prompt and one zip laid out by repository path, which includes `baseline/`.

**The question for the review:** is P9's fix now correct, so that a fix-only release candidate can be built from
production's `026699b906`?
