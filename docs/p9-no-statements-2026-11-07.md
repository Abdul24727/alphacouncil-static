# P9: the room is now told when a company has no financial statements (2026-11-07)

**What P9 is:** the second issue the 2026-11-07 comparison audit found in today's room (`docs/eval/presenter-comparison/audit.md`
§5.2). Advisors invented income-statement, quarterly and balance-sheet figures. 22 of the room's 23 invented figures were
statement data their briefs place in [P9].

**Review 78's step:** reproduce P9, trace where the invented figures come from, and fix it fail-closed on `rebuild`,
without changing the room, its presentation or its architecture. No paid calls, push or release.

Evidence: `docs/screenshots/p9-no-statements-2026-11-07/`.

## The reproduction

**In the comparison** (the existing evidence):
- **The packs:** all five frozen packs (`docs/eval/packs/*.json`, fetched 2026-10-27) hold P1 to P8. None has a P9, and
  their header does not mention one.
- **The briefs:** five of the six seats' briefs send them to [P9]'s statements. Buffett's says "Read [P9]'s income
  statement and its `calculations`". No brief and no line of the pack says what to do when there are none.
- **The result:** the invented figures were statement data, cited to [P1], [P2], [P3], [P7], [P9] or nothing.
  Buffett's D2 opening gave "SAR 16,578 million".

**On the live data today:**
- **How it was measured:** read through beta's API for all 714 tickers, counting reported numbers, not rows
  (`p9-sweep-values.py`; the raw data, one line per ticker, is `p9-sweep-values.json`; the classification is
  `p9-sweep-values-summary.txt`).
- **A correction (review 80):** the first sweep (`p9-sweep.py` / `p9-sweep.json`) counted rows. On it this record said
  that all 50 companies with no statement rows also had no quarters. Two of them have reported quarters.
- **No row anywhere was all null.** No statement row and no quarter row in P9 lacked a number.

| Group | Companies | What they hold | What P9 told every one of them |
|---|---|---|---|
| A. No annual statement figure and no quarterly figure | **48** (19 on Tadawul, 4330 to 4350 among them) | nothing: 0 of 334 calculations has a value | "NO CASH FLOW STATEMENT: … carry an income statement and a balance sheet only … dividend cover can be tested against earnings only" and "ONE INCOME-STATEMENT WINDOW: one window is available … the single quarters are the history there is" (`beta-4330-evidence-before.json`) |
| B. No annual statement figure, reported quarters | **2** (ALFIRDOU, TAALEEM) | 25 quarterly income numbers each, over five quarter-ends | the same two notes |
| C. A balance sheet and quarters, no annual income statement | **1** (232) | a balance sheet, and 25 quarterly income numbers | the same two notes (`beta-232-limitations-before.json`) |
| D. An income statement and a balance sheet | 663 | as before | unchanged by this fix |

- **For groups A to C, both notes are false.** They describe annual statements that do not exist, and nothing said
  there were none.
- **The pack's own header:** it said that reported figures are "in [P9] under `statements` and `quarters`" for these
  companies too.

**Where the invented figures come from:**
- **The cause:** a seat's brief sends it to statements, and the pack does not say that there are none. For the live
  companies, P9 even described them as present.
- **What the pack supplied:** no statement figure. The data carried no number for one. So these figures were the
  model's own, prompted by text that implied they existed.

## The fix (on `rebuild`; two source files, no change to the room's flow, prompts per seat, or presentation)

**What kind of fix this is** (review 79):
- **It is two things:** a missing-data instruction the room reads, plus the room's existing unverified-figure
  detection.
- **It is not guaranteed suppression.** The existing check (`checks.unverified_figures`) lists a figure only when it
  appears in no dataset, and the screen marks it but still shows it. A made-up figure that happens to equal a number
  elsewhere in the pack is not caught, even when cited to [P9].
- **What would show whether models invent less:** a model evaluation, and that is paid.

