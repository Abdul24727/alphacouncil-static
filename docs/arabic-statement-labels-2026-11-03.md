# Arabic line labels for Saudi statements, from Argaam's own Arabic pages

2026-11-03. Owner's choice in chat: **"Harvest Argaam Arabic"**, over translations drafted here.

## Outcome of the server harvest (2026-11-03 14:29–14:35 UTC, on the owner's "Yes, run it"): BLOCKED

- **The pilot** (2222, 1120, 8010) got no statement grid on any of the three pages and stopped itself
  after the third, as designed. Nothing was saved and the nightly's files were not touched.
- **One diagnostic visit to Aramco, in each language, with the same session**, settled why:
  - *English:* signed in (the account's name shows), the grid present, 102 rows. The session works.
  - *Arabic:* Argaam answers with **"Human Verification — Let's confirm you are human"**, a bot
    challenge. The page `/ar/tadawul/…` redirects to the older `/ar/company/financialstatement/…`
    route, and that route challenges the server. It is the same block that stopped F-D
    (Step 19) on the market-wide disclosures list.
- **The challenge is not to be got around**, so harvesting from the server is closed. Four Arabic
  page loads were made in all. Left on the server: `/root/argaam-ar-statements/_summary.json` and
  `_diag/` (the two diagnostic pages).
- **The route that remains: the owner's own browser.**
  - The owner signs in to Argaam in the desktop app's browser pane. Claude never types the password.
  - Claude then reads the Arabic statement pages there, as the owner's signed-in visit.
  - If a challenge appears there, it is the owner's to answer, not Claude's.
  - **Eight companies cover every line**: a greedy cover over all 269 English pages, 415 (row id,
    English label) pairs including the unit variants, 0 uncovered.
  - The eight: 5110 `saudi-energy` (+94), 8160 `aicc` (+86), 1150 `alinma` (+69), 1180 `snb` (+68),
    4083 `tasheel` (+54), 4350 `alistithmar-reit` (+40), 7211 `azm` (+3), 2222 `saudi-aramco` (+1).
  - So it is eight page visits, not 269. The pairing is unchanged: by row id, against each company's
    own English page on the server.

The plan as first written follows; its server harvest is superseded by the outcome above.

## The gap

Since the 2026-11-03 05:03 UTC publish, 250 Saudi income statements are in the database, and their
line labels are English: the nightly reads Argaam's English pages for Saudi companies. The Arabic
page shows each label through `web/src/content/data-labels.json`, which knows 4 of Aramco's 18 income
lines, because no Saudi income statement existed when it was built. **133 distinct labels** are
affected, across industrials, banks, insurers and finance companies. That re-opens commit `b548bbe`'s
guarantee: no English on Arabic pages outside an allow-list.

## What was established (read-only, 2026-11-03)

- **Argaam shows the statement grid to signed-in users only.** Signed out, the English and Arabic
  pages both answer 200 with "To Access this Content, Please Login…" / "يرجي تسجيل الدخول…" and no
  statement rows. So the Arabic pages can come only through the nightly's signed-in session; Claude
  does not sign in to Argaam.
- **The server has no Arabic statement page for any Saudi company.** The KSA harvest opens
  `/en/tadawul/tasi/{slug}/financial-statement` (`scrape_financial_statements`, which says so). Six
  pages that contain Arabic text turned out to be English grids with Arabic *footnotes* in a
  `relf-notesar` attribute.
- **The Arabic twin exists.** `/ar/tadawul/tasi/{slug}/financial-statement` redirects to
  `/ar/company/financialstatement/marketid/3/companyid/{id}/3/3/1/{arabic name}` for Aramco (3509),
  Al Rajhi (43) and Tawuniya (33), the three templates of the pilot.
- **Argaam numbers every line, and the number does not depend on the language.** Each row is
  `<tr id="tr384">` with the label in `<td data-fieldname=…>`. Over all 269 Saudi English pages there
  are **411 row ids, and each carries one English label everywhere** — but three, whose only
  difference is a unit (`… (Riyal)` on 205 pages, `… (Halala)` on 5; `Par Value` once without one).
  Pairing is per company, so a Halala row meets its own Arabic. **The English label and the Arabic
  label of one line are the two labels one row id carries on the two pages** — an exact pairing, not
  a guess by position, and a row on one page but not the other is reported rather than paired.

## Why a one-off harvest, not a nightly change

The labels are Argaam's fixed template, not data that moves. A nightly change would add about 269
page loads a night to the scraper and touch `main_patched2026_with_sectors.py`, for wording that
changes when Argaam adds a line. A one-off harvest into a folder of its own touches nothing the
nightly reads or writes, and can be run again when a new line shows up in English on an Arabic page.

## The tools (`scripts/argaam_ar_labels/`)

| Script | Where | What it does | Checked |
|---|---|---|---|
| `harvest_ar_statements.py` | server, pipeline Python | Opens the Arabic statement page per Tadawul ticker with the nightly's session and saves it to `/root/argaam-ar-statements/<ticker>.html` | `--dry-run` on the server: **269 URLs, 0 without a company path** |
| `pair_labels.py` | server, pipeline Python | Pairs the English page (the newest harvest run's grid) with the Arabic page by row id; reports unpaired rows and any English label with two Arabic ones | `--check-ids` on the server: the 411-id result above |
| `merge_pairs.py` | local | Adds only the English labels the dictionary lacks, as one new group at the end; never overwrites; lists every label where Argaam's Arabic differs from the dictionary's | On a copy: added 1, kept 1, listed 1 difference, refused a non-Arabic "translation"; the original byte-identical |

**What the harvest does on the server, exactly:**

- It reads `default_universe/_auth_state.json`, the signed-in Argaam session that the nightly's gate
  refreshes, into a **fresh** headless browser context, and **never writes it back**.
- It writes only to `/root/argaam-ar-statements/`. The harvest runs, the databases and the nightly are
  not touched.
- One page at a time, four seconds apart.
- It refuses to start between 23:30 and 03:00 UTC, or while the nightly's scrape or rebuild is
  running.
- It stops after three pages in a row come back without a grid (a lapsed session, or Argaam's "Human
  Verification").

**Order:** a pilot of three (2222, 1120, 8010: an industrial, a bank, an insurer; about a minute).
Then `pair_labels.py` on those three. Then, if every row pairs, all 269 (about 45 minutes, detached,
logged to `/root/argaam-ar-statements.log`).

## After the harvest

1. `pair_labels.py` (read-only) → the pairs and their report.
2. `merge_pairs.py` first **without** `--write`, and every label where Argaam's Arabic differs from
   the dictionary's goes to the owner before anything is replaced; then `--write` for the missing
   ones.
3. Web tests, then the Arabic Financials page on beta through the tunnel (2222, 1120, an insurer, at
   1440 and 390), then `check-arabic.mjs`.
4. Release beta → production (the owner's go-ahead per §4).

## Risks, and what limits them

- **It uses the Argaam account from the server in daytime.** The nightly uses the same session at
  night. Nothing new is stored. If the session has lapsed, the script stops at the third empty page,
  and the nightly's gate re-exports the session at 00:00 regardless.
- **Argaam could rate-limit or challenge it.** One page at a time, four seconds apart, about 269
  pages: less than one night's scrape, which opens many pages per ticker with four workers. A
  challenge stops it at the third empty page.
- **The nightly is unaffected:** separate folder, refusal inside its window, and the session file
  is read, never written.

## What was done instead (2026-11-03, after the owner's "there is no need to sign in")

The owner pointed out that signing in to Argaam anywhere else would sign the nightly's single session
out and break the scrape, so the browser-pane route was dropped unread. Signed out, Argaam's Arabic
statements page carries no table at all (0 rows; "للإستمرار في قراءة محتوى هذا القسم يرجي الدخول").

**The source used: Argaam's own Arabic, already on the server.**
- Argaam's row ids are shared across its markets, and the other Gulf markets' statement pages (ADX,
  DFM, KSE, QSE, MSM, BSE: 447 pages) are harvested in Arabic every quarter. So one row id carries a
  Saudi English label on one page and Argaam's Arabic label on another.
- 408 of the 411 Saudi row ids appear there. `scripts/argaam_ar_labels/pair_from_gulf.py`
  (read-only, no request to Argaam) pairs them.
  - Currency units are set to the Saudi ones: "(ريال)" / "(هللة)" in place of fils, dirham, baisa
    and so on, in 12 labels.
  - Where one English label covers two fields, the most used Arabic wins, and a tie goes to the
    shorter wording (one case: "Financing Investment" → "استثمارات تمويلية", not "…قصيرة الاجل").
  - Five outright misspellings in Argaam's text are corrected (missing letters or a misplaced hamza;
    listed in the script). Its informal spellings are kept.
- **284 English labels paired.** `merge_pairs.py` added the **129** the dictionary lacked. *Corrected
  2026-11-04 (below): 70 were already identical and **82 differ**, with 3 case variants inside the
  batch. The first report said 85 identical and 70 differ, because it compared against the wrong copy.*
  The differing ones were left as the dictionary has them. They are mostly spelling (the dictionary's
  hamzas and ة against Argaam's "إجمالى", "مبقاه"), and a few are more specific ("مطلوبات أخرى" where
  Argaam says "اخرى").
- **Unpaired, so still English:** "Net profit before deducting Mudaraba Instrument profit" and "EPS
  before deducting Mudaraba Instrument profit" (one company), and "Surplus Attributable to Insurance
  Operations" (on the pages, not in the database).

**Measured on the live data:** Saudi income-statement rows shown in Arabic went from **1,809 of 5,860
(31 %) to 5,858 of 5,860**; labels from 40 of 133 to 131. Balance sheets were already complete.
Rendered locally against the live data (`next dev`, beta's API by tunnel): 2222 (at 1440 and 390),
1120, 1150, 8010 and 4083 show **0 English line labels** on the Arabic Financials page.
`docs/screenshots/arabic-labels-2026-11-03.txt` and the PNGs beside it. Web suite 39/39, typecheck clean.

**Found while checking (F-15, recorded in PROJECT.md):** five finance companies (1182, 1183, 4081,
4082, 4083) have their balance-sheet lines inside the income statement, summed over four quarters.
The other gap seen, 19 REITs and funds (4330–4350) with no statement lines at all, predates the repair
(26 before it).

## Review fixes (2026-11-04, on the owner's "Yes, fix them")

The review of the unpushed work found three things to fix before these labels ship. All three are
fixed on `rebuild`. **Nothing is released.**

### 1. Sub-lines had lost the word their heading supplies

Argaam nests some lines under a heading: the row carries `data-ischildelement="yes"` and
`data-parentid`. Its Arabic for such a line often leans on the heading, as with "مرابحة" under the
financing-income heading. Our panel lists the lines without their headings.

A read-only scan of all 269 Saudi pages found 137 sub-lines (109 labels), 87 of which reach the
database. The rule applied:
- Where the English label carries the heading's word and the Arabic does not, the word is added.
- Argaam's wording is otherwise kept.
- Where a sibling line already has the composed form, it is matched: "مصاريف بيع و تسويق" leads to
  "مصاريف بيع و توزيع".
- Where the English is bare too ("Others", "Mushrakah", "Bei ajel", "Sukuk and Other investments"),
  both languages say the same, and nothing changed.

**13 labels changed:**

| English | Was | Now | Saudi companies with the line today |
|---|---|---|---|
| Selling and distribution expenses | بيع و توزيع | مصاريف بيع و توزيع | 163 |
| Other Investment Income | إستثمارات أخرى | دخل إستثمارات أخرى | 25 (insurers) |
| Others-Total Operating Expenses | اخرى | مصاريف عمليات اخرى | 7 (banks) |
| General & Administrative Expenses | مصاريف عمومية | مصاريف عمومية وإدارية | 6 (banks) |
| Income from Murabahat / Mutajara / Istisnaa / Installment sale | مرابحة / متاجرة / استصناع / بيع بالتقسيط | دخل المرابحة / دخل المتاجرة / دخل الاستصناع / دخل البيع بالتقسيط | 0 |
| Others-Fee and commission income | اخرى | دخل اتعاب و عمولات اخرى | 0 |
| Others-Special Commission Expenses | اخرى | مصاريف عمولات خاصة اخرى | 0 |
| Return On Customers’ Time Investments | استثمارات العملاء | العائد على استثمارات العملاء لأجل | 0 |
| Return on due to banks and financial institutions’ time investments | المطلوبات للبنوك واستثمارات المؤسسات المالية | العائد على المطلوبات للبنوك واستثمارات المؤسسات المالية لأجل | 0 |
| Property under development | استثمارات تحت التطوير | استثمارات عقارية تحت التطوير | 0 |

- "0" means the line is on Argaam's pages but carries no figures in today's database (three Islamic
  banks, the bank template's "Others-" lines, REITs). They are fixed so they read right when figures
  arrive.
- "Other Investment Income" is not a sub-line, but it had the same fault: it read as the
  balance-sheet "other investments".
- **Not changed:** an industrial's income statement shows both "Other" (أخرى, under operating
  expenses) and "Others" (اخرى, under investment income). That is Argaam's own English, and both
  languages are equally bare.
- **Checked after:** across 250 Saudi statements, no statement shows one Arabic label for two different
  lines. Saudi income-statement rows shown in Arabic: 5,705 of 5,707 in today's data. The F-15 fix
  moved 153 balance-sheet rows out of the income statement since the 5,860 above. The same two
  Mudaraba lines are left.

### 2. The merge report's count

- **The cause.** `merge_pairs.py` compared each label against the dictionary's *last* copy of it, but
  the site uses the *first*. The dictionary holds two different copies of 24 labels on purpose:
  - its own wording first, which Arabic pages show;
  - Argaam's Gulf spelling later, so Gulf rows stored in Arabic read back to English.
- It also counted 3 of the batch's own case variants as dictionary differences.
- **The fix.** The script now compares first-copy, as the site reads the dictionary, and lists case
  variants separately.
- **The recount**, against the dictionary as it was before the merge (`aa3dde6^`):

  | | Count |
  |---|---|
  | Added | **129**: the same 129 as `aa3dde6`, identical |
  | Already identical | **70** |
  | Differ | **82**: 47 in wording, 35 in spelling, spacing or the article only |
  | Case variants within the batch | **3**: 1 the same Arabic, 2 different; the site shows the first ("Employee Costs" → "تكاليف موظفين", "Other Expenses" → "مصاريف أخرى") |

- **So the first report understated the differences** rather than overstating them, as the review
  guessed. 18 labels change verdict between the first and the last copy, 17 of them towards
  "identical".
- **Nothing on the site changes:** the dictionary's wording was kept in every case. The 82 are listed
  in `docs/arabic-label-differences-2026-11-04.md`, in case the owner prefers Argaam's wording for any
  line.

### 3. English pages: Gulf lines that now read in English

The 129 also give 56 Gulf labels (1,702 rows) an English label on English pages, where they showed
Arabic before. Each was checked against Argaam's row ids on the Gulf and the Saudi pages (read-only
scan of every ticker's newest statement page):

- **54 are the same Argaam line** as the Saudi English label, so the English is Argaam's own for that
  field.
- **2 are partly a sibling line, with the same meaning:**
  - "ايرادات وساطة الاسهم و ادارة الصناديق" is also used for tr168 ("Share brokerage and fund
    management");
  - "متوسط عدد الاسهم (مليون)" is also used for tr1331, which no Saudi page has. "Average number of
    shares (mln)" is its literal translation.
- **0 are a different line.**

**Restoring six of them.** Fix 1 would have sent 6 of these back to Arabic, for example a Gulf bank's
"مرابحة". They are restored as later copies of Argaam's short wording, the dictionary's existing
pattern; a test pins both directions.

**Five more that the misspelling fix had blocked.** `pair_from_gulf.py` corrects five misspellings in
Argaam's Arabic, such as "بيع بالتقسط" → "بيع بالتقسيط". Gulf companies' rows are stored with Argaam's
spelling, so the corrected form could never read them back. Each misspelled form is one Argaam line,
matching the Saudi English (tr161, tr1165, tr1111, tr1061, tr1110). They are added as later copies
too: Arabic pages keep the corrected spelling, and English pages read 56 more Gulf rows in English
(AJMANBAN and five other Islamic banks, AMLAK, AMCREIT, DUBAIRES).

**One short form deliberately gets no English:** "إستثمارات أخرى". On 49 Gulf pages Argaam uses it for
both Other Investment Income (tr1255) and Other Investments (tr1289). No Gulf row in today's database
carries it.

**Against the committed `aa3dde6`, English pages change on 56 rows (5 labels), all from Arabic to
English.** None changes its English, and none goes back to Arabic. Against the dictionary before the
merge: 61 labels, 1,758 rows.

**Rendered locally** (`next dev` on this tree, beta's API by tunnel;
`docs/screenshots/arabic-labels-fix-2026-11-04.txt` and the 28 PNGs beside it):
- **English:** the 8 Gulf companies whose pages between them carry all 61 (AMLAK, AJMANBAN, AMCREIT,
  ADCB, 301, 821, BKIC.BH, EAND) at 1440, and AMLAK at 390. **All 72 expected English labels shown.**
- **Arabic:** 1010, 1211, 8010 and 2222 at 1440, and 2222 at 390. **0 English line labels**, and the
  composed labels shown.

**Still in Arabic on English pages (not new; a follow-up):**
- 92.4% of Gulf line rows now show in English (98,257 of 106,356), against 91% before the 129.
- 8,099 rows in 95 labels still show in Arabic, mostly Argaam's spelling and unit variants of lines
  the dictionary knows: "القيمة الاسمية (درهم)", "القيمة الدفترية (دينار كويتي)", "ارباح مبقاة",
  "إجمالي الموجودات".
- Nothing checks this direction, as `check-arabic.mjs` does for Arabic pages.

**Tests:** `web/src/lib/data-labels-content.test.ts`, 4 tests:
- the composed Arabic;
- the eleven read-backs;
- the ambiguous form left unmapped;
- the corrected spellings on Arabic pages.

Web suite 43/43; typecheck and lint clean.

## Release (2026-11-05, on the owner's "Yes, release it")

`5c18a3ae46` (= `rebuild` `5c18a3a`) went to beta, then production, with no commit in between. Against the
previous release `2e44ee6fbf`, the only app change is `web/src/content/data-labels.json`, plus its test.

- **Beta.** The render check from the review fixes, run through the tunnel:
  - 72 of 72 expected English labels on the Gulf English pages;
  - 0 English line labels on the Arabic pages (1010, 1211, 2222, 8010) at 1440 and 390;
  - every panel's row count identical to the local run.
- **Production.**
  - Health is 200 and `BILLING_OPEN=true` is untouched.
  - Financials is Pro-only, so a signed-out browser sees it locked; no account was made.
  - The served code carries the new labels: one chunk, byte-identical to beta's, the same file the public
    site serves (hash-compared). `2e44ee6fbf` had none of them.
  - `check-billing-public.mjs` passes everything.
- **Evidence:** `docs/screenshots/arabic-labels-release-2026-11-05/`.
- **Rollback:** `2e44ee6fbf` is still in both tiers' `releases/`.

## English pages: the Gulf lines still in Arabic (2026-11-06)

This was the follow-up the review fixes left: Gulf companies' statements are stored in Arabic, and lines
the dictionary could not put into English showed in Arabic on English pages. ChatGPT's review 02 named it
the next step.

**Before** (income statement and balance sheet, every Gulf company, all years):
- Live data: 8,085 of 106,300 rows (7.6 %) in 94 labels.
- After the 2026-11-06 publish, which moves F-16's cash flow out of nine balance sheets: 7,510 rows in 76
  labels.

**How each of the 76 got its English:**
- **Argaam's own English for the same row id on the Saudi pages** (row ids are shared across markets).
  This is the 11-04 method. Every label's ids gave one meaning, so none is ambiguous.
- **Units** are the listing's own, never the Saudi riyal, in the dictionary's Gulf style: "Par value
  (dirham)", "Book value (KWD)", "EPS Diluted (QAR)", "Earnings per unit (fils)". KWD, BHD and OMR are new
  to that style.
- **Translated, because Argaam's English names something else:**
  - "الضرائب و التبرعات": "Taxes and donations", not "Taxes and Zakat";
  - "متوسط عدد الوحدات (مليون)": "Average number of units (Million)", not "Shares Outstanding";
  - "القيمه الدفتريه للاصول العائده للوحده": "Book value per unit".
- **Two bank sub-lines** occur only in income statements, under "دخل العمولات الخاصة" / "مصاريف العمولات
  الخاصة". They read "Special commission income from banks & other FIs" and "Special commission expense on
  due to banks & other FIs", not the balance-sheet names their row ids carry.

**What changed and what did not:**
- 76 pairs were added, as one group appended at the end (495 pairs, was 419).
- **No existing mapping changed in either direction.**
- The 27 English labels that are new to the dictionary are used by no Saudi line, so **Arabic pages do not
  change**.
- Each Gulf line sits in the same statement as the Saudi line its English comes from, except the two bank
  sub-lines above.

**After:**
- 0 rows on the after-F-16 data.
- On live data until the publish: 575 rows in 18 labels, every one a cash-flow line inside an F-16
  company's balance sheet.

**Checks:**
- **The other direction now has a check.** `check-data-fixes.mjs` with `SWEEP=1` reads every company's
  statements and fails on any shown line the dictionary leaves in Arabic.
  - It says so instead of counting where statements are Pro-only (production signed out).
  - Run against beta before the publish, it **failed on exactly those 18 cash-flow labels in 8 companies**;
    everything else passed (`docs/screenshots/gulf-english-labels-2026-11-06-sweep-before-publish.txt`).
  - After the publish it is expected to pass. That run is still to do.
- **Rendered:** seven companies, one per market and unit (108 KWD, ABOB OMR, DUBK QAR, GFH.DU on Bahrain,
  ADCB and AJMANBAN AED, AMCREIT fund units), English and Arabic, at 1440 and 390.
  - Every expected English label shown (93 per width).
  - 0 English labels on the Arabic pages.
  - 0 Arabic labels on the English pages, except AMCREIT's 15 cash-flow lines (F-16, until the publish).
  - Evidence: `docs/screenshots/gulf-english-labels-2026-11-06/` and its `.txt`.
- Tests: 5 new; web suite 47/47.

**Left, and why:**
- **Bank income sub-lines that share their text with a balance-sheet line:** "الاستثمارات" (Investments),
  "قروض و سلف" (Loans and advances) and "ودائع العملاء" (Customer Deposits).
  - Under "Special commission income/expense" they mean income from, or expense on, those balances, but
    read as balances in the flat panel.
  - Argaam's own English pages show them bare the same way, for Saudi banks too.
  - The dictionary is keyed by text, so it cannot tell the two uses apart. Fixing it needs the panel to
    look a label up by statement, which is the review's root-cause note ("key by row id").
- **"property Real estate Investment":** an older dictionary entry, odd capitalisation, as on the 108
  balance sheet.
- **At 390 px the table opens on the oldest years** (FY2021–22 on 108), not the newest. Seen in the render;
  not part of the labels.
