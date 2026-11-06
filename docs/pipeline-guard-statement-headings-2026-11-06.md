# Statement headings the parser does not know: a guard, and F-16 (2026-11-06)

**Status:** APPLIED on the server 2026-11-05 22:44 UTC, on the owner's go-ahead (see "Applied" at the end).
**Still to do:** the check after the 2026-11-06 05:00 UTC publish, now as commands ("The check after the publish, as commands"; PENDING).

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

## Applied (2026-11-05 22:44 UTC, on the owner's "Yes, apply it now")

- Outside the nightly window, and no pipeline process was running (checked by a script on stdin).
- The parser before was `ac23a4f5…`, the file the patch was dry-run on. It is backed up as
  `llm-council/parse_financial_statements.py.bak-20261106`, md5 identical.
- `git apply --check`, then `git apply`, of `/root/pipeline-guard-statement-headings-2026-11-06.patch`.
- The parser is now `9a0b7aa0…`, **byte-identical to dry-run variant (c)**; 34 changed lines against the
  backup.
- The module imports, with `SECTION_MAP["التدفق النقدي"] == "Cash Flow Statement"` and F-15's mapping
  intact.
- The 00:00 UTC nightly re-parses into a fresh database, and the 05:00 UTC publish carries it. The check
  after the publish is the one under "Applying it".

## The check after the publish, as commands (2026-11-06, review 19)

**Status: PENDING.** It runs after the 2026-11-06 publish; nothing is claimed until then.

**1. The night, the publish and the served data, on the server, read-only.**
`scripts/pipeline-checks/f16_after_publish.py` checks 13 items (8 for the night and the publish, 5 for the
data) and exits with the number of failures:

```
ssh root@alphacouncil.tech '/opt/alphacouncil/pipeline-venv/bin/python -X utf8 - 2026-11-06' \
    < scripts/pipeline-checks/f16_after_publish.py
```

- **The night's run** (`/opt/alphacouncil/logs/daily_<day>.log` and its `.1`):
  - the patched parser is on disk, md5 `9a0b7aa0…`;
  - `[OK step 8] parse_financial_statements`;
  - the parse step's `DONE:` totals;
  - **no `UNKNOWN STATEMENT HEADING` line**;
  - the run's `ALERT [OK]`.
- **The publish:** a `<day> … published. /healthz/deep=ok` line in `/opt/alphacouncil/logs/db_publish.log`
  (and its `.1`), and a served `/var/lib/alphacouncil/screening.sqlite` dated that day. *A Friday night runs
  in full mode and logs to `cron_heavy.log`, but its run log is still `daily_<day>.log`.*
- **The data** (each item must fail on missing data, not pass on it):
  - each of the nine has a balance sheet;
  - none of F-16's 18 distinctive cash-flow lines left in the nine balance sheets (`fundamentals_lineitems`,
    `section='Balance Sheet'`; "اخرى" is left out of the list, being a balance-sheet line too);
  - `Cash Flow Statement` rows for the eight;
  - none for ADNIC, whose cash-flow lines carry no figures;
  - AMLAK's newest balance sheet has rows, and fewer than 50 (31 in the dry run).

**Proved before it is needed:**
- Against the 2026-11-05 publish it reports 10 PASS: the 8 night and publish items, the nine balance sheets
  present, and ADNIC with none. The three data items FAIL:
  - cash-flow lines in eight balance sheets, 40–80 rows each;
  - no Cash Flow Statement;
  - AMLAK 50 rows.

  That is F-16 before its fix.
- With `F16_DB=/tmp/f16/c/screening.sqlite`, the dry run's fixed copy, all 5 data items pass: the nine
  balance sheets present, 0 cash-flow lines, the eight with 40–95 cash-flow rows, ADNIC none, AMLAK 31.
- **Missing data fails** (review 20 found that an absent balance sheet passed the first version, and so did
  AMLAK at 0 rows). `scripts/pipeline-checks/test_f16_after_publish.py` runs 8 tests on in-memory
  databases, all OK:
  - the fixed data passes;
  - cash flow left in a balance sheet fails;
  - a missing balance sheet fails for each of the nine;
  - no balance sheets at all fails;
  - AMLAK at 0 rows fails, and AMLAK still at 50 fails;
  - a missing cash-flow statement fails;
  - ADNIC with one fails.
  Run it with `python -B -X utf8 scripts/pipeline-checks/test_f16_after_publish.py`.

**2. The English-label sweep, from a workstation:** beta's API reads the same published file
(`SCREENING_DB=/var/lib/alphacouncil/screening.sqlite`, as production's does).

```
ssh -o ServerAliveInterval=15 -N -L 8201:127.0.0.1:8200 root@alphacouncil.tech      # tunnel to beta's API
cd web && API_ORIGIN=http://127.0.0.1:8201 npm run dev -- -p 3100                    # local web on it
cd web && BASE_URL=http://localhost:3100 SWEEP=1 node scripts/check-data-fixes.mjs  # the sweep
```

It must read **714 of 714** companies and PASS "every statement line on an English page has English". Before
the publish it failed on exactly F-16's 18 labels in 8 companies
(`docs/screenshots/gulf-english-labels-2026-11-06-sweep-failclosed.txt`).
