# Output 31: review 30's three issues, fixed

Commit `5474b29`. `git diff --check` is clean.

**1. The temporary file is now disclosed the same way everywhere.** The report, `PROJECT.md` §5 and output 30
all say: read-only, with one disclosed deviation. One pass wrote a temporary list of sizes to `/tmp` and
removed it in the same command, which crossed review 29's boundary. The evidence pass for this output was
stdout-only and wrote nothing on the server. No new server file was created or deleted.

**2. Growth rates, labelled.** 33.77 GiB is available (`df -B1`), and 90% is 14.5 GiB away.

| Rate | Basis | Full in | 90% in |
|---|---|---|---|
| 1.26 GiB a night | the snapshot alone, its newest size | ~27 nights | ~11 nights |
| 1.45 GiB a night | **recorded:** 80% on 11-02 to 83% on 11-06, 0.75 point a day | ~23 nights | ~10 nights |
| 1.93 GiB a night | **conservative scenario:** one point a night | ~18 nights | ~8 nights |

The report notes that `df` rounds to whole points. `PROJECT.md` and the roadmap now say 0.75 point a day.

**3. Inventory and source excerpts, committed** in `docs/disk-2026-11-06/`. Both files were scanned with Step 2's
regex, for emails and IPs, and for the Argaam account name: 0 hits, apart from `127.0.0.1`.

`rebuild-snapshots-inventory.txt`:
- **Inventory:** all 143 snapshots, each with allocated bytes (`du -s --block-size=1`), apparent bytes and file
  count. 141 have three files; two (2026-06-13 and 2026-06-26) have two, `evidence.sqlite` and
  `screening.sqlite`. *(Corrected after review 31: this said "3 each". The file names are in
  `rebuild-snapshots-files.txt`.)*
- **Totals:** sum of allocated 97.30 GiB, equal to `du -s` of the folder.
- **Retention:**
  - keep 14: keeps 14 (16.86 GiB), removes **129**, frees **80.44 GiB**, disk about 41%;
  - keep 7: removes 136, frees 88.60 GiB;
  - keep 30: removes 113, frees 63.35 GiB.

`pipeline-excerpts.txt`, pinned by md5:
- **Writer:** `do_snapshot` at line 297 of `run_rebuild_pipeline.py`. It is called at line 507, and the chain
  aborts without it.
- **Reader:** `_latest_prev_snapshot_screening` at line 330, called once at line 399. It takes the newest snapshot
  **that contains `screening.sqlite`** as the baseline for the delta checks. That can fall back to an older
  folder if newer ones lack the file. Today all 143 contain it.
- **The folder:** the `--backups-dir` default `llm-council/backups` (line 461) is a symlink, since 2026-08-02, to
  `/var/backups/alphacouncil/rebuild-snapshots`.
- **The three pruning scripts:** `prune_history.py` (interaction records), the nightly hygiene (harvest runs) and
  `publish_dbs.sh` (keeps 5 of its own `dbpublish-*`). None touches the snapshots.
- **The full reference search:**
  - **Where it looked:** code, scripts, cron and systemd.
  - **Code that names `rebuild-snapshot`:** `run_rebuild_pipeline.py` and `tests/test_freshness.py`, which
    builds its own fake snapshot in a temporary folder. The other hits are 139 nightly logs.
  - **Cron:** 0 lines in the root crontab.

So the code reads only the newest *eligible* snapshot. The older ones serve as a fallback baseline after failed
snapshots, and as manual restore points; that is what the keep-14 decision weighs. *(Corrected after review 31:
this said no code reads anything older than the newest snapshot.)*

**Unchanged:** nothing is deleted and no pipeline change is made. Snapshot retention, any deletion and the
nightly prune are the owner's decisions.

**The question for the review:** is this sound, and what is the single next pre-approved step?
