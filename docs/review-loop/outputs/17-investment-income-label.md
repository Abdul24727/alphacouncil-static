# Output 17: review 16's step, "Income from investments & other operating income", and candidate `4a98832`

Commits `4a98832` (app) and `c08e409` (evidence, report, records).

**Source:** "income from investments & Other operating income" is Argaam's own English for row **tr166**.
- It is stored on 3 Saudi banks (1120, 1140, 1150), in the income statement.
- The Gulf pages store its Arabic "دخل الإستثمارات والعمليات الأخرى" (tr166, 23 pages). The dictionary's pair
  (line 413) gave that Arabic the lowercase English.

**The change** (`web/src/content/data-labels.json`):
- The pair's English is recased to "Income from investments & other operating income". Lookups ignore case,
  so the `toAr` key does not change.
- An alias maps the stored Saudi spelling to it. Pairs stay at 494; aliases go from 37 to 38.

**Proof:**
- `makeDataLabel()` was run with the previous and new dictionaries over 927 texts, in en and ar, in 3
  contexts. Exactly **6** differences: English pages only, for the Gulf Arabic and the stored Saudi
  spelling. Arabic is unchanged.
- One new test: both stored forms give the sentence-case English, and the Saudi spelling keeps its Arabic.
- `npm test` 67/67, `tsc` 0, lint 0, `npm run build` 93/93.

**Rendered** (check 8): 821 (Gulf) and 1120 (Saudi), income, en and ar, 1440 and 390. **8/8 PASS**.
- The sentence-case label shows; the old spelling does not; the Arabic is unchanged; newest-column values
  equal the API's.
- Inspected on `contact-sheet-investment-income.png`: 821 shows 2.82, and 1120 shows 1,503, in both
  languages.

**New candidate `4a98832`, the whole check re-run: all 8 PASS.**
- The 11-04 set, the Gulf English pages, newest-first, the bank sub-lines, the real-estate label,
  `check-arabic` (48 views, 0 stray English), the phone check (11/11, no cut periods), and check 8.
- Evidence: `docs/screenshots/release-candidate-4a98832/`, 159 screenshots and 8 logs.
- Two things in that run:
  - The first run lost its SSH tunnel to beta partway through ("Connection reset by peer"). Every check was
    re-run in full with a keep-alive tunnel; the saved files are the re-run's.
  - The 11-04 set's expectations named the old spelling for 821 and AJMANBAN. They were updated to the
    renamed label; that set's other labels were unchanged and passed.

**Readiness report:**
- Updated to `4a98832`: candidate lines, a visitor-table row, the `data-labels.json` description, check 8,
  and counts.
- The inventory was recomputed from `git diff 5c18a3ae46..4a98832`: 526 files, of which 25 are named, 467
  evidence and 34 review records. A script found 0 misses.
- `git diff --stat 4a98832..HEAD -- web/src api deploy web/messages web/public` is empty.

**Observation, recorded and not changed:**
- In development only, Next.js shows a "1 Issue" badge on every ticker Financials page: "uncached data in
  `generateMetadata()`" for `/[locale]/t/[ticker]/financials`, which holds back the page's metadata.
- It predates this work: no file under `web/src/app` changed since `5c18a3ae46`. The production build passes.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
