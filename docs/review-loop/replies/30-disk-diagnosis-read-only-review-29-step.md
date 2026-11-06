# Review 30: Disk diagnosis, read-only (review 29 step)

2026-11-06 06:47 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `30-disk-diagnosis.md`.

VERDICT: FIX

ISSUES:

1. [PROJECT.md:262](C:/projects/alphacouncil-platform/PROJECT.md:262) says “Nothing on the server was changed.” The [report:299](C:/projects/alphacouncil-platform/docs/release-readiness-2026-11-06.md:299) discloses creating and deleting a temporary file. That contradicts the project record and review 29’s explicit requirement that no server files be changed or deleted.
2. [Report:287](C:/projects/alphacouncil-platform/docs/release-readiness-2026-11-06.md:287): 80% on November 2 to 83% on November 6 is approximately **0.75 percentage points per day**, not a measured one point per night. Keep the faster rate as a conservative scenario, clearly labelled, or supply measurements supporting it.
3. [Report:279](C:/projects/alphacouncil-platform/docs/release-readiness-2026-11-06.md:279): the snapshot-reader claim and retention savings lack supporting source excerpts and a per-snapshot size inventory. The named pipeline files are absent from this repository, so the proposed deletion’s basis cannot be independently checked here. The deploy scripts do confirm keeping three releases.

DRIFT: The diagnosis stayed within existing launch preparation, but the temporary-file operation crossed the explicit read-only boundary. The destination remains the existing site finished, published and polished in both languages at 1440 and 390 px, under the unchanged master plan and owner approval gates.

NEXT STEP: Complete the existing disk decision record in `docs/release-readiness-2026-11-06.md` and reconcile `PROJECT.md`. Use strictly read-only SSH with output streamed directly back to capture snapshot paths, allocated sizes, and the relevant writer/reader/pruning source excerpts; correct the growth calculation and disclose the temporary-file exception consistently. This makes the pending retention decision reviewable without authorizing deletion or adding tooling.

DONE WHEN: The dated inventory reproduces the retention totals—including 14 kept and 129 proposed removals for the recorded 143 snapshots—and source excerpts support the baseline dependency. Growth assumptions are explicit, both records agree, `git diff --check` passes, and the follow-up creates or deletes no server files.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice—the principal unfinished launch requirement.
2. Decide snapshot retention and separately authorize any deletion and nightly pipeline change; resolve F-14’s rejected key.
3. Authorize beta release, then production after verification; separately authorize the public push after auditing the exact outgoing range.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot; the $393 run remains a separate decision.
5. Decide the gated `owns` patch, duplicate webhook and test-account cleanup. Renewal verification still awaits a real customer’s renewal.

Response complete
