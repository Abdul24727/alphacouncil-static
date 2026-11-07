# Output 73: P9, the room is told when a company has no statements (review 78's step)

**Commits on `rebuild`:** `17d9f8f` (the fix, tests and record) and `7300fc6` (the diff saved as `.patch`).
Nothing was paid for, pushed or released.

**Review 78's DONE WHEN, item by item** (the record `p9-no-statements-2026-11-07.md` is attached):

1. **The exact reproduction:**
   - **In the comparison:**
     - **The packs:** the five frozen packs hold P1 to P8, have no P9, and their header never mentions one.
     - **The briefs:** five of the six seats' briefs send them to [P9]'s statements. Buffett's, attached, says "Read
       [P9]'s income statement".
     - **What nothing said:** what to do when there are none.
   - **On live data** (`p9-sweep.py` over beta's API for all 714 tickers; `p9-sweep-summary.txt`):
     - **No statements at all: 50 companies.** For each, P9's `statements` is empty and 0 of their 348
       calculations has a value. Yet P9 told every one of them that the source "carry[s] an income statement and a
       balance sheet only" and that "one window is available … the single quarters are the history there is"
       (`beta-4330-evidence-before.json`).
     - **A balance sheet only: one company (232),** told the same (`beta-232-limitations-before.json`).
   - **Where the figures enter:** the application supplied no statement figure. The pack's text implied statements
     existed, and the briefs pointed at them. The figures are the model's own. The existing turn check already lists
     a figure found in no dataset as unverified.
2. **The minimal diff** (`p9-fix.patch`): two source files, about 70 lines, plus tests.
   - **`evidence.limitations_of`:**
     - **No statements:** "NO FINANCIAL STATEMENTS", saying no reported revenue, earnings, asset, liability,
       equity, cash flow, share count or quarterly result is in the dataset, "do not state, estimate or recall one,
       and do not cite [P9] for one".
     - **A balance sheet only:** "NO INCOME STATEMENT".
     - **The cash-flow note:** it names only the statements that exist.
     - **The 627 companies with both statements:** their text is unchanged, word for word.
   - **`pack.no_statements_note` in `Pack.prompt()`:**
     - **When:** the pack holds no statements (no P9, a P9 error, or empty `statements`).
     - **What:** one note after the header, saying the statements are not available and that a statement figure
       stated, estimated or recalled is invented, whatever tag it carries.
     - **Not changed:** packs with statements, the seats, the briefs, the rounds, the Chair and the site.
3. **A regression test with a no-statements fixture:**
   - **The fixture:** `Items([], [])`, which is what `/evidence` builds for such a company.
   - **The test:** `test_a_company_with_no_statements_is_told_so_and_supplied_no_figure`. It checks that there are
     no statements, no quarters, no calculation value and no operand, that the note comes first, and that none of
     the four false phrases appears.
   - **Beside it:**
     - the balance-sheet-only test;
     - the pack tests for all three no-statements cases, with no note when statements exist;
     - the five frozen comparison packs;
     - the audit's "SAR 16,578 million", cited to [P9] on a no-statements pack, listed as unverified.
4. **The existing tests** (`tests.txt`):
   - **`test_debate.py`, `test_copilot.py` and `test_evidence.py`:** 134 passed.
   - **The whole suite:** 601 passed, 10 skipped.
   - **ruff:** the same findings before and after in each changed file.
5. **Deterministic, not model output:**
   - **What the tests show:** the application supplies no statement figure for such a company, and says so where
     every seat reads it (`p9-after.txt` shows the fixed output for 4330's case and the five comparison packs).
   - **What they do not show:** whether a model then invents less. That needs a paid session, for example on 4330,
     with the owner's go-ahead.
6. **The Arabic production-audit invocation (review 78's issue 2):** recorded. `check-arabic.txt` was rerun at
   10:17 UTC and now begins with its exact command, `BASE_URL=https://alphacouncil.tech`. The result is the same: 48
   views, 0, exit 0.

**Not done, and why:**
- **The briefs:** they are unchanged. The pack note covers every seat at once without touching seven brief files.
- **Why 50 companies have no statements:** a data-coverage question for the pipeline. They include some large
  listings, so it may be worth a look later. It is outside this fix.

**The question for the review:** is P9's fix correct and sufficiently fail-closed, and what is the next step: a
fix-only release branch for the owner's decision, a paid check, or something else on the plan?
