# Review 80: P9: review 79's fixes

2026-11-07 11:04 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `74-p9-review-79-fixes.md`.

VERDICT: FIX

ISSUES:

1. Quarterly-only P9 still contains contradictory financial-data instructions.

api/app/evidence.py, lines 1527–1535: QUARTERS_ONLY says the source holds no reported income-statement figure, although its quarters can contain reported income-statement figures.

api/app/debate/pack.py, lines 113–119: the pack repeats that no income-statement figure exists while explicitly recognizing reported quarterly results.

api/app/evidence.py, lines 1487–1491: bounded_quarters always says the annual figures above were reconstructed from four quarters—even when no annual figures exist.

Independently reproduced: Items([], [Cell(label="Net Income", section="Income Statement", fiscal_year=2026, value=77.0, period_end="2026-06")]) produces statements=[], a reported quarterly net income of 77, and a quarters.note asserting annual figures exist above it.

Required fix: distinguish missing annual/TTM statement figures from available quarterly figures consistently in P9's limitations, quarterly note, and pack instruction. Preserve the reported quarter and its period. Add a regression test checking the entire P9 text, not just its limitations.

2. A balance sheet combined with quarterly income data is incorrectly described as having no income figures.

api/app/evidence.py, lines 1550–1567: limitations_of checks annual statement sections but disregards available quarters when constructing the missing-income warning.

Independently reproduced: one balance-sheet row (Total Assets=900) plus one quarterly income row (Net Income=77) produces:

quarters.rows = [["Net Income", 77.0]]

NO INCOME STATEMENT: ... Its revenue, earnings, margins and earnings per share are not in this dataset; do not state, estimate or recall them.

This is false for the reported quarterly net-income figure.

The attached p9-sweep.json, line 519, shows ticker 232 has a balance-sheet section and five quarterly rows. The sweep does not establish whether those rows contain non-null values, so the actual quarterly figures for 232 remain unverified.

Required fix: make missing-income wording distinguish unavailable annual figures from any reported quarterly values. Add a balance-sheet-plus-valued-quarters regression case. Keep the existing balance-sheet-only behavior unchanged.

3. The written sweep findings misstate the quarterly-data coverage.

docs/p9-no-statements-2026-11-07.md, lines 22–25, says all 50 companies with no statement rows have quarters=null.

p9-sweep.json contradicts this:

Line 377: ALFIRDOU, zero statement rows, five quarterly rows.

Line 426: TAALEEM, zero statement rows, five quarterly rows.

The independently rerun summarizer reproduces 50 companies with zero statement rows, but it does not distinguish those with quarterly rows.

A quarterly-row count alone does not establish how many reported numeric values exist.

Required fix: correct the record and summarize the three conditions separately: no annual statement rows and no reported quarterly figures; no annual statement rows but reported quarters; and partial annual statements with quarters. Determine numeric availability from the underlying values, not row counts.

4. Part of the reported evidence cannot be independently verified from the attachments.

p9-after.py, line 51, reads beta-4330-evidence-before.json, which is not attached. Its complete execution and the actual beta 4330 comparison therefore cannot be independently reproduced here.

docs/eval/presenter-comparison/audit.md and api/app/debate/checks.py are also absent. The original 22-of-23 invention count and the check's full implementation cannot be independently verified.

The reported 604 passed / 10 skipped suite result is present in tests.txt, but the full repository and dependencies are unavailable for an independent suite rerun.

Confirmed: both supplied patches reverse-apply cleanly against the four attached current source/test files. Reversing and reapplying the full patch reproduced those files byte-for-byte. All five frozen comparison packs contain P1–P8 and no P9. Independent execution of the attached P9 implementation confirmed the main empty-data behavior and revealed Issues 1–2. These are correctness defects, not patch-integrity defects.

DRIFT: The output stayed within the master plan: today's six-advisor room remains unchanged, the rejected presenter prototype remains excluded from release, and no new features, paid calls, pushes, or deployments were introduced. The fix is not yet ready for a release candidate because its missing-data language still contradicts valid quarterly evidence in supported cases.

NEXT STEP: On rebuild, complete the existing P9 correctness fix in api/app/evidence.py and api/app/debate/pack.py: resolve Issues 1–2, add the corresponding regression tests, and correct the sweep record in docs/p9-no-statements-2026-11-07.md. This is the highest-value pre-approved step because the room must not misrepresent available financial figures before a fix-only release candidate is prepared. Do not change the room's architecture, prompts per seat, presentation, or pipeline. No paid model run, push, or deployment.

DONE WHEN: Claude supplies:

Passing regression tests for empty P9, quarterly-only P9, all-null statements, balance-sheet-only P9, balance-sheet-plus-quarterly P9, and the normal two-year case. Every case must verify both the figures retained and the complete limitations/pack wording.

A refreshed deterministic P9 output showing no fictional annual figures, no false claim that reported quarterly values are absent, and no misleading reference to annual figures above an empty statement section.

A corrected sweep summary, explicitly distinguishing quarterly rows from non-null reported figures, with the underlying evidence needed to verify those classifications.

Successful python -m pytest -q for the entire API suite, git diff --check, and confirmation that the changes are limited to this P9 correction and its tests/evidence.

Once those checks pass, return the corrected P9 fix for review before constructing the release candidate.

OWNER ITEMS:

Highest priority — Step 7, legal review: Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the published site. This remains the largest owner-controlled launch dependency and does not need to wait for P9.

Later — P9 release authorization: After the corrected fix and its isolated release candidate are independently accepted, explicitly approve or reject deployment to beta, then production. No authorization is implied by this review.

No additional paid model evaluation is required for the deterministic corrections above.

Response complete
