# Review 101: Review 100's fix: only git and grep touch the data

2026-11-08 12:02 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `95-push-review-100-fixes.md`.

VERDICT: FIX

ISSUES:

1. UTF-8 validation is incomplete; an incorrectly encoded value can produce a false-clean result.

File: scripts/push-checks/count-exact-value.sh, lines 64–77.

Claim: UTF-16 value files are refused, preventing an unmatchable value from returning three zeros.

Finding: The script rejects UTF-16 byte-order marks but does not validate that the remaining bytes are valid UTF-8. LC_ALL=C permits invalid UTF-8 bytes.

Independent reproduction: In a throwaway Git repository containing the dummy value 中文测试 in an outgoing file:

Value-file encoding



File-content count



Exit




UTF-8



1



3




UTF-16BE without BOM



0



0




Latin-1 encoding of café, with UTF-8 café in Git



0



0

Git and grep operated normally. The value was present, but the guard returned a clean result.

Test gap: test-count-exact-value.sh, lines 129–135, tests BOM-bearing UTF-16 but not invalid UTF-8 or BOM-less UTF-16BE.

Fix: Validate the value file's UTF-8 bytes before generating search patterns, using Bash builtins to preserve the design. Reject invalid encodings with exit 2. Document that BOM-less UTF-16 cannot always be distinguished from valid UTF-8 by bytes alone.

Otherwise verified: All 46 supplied regression tests passed independently. The previous selective awk and sort omissions are addressed.

DRIFT: The implementation remains within the master plan's Step 2 pre-push security checkpoint. No product features, campaigns, or architectural changes were introduced.

NEXT STEP: On rebuild, fix the value-file encoding validation in scripts/push-checks/count-exact-value.sh and extend scripts/push-checks/test-count-exact-value.sh with the two reproduced false-clean cases. This is pre-approved repository work and removes a remaining unsafe clearance path before the owner's private Argaam check and next public push.

DONE WHEN:

bash -n passes for both scripts.

The complete regression suite passes.

A dummy value present in Git produces:

Correct UTF-8 input: exit 3.

Invalid UTF-8 input: exit 2.

BOM-less UTF-16BE reproduction: exit 2.

A genuinely absent value with valid UTF-8 input produces exactly three zeros and exit 0.

git diff --check passes, and no private account value is printed or committed.

OWNER ITEMS:

Step 7 — Legal: Send the accepted lawyer pack and questions to the lawyer. This remains the principal launch dependency.

Argaam checkpoint: After the encoding fix passes review, privately check the previously pushed eeb9a9d..dcc4189 range and the next outgoing origin/rebuild..rebuild range. Require three explicit zeros and exit 0 for each.

Public push: Give a separate explicit go-ahead before Claude pushes the 12 local commits. No push is authorized by this review.

Step 18, item 4: Verify an actual customer renewal when one occurs.

Response complete
