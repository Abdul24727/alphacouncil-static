# Review 05: Bank income sub-lines read within their statement (review 04 step)

2026-11-05 23:38 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `05-bank-sublines-in-statement.md`.

VERDICT: ACCEPT

ISSUES: none. Independently verified 63/63 tests, lint and typecheck; `pairs`/`aliases` are byte-unchanged, and lookup comparisons preserve prior behavior outside income statements. Saved screenshots support the rendering claims. Build and source harvest were not rerun.

DRIFT: This stays within existing bilingual statement polish. The destination remains the master plan’s finished, published and polished site, with scope, owner decisions and approval gates unchanged.

NEXT STEP: On `rebuild`, correct the documented “property Real estate Investment” wording in [data-labels.json:42](C:/projects/alphacouncil-platform/web/src/content/data-labels.json:42), preserving lookup compatibility with stored labels. Ticker 108’s saved balance-sheet screenshot confirms this remaining visible defect; it is actionable polish while F-16’s 2026-11-06 05:00 UTC publish remains ahead.

DONE WHEN: Ticker 108’s balance sheet uses clear, source-supported English, preserves Arabic and database values, and renders correctly at 1440 and 390 px. Record screenshots under `docs/`; tests, lint, typecheck and build pass.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Authorize each pending release and public-repository push separately after verification.
4. Fund and authorize the $66 pilot, settling D1/D3/D6 first; decide on the $393 run after its results.

Response complete
