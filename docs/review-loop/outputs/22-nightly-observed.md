# Output 22: review 21's step, tonight's run observed before the publish

Commit `ebe6818`. Recorded in `docs/pipeline-guard-statement-headings-2026-11-06.md`, "Tonight's run, observed
before the publish".

Observed at **2026-11-06 01:46 UTC**, read-only:
- **Parser hash:** `9a0b7aa05da2029167c8de1a5fffaf4c`, the patched parser.
- **Run log** `/opt/alphacouncil/logs/daily_20261106.log`: the run started 00:00:01 UTC, the Argaam session gate
  passed, and the scrape started 00:00:30 in **full** mode (Friday) with 8 workers.
- **Scrape progress**, from `batch_dailyrun_20261106_w*.done.json`: **329/716** companies (40–42 per worker),
  updated 01:44–01:46. That rate puts the end around 03:50 UTC; the rebuild then runs, with the parse as its
  step 8.
- **Explicitly PENDING:**
  - the parse step's completion and totals;
  - any `UNKNOWN STATEMENT HEADING` warning;
  - the run's `ALERT [OK]`;
  - the publish (hourly 05:00–10:00 UTC; whichever hour finds the night done);
  - all data items;
  - the 714/714 English-label sweep.
- The log's session-gate lines name the Argaam account. Under the owner's rule, nothing from them was copied;
  a grep of the two edited files for the name finds 0.

**Next timed events:**
- the scrape's end, around 03:50 UTC;
- the parse during the rebuild;
- the publish, at or after 05:00 UTC.

Then `scripts/pipeline-checks/f16_after_publish.py` runs, followed by the sweep.

**The question for the review:** is this sound, and what is the single next pre-approved step? Is there
pre-approved work worth doing before the run reaches its parse, or is the right step to wait for it?
