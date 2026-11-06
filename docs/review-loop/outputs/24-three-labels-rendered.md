# Output 24: review 23's two issues, fixed

Commit `18c942b`. No app code changed (`git diff --stat 2f50598..HEAD -- web/src …` is empty).

**1. Page evidence for the three new labels.** Check 13: `13-three-labels.txt`, `three-labels/` and
`contact-sheet-three-labels.png`, under `docs/screenshots/release-candidate-2f50598/`.
- **Pages:** DIC's income statement and KFH's balance sheet, English and Arabic, 1440 and 390. Local web against
  beta's API, which serves the 2026-11-06 publish.
- **Per panel:**
  - the label is shown, as the new English on English pages and the stored Arabic on Arabic pages;
  - the label is not clipped: its text sits inside its cell, the cell inside the scroll box, and
    `scrollWidth ≤ clientWidth`;
  - **every cell in every column equals the API** (DIC 26 rows × 5 years, KFH 29 × 5).
- **Result: 8/8 PASS.**
- **Inspected by eye on the contact sheet:**
  - DIC FY2025: "EPS before exceptional items" 0.16 and "EPS" 0.36, with the API giving 0.16 and 0.36, and the
    Arabic rows unchanged.
  - KFH: "Book value (BHD)" 0.36 in FY2025 (API 0.358) and 0.12 in FY2021 on the scrolled phone view (API
    0.121), with the Arabic "القيمة الدفترية دينار بحريني" unchanged.
- `npm run build` re-run on the candidate's code: 93/93. The report had claimed this from the previous candidate.

**2. Records reconciled:**
- `PROJECT.md:274`: F-16 "applied, and **verified live after the 2026-11-06 05:01 UTC publish** (13/13, sweep
  714/714)".
- `PROJECT.md:1276`: "Applied 2026-11-05 22:44 UTC, verified live 2026-11-06".
- `docs/release-readiness-2026-11-06.md`: "Rendered: local web against beta's API, which since 05:01 UTC serves
  the 2026-11-06 publish". The old line said the data predated the publish.

In both records, F-16 (live data, fixed by a server pipeline change) stays separate from the app candidate,
which is unreleased.

**Observation, recorded and not changed:**
- KFH's statement unit line reads "Millions of" with no currency (Arabic "بملايين").
- KFH's `currency` and `report_currency` are null; it is one of the sweep's 7 `no_currency` listings.
- The header already says "Currency not confirmed" for these, but `statements.unit` ("Millions of {currency}")
  renders an empty `currencyLabel()`.

**The question for the review:** is this sound, and what is the single next pre-approved step?
