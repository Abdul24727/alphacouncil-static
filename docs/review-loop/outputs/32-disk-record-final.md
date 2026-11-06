# Output 32: review 31's two corrections, made

Commit `b76ccf5`. `git diff --check` is clean. No server changes: one read-only `ls` over SSH, streamed to
stdout.

**1. File counts.** New evidence: `docs/disk-2026-11-06/rebuild-snapshots-files.txt`, the files in each of the
143 snapshots (2026-11-06 06:54 UTC).
- 141 hold `briefs_index.sqlite`, `evidence.sqlite` and `screening.sqlite`.
- Two, `rebuild-snapshot-20260613-023500` and `rebuild-snapshot-20260626-060119`, hold only `evidence.sqlite`
  and `screening.sqlite` (`do_snapshot` skips a database that does not exist).
- The report names both, and output 31 carries a correction note.

**2. The reader, described exactly.** `_latest_prev_snapshot_screening` takes the newest snapshot **that contains
`screening.sqlite`**.
- **Today that is the newest folder:** all 143 contain the file.
- **It can fall back.** `do_snapshot` creates the folder before it copies, so a failed copy can leave a newer
  folder without `screening.sqlite`. The reader then uses the next older one that has it.
- **Where this is now said:** the report, output 31 (with a correction note) and `PROJECT.md`. Each says the code
  reads only the newest *eligible* snapshot, and that the older ones are a fallback baseline and manual restore
  points.

**The decision, unchanged in its figures, sharpened in one point.** Keep the newest 14: 14 kept (16.86 GiB), 129
removed, **80.44 GiB** freed, disk about 41%.
- **All 14 kept hold `screening.sqlite`.**
- **What the record now adds:** the nightly rule should count only folders that hold `screening.sqlite`.
  Otherwise a run of failed snapshots could push out every eligible baseline.
- **Still the owner's:** the retention decision, any deletion and the pipeline change.

**The question for the review:** is this sound, and what is the single next pre-approved step?
