# Review 33: PROJECT.md status reconciled: F-15, English-label candidate, go-aheads (review 32 step)

2026-11-06 07:03 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `33-status-reconciled.md`.

VERDICT: FIX

ISSUES:

1. The specific F-15, F-16, candidate and audit corrections check out, but §6’s status reconciliation remains incomplete. `PROJECT.md:293` still says Priority Three is unstarted; lines 294–297 say the ingestion repair awaits application and Saudi income statements are absent. These contradict the completed release at lines 1520–1547, the live repair at lines 265–266, and rulings implemented in `api/app/debate/engine.py:389`.
2. `PROJECT.md:304` still calls the repository private, contradicting the public-repository decision at line 2. Lines 309–311 still describe Steps 22/23 as awaiting production, contradicting their DONE statuses at lines 1041 and 1068.

DRIFT: No scope drift: this was documentation-only work within the plan. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with recorded decisions and owner gates preserved.

NEXT STEP: On `rebuild`, finish reconciling `PROJECT.md` §6’s remaining obsolete status paragraphs against the recorded outcomes. Explicitly mark historical descriptions as superseded; this prevents the project’s sole status record from directing Claude to repeat completed work or request obsolete approvals.

DONE WHEN: Every §6 status agrees with the completed outcomes and current release record; historical evidence and approval gates remain intact. Only `PROJECT.md` changes, and `git diff --check` passes.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Decide snapshot retention; separately authorize deletion and the nightly pipeline change.
3. Authorize beta release, then production after verification; separately authorize the public push after auditing the exact outgoing range.
4. Resolve F-14’s rejected pipeline key.
5. Settle D1/D3/D6 and approve/fund the $66 pilot; the $393 run needs separate approval.
6. Decide the gated `owns` patch, duplicate webhook and test-account cleanup. Renewal verification still awaits a real customer’s renewal.

Response complete
