# Output 25: review 24's step, unit captions for an unconfirmed currency; candidate `de19095`

Commits `de19095` (app) and `9e0c840` (evidence and records).

**The change:**
- `web/src/components/stock/research-panels.tsx`: a new `unitCaption(t, currency, locale)`. If
  `currencyLabel()` gives a label, it returns `statements.unit` ("Millions of {currency}"); otherwise
  `statements.unitUnconfirmed`.
- Both callers use it: the statement table (formerly line 208) and the capital-changes panel (formerly line
  638), which had the same blank caption.
- `web/messages/en.json`: `"unitUnconfirmed": "Millions (currency not confirmed)"`.
- `web/messages/ar.json`: `"unitUnconfirmed": "بالملايين (العملة غير مؤكدة)"`. This reuses the header's existing
  wording, `stock.currencyUnconfirmed` "Currency not confirmed" / "العملة غير مؤكدة".
- No currency is guessed, and no figure changes.

**Proof:**
- `npm test` 68/68, `tsc` 0, lint 0, `npm run build` 93/93.
- **Check 14** (`docs/screenshots/release-candidate-de19095/14-unit-captions.txt`, `unit-captions/`,
  `contact-sheet-unit-captions.png`): KFH (no confirmed currency) and 108 (KWD, the control); income and
  balance; English and Arabic; 1440 and 390. **16/16 PASS**:
  - KFH's caption is exactly "MILLIONS (CURRENCY NOT CONFIRMED)" / "بالملايين (العملة غير مؤكدة)";
  - 108 keeps "MILLIONS OF KWD" / "بملايين د.ك";
  - the caption is not clipped (inside the panel, `scrollWidth ≤ clientWidth`);
  - **every cell in every column equals the API** (26 × 5 and 29 × 5).
  - Inspected by eye on the contact sheet.
- **Whole candidate re-run on `de19095`** against the 2026-11-06 published data:
  - checks 1–8 all PASS;
  - check 13 (the three labels) 8/8;
  - check 14, 16/16;
  - **sweep 714/714 PASS**, with `"no_currency":8`.

**Count corrected:** 8 listings, not 7. The readiness report and `PROJECT.md` now say 8, with a note on the
correction; a grep finds no "7 listings" left.

**Readiness report** (now candidate `de19095`):
- the visitor table has the caption row;
- app code is **7 files**, adding `web/messages/en.json` and `ar.json`; the report says `web/messages` changed;
- evidence and checks updated;
- the inventory is recomputed: 909 files, 29 named, 830 evidence, 50 review records, 0 misses.

`git diff --stat de19095..HEAD -- web/src api deploy web/messages web/public` is empty.

**The question for the review:** is this sound, and what is the single next pre-approved step?
