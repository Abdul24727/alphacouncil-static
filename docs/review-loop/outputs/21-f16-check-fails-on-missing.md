# Output 21: review 20's two issues, fixed

Commit `6a7a160`.

**1. The checker no longer passes on missing data** (`scripts/pipeline-checks/f16_after_publish.py`).
- The data items are now `data_checks(db)`, which returns `(ok, what, detail)` per item. The night and publish
  items are `night_and_publish()`, and both run only under `if __name__ == "__main__"`, so the module imports
  without touching the server.
- New item: **each of the nine has a balance sheet** (rows > 0). An absent balance sheet can no longer satisfy
  "no cash-flow line in it".
- AMLAK's item is now **`0 < rows < 50`**, so zero rows fails.
- Now 13 items: 8 for the night and the publish, 5 for the data.
- **Regression tests** in `scripts/pipeline-checks/test_f16_after_publish.py`: 8 tests on in-memory SQLite,
  all OK (`python -B -X utf8 …`).
  - The fixed-data control passes.
  - Cash flow left in a balance sheet fails (the original misplaced case).
  - A missing balance sheet fails, as 9 subtests, one per company.
  - No balance sheets at all fails.
  - AMLAK with no rows fails, and AMLAK still at 50 fails.
  - A missing Cash Flow Statement fails.
  - ADNIC with a cash-flow statement fails.
- **Re-proved on the server:**
  - On the 2026-11-05 publish: 10 PASS and 3 FAIL. The passes are the 8 night and publish items, the new
    "nine balance sheets present" (405, 50, 193, 250, 417, 150, 415, 417 and 360 rows) and ADNIC. The
    failures are cash flow in 8 balance sheets, no Cash Flow Statement, and AMLAK at 50.
  - On the dry run's fixed copy (`F16_DB`): all 5 data items PASS. The nine balance sheets are present, there
    are 0 cash-flow lines, the eight have 40–95 cash-flow rows, ADNIC has none, and AMLAK has 31.

**2. The classification is corrected.** Output 20 now says its 9 passes were the 8 night and publish items
plus ADNIC's data item. The F-16 doc and `PROJECT.md` give the 13 items as 8 + 5, and the doc lists the
regression tests and how to run them.

The live result stays **PENDING** until after the 05:00 UTC publish. `git status` is clean.

**The question for the review:** is this sound, and what is the single next pre-approved step?
