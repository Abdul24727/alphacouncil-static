# Response to the beta QA audit, run 2 (2026-10-17)

Every FAIL row in run 2, with what was done. Fixes are on `rebuild` (`af9aca8` … `61e6d35`) and deployed to beta.alphacouncil.tech. "Verified" means checked on staging after the deploy. Screenshots are in `screenshots/qa-run2/`.

## Fixed

| # | Finding | Cause | Fix | Verified |
|---|---|---|---|---|
| 1e (major) | Ownership tab shows a raw JSON dump; a date repeats in the series | The panel was a placeholder written before the pipeline collected ownership; it now has data for 670 tickers. The pipeline repeats some days (261 tickers). | A real panel: foreign ownership (current, limit, as of, a daily trend line), major holders, recent changes, each with a labelled empty state. One point per day; holder rows without a name ("0.00 %") dropped. Known institutions (Kingdom of Saudi Arabia, PIF, GOSI, QIA…) shown in the page's language. | `ownership-{en,ar}-{1440,390}.png`; brand fonts only (Phase 1 and 7) |
| 5f | AFNIC header shows a price with no "As of" | The database has no date for AFNIC's price (no price file; the briefs row is undated) | The header says "Price date unknown" at every width | `afnic-header-{1440,390}.png` |
| 7d | Answer with figures but no citation (METH.AD) | The model sometimes leaves figures untagged | After each answer the server lists sentences that quote a figure without a tag, with the tag of where the figure was read (attached panel, else database); the chat adds the chip. A figure no source shows gets no tag. A tag written after the full stop counts for its sentence. | METH.AD answer cites P1 and DB; API tests |
| 7e | Answer contains "Let me also check the ticker overview…" | The model writes text before calling a database tool | Text written in the same step as a database lookup is shown in the collapsible steps, not in the answer; the prompt asks for nothing before or between tool calls | AFNIC answer has no narration (3 questions re-asked) |
| 7f | Copilot slower than run 1 | OpenRouter's default host for DeepSeek was often slow (1.7 s to first token, 47 tok/s), and the model answered from the panel first, then looked data up and answered again | Hosts sorted by latency (`COPILOT_PROVIDER_SORT=latency`, default); the page ticker's overview, dividends and fundamentals are read before the model's first turn (about 2,500 tokens) | See the timing table below |
| 8a, 8b | English on Arabic pages: news headlines, chart tooltip "Charting by TradingView", "English version" | Items stored in English; library and link labels | An English news item shows our stored Arabic summary when there is one (7 of Aramco's 10); the rest keep the English headline, tagged "بالإنجليزية". Chart tooltip and the legal pages' language link are in the page's language. | `news-ar-2222-{1440,390}.png`; Phase 7: 0 English strings |
| 8c | English home: all 8 news items Arabic-only | The newest 200 stored items are all Arabic | The market feed shows items readable in the page's language first, from the whole archive (English headline, or English summary); the latest Arabic-only items are not shown to English readers | `home-news-en-{1440,390}.png`: 10 English items, newest 8 Oct |
| 9e (major) | Holding/alert ids are small and sequential | A running count shared by every account | New accounts, holdings and alerts get random 32-bit ids (still integers, so the API is unchanged); lists keep the order items were added. Existing rows keep their ids (qa1's 25, 29 and alert 1). Ownership was already checked on every read and delete. | API test: no two new ids are neighbours |

### Copilot timing (same questions, 1440 px, signed in)

| Question | Run 2: first word / full | Now: first word / full |
|---|---|---|
| Q1 2222 "Is the dividend safe?" | 2.4 s / 22.7 s | 1.9 s / 16.3 s |
| Q4 AFNIC last close and 1-month return | 12.5 s / 22.5 s | 3.4 s / 5.8 s |
| Q5 METH.AD EV/EBITDA and yield | 3.3 s / 32.4 s | 1.9 s / 11.0 s |

Times vary from run to run: the Phase 4 check's own dividend question took 32 s on the final build, while Phase 7 was loading the site at the same time.

Host ordering was measured on the deployed engine (two rounds each): latency 11–19 / 3.5–4.3 / 12 s full; throughput 79–86 / 8–17 / 10–18 s; OpenRouter's default 27–87 / 21 / 12–15 s.

## Checks after the fixes

- Full run of `check-all.mjs` on `0162175`: Phases 1-7 all pass (`screenshots/check-all-staging.txt`). API peak 499 MB of 2 GB, no swap, no worker restarts, no 5xx, no proxy failures.
- Final build `61e6d35` (prompt wording, Ownership table padding): Phase 4 and Phase 7 rerun and pass, 88 page views, 0 English strings on Arabic pages (`screenshots/check-phase4-7-61e6d35.txt`).
- Known: DeepSeek still sometimes quotes field names ("null", "na_sector") despite the prompt asking it not to. It is not a QA finding; the figures and citations are correct.

## Not tested in run 2, now covered

| Item | Coverage |
|---|---|
| Cross-account DELETE of another user's holding or alert | API test `test_one_account_cannot_change_anothers_holdings_or_alerts`: the DELETE by id changes nothing and the owner keeps both |
| Signed-out PUT /me/prefs and DELETE holdings/alerts | API test `test_signed_out_calls_never_answer_401`: every protected endpoint answers 403 signed out |

## By design (no change)

| # | Finding | Why |
|---|---|---|
| 1b | No sidebar at 390 px | The plan's phone layout: a bottom tab bar, and Copilot as a full-screen sheet. |
| 2b | BRAND.md is not served | It is a repository document (`BRAND.md` at the repo root). Give the file to the QA agent to compare tokens; run 2 found no banned colour, gradient, font or emoji on 148 page loads. |
| 5f (P/E) | AFNIC P/E n/a next to EPS 65.81 | No P/E is stored for AFNIC. Dividing by a price with no date would be an estimate, which the rules forbid. |
| 8a (part) | "Ctrl K" and the model name "deepseek/deepseek-v3.2" on Arabic pages | Key names as printed on keyboards, and the model's product name. |
| 9b | Signed-out app pages answer 200; APIs answer 403, not 401 | The pages show a sign-in prompt and no account data. 403 is deliberate: a 401 makes Chrome drop the staging-gate login (run 1's 9c, now PASS). |

## Needs your decision

| # | Finding | What is needed |
|---|---|---|
| 10b (blocker) | No Moyasar checkout | Your plan for existing subscribers, the Pro feature list (10c), and Moyasar test keys put on the server by you. |
| 10c | Pro placeholder on /pricing | Pro's features. |

## Data limits (pipeline)

- English news is scarce: none of the newest 200 stored items has English text, so the English home feed is about a week older than the Arabic one.
- Holder names are stored in one language; people's names are shown as stored (only known institutions are translated).