**Held means a reported number** (reviews 79 and 80):
- **Statements:** a statement counts as present only where a row carries a number. A section whose rows are all
  null is treated as absent.
- **Quarters:** the single quarters P9 carries are reported income-statement figures. What may be missing is the
  full-year or trailing-window statements, never the quarters, and nothing says otherwise.

1. **`api/app/evidence.py`, `limitations_of`** (now also given the `quarters` the dataset carries) **and
   `bounded_quarters`:**
   - **No statement figure and no quarter (group A):** "NO FINANCIAL STATEMENTS: the source holds no reported figure
     from an income statement, balance sheet or cash flow statement for this company, and no quarterly result …
     Do not state, estimate or recall one, and do not cite [P9] for one: say that the statements are not available."
   - **Single quarters only (group B):** "NO ANNUAL STATEMENTS: the source holds no full-year or trailing-window
     figure … The single quarters in `quarters` are reported income-statement figures and the only reported figures
     here: quote each with the quarter it covers. There is no annual income-statement figure, and no balance-sheet
     or cash-flow figure, in this dataset, and the quarters are not one …"
   - **A balance sheet and quarters (group C):**
     - "NO ANNUAL INCOME STATEMENT: … The single quarters in `quarters` are its only reported income figures: quote
       each with the quarter it covers. There is no annual revenue, earnings, margin or earnings per share in this
       dataset, and the quarters are not one …"
     - The cash-flow note names "a balance sheet and single income-statement quarters" and says dividend cover
       "cannot be tested against annual earnings or cash".
   - **A balance sheet and no income figure at all:** "NO INCOME STATEMENT", with no change from review 79.
   - **The quarters' own note** (`bounded_quarters`):
     - **When `statements` has an income-statement number:** it still says "the annual figures above are the sum of
       four consecutive columns".
     - **When it has none:** "There is no annual income-statement figure for this company in `statements`, and
       these quarters are not one: quote each with the quarter it covers".
   - **The window count:** it uses years with a number, which matches what `statements` shows.
   - **Unchanged (group D):** a company with an income statement and a balance sheet keeps exactly the text it had,
     including the quarters' note, asserted word for word.
   - **Who reads it:** the Copilot reads P9 through the same tool (`get_financial_statements`), so it gets the
     same notes.
2. **`api/app/debate/pack.py`, `no_statements_note`, added to `Pack.prompt()`:**
   - **When:** the pack holds no reported statement figure. That covers no P9, a P9 error, or statements with no
     number.
   - **What every seat reads, right after the header:** "NO FINANCIAL STATEMENTS IN THIS PACK (<why>): no income
     statement, balance sheet, cash flow statement or quarterly results for this company. Where a brief sends a
     seat to [P9]'s statements, the seat says plainly that they are not available and argues from the datasets that
     are here. Every figure a seat quotes must be one these datasets show: a statement figure stated, estimated or
     recalled from memory is invented, whatever tag it carries."
   - **Single quarters only:** "NO ANNUAL FINANCIAL STATEMENTS IN THIS PACK: [P9] holds single income-statement
     quarters only, and no full-year or trailing-window income statement, balance sheet or cash flow statement
     figure. The quarters in [P9] `quarters` are reported: quote each with the quarter it covers, and do not present
     them as an annual figure …"
   - **A balance sheet and quarters (group C):** it gets no pack note, because the pack holds a statement figure. P9's
     own notes say what is missing.
   - **Why in `prompt()`:** it covers live packs and saved packs alike, including the comparison's five.
   - **Packs with a reported statement figure:** they get no note.

**What it does not change:**
- **The site:** it never displays P9, so no page or Arabic copy changes.
- **The room:** the six seats, the rounds, the Chair and the briefs are untouched.
- **The data:** the pipeline and the data are untouched. Why 51 companies have no annual statements is a
  data-coverage question for the pipeline, outside this fix.

## The evidence

