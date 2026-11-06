# Review 07: Dollar unit in pair_from_gulf (review 06 step)

2026-11-05 23:58 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `07-dollar-unit.md`.

VERDICT: ACCEPT

ISSUES: none. Independently reproduced the old bug, verified the corrected dollar variants, and passed all four tests. The dictionary contains no dollar labels. The server-wide comparison is documented evidence; I did not rerun it.

DRIFT: The output follows review 06 and stays within existing bilingual polish. The destination remains the finished, published and polished site under the master plan’s existing approval gates.

NEXT STEP: On `rebuild`, prepare `docs/release-readiness-2026-11-06.md` covering the accumulated changes since deployed commit `5c18a3ae46`. Consolidate the existing check results and screenshots, identify the candidate commit, and explicitly retain F-16’s post-publish verification as pending. This makes the completed polish reviewable for release while the 05:00 UTC publish is still ahead.

DONE WHEN: The report accounts for `git diff --name-status 5c18a3ae46..509d7bf`, links the relevant passing checks and English/Arabic screenshots at 1440/390 px, and names the outstanding F-16 checks: corrected balance sheets, eight cash-flow statements, no unknown-heading warnings, and the label sweep rerun. Preparing this report requires no release or push.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`; billing is already open under the recorded waiver.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Approve each release and public-repository push separately when the candidate is verified.
4. Resolve D1/D3/D6 and authorize the $66 pilot; decide on the $393 run after its results.

Response complete
