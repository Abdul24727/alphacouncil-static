# Release readiness, 2026-11-06: candidate `de19095` against the deployed `5c18a3ae46`

**Status: ready for the owner's release decision.** This report needs no release and no push. Each release
(beta, then production) and each push is the owner's go-ahead in chat.

- **Deployed now:** `5c18a3ae46` on beta and production (2026-11-05).
- **Candidate:** `rebuild` at `de19095`. Commits after it change no app code: records, this report, the
  review loop. So the deploy script may ship a later `rebuild` HEAD whose app code equals `de19095`; the
  check is `git diff --stat de19095..HEAD -- web/src api deploy web/messages web/public`, which must be
  empty.
- *(`2f50598` was superseded by review 24's caption fix. Its evidence, including the live sweep and F-16
  check after the publish, stays in `docs/screenshots/release-candidate-2f50598/`.)*
- *(`4a98832` was superseded by three label pairs the live English-label sweep called for after the
  2026-11-06 publish. Its evidence stays in `docs/screenshots/release-candidate-4a98832/`, including the SEO
  checks 9 and 10, which still hold: no metadata code changed since.)*
- *(`307d2fc` was superseded by review 16's label change. Its evidence stays in
  `docs/screenshots/release-candidate-307d2fc/`.)*
- *(The first candidate, `509d7bf`, was superseded by review 13's phone-table fix. Its evidence stays in
  `docs/screenshots/release-candidate-509d7bf/`: 150 screenshots, not the 130 this report first said.)*
- **Pushed:** `origin/rebuild` is at `ccfe063`. Everything after it is unpushed.

## What a release changes for visitors

All of it is in `web/src` and `web/messages`; `api/`, `deploy/` and `web/public/` are unchanged.

| Change | Pages | Record |
|---|---|---|
| Gulf statement lines show in English on English pages: 79 labels; **0 left in Arabic on the 2026-11-06 published data, 714/714 companies swept** | English Financials, Gulf companies | `docs/arabic-statement-labels-2026-11-03.md`, "English pages" |
| Statement columns newest first, so a phone opens on the newest period | Financials, both languages | `PROJECT.md` §5, 2026-11-06 |
| Bank income sub-lines read as commission income/expense inside the income statement | Financials of banks, both languages | labels doc, "Bank income sub-lines" |
| "property Real estate Investment" reads "Real Estate Investments" | English Financials | labels doc, "property Real estate Investment" |
| Where a listing's currency is not confirmed (8 listings), the unit caption says "Millions (currency not confirmed)" / "بالملايين (العملة غير مؤكدة)" instead of "Millions of" with nothing after it | Financials and the capital-changes panel, both languages | `PROJECT.md` §5, 2026-11-06 (review 24) |
| "income from investments & Other operating income" reads "Income from investments & other operating income" | Financials, English: 3 Saudi banks and the Gulf companies with that line | `PROJECT.md` §5, 2026-11-06 (review 16) |
| On a phone, the line labels stay in place, each period fills the space beside them, and scrolling snaps to whole periods: no figure is shown cut in half | Financials on phones, both languages; desktop unchanged | `PROJECT.md` §5, 2026-11-06 (review 13) |

Arabic pages change only through rows 2, 3, 5 and 7: newest first, bank sub-lines, the unconfirmed-currency
caption, and phone tables. *(Corrected by review 25: this said rows 2, 3 and 6, from before the caption row
was added.)* No existing dictionary mapping changed, apart from the one
intended real-estate label.

## Every file changed since `5c18a3ae46`

