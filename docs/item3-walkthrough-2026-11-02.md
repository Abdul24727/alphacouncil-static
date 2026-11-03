# Item 3, walked through: the release, the two patches, and the publish

2026-11-02. Written for the owner to run at the server. Nothing in here was run against
production from this session; every command below is yours.

The sequence Next Up item 3 asks for is *ship the API to beta → apply the two pipeline patches →
publish the database*. Reading the deploy scripts and the server's own rebuild chain while writing
this turned up two things that change the order. They are first, because they decide the rest.

---

## Correction, 2026-11-03 (after the publish)

**§1's premise was half true, and A4 did not remove the exposure.** "After it, both tiers understand
`periods`" holds for the API only. The panel of the release that shipped (`df83e19404`,
`web/src/components/stock/research-panels.tsx`, `StatementPanel`) still heads every column
`t("statements.fy", { year })` and never reads `periods`, so after the 05:03 UTC publish Aramco's TTM
income statement and June-2026 balance sheet sit under "FY2026" on beta, and would for any Pro member on
production (0 today; the panel is locked signed out). Nobody compared the panel's code with this claim
before relying on it. The data and the API pass. The post-publish check and the fix are recorded in
PROJECT.md, Next Up item 3, as F-13.

## Corrections, 2026-11-02 evening (read before anything below)

Read-only checks at 20:33 UTC (server and repository). Four things below are now wrong or incomplete.

1. **`publish_dbs.sh` would not publish in B7.** The crontab runs it **hourly from 05:00 to 10:00 UTC**
   (`0 5-10 * * *`), not once. Each run publishes only when the in-tree `briefs_index` has a newer
   `MAX(as_of_date)` than the served one (the "is there anything newer to publish?" block); otherwise it
   logs "served data is already current — nothing to publish." and exits. That is what the 06:00–10:00 runs
   on 2026-11-02 logged. So a manual B7 after the day's 05:00 publish **does nothing**, because the four
   stages do not move the briefs date. The same gate is good news: the hourly runs cannot publish a
   half-checked `det_out/screening.sqlite` either. **The working shape follows from it:** apply, run the four
   stages and check (B3–B6) **before 00:00 UTC**. If the check is good, leave the patches applied: the nightly
   re-runs the chain with them, and its own 05:00 publish carries the repair. If it is not good, reverse the
   patches and restore `det_out` before 00:00. The nightly's rebuild finished at 02:17 UTC on 11-02
   (`det_out/screening.sqlite` mtime) after the scrape, so the manual stages must be done well before then.
2. **Billing is open on production since 2026-11-02 18:20 UTC** (PROJECT.md Step 18). §1's point 5 no longer
   holds: `/statements` is Pro-only and production's visitors are Free unless they pay, so the mislabelled
   columns of option (b) would reach paying members only. Nobody is subscribed today. (a) is still the order
   to use.
3. **Phase A ships all of `rebuild`, not only `periods`.** `git diff 74ce427bf6..rebuild -- api/app web/src
   web/messages deploy` is 24 files, about 2,600 lines. It includes:
   - P9 in every seat's pack (about +60 % input tokens per seat call, no prompt caching);
   - the mandates (Priority Two) and the Chair's rulings (Priority Three), which change what the paid room
     does;
   - the `llm.py` retry-path changes, which §6 of the plan says should carry one real-model session on beta
     before production.

   So A3 should be that session (about $0.30–0.60, a paid call), not only a look at the panel.
