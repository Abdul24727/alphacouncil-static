# Output 23: review 22's step, F-16 verified live; candidate `2f50598`

Commits `2f50598` (app: 3 label pairs) and `a5a4f6e` (evidence and records).

**The night** (watched read-only):
- The full-mode scrape finished at 716/716.
- The parse finished at 04:00 UTC: 682 companies, 139,985 line items, **no `UNKNOWN STATEMENT HEADING`**.
- The run ended 04:33 with `ALERT [OK]`: scrape, rebuild and restart complete, and `/api/screening` 200.
- The same run also raised `ALERT [FAIL] disk pressure` (root at 83 %). That is the owner's disk item, not a
  step failure. My watcher at first counted it as one, so I read the line and changed its pattern.

**Published 05:01:03 UTC with `/healthz/deep=ok`.**

**`scripts/pipeline-checks/f16_after_publish.py 2026-11-06`: ALL 13 PASS**
(`docs/screenshots/release-candidate-2f50598/12-f16-after-publish-2026-11-06.txt`):
- The 8 night and publish items pass.
- The nine balance sheets are present: 310, 50, 103, 155, 322, 78, 320, 322 and 320 rows.
- **0 cash-flow lines** are in them.
- **The eight have a Cash Flow Statement**, 46–95 rows each.
- ADNIC has none.
- **AMLAK's newest balance sheet is 31 rows** (was 50).
- Beta's API serves AMLAK as Income 23, Balance 31, Cash Flow 19.

**The English-label sweep on the published data:**
- **First run:** 714/714 read, and **FAIL on 3 labels**, none of them F-16's. All three came in with tonight's
  full harvest:
  - DIC's annual-page "ربح السهم" (tr552) and "ربح السهم قبل البنود الاستثنائية" (tr1373), with no unit.
    Its quarter page has "(درهم)" for the same rows.
  - KFH's annual-page "القيمة الدفترية دينار بحريني" (tr544), whose quarter page has "(دينار بحريني)".
- **Fix (`2f50598`):** "EPS" and "EPS before exceptional items", no unit, because the Arabic names none and
  the same text could appear for another currency; and "Book value (BHD)".
  - Lookups before and after over 932 texts: 9 English-page changes for these 3 Arabic labels, plus the 2 new
    English keys finding their Arabic. No Saudi line uses that English.
  - One new test; `npm test` 68/68, `tsc` 0, lint 0.
- **Re-run: PASS, 714 of 714 companies, 40,811 lines**
  (`11-sweep-on-the-2026-11-06-publish.txt`).

**Candidate `2f50598`: checks 1–8 re-run against the new published data, all PASS**
(`docs/screenshots/release-candidate-2f50598/`). AMLAK's English balance sheet is 31 rows and AMCREIT's 21,
with **0 Arabic labels on any English page**. The SEO checks 9 and 10 stay valid from `4a98832`, since no
metadata code changed.

**Records:**
- The F-16 doc is **VERIFIED LIVE** ("Verified live").
- `PROJECT.md`: F-16 CLOSED.
- The readiness report is now candidate `2f50598`:
  - the visitor row reads "0 left in Arabic … 714/714";
  - the pending section is replaced by "F-16, verified live";
  - the inventory is recomputed: 721 files, 27 named (the 2 pipeline-check files added), 648 evidence and
    46 review records, 0 misses.
- `git diff --stat 2f50598..HEAD -- web/src …` is empty.

**What remains is the owner's:**
- release and push;
- the `owns` patch;
- Step 7, the lawyer;
- F-14;
- the disk;
- the pilot.

**The question for the review:** is this sound, and what is the single next pre-approved step, if any remains?
