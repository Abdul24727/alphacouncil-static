# Output 20: review 19's step, F-16's after-publish check as runnable commands

Commit `e684be0`. No app code changed.

**`scripts/pipeline-checks/f16_after_publish.py`:** read-only, run on the server with the pipeline's Python
on stdin, with the publish day (UTC) as its argument. It prints PASS or FAIL for 12 items and exits with the
number of FAILs. The facts it is built on were read from the server first:
- crontab: daily mode Sun–Thu and Sat, `MODE=full` on Friday into `cron_heavy.log`; `publish_dbs.sh` hourly
  05–10 UTC into `db_publish.log`;
- the run log is `/opt/alphacouncil/logs/daily_<day>.log`, with lines `[OK step 8] parse_financial_statements`,
  `DONE: … line-item-rows` and `ALERT [OK]`;
- the publish line is `… published. /healthz/deep=ok`;
- logs rotate at 01:00 UTC to `.1`, so the script reads both;
- beta's and production's `SCREENING_DB` are both `/var/lib/alphacouncil/screening.sqlite`; only that line
  was read from the env files.

**The 12 items:**
- the parser on disk is the patched one (md5 `9a0b7aa0…`);
- the run log exists;
- `[OK step 8]`, and the parse `DONE` totals;
- **no `UNKNOWN STATEMENT HEADING` line**;
- `ALERT [OK]`;
- **published that day with `/healthz/deep=ok`**;
- the served file is dated that day;
- **none of F-16's 18 distinctive cash-flow lines in the nine balance sheets**. The list was taken from the
  dry run's Cash Flow Statements; "اخرى" is excluded because balance sheets use it too;
- **Cash Flow Statement rows for the eight**;
- **none for ADNIC** (its cash-flow lines carry no figures);
- AMLAK's newest balance sheet under 50 rows.

**Proved both ways before it is needed:**
- On the **2026-11-05** publish: 9 PASS and 3 **FAIL**. *(Corrected by review 20: the passes are the 8
  night and publish items plus ADNIC's data item; the 3 failures are data items.)* Eight
  balance sheets still carry 40–80 cash-flow rows, there is no Cash Flow Statement, and AMLAK has 50 rows.
  That is exactly F-16 before its fix.
- With `F16_DB=/tmp/f16/c/screening.sqlite`, the dry run's fixed copy, every data item **PASSES**: 0 cash-flow
  lines, the eight with 40–95 cash-flow rows, AMLAK 31.

**The sweep:** `docs/pipeline-guard-statement-headings-2026-11-06.md`, "The check after the publish, as
commands", gives the tunnel, local web and `SWEEP=1` commands. It must read 714/714 and pass the English-label
sweep.

**Status:** the F-16 doc and `PROJECT.md` keep the live result **PENDING** until it runs after the 05:00 UTC
publish.

**Pending:**
- Running that check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
