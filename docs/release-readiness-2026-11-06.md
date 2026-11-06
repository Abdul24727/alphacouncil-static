# Release readiness, 2026-11-06: candidate `307d2fc` against the deployed `5c18a3ae46`

**Status: ready for the owner's release decision.** This report needs no release and no push. Each release
(beta, then production) and each push is the owner's go-ahead in chat.

- **Deployed now:** `5c18a3ae46` on beta and production (2026-11-05).
- **Candidate:** `rebuild` at `307d2fc`. Commits after it change no app code: records, this report, the
  review loop. So the deploy script may ship a later `rebuild` HEAD whose app code equals `307d2fc`; the
  check is `git diff --stat 307d2fc..HEAD -- web/src api deploy web/messages web/public`, which must be
  empty.
- *(The first candidate, `509d7bf`, was superseded by review 13's phone-table fix. Its evidence stays in
  `docs/screenshots/release-candidate-509d7bf/`: 150 screenshots, not the 130 this report first said.)*
- **Pushed:** `origin/rebuild` is at `ccfe063`. Everything after it is unpushed.

## What a release changes for visitors

All of it is in `web/src`; `api/`, `deploy/`, `web/messages/` and `web/public/` are unchanged.

| Change | Pages | Record |
|---|---|---|
| Gulf statement lines show in English on English pages: 76 labels, 0 of 105,623 Gulf rows left in Arabic once F-16 is published | English Financials, Gulf companies | `docs/arabic-statement-labels-2026-11-03.md`, "English pages" |
| Statement columns newest first, so a phone opens on the newest period | Financials, both languages | `PROJECT.md` §5, 2026-11-06 |
| Bank income sub-lines read as commission income/expense inside the income statement | Financials of banks, both languages | labels doc, "Bank income sub-lines" |
| "property Real estate Investment" reads "Real Estate Investments" | English Financials | labels doc, "property Real estate Investment" |
| On a phone, the line labels stay in place, each period fills the space beside them, and scrolling snaps to whole periods: no figure is shown cut in half | Financials on phones, both languages; desktop unchanged | `PROJECT.md` §5, 2026-11-06 (review 13) |

Arabic pages change only through rows 2, 3 and 5. No existing dictionary mapping changed, apart from the one
intended real-estate label.

## Every file changed since `5c18a3ae46`

