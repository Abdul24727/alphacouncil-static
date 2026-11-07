# Review 82: P9: review 81's fixes

2026-11-07 12:56 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `76-p9-review-81-fixes.md`.

VERDICT: FIX

ISSUES:

api/app/evidence.py, lines 1599–1605 and 1529–1559 — the new visibility-based logic can make a false claim about the underlying source.

Independently reproduced using the attached code and the capped fixture in api/tests/test_evidence.py, lines 449–451 and 484–488.

The fixture has 30 protected rows containing null values, followed by an actual reported income-statement figure: Zakat & Tax = 5.0. The 30-row cap excludes that figure. P9 therefore contains no annual income-statement number, although the source does.

The resulting limitation says:

NO ANNUAL STATEMENTS: the source holds no full-year or trailing-window figure from an income statement...

That is factually incorrect. The source has a figure; the bounded P9 dataset does not show it.

The review 81 correction rightly determines availability from what P9 displays. Its missing-data language must distinguish not available in the supplied P9 dataset from not present at the underlying source.

This affects the NO_STATEMENTS, QUARTERS_ONLY, NO_INCOME_STATEMENT and NO_ANNUAL_INCOME_STATEMENT wording where a source figure can be omitted by the cap or budget. Preserve the established wording for cases where source absence is actually known, and make the capped cases accurate.

api/app/evidence.py, lines 1636–1640 — the date-mismatch limitation still uses raw statements and can contradict the corrected missing-data limitation.

Independently reproduced by extending the attached capped fixture with:

The omitted income-statement figure ending 2025-12.

A visible balance-sheet figure of 900.0 ending 2025-09.

A reported quarterly income figure of 77.0.

P9 correctly identifies the balance sheet as its only visible annual statement and produces NO ANNUAL INCOME STATEMENT.

However, it simultaneously says:

The income statement covers a window ending 2025-12 while the balance sheet is struck at 2025-09...

The annual income-statement figure is not available to the room. This contradicts the intended rule that the limitations describe what P9 actually supplies.

Gate the flow-versus-position date warning on both relevant statements containing reported numbers in the final bounded dataset. Add a regression that checks the entire limitations list, not just the presence of NO ANNUAL INCOME STATEMENT.

Production baseline verification — tests.txt.

The attached evidence reports identical Git blob IDs for all four changed files at 73d7140 and production 026699b906. However, the ZIP contains neither Git object database nor production commit tree, so I cannot independently establish that equality from the attachments.

The attached source and both patches are internally consistent. I independently confirmed that both p9-fix.patch and p9-fix-review-81.patch reverse-apply cleanly to the supplied files.

I also independently reran the summarizer against both JSON files. Their classifications agree exactly: 48 / 2 / 1 / 663, with zero all-null rows among 30,761 statement rows and 1,726 quarterly rows.

The recorded 614 passed, 10 skipped is consistent with tests.txt, but the full test suite could not be independently rerun because the complete repository and test environment were not attached. Verify the baseline against actual Git objects when building the release candidate.

DRIFT:

No scope drift. Output 76 remains within the owner's authorized P9 correction: today's room, presentation, architecture, and decisions are preserved. The two remaining defects are correctness issues within that same fix, not grounds for additional features, paid comparisons, or reopening the rejected presenter option.

NEXT STEP:

On rebuild, correct the two remaining P9 limitation contradictions in api/app/evidence.py and extend the existing regression table in api/tests/test_evidence.py.

Specifically, make source-absence wording accurate when an annual figure exists in raw data but is omitted from P9, and prevent the flow-versus-position date warning from asserting an annual statement that the bounded dataset does not contain.

Keep the existing normal-case wording and all already-correct quarterly behavior unchanged. Do not modify the room, advisors' prompts, presentation, or pipeline.

This is the most valuable immediate step because the release candidate must not introduce misleading financial-data availability claims while attempting to prevent invented financial figures.

DONE WHEN:

Claude supplies evidence that:

The existing ten P9 table cases still pass word for word where their claims remain valid.

The capped case explicitly verifies that a raw source figure exists but is omitted from P9, and the resulting limitation does not falsely claim source absence.

A new capped case with a visible balance sheet, reported quarters, and mismatched raw statement dates produces no contradictory annual-income-statement availability or date warning.

The normal two-year case, one-window cases with and without quarters, and quarters-only cases retain their established behavior.

The following commands pass:

Bash
.venv/Scripts/python.exe -m pytest -q tests/test_evidence.py tests/test_debate.py tests/test_copilot.py
.venv/Scripts/python.exe -m pytest -q
git diff --check 73d7140 HEAD

The revised record and patch demonstrate that only the four authorized P9 files changed outside documentation, and that the new patch reverse-applies cleanly.

Return the exact test output, revised patch, and corrected P9 record for independent review. Do not build the fix-only release candidate until this correction is accepted.

OWNER ITEMS:

Highest priority — Step 7, legal review. Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the already-published site. This remains the major outstanding owner-dependent launch requirement and does not need to await the P9 correction.

P9 release authorization — later. Once the corrected fix-only candidate has independently passed review, the owner must separately authorize beta deployment and production deployment under the existing rules. No authorization is implied by this review.

Step 18, item 4 — real renewal. Completion still depends on an actual customer renewal. Do not manufacture a transaction or treat the existing payment test as proof of renewal.

No paid model calls, repository push, or release is authorized by this verdict.

Response complete
