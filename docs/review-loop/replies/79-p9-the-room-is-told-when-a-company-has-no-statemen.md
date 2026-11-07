# Review 79: P9: the room is told when a company has no statements

2026-11-07 10:49 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `73-p9-no-statements.md`.

VERDICT: FIX

ISSUES:

api/app/evidence.py:1516–1522, 1528–1535 — Quarterly-only financial data produces a false absence statement.

I reproduced this against the attached evidence.py using dataset_of() with Items([], [Cell(...)]), containing a reported quarterly income-statement figure of 77.0.

The resulting P9 contains a populated quarters object with that figure, but its limitation says that statements and quarters are empty and that no quarterly result exists.

This contradicts the actual dataset. The new guard checks annual statement sections but ignores available quarterly data.

Required fix: Distinguish no financial data from quarterly-only financial data. Never describe a reported quarterly figure as unavailable.

api/app/evidence.py:1533–1555 and api/app/debate/pack.py:92–103 — Statement sections without numeric values can bypass the warning.

I reproduced this with an income-statement row whose value is None.

The resulting P9 contains a statement section but no usable financial figure. Nevertheless:

limitations_of() says an income-statement window is available.

It says dividend coverage can be tested against earnings.

no_statements_note() does not produce the room-level warning because statements is nonempty.

The code therefore treats the presence of a section as proof that financial evidence exists.

Required fix: Determine usable statement availability from actual reported numeric values, not merely section names or row counts. Add a regression test for all-null statements.

api/app/debate/checks.py:110–117, 120–153 — The fix is advisory, not a deterministic fail-closed guarantee.

The existing checker flags a figure only when it appears nowhere in the combined data pack. A fabricated statement figure that coincidentally matches a number in another dataset can escape that check, even when attributed to [P9].

Also, Checked.text() retains unverified figures and records flags; it does not suppress them.

The new prompt warning is a valuable correction, but it cannot independently guarantee that unsupported statement figures will never reach the reader.

Required clarification: Describe this as missing-data instruction and existing unverified-figure detection, not guaranteed suppression. Do not claim the hallucination problem is solved without an actual model evaluation. Keep any additional enforcement narrowly scoped to existing room behavior.

p9-sweep-summary.txt, p9-after.txt, and tests.txt — Evidence supports the principal reproduction, with verification limits.

The supplied evidence establishes that the recorded sweep covered 714 tickers, reporting 50 with no statement rows, one balance-sheet-only company, and zero valued calculations among the 50. The attached 4330 and 232 records confirm the misleading previous limitations.

The new warning also works correctly for the reproduced 4330 case, missing-P9 packs, and P9 errors. The recorded test results are 134 targeted passes and 601 passes with 10 skips overall. The production Arabic check records 48 views, zero English strings outside the allow-list, and exit code 0.

However, the raw 714-ticker sweep results, four of the five frozen comparison packs, and complete test files are not attached. Their aggregate claims are supported by recorded outputs rather than independently reproduced here.

This limitation does not invalidate the demonstrated fix, but the two reproducible edge cases prevent acceptance as fail-closed.

DRIFT: The work stayed within the master plan: today's six-advisor room remains, the rejected option-2 prototype is not adopted, and no paid calls, push, or release occurred. The remaining problems concern correctness of the existing P9 protection, not new product scope.

NEXT STEP: Complete the P9 missing-data correction on rebuild, without releasing it. Update api/app/evidence.py and api/app/debate/pack.py so the warnings accurately distinguish missing statements, quarterly-only evidence, statement sections with no numeric values, and genuinely available reported figures. Add focused regression tests to the existing suites. Preserve ordinary packs, advisor briefs, rounds, Chair, presentation, and room architecture.

This is more valuable than creating a release branch now because the present patch can still communicate false financial-data availability. No paid model calls are necessary for this deterministic correction.

DONE WHEN: Claude provides the revised diff and demonstrates:

Empty P9: explicit no-financial-statements warning, with no fabricated figures.

Quarterly-only P9: actual quarters remain available and are not described as missing.

All-null statement rows: no assertion of available earnings or usable dividend coverage.

Balance-sheet-only P9: explicit missing-income-statement warning.

Normal income-statement-plus-balance-sheet P9: existing limitations unchanged.

Missing-P9 and error packs: room-level warning appears before the datasets.

All existing API tests pass with no new failures.

Run:

Bash
cd api
.venv/Scripts/python.exe -m pytest -q tests/test_evidence.py tests/test_debate.py tests/test_copilot.py
.venv/Scripts/python.exe -m pytest -q

Include the focused test results, a deterministic output demonstrating the corrected cases, and the exact diff. No deployment, push, or paid session.

OWNER ITEMS:

Step 7 — Lawyer: Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for review of the published site. This remains the most important owner-controlled launch dependency.

P9 release authorization: Once the corrected fix is accepted and isolated into a production-based release candidate, the owner must separately approve beta deployment and then production deployment.

Optional paid verification: A real council session on 4330 or another company without statements would test whether model behavior improves. This requires the owner's separate approval and is not authorized by this review.

Step 18, item 4: Real customer renewal remains pending and cannot be substituted with a simulated renewal.

Response complete