All 360 files of `git diff --name-status 5c18a3ae46..307d2fc`: 25 outside `docs/screenshots/` and
`docs/review-loop/`, all named below; 307 evidence files under `docs/screenshots/` (one of them, a corrected
header, is also named below); and 28 review-loop records under `docs/review-loop/`. *(Reconciled with the diff
2026-11-06, after ChatGPT's review 14 found three script files missing from the first list.)*

**App code, which ships with a release (5 files):**
- `M web/src/content/data-labels.json`: 76 English-page pairs; `in_statement` (5 bank sub-lines); the garbled
  real-estate pair becomes an alias.
- `A web/src/lib/data-labels-core.ts`: the lookup, with no imports, taking an optional statement.
- `M web/src/lib/data-labels.ts`: now `makeDataLabel(data)`; same import path for every caller.
- `M web/src/lib/statement-period.ts`: `statementColumns()` newest first; `phoneColumnWidth()`, the phone
  width rule.
- `M web/src/components/stock/research-panels.tsx`: the statement table passes its statement to
  `dataLabel`; sticky label column; on a phone, measured period widths with snap scrolling.

**Tests, which ship but do not run on the server (3 files):**
- `A web/src/lib/data-labels-core.test.ts`;
- `M web/src/lib/data-labels-content.test.ts`;
- `M web/src/lib/statement-period.test.ts`.

**Check scripts (4 files):**
- `M web/scripts/check-data-fixes.mjs`: the English-label sweep;
- `A web/scripts/lib/label-sweep.mjs` and `A web/scripts/lib/label-sweep.test.mjs`: the sweep fails closed;
- `M web/scripts/check-advisors.mjs`: two INFO lines were blind to the chips and fault lines.

**Pipeline tooling, not part of the web release (6 files under `scripts/argaam_ar_labels/`):**
- `A argaam_pages.py`: the page reading the two pairing scripts share (`page_rows()`, `norm()`, `ROW_ID`).
- `M pair_from_gulf.py`: the dollar as a currency unit, and it uses `argaam_pages.py`.
- `M pair_labels.py`: it uses `argaam_pages.py`, and its `--ar-dir` usage is marked superseded.
- `M harvest_ar_statements.py`: docstring only, marked superseded (do not run).
- `A test_pair_from_gulf.py`: the unit rule's tests.

**Review loop tooling (1 file):** `A scripts/review-loop/ask_chatgpt.py`.

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
  counted among the 307 evidence files.

**Evidence and review records:**
- 307 files under `docs/screenshots/`, the folders this report and the labels doc cite;
- 28 under `docs/review-loop/`: the master plan, outputs, replies and log.

## Checks on the candidate (`307d2fc`), all run together on 2026-11-06

Run after the last change, so no later step can have broken an earlier one.

**Static checks:**
- `npm test` 66/66; `tsc --noEmit` exit 0; `npm run lint` exit 0; `npm run build` passes (93/93 pages).
- `python -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py`: OK (4 tests).

**Rendered:** local web against beta's API, beta's data being before the F-16 publish. Evidence is in
`docs/screenshots/release-candidate-307d2fc/`: 150 screenshots, plus one `.txt` per check (7).

| # | Check | Covers | Result |
|---|---|---|---|
| 1 | 2026-11-04 label set (`labels-fix-check.mjs`) | Arabic 1010, 1211, 8010, 2222; English AMLAK, AJMANBAN, AMCREIT, ADCB, 301, 821, BKIC.BH, EAND | PASS, every expected label; 0 English labels on Arabic pages |
| 2 | Gulf English pages | 108, ABOB, DUBK, GFH.DU, ADCB, AJMANBAN, AMCREIT; en + ar; 1440 + 390 | PASS, every expected label |
| 3 | Newest first | 108, 2222; en + ar; 1440 + 390; 16 panels | PASS: newest beside the labels on load, oldest reachable |
| 4 | Bank sub-lines | ADCB, 1010; both panels; en + ar; 1440 + 390 | PASS 16/16, with values equal to the API's row by row |
| 5 | Real-estate label | 108, 1211; en + ar; 1440 + 390 | PASS 8/8, with values equal to the API's |
| 6 | `check-arabic.mjs` with `WIDTHS=1440,390` | 48 Arabic page views signed out, including `/t/2222/financials` | 0 English strings outside the allow-list |
| 7 | Phone gap (review 12) and phone tables (review 13) | English income + balance for 301, 821, BKIC.BH, EAND; Arabic income + balance for 8010; Arabic income for 1211; 11 panels at 390 | PASS 11/11: expected labels shown; **every cell in every column** equal to the API's; newest in view on load; scrolled to the end, the oldest in view **beside the labels, which stay in view**; **no period shown cut**, on load, at every column step or at the end (`7-phone-gap.txt`, `phone-gap/`). Run on the previous commit, the same check fails 9 of the 11, so it does catch the defect. |

**What is still Arabic on English pages, and where:**
- In the rendered samples, the only Arabic left is the cash-flow lines inside AMLAK's and AMCREIT's balance
  sheets: 15–16 per panel, every one a cash-flow line.
- These are samples. The **full sweep** over all 714 companies
  (`docs/screenshots/gulf-english-labels-2026-11-06-sweep-failclosed.txt`) found **18 such labels across
  eight companies**: ADAV.AD, AMCREIT, AMLAK, DSI, DUBAIRES, EMSTEEL, QIC and UPP. All of them are F-16's
  cash-flow lines in a balance sheet, and no other label is left.
- They are **expected** to go with the 05:00 UTC publish, and that is **unverified** until the
  after-publish checks below have run. *(Corrected 2026-11-06 by ChatGPT's review 08: this paragraph read as
  if the two rendered companies were all of it, and as if the publish had already removed them.)*

**On production after a release:** Financials is Pro-only there, so a signed-out check cannot render it. As
on 2026-11-05, production is checked through its served code: the new chunk byte-identical to beta's, and
hash-equal on the public site. Then `check-billing-public.mjs`, health, and `BILLING_OPEN` unchanged.

**Inspected by eye:** all 11 phone panels on load, and the 9 that scroll in their scrolled state. They were
put side by side on contact sheets, with a sample of the 1440 panels for comparison. The desktop layout is
unchanged. *(Review 13 found that only two of the phone panels had been looked at before.)*

**Seen on the phone screenshots, left for review:**
- 821's English income statement shows "income from investments & Other operating income". That is
  Argaam's own English, with a lowercase first word, through the dictionary, like the real-estate label
  fixed today.
- *(Fixed in `307d2fc`: scrolled to its oldest year, a phone table used to scroll the line labels out of
  view and show a period cut in half beside them.)*

## Still pending, and not a reason to wait

**F-16's check after the publish** (2026-11-06 05:00 UTC). On `/var/lib/alphacouncil/screening.sqlite`,
read-only:
1. The nine companies' balance sheets hold no cash-flow line (ADAV.AD, ADNIC, AMCREIT, AMLAK, DSI,
   DUBAIRES, EMSTEEL, QIC, UPP).
2. Eight of them have a "Cash Flow Statement"; ADNIC's held-back lines carried no figures.
3. The night's parse log shows no "UNKNOWN STATEMENT HEADING" line.
4. `check-data-fixes.mjs` `SWEEP=1` against beta now passes the English-label sweep, 714/714 read. Before
   the publish it failed only on F-16's 18 labels.

**Optional, by the same pattern as 2026-11-05:** re-render AMLAK's and AMCREIT's balance sheets on beta
after the publish.

**Release order** (`CLAUDE.md`, `PROJECT.md` §4): `scripts/deploy-staging.sh`, then check beta, then
`scripts/deploy-production.sh` with no commit in between, then check production. The rollback is
`5c18a3ae46`, still in both tiers' `releases/`.
