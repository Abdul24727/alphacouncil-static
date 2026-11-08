# Review 100: Review 99's fix: the exact-value check fails closed

2026-11-08 11:39 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `94-push-review-99-fixes.md`.

VERDICT: FIX

ISSUES:

1. FAIL-OPEN: incomplete blob enumeration can return three zeros.

File: scripts/push-checks/count-exact-value.sh, lines 129–146.

The integrity check verifies that every blob in the tip appears in the blob list. It does not verify blobs from every earlier snapshot.

Reproduced: Created a temporary Git repository containing a dummy account value in a file deleted by the outgoing range.

Normal execution: file-contents 1, exit 3.

Injected an awk wrapper that returned exit 0 without output only for the base snapshot, while processing the tip normally.

Actual result: commits 0 / file-contents 0 / file-names 0, exit 0.

Fix: Verify blob enumeration against every snapshot, including boundary commits, not only the tip. A missing blob must produce exit 2.

2. FAIL-OPEN: incomplete filename enumeration can pass its length check.

File: scripts/push-checks/count-exact-value.sh, lines 155–160.

The script checks that the deduplicated name list contains at least as many entries as the tip. That does not establish that names from earlier snapshots survived.

Reproduced: Created a temporary repository with a dummy account value in a filename that the outgoing range deletes.

Normal execution: file-names 1, exit 3.

Injected a sort wrapper that silently omitted that base-only filename, returned exit 0, and retained the tip's names.

Actual result: three zeros, exit 0.

Fix: Validate complete pathname coverage across every snapshot, including deleted and renamed paths. Missing entries must produce exit 2.

The attached 69-test suite also passed when run independently. Its 42 fault-injection cases replace each tool for an entire execution; they do not cover selective omissions affecting only one snapshot. The two reproductions above demonstrate that the claimed fail-closed behavior remains incomplete.

DRIFT:

No scope drift. The changes remain focused on the owner's existing pre-push Argaam confidentiality checkpoint. No new site functionality, paid activity, or release was introduced.

NEXT STEP:

Claude should make one targeted correctness fix on local branch rebuild in scripts/push-checks/count-exact-value.sh and its existing test script.

Make the blob and filename completeness checks cover every snapshot, not only the tip. Add the two reproduced selective-omission cases as regression tests.

This is the highest-value pre-approved action because the confidentiality checkpoint must be reliable before the owner authorizes another push to the public repository.

Do not push or expand the work.

DONE WHEN:

bash -n passes for both scripts.

The existing 69 tests continue to pass.

A selectively silent awk omitting a base-only blob produces exit 2, not exit 0.

A selectively incomplete sort omitting a base-only filename produces exit 2, not exit 0.

Ordinary present and absent dummy values still produce exits 3 and 0 respectively.

git diff --check passes, with a clean committed change on rebuild.

Claude supplies the updated scripts, test results, and diff for review.

OWNER ITEMS:

Step 7 — Lawyer: Send the accepted lawyer review pack and legal questions to the lawyer for evaluation of the live site. This remains the principal launch dependency.

Argaam checkpoint: Once the script is accepted, privately run the exact-value check over eeb9a9d..dcc4189 and the pending outgoing range. Report only the three counts and exit status. No account name should be disclosed or committed.

Push authorization: Give a separate explicit go-ahead for pushing the pending rebuild commits, only after the confidentiality checks pass.

Step 18, item 4: Await a real customer renewal to complete billing verification. No synthetic renewal or paid test is authorized.

Response complete
