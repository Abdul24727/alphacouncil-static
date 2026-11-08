# Review 104: Review 103's fixes: real objects only, no tags or submodules

2026-11-08 12:44 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `98-push-review-103-fixes.md`.

VERDICT: FIX

ISSUES:

1. HIGH — The scan is not bound to the commit being pushed.
PROJECT.md, Step 2 (diff lines 26–31), and count-exact-value.sh, lines 160–178.

The check scans origin/rebuild..rebuild, but the documented push uses the current rebuild tip. A new commit between those operations can therefore be published without being scanned.

Independently reproduced: the check returned three zeros and exit 0. I then committed a dummy value and ran the documented push. The remote received that value.

Fix: Resolve both range endpoints to immutable commit SHAs, scan that exact range, and push only the checked tip using git push --no-follow-tags --recurse-submodules=no origin "<checked-sha>:refs/heads/rebuild". If the remote base changes, stop and repeat the check.

2. LOW — The tag-push regression test can falsely pass.
test-count-exact-value.sh, lines 203–209.

The test doesn't assert that its first push succeeded or that the remote received the intended branch commit. A failed push could satisfy the two assertions that no tag appeared.

Fix: Check the push exit status and compare the remote branch SHA with the intended commit before declaring the tag-suppression test passed.

Verified: I independently ran the supplied suite: 63 PASS, 0 FAIL. The replacement-object correction, graft-file rejection, and tag-suppression behavior work in the supplied scenarios. The attached Git transcript supports the reported clean working tree and 17 unpushed commits, but the actual project repository and remote state could not be independently inspected.

DRIFT: No material drift. The changes remain within the existing public-repository safety checkpoint; excluding tags and submodule pushes is consistent with the master plan. The remaining problem is verification completeness, not product scope.

NEXT STEP: On rebuild, close the existing Step 2 pre-push safety gate by pinning the checked commit SHA to the pushed SHA and correcting the tag-test assertion. This is pre-approved local repository work and is the most valuable Claude-controlled step before the next public push. Do not push yet.

DONE WHEN:

bash -n passes for both scripts.

bash scripts/push-checks/test-count-exact-value.sh reports zero failures.

A regression proves that a commit introduced after a clean scan cannot be published by the pinned-SHA command.

The tag test proves both successful branch publication and absence of the annotated tag.

git diff --check passes.

Claude records the exact checked SHA and test results without recording the private account name.

OWNER ITEMS:

Step 7 — Legal review (highest priority). Confirm the remaining lawyer-pack facts and send the accepted pack and legal questions to the lawyer. Written legal advice remains the primary launch dependency.

Argaam checkpoint. Privately verify the historical eeb9a9d..dcc4189 range, which was pushed without the exact-value check. After the fix, run the checkpoint again for the final proposed push range. Share only the three counts and exit status.

Public push approval. Explicitly authorize pushing the checked commit after its safety gate passes. The existing approval for the November 8 push does not authorize another push.

Step 18, item 4. Await a genuine customer renewal to complete the outstanding billing verification.

No new paid model runs, deployment, or scope expansion is required.

Response complete