All 909 files of `git diff --name-status 5c18a3ae46..de19095`: 29 outside `docs/screenshots/` and
`docs/review-loop/`, all named below; 830 evidence files under `docs/screenshots/` (one of them, a corrected
header, is also named below); and 50 review-loop records under `docs/review-loop/`. *(Reconciled with the diff
2026-11-06, after ChatGPT's review 14 found three script files missing from the first list.)*

**App code, which ships with a release (7 files):**
- `M web/src/content/data-labels.json`: 79 English-page pairs (76, plus 3 annual-page spellings the live sweep
  found after the 2026-11-06 publish); `in_statement` (5 bank sub-lines); the garbled
  real-estate pair becomes an alias; the tr166 label is recased, with an alias for Argaam's spelling.
- `A web/src/lib/data-labels-core.ts`: the lookup, with no imports, taking an optional statement.
- `M web/src/lib/data-labels.ts`: now `makeDataLabel(data)`; same import path for every caller.
- `M web/src/lib/statement-period.ts`: `statementColumns()` newest first; `phoneColumnWidth()`, the phone
  width rule.
- `M web/src/components/stock/research-panels.tsx`: the statement table passes its statement to
  `dataLabel`; sticky label column; on a phone, measured period widths with snap scrolling; `unitCaption()`
  for an unconfirmed currency.
- `M web/messages/en.json` and `M web/messages/ar.json`: `stock.statements.unitUnconfirmed`, one line each.

**Tests, which ship but do not run on the server (3 files):**
- `A web/src/lib/data-labels-core.test.ts`;
- `M web/src/lib/data-labels-content.test.ts`;
- `M web/src/lib/statement-period.test.ts`.

**Check scripts (4 files):**
- `M web/scripts/check-data-fixes.mjs`: the English-label sweep;
- `A web/scripts/lib/label-sweep.mjs` and `A web/scripts/lib/label-sweep.test.mjs`: the sweep fails closed;
- `M web/scripts/check-advisors.mjs`: two INFO lines were blind to the chips and fault lines.

**Pipeline tooling, not part of the web release (5 files under `scripts/argaam_ar_labels/`):**
- `A argaam_pages.py`: the page reading the two pairing scripts share (`page_rows()`, `norm()`, `ROW_ID`).
- `M pair_from_gulf.py`: the dollar as a currency unit, and it uses `argaam_pages.py`.
- `M pair_labels.py`: it uses `argaam_pages.py`, and its `--ar-dir` usage is marked superseded.
- `M harvest_ar_statements.py`: docstring only, marked superseded (do not run).
- `A test_pair_from_gulf.py`: the unit rule's tests.

**Review loop tooling (1 file):** `A scripts/review-loop/ask_chatgpt.py`.

**Pipeline checks (2 files, not part of the web release):**
- `A scripts/pipeline-checks/f16_after_publish.py`: F-16's read-only after-publish check;
- `A scripts/pipeline-checks/test_f16_after_publish.py`: its regression tests (missing data must fail).

**Patches and pipeline records (5 files under `docs/`):**
- `A pipeline-guard-statement-headings-2026-11-06.patch`, applied on the server 2026-11-05 22:44 UTC on the
  owner's go-ahead;
- `A pipeline-guard-statement-headings-guard-only-2026-11-06.patch`, the unused alternative;
- `A pipeline-guard-statement-headings-2026-11-06.md`, its record;
- `A check-advisors-owns-case-2026-11-06.patch`, prepared and **not applied**: it waits on the owner's
  go-ahead;
- `A release-readiness-2026-11-06.md`, this report.

**Records (3 files):**
- `M PROJECT.md`;
- `M docs/arabic-statement-labels-2026-11-03.md`;
- `M docs/screenshots/launch-2026-10-27/advisors-signed-in/check-advisors.txt`: a corrected header. It is also
  counted among the 830 evidence files.

**Evidence and review records:**
- 830 files under `docs/screenshots/`, the folders this report and the labels doc cite;
- 50 under `docs/review-loop/`: the master plan, outputs, replies and log.

## Checks on the candidate (`de19095`), all run together on 2026-11-06

Run after the last change, so no later step can have broken an earlier one.

**Static checks:**
- `npm test` 68/68; `tsc --noEmit` exit 0; `npm run lint` exit 0; `npm run build` passes (93/93 pages).
- `python -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py`: OK (4 tests).

**Rendered:** local web against beta's API, which since 05:01 UTC serves the 2026-11-06 publish. Evidence is in
`docs/screenshots/release-candidate-de19095/`: checks 1–8 re-run on this candidate against the 2026-11-06
published data, all PASS. The same folder holds:
- check 13 (the three labels, 8/8);
- check 14 (unit captions, 16/16);
- `11-sweep.txt`: **714/714, PASS**.

The F-16 check after the publish (13/13) and the first live sweep are in the `2f50598` folder; the SEO checks
9 and 10 are in the `4a98832` folder.

**Check 13, the three labels the live sweep called for** (`13-three-labels.txt`, `three-labels/`; the
contact sheet is in the `2f50598` folder): DIC's income statement and KFH's balance sheet, English and Arabic, 1440 and
390. 8/8 PASS:
- "EPS", "EPS before exceptional items" and "Book value (BHD)" are shown and not clipped, and the Arabic is
  unchanged;
- every cell in every column equals the API (DIC 26 × 5, KFH 29 × 5);
- inspected by eye: DIC's FY2025 EPS is 0.36 and before exceptional items 0.16; KFH's book value is 0.36 in
  FY2025 and 0.12 in FY2021.

`npm run build` was re-run on this candidate's code (93/93).

**Check 14, unit captions** (`14-unit-captions.txt`, `unit-captions/`, `contact-sheet-unit-captions.png`):
KFH, whose currency is not confirmed, and 108 (KWD) as the control; income and balance; English and Arabic;
1440 and 390. 16/16 PASS:
- KFH reads "MILLIONS (CURRENCY NOT CONFIRMED)" / "بالملايين (العملة غير مؤكدة)";
- 108 keeps "MILLIONS OF KWD" / "بملايين د.ك";
- no caption is clipped;
- every cell in every column equals the API.

**Check 15, the capital-changes panel's caption** (`15-capital-captions.txt`, `capital-captions/`). It uses the
same `unitCaption()`; Calendar tab, English and Arabic, 1440 and 390. 8/8 PASS:
- **Confirmed currency, 1010 (SAR):** "MILLIONS OF SAR" / "بملايين ر.س", not clipped; all 9 rows' date,
  capital after and change equal the API's.
- **Unconfirmed currency: no data to show it.** None of the 8 listings without a confirmed currency has a
  capital change (`/corporate` gives 0 rows each). KFH's panel therefore shows its empty message and no
  caption, which was checked. No row was invented to show the unconfirmed caption there.
- **Seen on check 15, left for review:** on 1010's Arabic panel at 390 the date and type columns run
  together ("2026-04-05أسهم منحة"), because neither cell has inline padding. That predates today's work.

The sweep counts **8** listings with no confirmed currency (`"no_currency":8`). *(Corrected by review 24: this
report and `PROJECT.md` first said 7, taken from the 2026-11-05 sweep.)*

| # | Check | Covers | Result |
|---|---|---|---|
| 1 | 2026-11-04 label set (`labels-fix-check.mjs`) | Arabic 1010, 1211, 8010, 2222; English AMLAK, AJMANBAN, AMCREIT, ADCB, 301, 821, BKIC.BH, EAND | PASS, every expected label; 0 English labels on Arabic pages |
| 2 | Gulf English pages | 108, ABOB, DUBK, GFH.DU, ADCB, AJMANBAN, AMCREIT; en + ar; 1440 + 390 | PASS, every expected label |
| 3 | Newest first | 108, 2222; en + ar; 1440 + 390; 16 panels | PASS: newest beside the labels on load, oldest reachable |
| 4 | Bank sub-lines | ADCB, 1010; both panels; en + ar; 1440 + 390 | PASS 16/16, with values equal to the API's row by row |
| 5 | Real-estate label | 108, 1211; en + ar; 1440 + 390 | PASS 8/8, with values equal to the API's |
| 6 | `check-arabic.mjs` with `WIDTHS=1440,390` | 48 Arabic page views signed out, including `/t/2222/financials` | 0 English strings outside the allow-list |
| 7 | Phone gap (review 12) and phone tables (review 13) | English income + balance for 301, 821, BKIC.BH, EAND; Arabic income + balance for 8010; Arabic income for 1211; 11 panels at 390 | PASS 11/11: expected labels shown; **every cell in every column** equal to the API's; newest in view on load; scrolled to the end, the oldest in view **beside the labels, which stay in view**; **no period shown cut**, on load, at every column step or at the end (`7-phone-gap.txt`, `phone-gap/`). Run on the previous commit, the same check fails 9 of the 11, so it does catch the defect. |
| 8 | The tr166 label (review 16) | 821 (Gulf, Arabic-stored) and 1120 (Saudi, Argaam's spelling); income; en + ar; 1440 + 390 | PASS 8/8: the sentence-case label shows in English, the old spelling does not, the Arabic is unchanged, and the newest-column values equal the API's (`8-investment-income-label.txt`, contact sheet) |

**What is still Arabic on English pages:** nothing. On the 2026-11-06 published data the sweep read all 714
companies, 40,811 lines, and every one has English. The F-16 cash-flow lines left the balance sheets with
the publish, and the 3 annual-page spellings it then found are in `2f50598`.

**On production after a release:** Financials is Pro-only there, so a signed-out check cannot render it. As
on 2026-11-05, production is checked through its served code: the new chunk byte-identical to beta's, and
hash-equal on the public site. Then `check-billing-public.mjs`, health, and `BILLING_OPEN` unchanged.

**Inspected by eye:** all 11 phone panels on load, and the 9 that scroll in their scrolled state. They were
put side by side on contact sheets, with a sample of the 1440 panels for comparison. The desktop layout is
unchanged. *(Review 13 found that only two of the phone panels had been looked at before.)*

**Seen on the screenshots, left for review:**
- *(Fixed in `4a98832`: 821's "income from investments & Other operating income" now reads "Income from
  investments & other operating income".)*
- In development only, Next.js shows a "1 Issue" badge on every ticker Financials page: `generateMetadata()`
  for `/[locale]/t/[ticker]/financials` reads uncached data, so the page's metadata is held back while the
  rest prerenders. No route file changed since `5c18a3ae46`. **Verified on a local production build (review
  17): a development diagnostic, not a production defect.**
  - `getTickerRef()` calls `connection()` on purpose: a stock page's title comes from the API at request
    time.
  - Built and served with `next start` against beta's API, the production server logs no such notice.
  - **What was tested, by user agent** (`10-metadata-production-build.txt`, for `/t/2222/financials`,
    `/ar/t/2222/financials` and an unknown ticker in both languages):
    - **Googlebot**, raw HTML: the title, description, canonical, `og:title`, `og:url`, `og:image`,
      `og:locale` and the en / ar / x-default alternates are all in `<head>`. `next.config.ts` puts the
      crawlers on its `HTML_LIMITED_BOTS` list there (Next's list plus Googlebot); only Googlebot was
      tested.
    - **An ordinary Chrome user agent**, raw HTML: the same fields arrive **streamed into `<body>`**, as
      `next.config.ts` says they do for ordinary visitors.
    - **An ordinary Chrome browser after load:** the document has the right title, description, canonical,
      preview tags and alternates.
  - **The values:** "Saudi Aramco (2222) · Tadawul · AlphaCouncil" and "أرامكو السعودية (2222) · تداول ·
    AlphaCouncil", each with its own description. Canonical `/t/2222` and `/ar/t/2222`; `og:image`
    `/og/en.png` and `/og/ar.png`; `og:locale` `en_US` and `ar_SA`.
  - **An unknown ticker** keeps the soft not-found ("Unknown ticker" / "رمز غير معروف"). Its robots tag reads
    `noindex, nofollow` for Googlebot and `noindex` for a browser; both keep it out of search.
  - `check-seo.mjs` against that production server: **62 PASS, 0 FAIL** ("ALL PASS"). It reads as Googlebot
    and a link-preview bot. Of the Financials URLs, it checks only English `/t/2222/financials`'s canonical;
    the rest above comes from file 10.
  - Evidence: `docs/screenshots/release-candidate-4a98832/9-check-seo-production-build.txt`,
    `10-metadata-production-build.txt` and `seo-production-build/` (12 screenshots). *(Corrected by review
    18: the screenshots had been written under an untracked `web/docs/`; file 10 had left out the
    descriptions and alternates; and this paragraph had claimed every stock page's metadata is in `<head>`
    without saying that was true for crawlers only.)*
- *(Fixed in `307d2fc`: scrolled to its oldest year, a phone table used to scroll the line labels out of
  view and show a period cut in half beside them.)*

## F-16, verified live (2026-11-06)

The after-publish check ran on the 05:01 UTC publish: all 13 items PASS, and the English-label sweep
PASSED 714/714. Details are in `docs/pipeline-guard-statement-headings-2026-11-06.md`, "Verified live".

**Release order** (`CLAUDE.md`, `PROJECT.md` §4): `scripts/deploy-staging.sh`, then check beta, then
`scripts/deploy-production.sh` with no commit in between, then check production. The rollback is
`5c18a3ae46`, still in both tiers' `releases/`.