**After** (`p9-after.txt`, from `p9-after.py`, run on the fixed code), every case reviews 79 and 80 name:
1. **Empty P9 (group A):** the NO FINANCIAL STATEMENTS note and the pack note, with 0 of 7 calculations valued.
2. **Quarterly-only P9 (group B):**
   - The quarter stays (`[['Net Income', 77.0]]`), and its note says there is no annual figure, not that one is above.
   - The limitation is NO ANNUAL STATEMENTS, and nothing calls the quarters absent.
   - The pack note says to quote them with their quarter.
3. **All-null statement rows:** treated as no statements. There is no window, no cash-flow line and no "tested
   against earnings", and the pack note appears.
4. **A balance sheet only:** NO INCOME STATEMENT, and "dividend cover cannot be tested against earnings or cash".
   - **4b. A balance sheet and quarters (group C):** the quarter stays, under NO ANNUAL INCOME STATEMENT. The
     cash-flow note names the quarters, and there is no pack note.
5. **Normal (group D, two years):** the old text and no pack note.
   - **5b. With quarters:** the quarters' note is the old one.
6. **No P9, or a P9 error:** the pack note is line 2, and the data starts at line 3.
7. **4330's pack with beta's P9 today, and the five comparison packs:** each carries the note.

**Tests** (`tests.txt`):
- **`test_p9_says_exactly_what_it_holds`** (review 80), across seven cases:
  - **The cases:** empty, quarterly only, all-null rows, balance sheet only, balance sheet and quarters, normal over
    two years, and normal with quarters.
  - **What each checks:** the statements and quarter rows kept, the quarters' note, the whole list of limitations
    and the pack note, all word for word.
- **The other P9 tests:** 9 pass, 8 new and 1 extended.
  - `test_a_company_with_no_statements_is_told_so_and_supplied_no_figure`:
    - **The fixture:** `Items([], [])`, called as the live route calls it, with a dividend history and the price.
    - **What it checks:** no statements, no quarters, no calculation value and no operand; the note comes first; and
      none of the four false phrases appears.
  - `test_quarters_alone_stay_reported_and_are_not_called_missing` (review 79);
  - `test_statement_rows_without_a_number_are_not_a_statement` (review 79);
  - `test_a_balance_sheet_alone_is_not_described_as_an_income_statement`;
  - `test_no_cash_flow_statement_is_stated_rather_than_left_to_be_noticed`: extended to assert the common case's text
    word for word;
  - `test_a_pack_without_statements_tells_the_room_so`:
    - **The cases:** no P9, an error, empty, and all-null.
    - **What it checks:** the note comes before the data, and there is no note when a figure exists.
  - `test_a_pack_whose_only_figures_are_quarters_keeps_them` (review 79);
  - `test_the_comparison_packs_now_carry_the_no_statements_note`: the five frozen packs;
  - `test_an_invented_statement_figure_on_a_pack_without_statements_is_flagged`: the audit's "SAR 16,578 million",
    cited to [P9] on a no-statements pack, is listed as unverified.
- **`test_evidence.py`, `test_debate.py` and `test_copilot.py`:** 144 passed (129 before).
- **The whole API suite:** 611 passed, 10 skipped (596 before).
- **ruff:** in each changed file, the same findings at `73d7140` (before any P9 change) and now. All are
  pre-existing.
- **The diffs:**
  - `p9-fix.patch` is the whole change since `73d7140`.
  - `p9-fix-review-79.patch` and `p9-fix-review-80.patch` are each review's part.

**What this does not prove:** that a model now writes no invented statement figure. The tests show what the
application supplies and says. They do not show what a model does with it.
- **Measuring that:** a paid session on a no-statements company (4330, say), which needs the owner's go-ahead per
  run.

**Release:** none.
- **Why `rebuild` can't ship as it is:** it carries the rejected prototype.
- **What a release would take:** a fix-only branch from production's `026699b906` with these two files and their
  tests, like the sector-standing release, and the owner's go-ahead.
