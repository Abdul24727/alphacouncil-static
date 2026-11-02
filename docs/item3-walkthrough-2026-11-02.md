# Item 3, walked through: the release, the two patches, and the publish

2026-11-02. Written for the owner to run at the server. Nothing in here was run against
production from this session; every command below is yours.

The sequence Next Up item 3 asks for is *ship the API to beta → apply the two pipeline patches →
publish the database*. Reading the deploy scripts and the server's own rebuild chain while writing
this turned up two things that change the order. They are first, because they decide the rest.

---

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
3. The live production release is `3228ab57e9`. It serves `/statements`
   (`api/app/routers/ticker_research.py:203` at that commit) and returns
   `Statements(years=sorted(yrs), …)` with each row's `values` keyed by fiscal year — **no
   `periods`**. `git merge-base --is-ancestor f921011 3228ab57e9` is false: the evidence work is
   not in it.
4. `web/src/components/stock/research-panels.tsx` at that commit renders one column per year,
   headed `t("statements.fy", { year })`, and that release's `web/messages/en.json:508` defines
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
