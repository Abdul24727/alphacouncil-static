# Output 75: P9, review 80's fixes

**Commits on `rebuild`:** `7a94f98` (the revision, tests, sweep and record) and `6b44f55` (review 80's patch saved
with one line of context). Nothing was paid for, pushed or released.

**Review 80's issues:**
1. **Quarterly-only wording:**
   - **The principle:** the single quarters are reported income-statement figures. So what may be missing is the
     full-year or trailing-window statements, and nothing now says otherwise.
   - **`QUARTERS_ONLY`:** "NO ANNUAL STATEMENTS: the source holds no full-year or trailing-window figure … The single
     quarters in `quarters` are reported income-statement figures and the only reported figures here: quote each with
     the quarter it covers … and the quarters are not one".
   - **The pack's quarters-only note:** "[P9] holds single income-statement quarters only, and no full-year or
     trailing-window … figure … do not present them as an annual figure".
   - **`bounded_quarters`:** it keeps its old note ("the annual figures above are the sum …") only where `statements`
     holds an income-statement number. Otherwise: "There is no annual income-statement figure for this company in
     `statements`, and these quarters are not one: quote each with the quarter it covers".
2. **A balance sheet with quarterly income:**
   - **`NO ANNUAL INCOME STATEMENT`:** "the single quarters in `quarters` are its only reported income figures: quote
     each with the quarter it covers. There is no annual revenue, earnings, margin or earnings per share …, and the
     quarters are not one".
   - **The cash-flow note:** it names "a balance sheet and single income-statement quarters", and dividend cover
     "cannot be tested against annual earnings or cash".
   - **A balance sheet with no income figure at all:** unchanged ("NO INCOME STATEMENT").
3. **The sweep record:**
   - **How it was redone:** `p9-sweep-values.py` counts reported numbers in every statement row and quarter row.
     The raw output is `p9-sweep-values.json`, one line per ticker; the classification is
     `p9-sweep-values-summary.txt`, made by `p9-sweep-values-summarize.py`.
   - **The groups:**
     - **A, no annual statement figure and no quarterly figure:** 48;
     - **B, quarters only:** 2 (ALFIRDOU, TAALEEM), 25 numbers each;
     - **C, a balance sheet and quarters:** 1 (232), 25 quarterly numbers;
     - **D, an income statement and a balance sheet:** 663.
   - **Null rows:** no row anywhere was all null.
   - **The record:** corrected. It says plainly that the first sweep counted rows and that its claim about quarters
     was wrong.
4. **Unverifiable evidence:** `beta-4330-evidence-before.json`, `beta-232-limitations-before.json`, `checks.py`,
   `audit.md` and all five frozen packs are attached, so `p9-after.py` runs on the attachments.

**Review 80's DONE WHEN:**
- **The table test:** `test_p9_says_exactly_what_it_holds` covers seven cases: empty, quarterly only, all-null,
  balance sheet only, balance sheet and quarters, normal over two years, and normal with quarters. Each checks, word
  for word:
  - the statements and quarter rows kept;
  - the quarters' note;
  - the whole list of limitations;
  - the pack note.
- **The demonstration:** `p9-after.txt` shows every case. It contains no annual figure that does not exist, no claim
  that reported quarters are absent, and no "annual figures above" over an empty statement section.
- **The tests:** 16 P9 tests pass; the three named files 144 passed; the whole suite 611 passed, 10 skipped. ruff
  findings are the same at `73d7140` and now.
- **Whitespace:** `git diff --check 73d7140 HEAD` exits 0.
- **The scope:** since `73d7140`, the only files changed outside `docs/` and `PROJECT.md` are `api/app/evidence.py`,
  `api/app/debate/pack.py`, `api/tests/test_evidence.py` and `api/tests/test_debate.py`.
- **The diffs:**
  - `p9-fix.patch` is the whole change since `73d7140`.
  - `p9-fix-review-80.patch` is this revision.
  - Both reverse-apply cleanly.

**The question for the review:** is P9's fix now correct, so that a fix-only release candidate can be built from
production's `026699b906`? Production's versions of the four files are identical to `73d7140`'s, so the patch applies
to it as it stands.
