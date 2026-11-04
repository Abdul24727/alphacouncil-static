# F-15: five Saudi finance companies' balance sheets summed as income

2026-11-03. Found while checking the Arabic statement labels; prepared and dry-run, **not applied**.

## The defect

Since the 2026-11-03 05:03 UTC publish, five Saudi finance companies — **1182, 1183, 4081, 4082 and
4083** (Tasheel) — have their balance-sheet lines inside the income statement, each added up over
four quarters as if it were income. Tasheel's statement shows "Total Assets" **12,918.83 (TTM)**.
The real figures are **3,197.89 at Dec 2025 and 3,365.01 at Jun 2026**, so the number shown is about
four quarter-end balances added together. Before the repair these five had no statement lines at
all, so this arrived with the repair.

**Where it shows:**
- the Financials panel: beta, and Pro members on production (none today);
- the Council's statement evidence (P9) for these five companies.

**Gauges are unaffected:** every gauge row is identical with and without the fix (below).

## The cause

The parser switches section on a header row it recognises (`SECTION_MAP` in
`llm-council/parse_financial_statements.py`). The finance-company template heads its balance sheet
**"Financial Position"** (`<tr id="tr1188" class="level1">`, where Aramco's template says
"Balance Sheet", `tr402`). The map has the Arabic "المركز المالي" but not the English, so on the
English pages the parser never leaves the income statement.

## The fix

`docs/pipeline-fix-financial-position-2026-11-03.patch`: one line, `"Financial Position": "Balance
Sheet"`, with a comment. **`git apply --check` passes** against the server's current parser (md5
`df2f3422…`, i.e. with last night's two patches applied).

## Dry run (2026-11-03 15:28 UTC, all in `/tmp/f15`)

Done on a copy of `det_out/screening.sqlite` and a patched copy of the parser. The five companies'
rows were cleared in the copy and re-parsed, then the gauge, sector-average and ranking stages were
run on the copy.

- The five now read like Aramco: an income statement (TTM to 2026-06, 20–23 rows) and balance sheets
  at FY 2025-12 and Q 2026-06 (30–31 rows each), 81–85 rows in all.
- **No income statement holds "Total Assets" or "Total equity" any more.**
- **Every row outside the five is identical to the live file**, and **all 6,620 gauge rows are
  identical** (status, value, rank). So the fix touches nothing else.

## Applying it (the owner's go-ahead: it changes the server's pipeline)

The same pattern as item 3's B2/B3, from `/opt/alphacouncil/backend`:

```
cp -p llm-council/parse_financial_statements.py llm-council/parse_financial_statements.py.bak-20261103
git apply --check -p1 /root/pipeline-fix-financial-position-2026-11-03.patch && git apply -p1 /root/pipeline-fix-financial-position-2026-11-03.patch
```

- **Before 00:00 UTC**, the nightly re-parses everything into a freshly created database (step 5),
  so no leftovers. The 05:00 publish then carries the fix with no manual step.
- **Check after the publish:** the five companies' sections, as in the dry run.
- **Reverse:** `git apply -R -p1` the same file, or restore the `.bak`.

## Applied (2026-11-03 15:38 UTC, on the owner's "Yes, apply it")

- No pipeline process was running. A first attempt stopped on its own guard because `pgrep -f`
  matched the ssh command line that contained the pattern. Re-run as a script on stdin, it found
  none.
- Backup `llm-council/parse_financial_statements.py.bak-20261103`: md5 `df2f3422…`, identical to
  the file before.
- `git apply --check` then `git apply`; md5 now `ac23a4f5…`.
- `diff` against the backup is exactly the three intended lines (67–69).
- The file parses, and importing it gives `SECTION_MAP["Financial Position"] == "Balance Sheet"`.
- The nightly (00:00 UTC, daily mode) re-parses into a freshly created database, and the 05:00 UTC
  publish carries it.

**Check after 05:00 UTC on 2026-11-04 (08:00 Riyadh):**
- On `/var/lib/alphacouncil/screening.sqlite`, read-only:
  - 1182, 1183, 4081, 4082 and 4083 have an Income Statement (TTM) and Balance Sheets (FY 2025-12,
    Q 2026-06);
  - no income statement holds "Total Assets";
  - 4083's Total Assets reads about 3,365 at 2026-06.
- Gauge totals change only by whatever the night's fresh scrape moves.

## Verified live (2026-11-04, after the 05:03:45 UTC publish)

The nightly ran clean: 716/716, rebuild exit 0. The publish reported `/healthz/deep=ok`. On the live
`screening.sqlite`, read-only:

- 1182, 1183, 4081, 4082 and 4083 each have Income Statement TTM 2026-06 (20–23 rows) and Balance
  Sheets FY 2025-12 and Q 2026-06 (30–31 rows each).
- No income statement holds "Total Assets" or "Total equity".
- 4083's Total Assets: 3,197.89 (FY 2025-12), 3,365.01 (Q 2026-06).
- Unchanged elsewhere: Tadawul income statements still 250, NULL periods 0, gauges `ok 3218 /
  missing_inputs 1109 / na_sector 2241 / undefined_nonpositive 52`.

**F-15 is closed.**
