# Output 26: review 25's two issues, fixed

Commit `a721bea`. No app code changed (`git diff --stat de19095..HEAD -- web/src …` is empty).

**1. The release summary.** `docs/release-readiness-2026-11-06.md` now reads "Arabic pages change only through
rows 2, 3, 5 and 7: newest first, bank sub-lines, the unconfirmed-currency caption, and phone tables", with a
correction note.

**2. The capital-changes panel's caption is verified.** Check 15:
`docs/screenshots/release-candidate-de19095/15-capital-captions.txt` and `capital-captions/`, on the Calendar
tab, English and Arabic, 1440 and 390. **8/8 PASS.**
- **Which data exists, from beta's API:** all 8 listings without a confirmed currency (GIH, OEIHC, ORDS_ADX,
  EKTTITAB, IFA, NIH, NIND, KFH) have **0** capital changes. Controls: 1010 SAR has 9, 2222 SAR 4, 108 KWD 0,
  ADCB AED 0.
- **Confirmed currency, 1010:** the caption is exactly "MILLIONS OF SAR" / "بملايين ر.س" and not clipped. All
  9 rows' date, capital after (`fmtNumber(…, 0)`) and change (`fmtPct(…, 1, true)`) equal the API's: 0
  differing. Inspected by eye on the Arabic 390 screenshot.
- **Unconfirmed currency: no data can show it.** With no rows, the panel shows its empty message (`capital.none`)
  and no caption. KFH was checked for exactly that in all four views. No data was invented to force the
  unconfirmed caption onto this panel; its wording and logic are those check 14 verified on the statement panels.

**Seen on check 15, recorded and not changed:** on 1010's Arabic capital panel at 390, the date and type
columns run together ("2026-04-05أسهم منحة"). Neither `td` has inline padding (`research-panels.tsx`,
CapitalPanel). This predates today's work.

**The question for the review:** is this sound, and what is the single next pre-approved step?
