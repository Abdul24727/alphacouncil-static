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
- **284 English labels paired.** `merge_pairs.py` added the **129** the dictionary lacked; 85 were
  already identical. **70 differ from the dictionary and were left as the dictionary has them**,
  mostly spelling (the dictionary's hamzas and ة against Argaam's "إجمالى", "مبقاه"), a few more
  specific ("مطلوبات أخرى" where Argaam says "اخرى").
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