4. **Unchanged and confirmed:** production and beta both run `74ce427bf6`. The pipeline repo is at
   `a38dc07`, and neither file the patches edit is modified. The other modified tracked files each map to a
   `docs/` patch (`ingest_ticker_insights.py` is F-F's), plus `RELEASE.json`. `publish_dbs.sh` is in
   `/opt/alphacouncil/bin/`. 40 GB is free for the B1 copies (`screening.sqlite` is 29 MB). Nothing in the
   pipeline was running. The API suite on `rebuild` is 576 passed, 11 skipped, after a flaky F-11 test was
   fixed (`b0a6c36`).

5. **B6's query and expected counts, corrected after the run (21:28 UTC).**
   - The query `… GROUP BY ticker_key HAVING COUNT(DISTINCT period_end) > 1` flags every multi-year annual
     income statement, because each FY has its own year-end. The right test groups by `ticker_key, section,
     fiscal_year`. It returned none on the repaired file.
   - The expected gauge statuses (`ok 1679…1954`) came from runs that never parsed Tadawul in full. With
     250 Tadawul income statements back, the real result is `missing_inputs 1109, na_sector 2241, ok 3218,
     undefined_nonpositive 52`. Every change is on Tadawul and every move is an income-statement gauge
     becoming computable (PROJECT.md, Next Up item 3, "B6").

**Still the owner's, before item 4 rather than before the publish:** probes D1, D3 and D6 change their
correct answers once the repair lands. The closeout left their bands untouched. Retire or re-register them
before the pilot is scored.

## 1. Publishing the database is a production change, and "ship to beta first" does not protect production

`docs/priority-one-closeout-2026-10-29.md` step 5 says to ship the API change to **beta** before
publishing, because after the repair one balance-sheet row carries a December-2025 figure beside a
June-2026 one and the old response shape labels them only "2025" and "2026". That protects beta.
Production reads the same file.

Five checks, all from the repository:

1. `deploy/acp-prod-api.service` — `ReadOnlyPaths=/var/lib/alphacouncil /opt/alphacouncil`.
2. `scripts/deploy-production.sh --setup` builds production's env by copying the market-data lines
   straight out of staging's:
   `grep -E '^(BRIEFS_DB|SCREENING_DB|EVIDENCE_DB|…)=' "$STAGING" > "$ENVDIR/api.env"`. So
   production's `SCREENING_DB` **is** `/var/lib/alphacouncil/screening.sqlite`, the path
   `publish_dbs.sh` replaces.
3. The live production release is **`74ce427bf6`** (2026-10-27 21:27 UTC, F-10 and F-11 over
   `3228ab57e9`). It serves `/statements`
   (`api/app/routers/ticker_research.py:203` at that commit, `Depends(require_pro)`) and
   returns `Statements(years=sorted(yrs), …)` with each row's `values` keyed by fiscal year —
   **no `periods`**. `git merge-base --is-ancestor f921011 74ce427bf6` is false: the evidence
   work is not in it. *(Corrected 2026-11-02: this read `3228ab57e9`, which is the release
   BEFORE the live one. Both lack `periods`, so nothing below changes — but a hash named as
   the live release is what a later reader checks against, so it has to be the live one.)*
4. `web/src/components/stock/research-panels.tsx:153` at that release renders one column per
   year, headed `t("statements.fy", { year })`, and its `web/messages/en.json:509` defines
   `"fy": "FY{year}"`.
5. `/statements` is `dependencies=[Depends(require_pro)]`, and production sets none of
   `BILLING_OPEN` / `EARLY_ACCESS`, so `plans.plan_of` returns `pro` for everyone
   (`docs/launch-check-2026-10-27.md`, "Before you run those two"). Every production visitor can
   open the panel.

**So the first publish puts a TTM@2026-06 income statement and a Q@2026-06 balance-sheet snapshot
under a column headed "FY2026", beside "FY2025", on the live site.** That is the defect the
closeout's §2 calls "worse than today's defect", and it would be live and unattended.

Two ways out, and the choice is yours:

- **(a) Ship the release to production as well, before publishing.** It costs one more script run.
  `scripts/deploy-production.sh` already enforces beta-first (it reads
  `readlink -f /opt/alphacouncil-platform/current` and refuses unless beta runs the identical
  sha), so the gate you want is built in. **This is what I would do**, and the walkthrough below
  is written for it.
- **(b) Publish first and accept the mislabelled columns on production** until the release lands.
  Defensible if you want the data repaired tonight and the release reviewed on its own time —
  production had run no sessions in 30 days as of 2026-10-27 — but it is the one state the
  closeout argues against, so decide it deliberately rather than by sequence.

One thing to weigh before (a): the release also carries **P9 into production's debate path**,
about +60 % input tokens per seat per call with no prompt caching. That costs nothing while nobody
convenes a room, and the single constant is `evidence.DATASET_BUDGET`.

## 2. If you apply the patches and stop, the server publishes them for you

- Root's crontab runs `/opt/alphacouncil/bin/nightly_pipeline.sh` at **00:00 UTC**
  (`docs/data-audit-part2-2026-10-19.md`, "How the nightly run works").
- Its rebuild step is `llm-council/run_rebuild_pipeline.py`, and at the server's base `a38dc07`
  that chain's ordered steps include **8 `parse_financial_statements`**,
  **11 `compute_fundamental_gauges`**, **13 `compute_sector_averages`** and
  **14 `compute_gauge_scores`** — the whole one-pass, over the whole universe, unattended.
- `publish_dbs.sh` publishes at about **05:00 UTC** (observed: published 05:00:43 on 2026-10-23;
  the `dbpublish-*` backups are one per day at 05:00:01Z).

So the closeout's "**Do not publish yet**" is not a state the server will hold for you. Applying
the patches *is* the decision to publish, unless the manual pass and its checks finish inside the
same UTC day. Run `date -u` on the server before you start and give yourself room; the 714-ticker
parse is the long stage and I have no timing for it from here.

If you need to stop midway, the safe parking place is **before** `git apply` — not after.

## 3. A third thing, smaller: do not use `--from-step 8`

It is the obvious shortcut and it is wrong here. The chain continues past step 14 to
`evidence_builder`, `news_indexer` and **`generate_news_ai`**
(`generate_news_ai.py --db evidence --days 21 --limit 120`) — an LLM step. That is a paid call,
against §4 and against the closeout's own rule of no paid run between application and the
post-publish check. Run the four scripts individually.

---

## Phase A — the release, on both tiers. No data changes.

**A1. The tree.** Both deploy scripts ship `git archive HEAD`, so they ship the last **commit**.
`deploy-production.sh` refuses on a dirty tree; `deploy-staging.sh` does not check, and would
silently leave uncommitted work out of beta. Confirm you are clean and on `rebuild`:

```
git status -sb
```

Pushing is not required by either script — both read the local HEAD. The commits unpushed right
now mean the deployed sha would not be on the public remote; that is a provenance gap, not a
blocker, and the push is a separate go-ahead whenever you want it.

**A2. Beta.**

```
scripts/deploy-staging.sh
```

It uploads, builds, switches the symlink, restarts `acp-api` and `acp-web`, waits for both health
checks and prints `deployed <sha>`.

**A3. Look at beta.** The database is still the old one at this point, so this checks the
*release*, not the repair: `https://beta.alphacouncil.tech`, a Tadawul ticker, the Financials
panel. Open it on **`beta.alphacouncil.tech`**, not an IP — and on localhost work use
`localhost`, never `127.0.0.1` (`CLAUDE.md` line 50; Next 16 blocks dev resources from an unknown
host and the page then renders its shell with every panel stuck on its skeleton and nothing in the
console to say why).

**A4. Production.**

```
scripts/deploy-production.sh
```

It re-checks that beta runs the same sha, refuses a dirty tree, builds, switches and restarts
`acp-prod-api` / `acp-prod-web`. **This is the step that removes the exposure in §1** — after it,
both tiers understand `periods`.

**A5. Confirm.** `https://alphacouncil.tech`, same ticker, same panel. Unchanged data, new release.

## Phase B — the pipeline. One sitting, started early in the UTC day.

**B1. Named safety copies, outside the five-day rotation.** `publish_dbs.sh`'s own backups are a
rotation of five, so five more publishes evict them.

```
cp -a /opt/alphacouncil/backend/llm-council/det_out/screening.sqlite /opt/alphacouncil/backups/prestatementrepair-det_out-screening.sqlite
cp -a /var/lib/alphacouncil/screening.sqlite /opt/alphacouncil/backups/prestatementrepair-live-screening.sqlite
```

**B2. Copy the two patches up**, then back up each target file per the standing rule:

```
cd /opt/alphacouncil/backend
cp -p llm-council/parse_financial_statements.py llm-council/parse_financial_statements.py.bak-20261102
cp -p llm-council/compute_fundamental_gauges.py llm-council/compute_fundamental_gauges.py.bak-20261102
```

**B3. Check, then apply.** `-p1`, from `/opt/alphacouncil/backend`:

```
git apply --check -p1 /root/pipeline-fix-statements-2026-10-28.patch && git apply -p1 /root/pipeline-fix-statements-2026-10-28.patch
git apply --check -p1 /root/pipeline-fix-gauges-2026-10-29.patch && git apply -p1 /root/pipeline-fix-gauges-2026-10-29.patch
```

Both are verified to apply against `a38dc07`, and your 2026-11-02 check confirmed the server is
still there with neither file modified — so `--check` should pass. If it does not, stop: something
changed since this morning, and nothing after this line is safe to assume.

Then compile both before running anything:

```
/opt/alphacouncil/pipeline-venv/bin/python -m py_compile llm-council/parse_financial_statements.py llm-council/compute_fundamental_gauges.py
```

**B4. Get the four exact command lines from the server itself.** `--dry-run` executes nothing — no
snapshot, no dead-man's-switch ping — and prints the `cwd` and full `cmd` of every step with the
real resolved paths and interpreter:

```
cd /opt/alphacouncil/backend/llm-council && python run_rebuild_pipeline.py --dry-run
```

Take the `cmd` lines for steps **8, 11, 13, 14** out of that output. They will look like
`… parse_financial_statements.py --universe <universe> --db <screening>`,
`… compute_fundamental_gauges.py --db <screening> --universe <universe>`,
`… compute_sector_averages.py --db <screening>` and `… compute_gauge_scores.py --db <screening>` —
but use the printed ones, not these, so the interpreter and the paths are the server's own.

**B5. Run those four, in that order, and do not publish.** `--db` points at
`llm-council/det_out/screening.sqlite`, which is not what the API reads, so nothing is live yet.
**Stage 14 must run**: the gauge patch clears a ranking whose value moved, so without it every
changed gauge is correct and unranked — safe, but no percentiles.

**B6. Check `det_out/screening.sqlite` before publishing.** The server has no `sqlite3` binary, so
run this through the interpreter the dry run printed. Save it as `/root/check-repair.py` and run
it, rather than pasting a heredoc:

```python
import sqlite3
db = "/opt/alphacouncil/backend/llm-council/det_out/screening.sqlite"
c = sqlite3.connect("file:" + db + "?mode=ro", uri=True)
q = lambda s: c.execute(s).fetchall()

print("tadawul income statements:", q(
    "SELECT COUNT(DISTINCT ticker_key) FROM fundamentals_lineitems"
    " WHERE ticker_key LIKE '%_TADAWUL' AND section='Income Statement'"))
print("reporting modes:", q(
    "SELECT period, COUNT(*) FROM fundamentals_lineitems GROUP BY period"))
print("income sections spanning >1 period_end (want none):", q(
    "SELECT ticker_key FROM fundamentals_lineitems WHERE section='Income Statement'"
    " GROUP BY ticker_key HAVING COUNT(DISTINCT period_end) > 1 LIMIT 5"))
print("2222 sections:", q(
    "SELECT section, period, period_end FROM fundamentals_lineitems"
    " WHERE ticker_key='2222_TADAWUL' GROUP BY section, period, period_end"))
print("gauge statuses:", q(
    "SELECT status, COUNT(*) FROM fundamentals_gauges GROUP BY status"))
print("ok gauges with no ranking (want 0):", q(
    "SELECT COUNT(*) FROM fundamentals_gauges WHERE status='ok' AND score IS NULL"))
```

What to expect: Tadawul income statements go from **0** towards the exchange's **243** tickers —
**how far is not predictable from here**, because the full 714-ticker parse needs the harvest pages
and was never run locally; a ticker gets one only where the page carries four consecutive
quarters, so read this as "0 became a large number", not as a target to hit. `period` is populated
rather than NULL; no income-statement section spans more than one `period_end`; 2222 shows
`Income Statement TTM 2026-06` beside `Balance Sheet Q 2026-06` — the same date, which is the
whole point of the repair; the gauge statuses stay close to
`{missing_inputs 2325, na_sector 2500, ok 1679…1954, undefined_nonpositive 26}`; and no `ok` gauge
is unranked. (`period`, `period_end` and `source_json` are added to `fundamentals_lineitems` by the
patch's own `ALTER TABLE`, and `fundamentals_lineitems_quarterly` is new — so a query naming them
failing means the parse stage did not run.)

**B7. Publish, then look.**

```
publish_dbs.sh
```

Then production and beta, same ticker, Financials — now with the repaired data under correctly
labelled periods — and `/healthz/deep`. **No paid run between B3 and here**: rollback restores the
file but cannot undo what was read while it was live.

---

## Rollback

```
cd /opt/alphacouncil/backend
patch -R -p1 < /root/pipeline-fix-statements-2026-10-28.patch
patch -R -p1 < /root/pipeline-fix-gauges-2026-10-29.patch
cp -a /opt/alphacouncil/backups/prestatementrepair-live-screening.sqlite /var/lib/alphacouncil/screening.sqlite
```

Both patches are proven reversible byte for byte. The added columns are nullable and SQLite cannot
drop them; restoring the file makes that moot. For the release, `deploy-*.sh` keeps the three
newest releases under `…/releases/`, so the previous sha is still on disk and the symlink can be
pointed back at it.

## What this file does not know

- **How long the four stages take over 714 tickers.** The nightly's 00:00 → 04:55 window includes
  the scrape, so it is not an answer. Budget generously.
- **Anything under `/opt/alphacouncil/bin/`.** Your 2026-11-02 `git status` could not see it —
  `_bin/` is not tracked at `a38dc07` and is not inside `/opt/alphacouncil/backend`. Neither patch
  here touches it.
- **Whether `publish_dbs.sh` is on `PATH`.** It is referred to by name throughout the docs; find
  it before B7 rather than during it.
- **Production's env file.** Reading `/etc/alphacouncil-platform/prod/api.env` is a credentials
  read and was refused, so §1's conclusion about production's `SCREENING_DB` rests on the service
  unit and on the setup script that writes that file, not on the file itself.
