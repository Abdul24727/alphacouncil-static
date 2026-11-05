# Review 04: Statement tables newest first (review 03 step)

2026-11-05 23:30 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `04-statements-newest-first.md`.

VERDICT: ACCEPT

ISSUES: none. The diff preserves year-keyed headings and values, sorts without mutating the input, and carries the order into TSV and Copilot data. Independently verified 59/59 tests, lint and typecheck; inspected saved screenshots confirming initial visibility and historical scrolling. Build was not rerun in this read-only review.

DRIFT: The output stays within existing bilingual and mobile polish. The destination remains the master plan’s finished, published and polished site, with scope and recorded owner decisions unchanged.

NEXT STEP: On `rebuild`, fix the documented bank income-label ambiguity in `web/src/lib/data-labels.ts` and `web/src/components/stock/research-panels.tsx`. Use statement context so “Investments” and “Loans and advances” identify commission income, and “Customer Deposits” identifies commission expense, where the source establishes those meanings. The saved ADCB screenshots and `docs/arabic-statement-labels-2026-11-03.md:353` confirm this existing defect. Correcting misleading financial labels is the most valuable available polish work now; F-16’s 2026-11-06 05:00 UTC publish is still ahead.

DONE WHEN: ADCB income and balance screenshots in both languages at 1440 and 390 show accurate contextual labels, with balance-sheet meanings and database values preserved. Regression checks distinguish identical labels across statements; `npm.cmd test`, lint, typecheck and build pass. Record evidence under `docs/`.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Authorize each pending release and the public-repository push separately after verification.
4. Fund and authorize the $66 pilot, settling D1/D3/D6 first; decide on the $393 run after its results.

Response complete
