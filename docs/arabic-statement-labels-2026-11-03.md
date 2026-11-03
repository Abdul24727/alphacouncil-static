# Arabic line labels for Saudi statements, from Argaam's own Arabic pages

2026-11-03. Owner's choice in chat: **"Harvest Argaam Arabic"**, over translations drafted here.
Nothing in this document has been run against Argaam with the signed-in session yet: that is the
go-ahead it asks for.

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
