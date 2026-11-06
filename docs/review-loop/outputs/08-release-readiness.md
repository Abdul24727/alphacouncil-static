# Output 08: review 07's step, the release-readiness report

Commit `63e5622`. The report is `docs/release-readiness-2026-11-06.md`.

- **Candidate:** `509d7bf`, against the deployed `5c18a3ae46`.
  - `git diff --stat 509d7bf..HEAD -- web/src api deploy web/messages web/public` is empty, so commits
    after it (records) change no app code.
  - `origin/rebuild` is at `ccfe063`.
- **Every changed file** is accounted for from `git diff --name-status 5c18a3ae46..509d7bf`, grouped:
  - **app** (5, all `web/src`): `data-labels.json`, `data-labels-core.ts` (new), `data-labels.ts`,
    `statement-period.ts`, `research-panels.tsx`;
  - **tests** (3);
  - **check scripts** (4);
  - **pipeline tooling and patches**, applied separately on the owner's go-ahead;
  - **the review loop**;
  - **records and evidence**.
  - No change to `api/`, `deploy/`, `web/messages/` or `web/public/` (verified: 0 files).
- **Visitor-facing changes** (a table in the report): Gulf English labels; newest-first columns; bank income
  sub-lines; the real-estate label. Each has its record.
- **Re-run together on the candidate**, so no later step breaks an earlier one:
  - `npm test` 64/64, `tsc` 0, lint 0, `npm run build` 93/93, and the Python unit tests OK.
  - Five render checks, local web against beta's API, all PASS: the 11-04 label set; the Gulf English pages;
    newest-first; bank sub-lines (values equal to the API); the real-estate label (values equal to the API).
  - `check-arabic.mjs` with `WIDTHS=1440,390`: 48 Arabic views, 0 stray English.
  - Evidence: `docs/screenshots/release-candidate-509d7bf/`, 130 screenshots and 6 logs.
- **The only Arabic left on English pages** is the cash-flow lines in AMLAK's and AMCREIT's balance sheets.
  Every one was checked to be a cash-flow line. That is F-16, removed by the 05:00 UTC publish.
- **Still pending, named in the report:**
  - F-16's four after-publish checks: no cash flow in the nine balance sheets; eight Cash Flow Statements; no
    UNKNOWN STATEMENT HEADING line; the label sweep passing 714/714.
  - The production check method, which is served code because Financials is Pro-only signed out.
  - The release order and rollback.
- **Nothing is released or pushed.**

**The question for the review:** is this sound, and what is the single next step?
