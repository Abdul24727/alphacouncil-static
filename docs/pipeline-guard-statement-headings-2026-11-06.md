# Statement headings the parser does not know: a guard, and F-16 (2026-11-06)

**Status:** prepared and dry-run on copies. **Not applied:** it changes the server's pipeline, so applying it is
the owner's go-ahead.

**Patches:**
- `docs/pipeline-guard-statement-headings-2026-11-06.patch` (recommended): the guard plus one mapping line.
- `docs/pipeline-guard-statement-headings-guard-only-2026-11-06.patch`: the guard without the mapping.

Both apply cleanly (`git apply --check`) to the live `llm-council/parse_financial_statements.py`, md5
`ac23a4f5…`, which is the file as F-15 left it.

## Why

`parse_financial_statements.py` decides which statement a row belongs to from the last heading it saw, and
it knows headings only by exact text (`SECTION_MAP`). A heading it does not know has no numbers, so it was
skipped as an empty row, and **every line under it was filed under the statement above it**.

- That is how F-15 happened (2026-11-03): five finance companies head their balance sheet "Financial
  Position", so their balances were summed into the income statement as flows.
- The 2026-11-04 review's root-cause note asked for an unknown heading to be loud instead of silent.

## What a survey of every page found: F-16

A read-only survey of the statement page the parser reads for each company (710 pages):
- Argaam marks a statement's own heading with the row class `level1`; sub-headings such as "Assets" or
  "الموجودات" are `head`, and lines are `level2`.
- Six `level1` texts exist: "قائمة الدخل" 441, "المركز المالي" 441, "Income Statement" 269, "Balance Sheet"
  264, "التدفق النقدي" 9, "Financial Position" 5.
- **"التدفق النقدي" is not in `SECTION_MAP`.**
  - Nine UAE companies carry it: ADAV.AD, ADNIC, AMCREIT, AMLAK, DSI, DUBAIRES, EMSTEEL, QIC and UPP.
  - Their whole cash-flow statement is in the live database **as part of their balance sheet**.
  - Beta's API serves AMLAK's balance sheet with 50 lines, of which the last 19 are its cash flow, from
    "صافي الارباح" (net profit, 1,655) down to free cash flow.
  - Their pages are annual grids, so the figures themselves are as published; only the statement they sit
    in is wrong.
  - Who sees it: anyone opening these companies' balance sheets (Pro on production, everyone on beta), and
    the advisors' room, whose evidence for these companies reads their cash flow as balance-sheet lines.

## The change

- `parse_grid` keeps whether each row is a `level1` heading.
- In `ingest_one`, a `level1` heading that `SECTION_MAP` does not know **holds back its lines** until the
  next known heading, instead of filing them under the statement above. A statement that is missing shows
  as missing; one filed under the wrong statement shows as wrong figures.
- `main` logs a WARNING per company ("UNKNOWN STATEMENT HEADING … row(s) held back … add it to
  SECTION_MAP") and one summary line after `DONE`. The exit code is unchanged: nothing wrong is written, so
  there is no reason to halt the night.
- **The recommended patch also maps "التدفق النقدي" to "Cash Flow Statement"**, so the nine get their cash
  flow as a statement of its own.

## Dry run (2026-11-05 22:22–22:30 UTC, all in `/tmp/f16`)

**Method:**
- Three copies of `det_out/screening.sqlite`, each with both line-item tables emptied.
- Each parsed afresh over all 716 companies by one variant:
  - (a) the live parser;
  - (b) guard only;
  - (c) guard plus mapping.
- Then the gauge, sector-average and gauge-score stages, run on each copy.
- Read-only on everything else.
- The nightly window and a running pipeline were refused by the script; neither applied.

**Baseline:** (a) reproduces the live file exactly: 136,688 line items, 100,044 quarterly rows, and all
6,620 gauge rows (timestamps aside).

| | Line items | Quarterly | Gauges | Sector averages |
|---|---|---|---|---|
| (b) guard only | 677 rows gone: the cash-flow lines of 8 companies' balance sheets; nothing else | identical | **identical** | identical |
| (c) guard + mapping | the same 677 rows, **same lines, years and values**, now under "Cash Flow Statement"; nothing else | identical | 12 rows on 5 companies change **status only** | identical |

- The guard fired on exactly the nine companies and on no other heading. ADNIC's held-back lines carried no
  figures, so its rows do not change.
- **(c)'s gauge rows:**
  - ADAV.AD, DSI, EMSTEEL, QIC and UPP: EV/EBITDA and FCF yield go from `na_sector` ("UAE: no cash-flow
    statement published") to `missing_inputs`.
  - DSI and EMSTEEL's payout stays `missing_inputs`, with a note naming the cash-flow statement instead of
    its absence.
  - No value or score changes.
  - On screen that is "Not meaningful for this sector" becoming "Missing inputs", which is the true one:
    these companies publish cash flow, and the gauge stage searches English labels only (`OCF_LABELS`), so
    it cannot read the Arabic ones yet.
- **The Financials page** shows only the income and balance panels (`tabs.tsx`), so under either patch these
  nine balance sheets simply lose their stray lines (AMLAK 50 → 31). Under (c) the API also returns their
  cash flow, which the advisors' evidence pack reads as a statement of its own (`evidence.py`).
- The patched file `git apply` gives on a copy is byte-identical to the (c) that was dry-run (md5
  `9a0b7aa0…`).

## Recommendation

Apply the recommended patch (c).
- The guard alone fixes the balance sheets and changes no gauge.
- The mapping also stops five companies' gauges claiming they publish no cash flow, and gives the room their
  cash flow.

A follow-up, not in this patch: Arabic cash-flow labels in `compute_fundamental_gauges.py` would turn those
`missing_inputs` into real FCF yields and EV/EBITDA for these companies.

## Applying it (the owner's go-ahead: it changes the server's pipeline)

From `/opt/alphacouncil/backend`, outside 23:30–03:00 UTC and with no pipeline running:

```
cp -p llm-council/parse_financial_statements.py llm-council/parse_financial_statements.py.bak-20261106
git apply --check -p1 /root/pipeline-guard-statement-headings-2026-11-06.patch && git apply -p1 /root/pipeline-guard-statement-headings-2026-11-06.patch
```

- The nightly re-parses everything into a freshly created database, and the 05:00 UTC publish carries it.
- **Check after the publish** (`/var/lib/alphacouncil/screening.sqlite`, read-only):
  - the nine have no cash-flow line in their balance sheet;
  - eight of them have a "Cash Flow Statement";
  - the night's parse log has no "UNKNOWN STATEMENT HEADING" line.
- **Reverse:** `git apply -R -p1` the same file, or restore the `.bak`.
