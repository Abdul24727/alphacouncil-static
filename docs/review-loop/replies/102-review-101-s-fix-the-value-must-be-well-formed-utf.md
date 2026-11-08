# Review 102: Review 101's fix: the value must be well-formed UTF-8

2026-11-08 12:16 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `96-push-review-101-fixes.md`.

VERDICT: FIX

ISSUES:

1. Critical — divergent Git ranges can produce a false clean result.

File: scripts/push-checks/count-exact-value.sh, lines 150–164 and 176–179.

The script assumes git rev-list --boundary A..B includes commit A. That is true for the normal linear history, but not necessarily when A and B have diverged.

Independently reproduced using the attached script:

Created two branches from a common ancestor.

Added dummy.secret-987 to a file on branch A.

Created branch B without that value.

git diff A..B showed the sensitive file being deleted.

The scanner returned:

Plain text
commits 0
file-contents 0
file-names 0
exit 0

Neither Git nor grep malfunctioned. The scanner simply never examined A's tree.

Required fix: Resolve the range's starting commit explicitly and include its tree in the snapshot list, regardless of the boundary output. Add a regression test using diverged branches that must return exit 3.

This defect does not invalidate the successful tests for normal linear ranges, but it makes the scanner's general claim of checking everything the range shows incorrect.

DRIFT: No product-scope drift. The UTF-8 validation addresses review 101's two failures, and I independently reran all 55 tests successfully. Both attached scripts also match the Git blob hashes reported in git-state-96.txt. The remaining problem is an overstated coverage guarantee, not a new feature requirement.

NEXT STEP: On rebuild, fix scripts/push-checks/count-exact-value.sh to include the explicitly resolved starting commit in snaps, alongside the tip and existing boundary snapshots. Add the divergent-branch regression to test-count-exact-value.sh. This closes the demonstrated false-pass path before the owner's private Argaam checkpoint. Commit locally; do not push.

DONE WHEN:

The divergent-branch reproduction returns exit 3, with file-contents greater than zero.

All 55 existing tests and the new regression pass.

bash -n passes for both scripts.

git diff --check passes.

The scanner still prints only three count lines and never reveals the value.

No release, push, or paid call occurs.

OWNER ITEMS:

Step 7 — Legal review: Confirm the three flagged facts, including the hosting data-centre country, and send the accepted lawyer pack with the legal questions.

Argaam checkpoint: After the scanner fix, privately run the exact-value check for eeb9a9d..dcc4189. Keep the account name outside the public repository.

Push approval: Give a separate explicit go-ahead before Claude pushes the 14 locally ahead commits and the additional fix.

Step 18 item 4: Wait for an actual customer renewal and record its result. Do not substitute a synthetic transaction.

The optional Moyasar duplicate-webhook cleanup and server hardening remain lower priority.

Response complete
