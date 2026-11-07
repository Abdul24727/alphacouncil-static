# Review 84: P9: review 83's fixes

2026-11-07 13:33 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `78-p9-review-83-fixes.md`.

VERDICT: ACCEPT

ISSUES: none.

The P9 fix is sufficiently verified to proceed to a fix-only release candidate.

Independent checks against the attachments confirm:

1. Year hidden by the cap — fixed. api/app/evidence.py:1454–1463 retains a reported figure for every source year represented in the loaded columns. The reproduction now shows 2025 and 2024, retains the 2025 figure of 555, and removes the incorrect one-window limitation.

2. Quarter outside the carried series — fixed. api/app/evidence.py:1627–1656 distinguishes quarterly figures reported at the source from those included in P9. The limitation no longer falsely says the source has no quarterly result.

3. Pack wording — fixed. api/app/debate/pack.py:124–130 explicitly describes what this pack contains rather than making an unsupported claim about all company reporting.

4. Budget trimming — verified. api/app/evidence.py:1700–1710 protects the last reported figure in each displayed year. The supplied tight-budget scenario independently trims 23 of 24 rows while preserving both years. An additional 150 generated cases passed the year-preservation checks.

5. Reproductions — verified. Both review-83 before/after outputs were reproduced exactly, including the five frozen comparison-pack scenarios in p9-after.py.

6. Production patch — verified. All four files at 73d7140 and 026699b906 have identical baseline Git blob hashes. Applying p9-fix.patch to the supplied production files reproduces all four candidate files byte-for-byte. Reverse application restores the production baseline exactly.

7. Tests — evidence consistent. tests.txt records 25 passing P9 tests, 153 passing targeted tests, and 620 passed with 10 skipped in the complete API suite. The full suite cannot be independently rerun from this partial repository archive; the recorded results are not presented as an independently reproduced full-suite run.

The fix does not establish that a language model will never invent a statement figure. It corrects the supplied evidence and instructions; the existing unverified-figure detection remains unchanged.

DRIFT: None. The work stays within the owner's approved P9 correction, preserves today's six-advisor room and its presentation, and introduces no new features, paid evaluation, pipeline changes or release. The rejected prototype remains excluded from the proposed production fix.

NEXT STEP: Build a local, fix-only P9 release candidate from the exact production commit 026699b906ea3a513b4f2dbfc37672fa68ee9d42.

In an isolated worktree, apply docs/screenshots/p9-no-statements-2026-11-07/p9-fix.patch, containing only:

api/app/evidence.py

api/app/debate/pack.py

api/tests/test_evidence.py

api/tests/test_debate.py

Run the complete checks against that candidate, record its exact commit and file hashes, and prepare a release-readiness report under docs/. Do not include the option-2 prototype, push, deploy, or make paid model calls.

This is the most valuable pre-approved step because it converts the accepted P9 correction into an independently testable release artifact based on the actual live production version.

DONE WHEN:

The release candidate is based directly on 026699b906, and git diff --name-only 026699b906 lists exactly the four files above.

git diff --check 026699b906 passes.

The candidate reproduces the expected Git blob hashes for all four patched files.

The review-83 reproduction and the P9 tests pass on the isolated candidate.

The complete API test suite and applicable build/check commands pass, with results recorded in the release-readiness report.

The report proves that the rejected presenter prototype is absent and states that nothing was pushed or deployed.

OWNER ITEMS:

Highest priority — Step 7, legal review. Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the published site. This remains the largest outstanding owner-dependent launch requirement.

P9 deployment approval. Once the isolated candidate is reviewed and accepted, the owner must separately authorize its beta release and, after beta verification, its production release. Acceptance of this code review is not deployment permission.

Step 18, item 4. Verification of a real customer's renewal remains pending until an actual renewal occurs. No substitute test payment is authorized.

Response complete
