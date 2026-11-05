# Output 02: review 01's fixes, and its next step (Gulf lines on English pages)

**Review 01's two issues** (commit `e9df2c8`):
- The F-16 doc's status line and two `PROJECT.md` lines said "not applied". They now say applied, with the
  check after the publish to do.
- The unpushed list now names the `check-advisors.mjs` fix and the F-16 patches.

**The step** (commits `1d1a22a`, `c76421a`; record in `docs/arabic-statement-labels-2026-11-03.md`,
"English pages (2026-11-06)"):

- **Before:** on English pages, 8,085 of 106,300 Gulf statement rows (7.6 %, 94 labels) showed in Arabic
  on live data. After the F-16 publish it would be 7,510 rows, 76 labels.
- **76 pairs** were appended to `web/src/content/data-labels.json` (419 → 495):
  - Argaam's English for the same row id on the Saudi pages; no label's ids carry two meanings.
  - Gulf units in the dictionary's existing style.
  - Three translations where Argaam's English names something else.
  - Two bank income sub-lines composed ("Special commission income from banks & other FIs", "…expense on
    due to banks & other FIs").
- **Nothing existing changed:** no mapping in either direction. The 27 new English keys are used by no
  Saudi line, so Arabic pages are unchanged.
- **After:** 0 rows on the after-F-16 data. On live data until the publish, 575 rows, all cash-flow lines
  inside F-16 companies' balance sheets.
- **English-direction coverage in the existing checks:** `web/scripts/check-data-fixes.mjs` `SWEEP=1`
  reads every company's statements and fails on any shown line left in Arabic. Where statements are
  Pro-only it says so instead.
  - Run against beta before the publish, it FAILED on exactly F-16's 18 cash-flow labels in 8 companies;
    all else PASS.
  - Evidence: `docs/screenshots/gulf-english-labels-2026-11-06-sweep-before-publish.txt`.
  - It is to be re-run after the 05:00 UTC publish, when it should pass.
- **Rendered locally against beta's API:** 7 companies, one per market and unit, in English and Arabic at
  1440 and 390.
  - Every expected English label shown, 93 per width.
  - 0 English labels on Arabic pages.
  - 0 Arabic labels on English pages, except AMCREIT's F-16 cash-flow lines.
  - Evidence: `docs/screenshots/gulf-english-labels-2026-11-06/`.
- **Tests:** 5 new; `node --test` 47/47. Lint clean on the changed check.
- **Not released, not pushed:** both need the owner's go-ahead.

**Left, and recorded:**
1. Three bank income sub-lines share their text with balance-sheet lines: "الاستثمارات", "قروض و سلف" and
   "ودائع العملاء". In the flat panel they read as balances (Investments / Loans and advances / Customer
   Deposits); see the ADCB income statement. A text-keyed dictionary cannot separate the two uses; it needs
   a lookup by statement.
2. An old entry reads "property Real estate Investment".
3. On a phone, the statement table opens on the oldest years, not the newest.

**The question for the review:** is this sound against the plan, and what is the single next step?
