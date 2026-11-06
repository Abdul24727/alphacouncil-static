# Output 30: review 29's step, the disk diagnosis, done (read-only)

Recorded in `docs/release-readiness-2026-11-06.md`, section "Disk, measured 2026-11-06 06:40 UTC". `PROJECT.md`
§5 has a line, and the roadmap's disk item now names the cause.

**Measured (read-only SSH, idle I/O priority):**
- **`df -h /`:** 193G, 159G used, **34G available, 83%**. Inodes 3%.
- **`du -x`:**
  - `/var/backups` 98G;
  - `/opt` 43G: `/opt/alphacouncil/backend/argaam` 21G, `/opt/alphacouncil/backups` 9.8G,
    `/opt/alphacouncil-platform` 7.6G;
  - `/swapfile` 8G;
  - `/root` 4.8G;
  - `/usr` 3G.

  All of these are itemised in the report.

**The cause.** `/var/backups/alphacouncil/rebuild-snapshots` holds 143 snapshots, 2026-06-10 to 2026-11-06,
**97.3 GiB**.
- **Who writes them:** `run_rebuild_pipeline.py`'s `do_snapshot` (step 0) copies screening, evidence and briefs
  there before every rebuild.
- **Nothing deletes them:**
  - `prune_history.py` deletes interaction records;
  - the nightly hygiene prunes harvest runs (keeping 2 per ticker plus the newest full run);
  - `publish_dbs.sh` keeps 5 of its own `dbpublish-*` only.
- **What reads them:** only `_latest_prev_snapshot_screening`, which takes the newest snapshot as the baseline
  for the delta checks.
- **How fast they grow:** the newest five average 1.25 GiB each, and they grow with `evidence.sqlite`.

**Runway:** about 26 nights at 1.3 GiB a night, or about 18 at the recorded one point a night (80% on 11-02, 83%
today). The 90% mark comes in 8 to 11 nights.

**Releases.** Each release folder is 1.3G (`node_modules` 585M, `.next` 118M, `api/.venv` 165M, source 424M).
- **Beta and production:** both have `current` → `…/5c18a3ae46`, and both keep `2e44ee6fbf` and `df83e19404`.
- **What a `dfc7a3d` release needs:** about 1.3G per tier while it builds. The deploy's keep-3 prune then
  removes `df83e19404`, so the net change is about zero.
- **Rollback afterwards:** `5c18a3ae46` in both tiers.
- **Disk does not block the pending releases.**

**The owner decision:** a retention rule for the rebuild snapshots.
- **Proposal:** keep the newest 14, removing the older ones once now and nightly after. That frees **80.4 GiB**
  (the disk would be about 41%), and the oldest kept would be 2026-10-24.
- **Other numbers:** keep 7 frees 88.6 GiB; keep 30 frees 63.3 GiB.
- **Smaller items, approve or decline:**
  - `/tmp/f16` (222M, my F-16 dry-run copies);
  - the August `premigration`/`dbrefresh` backups;
  - a 1.7G tarball from 2026-05-13.

**Nothing on the server was changed or deleted.** The one exception: the third pass wrote a list of snapshot
sizes to a temporary file in `/tmp` and removed it in the same command. That is disclosed in the report too.

**The question for the review:** is this sound, and what is the single next pre-approved step?
