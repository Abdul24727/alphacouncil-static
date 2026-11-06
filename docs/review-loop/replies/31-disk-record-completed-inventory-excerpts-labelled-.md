# Review 31: Disk record completed: inventory, excerpts, labelled rates (review 30 step)

2026-11-06 06:54 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `31-disk-record-completed.md`.

VERDICT: FIX

ISSUES:

1. Output 31’s “3 each” contradicts the inventory: [line 12](C:/projects/alphacouncil-platform/docs/disk-2026-11-06/rebuild-snapshots-inventory.txt:12) and line 16 each record **two files**. Correct breakdown: 141 snapshots with three files, two with two. The retention counts and savings do reproduce.
2. The claim “no code reads anything older than the newest snapshot” is too absolute. The [reader excerpt](C:/projects/alphacouncil-platform/docs/disk-2026-11-06/pipeline-excerpts.txt:74) selects the newest snapshot **containing `screening.sqlite`**, so it can fall back to an older directory. Correct this in output 31 and the readiness report.

DRIFT: This follow-up stayed within launch preparation; the earlier temporary-file boundary breach is now disclosed consistently. The destination remains the existing site finished, published and polished in both languages at 1440 and 390 px, under the unchanged master plan and owner gates.

NEXT STEP: On `rebuild`, finish the existing disk decision record by correcting these two claims in `docs/review-loop/outputs/31-disk-record-completed.md`, `docs/release-readiness-2026-11-06.md` and corresponding `PROJECT.md` wording. The committed evidence is sufficient; this makes the urgent retention proposal accurate and ready for the owner’s decision.

DONE WHEN: The records distinguish the two file-count exceptions, describe the newest eligible baseline correctly, retain the verified keep-14 figures—14 kept, 129 removed, 80.44 GiB freed—and `git diff --check` passes. No server changes are needed.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice—the principal unfinished launch requirement.
2. Decide snapshot retention; separately authorize deletion and the nightly pipeline change.
3. Authorize beta release, then production after verification; separately authorize a public push after auditing the exact outgoing range.
4. Resolve F-14’s rejected pipeline key.
5. Settle D1/D3/D6 and authorize/fund the $66 pilot; the $393 run remains separate.
6. Decide the gated `owns` patch, duplicate webhook and test-account cleanup. Renewal verification still awaits a real customer’s renewal.

Response complete
