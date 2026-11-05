# Output 04: review 03's step, statement tables newest first

Commit `f19f7ae`.

**The defect:** `statementColumns()` returned the years oldest first, and the table scrolls sideways from
the line labels (`min-width` up to 560 px). So on a 390 px phone, in both languages, the labels sat beside
FY2021–22. The 2026-11-06 render saw it on 108.

**The change** is in `web/src/lib/statement-period.ts` only; `research-panels.tsx` is its one caller and
needed no change.
- `statementColumns()` sorts a copy of the years newest first. The caller's array is not reordered.
- The doc comment says why: newest first, as in Argaam's own grid, so the newest period sits beside the
  labels.
- Headings, period notes and values are unchanged, and each cell is still keyed by its year. The copy
  (TSV) and the Copilot payload follow the same order; the Copilot also gets its year → heading map.

**Tests:** `web/src/lib/statement-period.test.ts`. Five expectations were updated to the new order. One new
test: newest first from an unordered list, in both locales, without mutating the input. `npm test` is
59/59; typecheck, lint and `npm run build` (93/93 pages) pass.

**Checked in the browser:** local web against beta's API, 108 (five annual years) and 2222 (mixed periods:
TTM Jun 2026, Jun 2026, FY2025), in English and Arabic at 1440 and 390, both panels (16 panels). For each
panel the script reads:
- the heading order;
- whether the first (newest) column is inside the scroll box on load;
- whether the last (oldest) column comes into view after scrolling the box to its far end (negative
  `scrollLeft` in RTL).

All 16 PASS. For example, 108 at 390: FY2025, FY2024 beside the labels on load, and FY2021 after scrolling.
2222's Arabic balance sheet opens on "يونيو 2026", with 2025 at the scroll edge.

Evidence is in `docs/screenshots/statements-newest-first-2026-11-06/`, with `-scrolled` images for the panels
that scroll, and in `.txt`.

**Still pending:**
- F-16's check after the 05:00 UTC publish, and the label sweep re-run then.
- Nothing is released or pushed. That is the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next step?
