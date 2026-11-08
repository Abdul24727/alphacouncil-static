# Review 98: Review 97's fixes: the exact-value check reads raw objects

2026-11-08 11:08 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `92-push-review-97-fixes.md`.

VERDICT: FIX

ISSUES:

The 24 supplied tests pass when rerun independently, including both Review 97 regressions. However, two additional false negatives remain.

1. Deleted file contents escape detection.
File: scripts/push-checks/count-exact-value.sh, lines 68–79.

Independently reproduced in a throwaway Git repository:

The base commit contains dummy.deleted-41 in prior.txt.

The outgoing commit deletes that file.

git log -p base..tip exposes -dummy.deleted-41.

The scanner returns:

Plain text
commits 0
file-contents 0
file-names 0

Exit: 0 (incorrect).

The script scans blobs in the outgoing range and at the tip, but misses deleted content originating exclusively from the base. This regresses the previous patch-history coverage.

2. Deleted filenames escape detection.
File: scripts/push-checks/count-exact-value.sh, lines 82–90.

Independently reproduced:

Base contains user-dummy.deleted-name-91.txt.

The first outgoing commit deletes it.

The outgoing patch exposes that filename.

The scanner again returns three zeros and exit 0.

The filename is absent from every outgoing commit's final tree. Reading those trees does not capture the deleted path from the base.

Fix both: include the pre-change blobs and pathnames of deleted or modified entries, including the range boundary, without printing private values or filenames. Add both regressions to the existing test suite.

These examples involve material already present in the base commit, not newly introduced secrets. Nevertheless, the outgoing patches expose the exact values, and the current check silently reports success.

DRIFT: The work remains within the master plan: improving the existing public-repository security checkpoint, with no new product features or tooling. The two remaining defects prevent accepting the claimed completeness, but do not change any settled launch decisions.

NEXT STEP: Claude should fix the two false negatives in scripts/push-checks/count-exact-value.sh and extend test-count-exact-value.sh, on branch rebuild.

This is the highest-value pre-approved work Claude can perform now because it removes the demonstrated fail-open cases before the next public push. Do not push or release as part of this step.

DONE WHEN:

Both independent regression scenarios produce exit 3, never 0, with nonzero counts and no private values printed.

All original 24 tests still pass.

The absent-value case still produces exactly three zeros and exit 0.

Bad input and Git errors still produce exit 2.

git diff --check passes, the changes are committed on rebuild, and the test transcript is recorded under docs/screenshots/push-2026-11-08/.

OWNER ITEMS:

Step 7 — Lawyer (highest priority): Confirm the outstanding owner facts and send the accepted lawyer pack with docs/legal-questions-2026-10-27.md. The lawyer evaluates the already-published site. This can proceed independently of the scanner fix.

Argaam checkpoint: After the fix, privately run the corrected exact-value check against the already-pushed eeb9a9d..dcc4189 range and the next outgoing range. Record only the three counts and exit status. The earlier push's unresolved exception remains until checked.

Public push: Give a separate explicit approval before Claude pushes the six local commits, including the subsequent fix commit(s), after all required scans pass.

Step 18, item 4: Wait for a real customer's renewal to verify the remaining billing requirement. Do not substitute a synthetic renewal.

Response complete
