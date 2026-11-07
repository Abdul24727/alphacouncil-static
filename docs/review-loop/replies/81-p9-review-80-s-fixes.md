# Review 81: P9: review 80's fixes

2026-11-07 12:29 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High (chatgpt.com), with the attached files.
Output reviewed: `75-p9-review-80-fixes.md`.

VERDICT: FIX

ISSUES:

api/app/evidence.py:1592–1599 — A false quarterly-history statement remains for 25 companies in the attached beta sweep.

limitations_of() produces ONE INCOME-STATEMENT WINDOW whenever an income statement has fewer than two reported years. Its wording always ends:

the single quarters are the history there is.

But the attached p9-sweep-values.json identifies 25 companies with reported income statements and balance sheets, one income-statement window, and zero quarterly rows, including 8010, 8012 and 8020.

I independently reproduced the problem with a one-year income statement and balance sheet, without quarters. The resulting P9 correctly contained quarters: None but still claimed quarterly history existed.

The seven-case table in api/tests/test_evidence.py:465–481 does not cover this combination. Add an exact-text case for one income-statement year, a balance sheet, and no quarters, and make the limitation distinguish it from a company that actually holds quarters. Preserve the existing wording where it is factually correct.

api/app/evidence.py:1487–1496 — The revised quarterly note checks raw income figures rather than the figures actually displayed.

bounded_quarters() determines whether annual figures exist using items.rows. But bounded_statements() limits statement rows, and fit() can trim them further.

I reproduced a contradictory output using 30 protected, null-valued income rows, one additional reported income figure excluded by the 30-row limit, and one reported quarterly figure:

Visible annual income figures: 0

Quarterly note: “the annual figures above are the sum …”

Pack note: “NO ANNUAL FINANCIAL STATEMENTS IN THIS PACK”

This is a synthetic boundary case, not an established occurrence in the 714-ticker sweep. Nevertheless, it violates review 80's explicit rule that the note must describe figures actually present in statements.

Determine annual-figure presence from the final bounded P9 statement content, including any budget trimming. Add a regression test proving that the quarterly note and the pack note cannot contradict each other.

p9-sweep-values-summarize.py:32–35 and docs/p9-no-statements-2026-11-07.md:28 — The all-null-row claim exceeds what the evidence measures.

The record states that no individual statement or quarterly row anywhere was all null.

However, p9-sweep-values.py:33–36 records aggregate row counts and numeric-value counts, not the number of individually all-null rows. The summarizer checks whether an entire company's statement section or quarterly series contains zero numbers.

A section can contain a completely null row and still have a positive aggregate numeric count.

The independently reproduced classification is correct: 48 + 2 + 1 + 663 = 714, with zero non-200 responses. But this does not establish the stronger per-row assertion.

Correct the report to state precisely what was measured, or calculate the per-row statistic from the original response data. Do not treat the existing aggregate as proof.

Output 75, final paragraph and test claims — Two verification limits remain.

Both p9-fix.patch and p9-fix-review-80.patch reverse-apply cleanly against the attached source. I also independently executed p9-after.py against the supplied source and frozen packs using local stubs for unavailable imports. Its 52 output lines matched p9-after.txt after normalizing line endings.

The reported 16 P9 tests, 144 targeted tests, and 611 passed/10 skipped are supported by tests.txt, but the full suite cannot be independently rerun from this partial repository: application modules, fixtures and other dependencies are missing.

Likewise, the claim that production commit 026699b906 contains exactly the same four original files as 73d7140 cannot be established without those Git objects or equivalent snapshots. Claude must verify that equivalence in the repository before preparing the release candidate.

DRIFT: The output stayed within the owner's master plan: retain today's six-advisor room, correct P9's missing-data instructions, preserve the presentation and architecture, and make no unauthorized paid calls, pushes or releases. The remaining defects concern factual accuracy and proof of this same fix, not additional scope.

NEXT STEP: On branch rebuild, complete one final P9 correctness revision. In api/app/evidence.py, correct the one-window limitation when quarters are absent and make the quarterly annual-figure note depend on numeric figures retained in the final displayed statements. Extend api/tests/test_evidence.py with exact-output regression cases for both defects, and correct the unsupported sweep wording in docs/p9-no-statements-2026-11-07.md and its summary. This is the most valuable pre-approved action because it eliminates a demonstrated false instruction affecting 25 existing companies and closes the remaining consistency gap before building a fix-only release candidate. Do not alter the room architecture, pipeline, prototype, or deployment state.

DONE WHEN:

Regression tests prove that a one-year income statement without quarterly rows never claims quarterly history exists, while cases with actual quarterly figures preserve the correct wording.

A bounded or trimmed income statement with zero visible numerical figures cannot cause bounded_quarters() to claim annual figures are displayed. The pack note and quarterly note agree.

The original seven-case exact-text table remains passing, and the two new cases are included. Re-run p9-after.py and retain its output.

From api/, run:

Bash
python -m pytest -q tests/test_evidence.py tests/test_debate.py tests/test_copilot.py
python -m pytest -q

All previously passing tests remain passing, with no new failures.

Re-run p9-sweep-values-summarize.py on the frozen JSON. Confirm the unchanged classification of 48/2/1/663 and that the corrected report makes no unsupported per-row claim.

Run git diff --check 73d7140 HEAD; confirm that only the intended P9 source, tests and documentation changed. Verify the four relevant baseline file blob hashes match between 73d7140 and 026699b906. Provide the final diff for review. No push, deployment or paid session.

OWNER ITEMS:

Highest priority — Step 7, legal review: Send docs/lawyer-review-pack-2026-11-06.md to the lawyer for evaluation of the already-published site. This remains the most important owner-controlled blocker to completing the launch plan and does not depend on the P9 fix.

P9 release authorization: After the corrected fix-only candidate has passed review, beta and production deployments each require the owner's separate explicit approval. No approval is implied by this review.

Step 18, item 4: Real customer renewal verification remains outstanding. It must be established through an actual renewal, not a simulated transaction.

Response complete
