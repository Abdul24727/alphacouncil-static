# Review 83: P9: review 82's fixes

2026-11-07 13:16 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `77-p9-review-82-fixes.md`.

VERDICT: FIX

ISSUES:

1. The 30-row cap can still hide an entire reporting year and produce a false limitation. In api/app/evidence.py:1427–1453, numbered protected rows take priority over unprotected rows regardless of fiscal year. I reproduced this using 30 numbered protected income-statement rows from 2024 and one unprotected Zakat & Tax figure of 555.0 from 2025. dataset_of() omitted the 2025 figure (rows_omitted=1), retained all 30 figures from 2024, and returned columns=["label", "2025", "2024"] with no visible 2025 number. Nevertheless, limitations_of() (1642–1657) stated “the prior year's income statement is not”, although 2024 is precisely the year shown. The statement also retained period_end="2025-12" despite displaying only 2024 figures. The new capped tests in api/tests/test_evidence.py:449–523 use single-year examples and do not catch this. Review 82's change protects statement-section presence, but not reporting-year coverage or the accuracy of the associated period metadata. Fix before release: preserve reporting-year coverage where feasible, including during fit(), and make limitations and period descriptions accurately distinguish source availability from rows omitted by bounding.

2. A reported quarterly figure can still cause P9 to falsely claim that the source has no quarterly result. In api/app/evidence.py:1473–1494, bounded_quarters() selects only labels in QUARTERLY_INTEREST. I independently reproduced the failure with Items([], [Cell(label="Other operating gain", section="Income Statement", fiscal_year=2026, value=12.0, period="Q", period_end="2026-06")]). Although the source contains a reported quarterly figure, bounded_quarters() returns None. Consequently, dataset_of() emits NO FINANCIAL STATEMENTS (1537–1543), stating “the source holds no ... quarterly result”. That source-absence claim is false. The tests exercise quarterly Net Income, which is on the selected-label list, but not an otherwise valid quarterly figure excluded by the selection rule. Fix before release: distinguish quarters not supplied in P9 from quarters genuinely absent at the source. Do not expand the displayed quarter series merely to solve the wording.

3. Verification boundary, not an additional implementation defect. I independently recomputed the Git blob hashes for all eight baseline files: each of the four files has identical hashes at 73d7140 and 026699b906, matching tests.txt. Applying p9-fix.patch to the supplied production baseline reproduces all four changed files byte-for-byte. Both patches reverse-apply successfully. Both sweep summaries reproduce from their respective JSON files after normalizing line endings. The attached tests.txt reports 22 P9 tests passing, 150 related tests passing, and 617 passing with 10 skipped across the API suite. Those full-suite results, commit 0033105, and the actual branch state cannot be independently reproduced or verified without the rest of the repository and its Git metadata.

DRIFT: The work stays within the owner's chosen direction: retain today's advisors' room and correct P9's missing-data guidance, without new features, changes to the room's architecture, paid calls or deployment. The two remaining defects are correctness gaps inside that approved fix, not reasons to reopen the rejected presenter prototype.

NEXT STEP: On rebuild, correct the reporting-year and quarterly-source availability logic in api/app/evidence.py, and add narrowly targeted regressions in api/tests/test_evidence.py. This is the highest-value pre-approved step because inaccurate financial-data limitations must be eliminated before assembling the P9 fix-only release candidate from production 026699b906. Preserve existing behavior for the established cases and do not release anything.

DONE WHEN: Claude provides evidence that:

The two reproductions above fail against the current implementation and pass after the correction.

A section containing reported figures from two source years either preserves both years in P9 or explicitly and accurately identifies which year was omitted; no limitation falsely describes the missing year, and period metadata agrees with displayed figures.

A reported quarter excluded from P9's selected series never causes a claim that the source itself has no quarterly result.

The existing twelve-case P9 table still passes word for word wherever its expected behavior is unchanged. The direct limitations_of() guard and all other P9 tests pass.

The related suite and whole API suite pass, with their actual results recorded using python -m pytest -q tests/test_evidence.py tests/test_debate.py tests/test_copilot.py and python -m pytest -q from api/.

git diff --check 73d7140 HEAD passes, the complete P9 patch applies cleanly to a fresh copy of production's four baseline files, and the resulting P9 files match the reviewed implementation. No unrelated files change.

OWNER ITEMS:

Step 7 — lawyer review, highest priority. Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the already published site. This is the principal remaining owner-controlled dependency for the launch goal.

P9 release approvals — later, separately. Once the corrected fix-only candidate passes review, the owner must authorize beta deployment and subsequently production deployment. Neither is authorized by this review.

Step 18, item 4 — real renewal. Verification remains dependent on an actual customer's renewal. Do not substitute a simulated renewal or claim this requirement complete.

Response complete
