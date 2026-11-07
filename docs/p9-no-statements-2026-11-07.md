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

**On the live data today** (`p9-sweep.py`, read through beta's API for all 714 tickers; summary in
`p9-sweep-summary.txt`):
- **No statements at all: 50 companies.** 19 are on Tadawul (4330 to 4350 among them). For them, P9's `statements` is
  empty, `quarters` is null, and 0 of their 348 calculations has a value.
- **What P9 told every one of those 50,** in its `limitations` (`beta-4330-evidence-before.json`):
  - "NO CASH FLOW STATEMENT: the source's pages for this company carry an income statement and a balance sheet
    only … dividend cover can be tested against earnings only";
  - "ONE INCOME-STATEMENT WINDOW: one window is available … the single quarters are the history there is".
  - Both are false. They describe statements that do not exist, and nothing said there were none.
- **A balance sheet and no income statement: one company (232),** which was told the same two things
  (`beta-232-limitations-before.json`).
- **The pack's own header:** it said that reported figures are "in [P9] under `statements` and `quarters`" for these
  companies too.

**Where the invented figures come from:**
- **The cause:** a seat's brief sends it to statements, and the pack does not say that there are none. For the live
  companies, P9 even described them as present.
- **What the pack supplied:** no statement figure. The data carried no number for one, and the existing turn checks
  (`checks.unverified_figures`) list any figure that appears in no dataset as unverified, and the screen marks it.
  So these figures were the model's own, prompted by text that implied they existed.

## The fix (on `rebuild`; two source files, no change to the room's flow, prompts per seat, or presentation)

1. **`api/app/evidence.py`, `limitations_of`:**
   - **No statements at all:** P9 now says "NO FINANCIAL STATEMENTS: … There is no reported revenue, earnings,
     asset, liability, equity, cash flow, share count or quarterly result for this company in this dataset. Do not
     state, estimate or recall one, and do not cite [P9] for one: say that the statements are not available."
   - **The other notes:** the cash-flow note names only the statements that exist. A company without an income
     statement gets "NO INCOME STATEMENT", not "ONE INCOME-STATEMENT WINDOW".
   - **Unchanged:** the 627 companies with an income statement and a balance sheet get exactly the text they had
     (asserted word for word in a test).
   - **Who reads it:** the Copilot reads P9 through the same tool (`get_financial_statements`), so it gets the
     same note.
2. **`api/app/debate/pack.py`, `no_statements_note`, added to `Pack.prompt()`:**
   - **When:** the pack holds no statements: no P9, a P9 error, or a P9 with empty `statements`.
   - **What every seat reads, right after the header:** "NO FINANCIAL STATEMENTS IN THIS PACK (<why>): no income
     statement, balance sheet, cash flow statement or quarterly results for this company. Where a brief sends a
     seat to [P9]'s statements, the seat says plainly that they are not available and argues from the datasets that
     are here. Every figure a seat quotes must be one these datasets show: a statement figure stated, estimated or
     recalled from memory is invented, whatever tag it carries."
   - **Why in `prompt()`:** it covers live packs and saved packs alike, including the comparison's five.
   - **Packs with statements:** they get no note.

**What it does not change:**
- **The site:** it never displays P9, so no page or Arabic copy changes.
- **The room:** the six seats, the rounds, the Chair and the briefs are untouched.
- **The data:** the pipeline and the data are untouched. Why 50 companies have no statements is a data-coverage
  question for the pipeline, outside this fix.

## The evidence

**After** (`p9-after.txt`, from `p9-after.py`, run on the fixed code):
- **The no-statements P9:** its one limitation is the new note, and 0 calculations have a value.
- **4330's pack:** built with beta's P9 as it is today, it carries the pack note "([P9] holds none for this company)".
- **The five comparison packs:** each carries "(the pack has no [P9])".

**Tests** (`tests.txt`):
- **The P9 tests, all passing:**
  - `test_a_company_with_no_statements_is_told_so_and_supplied_no_figure`: the no-statements fixture is
    `Items([], [])`. There are no statements, no quarters, no calculation value and no operand, the note comes first,
    and none of the four false phrases appears.
  - `test_a_balance_sheet_alone_is_not_described_as_an_income_statement`;
  - `test_no_cash_flow_statement_is_stated_rather_than_left_to_be_noticed`: extended to assert the common case's text
    word for word;
  - `test_a_pack_without_statements_tells_the_room_so`: the three cases, the note placed before the data, and no
    note with statements;
  - `test_the_comparison_packs_now_carry_the_no_statements_note`: the five frozen packs;
  - `test_an_invented_statement_figure_on_a_pack_without_statements_is_flagged`: the audit's "SAR 16,578 million",
    cited to [P9] on a no-statements pack, is listed as unverified.
- **`test_debate.py`, `test_copilot.py` and `test_evidence.py`:** 134 passed (129 before).
- **The whole API suite:** 601 passed, 10 skipped (596 before).
- **ruff:** the same findings before and after in each changed file (all pre-existing).

**What this does not prove:** that a model now writes no invented statement figure. The tests show what the
application supplies and says. They do not show what a model does with it.
- **Measuring that:** a paid session on a no-statements company (4330, say), which needs the owner's go-ahead per
  run.

**Release:** none.
- **Why `rebuild` can't ship as it is:** it carries the rejected prototype.
- **What a release would take:** a fix-only branch from production's `026699b906` with these two files and their
  tests, like the sector-standing release, and the owner's go-ahead.
