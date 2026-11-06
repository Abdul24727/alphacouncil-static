# Release readiness, 2026-11-06: candidate `509d7bf` against the deployed `5c18a3ae46`

**Status: ready for the owner's release decision.** This report needs no release and no push. Each release
(beta, then production) and each push is the owner's go-ahead in chat.

- **Deployed now:** `5c18a3ae46` on beta and production (2026-11-05).
- **Candidate:** `rebuild` at `509d7bf`. Commits after it change no app code: records, this report, the
  review loop. So the deploy script may ship a later `rebuild` HEAD whose app code equals `509d7bf`; the
  check is `git diff --stat 509d7bf..HEAD -- web/src api deploy web/messages web/public`, which must be
  empty.
- **Pushed:** `origin/rebuild` is at `ccfe063`. Everything after it is unpushed.

## What a release changes for visitors

All of it is in `web/src`; `api/`, `deploy/`, `web/messages/` and `web/public/` are unchanged.

| Change | Pages | Record |
|---|---|---|
| Gulf statement lines show in English on English pages: 76 labels, 0 of 105,623 Gulf rows left in Arabic once F-16 is published | English Financials, Gulf companies | `docs/arabic-statement-labels-2026-11-03.md`, "English pages" |
| Statement columns newest first, so a phone opens on the newest period | Financials, both languages | `PROJECT.md` §5, 2026-11-06 |
| Bank income sub-lines read as commission income/expense inside the income statement | Financials of banks, both languages | labels doc, "Bank income sub-lines" |
| "property Real estate Investment" reads "Real Estate Investments" | English Financials | labels doc, "property Real estate Investment" |

Arabic pages change only through rows 2 and 3. No existing dictionary mapping changed, apart from the one
intended real-estate label.

## Every file changed since `5c18a3ae46`

From `git diff --name-status 5c18a3ae46..509d7bf`, grouped. The full list is reproducible with that command.

**App code, which ships with a release (5 files):**
- `M web/src/content/data-labels.json`: 76 English-page pairs; `in_statement` (5 bank sub-lines); the garbled
  real-estate pair becomes an alias.
- `A web/src/lib/data-labels-core.ts`: the lookup, with no imports, taking an optional statement.
- `M web/src/lib/data-labels.ts`: now `makeDataLabel(data)`; same import path for every caller.
- `M web/src/lib/statement-period.ts`: `statementColumns()` newest first.
- `M web/src/components/stock/research-panels.tsx`: the statement table passes its statement to `dataLabel`.

**Tests, which ship but do not run on the server (3 files):**
- `A web/src/lib/data-labels-core.test.ts`;
- `M web/src/lib/data-labels-content.test.ts`;
- `M web/src/lib/statement-period.test.ts`.

**Check scripts (4 files):**
- `M web/scripts/check-data-fixes.mjs`: the English-label sweep;
- `A web/scripts/lib/label-sweep.mjs` and `A web/scripts/lib/label-sweep.test.mjs`: the sweep fails closed;
- `M web/scripts/check-advisors.mjs`: two INFO lines were blind to the chips and fault lines.

**Pipeline tooling and patches** (not part of the web release; the server's parser was changed separately,
on the owner's go-ahead):
- `M scripts/argaam_ar_labels/pair_from_gulf.py` (the dollar unit) and
  `A scripts/argaam_ar_labels/test_pair_from_gulf.py`;
- `A docs/pipeline-guard-statement-headings-2026-11-06.patch` (applied 2026-11-05 22:44 UTC) and its
  guard-only variant, with `A docs/pipeline-guard-statement-headings-2026-11-06.md`.

**Review loop:**
- `A scripts/review-loop/ask_chatgpt.py`;
- `A docs/review-loop/` (master plan, outputs 01–06, replies 01–06, log).

**Records and evidence:**
- `M PROJECT.md` and `M docs/arabic-statement-labels-2026-11-03.md`;
- `M docs/screenshots/launch-2026-10-27/advisors-signed-in/check-advisors.txt` (a corrected header);
- added evidence under `docs/screenshots/`: `arabic-labels-release-2026-11-05/`, `check-advisors-info-2026-11-06/`,
  `gulf-english-labels-2026-11-06/` with its three `.txt` files, `statements-newest-first-2026-11-06/`,
  `bank-sublines-2026-11-06/`, and `real-estate-label-2026-11-06/`.

## Checks on the candidate (`509d7bf`), all run together on 2026-11-06

Run after the last change, so no later step can have broken an earlier one.

**Static checks:**
- `npm test` 64/64; `tsc --noEmit` exit 0; `npm run lint` exit 0; `npm run build` passes (93/93 pages).
- `python -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py`: OK (4 tests).

**Rendered:** local web against beta's API, beta's data being before the F-16 publish. Evidence is in
`docs/screenshots/release-candidate-509d7bf/`: 130 screenshots, plus one `.txt` per check.

| # | Check | Covers | Result |
|---|---|---|---|
| 1 | 2026-11-04 label set (`labels-fix-check.mjs`) | Arabic 1010, 1211, 8010, 2222; English AMLAK, AJMANBAN, AMCREIT, ADCB, 301, 821, BKIC.BH, EAND | PASS, every expected label; 0 English labels on Arabic pages |
| 2 | Gulf English pages | 108, ABOB, DUBK, GFH.DU, ADCB, AJMANBAN, AMCREIT; en + ar; 1440 + 390 | PASS, every expected label |
| 3 | Newest first | 108, 2222; en + ar; 1440 + 390; 16 panels | PASS: newest beside the labels on load, oldest reachable |
| 4 | Bank sub-lines | ADCB, 1010; both panels; en + ar; 1440 + 390 | PASS 16/16, with values equal to the API's row by row |
| 5 | Real-estate label | 108, 1211; en + ar; 1440 + 390 | PASS 8/8, with values equal to the API's |
| 6 | `check-arabic.mjs` with `WIDTHS=1440,390` | 48 Arabic page views signed out, including `/t/2222/financials` | 0 English strings outside the allow-list |

The only Arabic text left on English pages in these runs is the cash-flow lines inside AMLAK's and
AMCREIT's balance sheets: 15–16 per panel, every one a cash-flow line. That is F-16, which the 05:00 UTC
publish removes. Nothing else is left.

**On production after a release:** Financials is Pro-only there, so a signed-out check cannot render it. As
on 2026-11-05, production is checked through its served code: the new chunk byte-identical to beta's, and
hash-equal on the public site. Then `check-billing-public.mjs`, health, and `BILLING_OPEN` unchanged.

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
