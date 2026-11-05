# Output 06: review 05's step, "property Real estate Investment"

Commit `9b7abbc`. Record: `docs/arabic-statement-labels-2026-11-03.md`, "property Real estate Investment".

**Source:** the harvested pages' row ids (`gulf_ids.py` output) show two things.
- "property Real estate Investment" is Argaam's own English for row **tr432** on 210 Saudi pages. Saudi
  rows store it in English.
- Gulf pages store "استثمارات عقارية" on tr432 (333 pages), tr234 and tr1066. Argaam's English for that
  Arabic on row **tr73** is "Real Estate Investments", already the dictionary's next pair for it.

Line 42 made the garbled text the first English for "استثمارات عقارية", so 333 Gulf pages showed it as well.

**The change** (`web/src/content/data-labels.json`):
- The pair `["property Real estate Investment", "استثمارات عقارية"]` is removed (495 → 494 pairs).
- An alias `"property Real estate Investment": "Real Estate Investments"` is added (36 → 37). `aliases` is
  the existing mechanism for stored spellings. It turns the Saudi stored text into the clean English, and
  through `toAr` of the canonical English it keeps "استثمارات عقارية" on Arabic pages.

**Proof that nothing else moved:** `makeDataLabel()` ran with the previous and new dictionaries over 926
texts: every pair's English and Arabic, every alias key, and every Saudi and Gulf label on the harvested
pages. Each in en and ar, with no statement, "Income Statement" and "Balance Sheet". Exactly **6**
differences, all on English pages: "استثمارات عقارية" and "property Real estate Investment" became "Real
Estate Investments" in each context.

**Checks:**
- One new test: both stored texts give the clean English, and the Saudi spelling still gives its Arabic.
- Suite 64/64. `tsc` exits 0, lint exits 0, `npm run build` passes (93/93).
- **Rendered** (local web against beta's API): 108 (Gulf) and 1211 (Ma'aden, Saudi, stores the garbled
  spelling), balance sheets, en and ar, 1440 and 390. 8/8 PASS: "Real Estate Investments" shows, the garbled
  text does not, Arabic shows "استثمارات عقارية", and the newest-column values equal the API's row by row.
  Example: 108's 465 / 366.
- Evidence: `docs/screenshots/real-estate-label-2026-11-06/` and `.txt`.

**Still pending:**
- F-16's check after the 05:00 UTC publish, and the sweep re-run.
- Nothing is released or pushed. That is the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next step?
