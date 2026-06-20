# AlphaCouncil — AUDIT-FINDINGS.md

Independent QA audit against the **live site** (https://alphacouncil.tech). Governing rules: `constitution.md` (real data only, nothing half-baked, evidence-based DoD). Prior "done/passing" claims are **not trusted** — every page re-verified from scratch.

- **Frontend workspace:** `C:\projects\alphacouncil-static` (static HTML + inline scripts; `adviser-core.js`, `js/api.js`, `js/i18n.js`; deployed to VPS `/opt/alphacouncil/static-v2`, now served at root).
- **Backend:** `C:\projects\alphacouncil\llm-council\backend` (FastAPI; VPS `alphacouncil-backend.service`).
- **Out of scope (founder directive):** payments / billing / Tap / Stripe — not touched.
- **Test harness:** Playwright (`npx playwright test`), live-site target, QA account in gitignored `.env.test`.

## Real-ticker test set
- **Tadawul (SAR):** 2222 (Aramco), 1120 (Al Rajhi), 2010 (SABIC), 7010 (STC), 1180 (SNB), 7020 (Mobily), 4321
- **ADX (AED):** ALDAR, FAB, ADCB, IHC, ADIB
- **DFM (AED):** EMAAR, DIB, DU, TALABAT, AIRARABIA
- **Genuinely-missing data:** POLTRY_BSE (all fundamentals `not_available`), INOVEST_BSE (partial)
- **Bad ticker:** ABRAAJ_BSE (listed in screening but fundamentals 404), ZZZZ_TADAWUL (fully invalid)

## Severity key
- **blocker** — broken core flow, fabricated data shown as live, crash/console error on a main path, security-looking control that secures nothing.
- **major** — a control that doesn't work / claims persistence it lacks, real data not populating, state lost on reload/nav, wrong currency/locale, failed network request.
- **minor** — cosmetic, copy, edge-case polish. (Left under NEEDS FOUNDER REVIEW if ambiguous.)

---

# ROUND 1

_Started 2026-06-20. Status: in progress._

## Findings

### Environment / orientation
- Session opened in the **stale Documents husk** (`C:\Users\Abdul\Documents\THE project\…`) which holds only an empty `.claude/` folder. Real work: frontend `C:\projects\alphacouncil-static` (git `master`), backend `C:\projects\alphacouncil` (git `main`). Live root = nginx `root /opt/alphacouncil/static-v2`. Constitution read from `C:\Users\Abdul\Downloads\constitution.md`.
- Prior suite baseline (live): **72 passed / 1 failed** (thesis-auth). Not the "55 green" claimed.

### R1-01 — stock-detail.html ships fabricated data on every page — **BLOCKER** — FIXED
- **Repro:** open `/stock-detail.html?ticker=EMAAR_DFM` (any non-Aramco). Header logo shows `2222`; subtitle `2222.SR · Energy · Saudi Arabia · Large Cap`; day-change `+0.45 (+1.58%)`; freshness `Updated 2 min ago`. None are updated by JS (confirmed in live served HTML + source: no JS writer for `.stock-logo/.stock-subtitle/.stock-change/.stock-updated`).
- **Repro 2 (worse):** open `/stock-detail.html?ticker=ZZZZ_TADAWUL` (invalid) or any ticker whose summary fetch fails → page falls back to hardcoded **Saudi Aramco** header + a full fabricated **12-dimension thesis** (7.8/10, "ROE 32.1%", "PIF 98% stake") + fabricated council snapshot. Root cause: `loadRealStock` catch did `console.warn(...); return;` leaving hardcoded markup.
- **Fix:** neutralized static header/title/breadcrumb/context/chat-intro; removed the `stocksDatabase` mock + fabricated static thesis grids + fabricated council text; `loadThesis()` now runs at init (strips placeholders, no flash); `loadRealStock` populates logo/subtitle(real sector+country)/price/day-change(`day_change_pct`)/freshness(`as_of_date`) from the real summary and shows an honest **"Stock not found"** state on failure/invalid ticker.

### R1-02 — `Sample-Dashboard.html` publicly served fabricated dashboard — **BLOCKER** — FIXED
- **Repro:** `GET https://alphacouncil.tech/Sample-Dashboard.html` → 200. Fully fabricated ("Good morning, Sami", SAR 847,250, 32.2% banking, **canned interactive AI chat** returning fake analysis). Linked from 7 "View sample dashboard" CTAs on index/features/how-it-works/markets.
- **Fix:** removed the 7 CTAs and deleted the file. (Whether to build an *honest* labeled sample → NEEDS FOUNDER REVIEW.)

### R1-03 — stock-detail fundamentals 404 → console error for screening-listed tickers — **MAJOR** — ✅ FIXED
- **Repro:** `/stock-detail.html?ticker=ABRAAJ_BSE` (in `/api/screening`, summary 200) → `GET /api/ticker/ABRAAJ_BSE/fundamentals` **404** → console error + failed request (DoD violation). POLTRY_BSE (also no fundamentals) returns honest **200-with-nulls** — backend is inconsistent. Page renders honest "—" visually; only the 404 is the defect.
- **Planned fix:** backend `/fundamentals` returns 200 honest-empty for a valid ticker lacking a fundamentals row (consistent with POLTRY).

### R1-04 — portfolio.html ships orphaned fabricated markup — **MAJOR** — ✅ FIXED
- Orphaned `#councilModal` (hardcoded "32.2% banking / SABIC 7.2% / Saudi 51.6% / 5.8/10") + `#adjustModal` + `holdingsData` mock (Aramco 5470 @ 25.40 …) + dead `openAdjustModal/confirmAdjust` + 7 static fabricated `<tr>` holding rows + per-row tx-history. **Not shown** to users (real `onPortfolioReady` overwrites `#holdingsBody`; `openCouncilModal` builds a separate `councilModalOverlay` with a real `/api/adviser/council/ask`; modal-overlay is `opacity:0`) — but fabricated financial content is shipped in the page (rule 2) and flashes pre-hydration.
- **Planned fix:** remove the orphaned modals/mock/handlers; neutralize static metric literals + holding rows.

### R1-05 — stale "Action completed" toast visible by default on portfolio — **MAJOR** — ✅ FIXED
- Full-page screenshot (authed + anon) shows a large "Action completed / Your request has been processed" toast rendered at page bottom with no action taken.

### R1-06 — dead `href="#"` links — **MAJOR** — ✅ FIXED
- forgot-password.html (3 visible), onboarding.html (1), stock-detail.html (1). (news.html's 12 static `#` links are replaced by the real feed render — not user-reachable.)

### R1-07 — settings.html ships fake identity defaults — **MINOR** — ✅ FIXED
- `<input id="firstName" value="Saeed">` / `<input id="lastName" value="Al-Khalidi">`. `loadProfile()` clears+fills from `/auth/me`, but the fake names ship in markup and flash before the async fetch (and the B1 nav check only scanned "SK"/"Sami").

### R1-08 — thesis-auth regression test is brittle — ✅ FIXED (reconciled)
- Test asserts anon `POST /api/thesis/2222 {}` is 200/404 (public cached read). Backend keys the cache on `(model, as_of_date)`; `as_of_date` rolls forward nightly so pre-generated theses go stale → cache miss → anon **401** (by design). The UI handles 401 honestly ("Please log in to generate an AI thesis"); no page-load fetch. So the failure is a brittle assumption, not a user defect.
- **Planned:** reconcile the test to assert the real security invariant; flag the product nuance (logged-out visitors effectively never see a pre-generated thesis) for founder review.

### Verified-OK (audited, no defect)
- Missing-data ticker **POLTRY_BSE**: honest page — real name/BHD price/real price chart, empty gauges, CTAs. ✓
- Anon dashboard/portfolio: honest empty states + "sign in" prompts; `SAR 0` not `847,250`. ✓ (residual: 401 console noise — see NEEDS FOUNDER REVIEW)
- scenarios.html `847,250`/`32.2%` Before-After block is **not rendered** (hidden); not shown to users. (Dead markup — low priority.)
- Marketing platform numbers, currency pegs, alerts/news real feeds: consistent with prior tests.

---

## ROUND 1 — fixes applied, deployed & verified
- **Frontend commits:** `32d6b47` (main fixes), `f89227e` (follow-up). Deployed to VPS `/opt/alphacouncil/static-v2` (backup in `static-v2/_qa_backup_round1/`).
- **Backend:** `frontend_api.py` fundamentals fix deployed by scp (backup `frontend_api.py.qa_bak_round1`) + `systemctl restart alphacouncil-backend` (import-checked first; `{"status":"ok","tickers":716}`). NOTE: the backend repo has 8 unpushed commits + unrelated uncommitted changes from prior sessions — I deployed ONLY the single fundamentals function (diff-verified it was the sole delta vs live) and did **not** touch that backlog → see NEEDS FOUNDER REVIEW.
- **Regression tests (live):** `tests/round1-fixes.spec.js` 7/7 green; `tests/thesis-auth.spec.js` green. Raw:

```
==BEGIN round1-fixes==
  ok 1 R1-01 stock-detail: real header, no fabricated change/freshness/thesis (6.7s)
  ok 2 R1-01b stock-detail: invalid ticker shows honest not-found, no Aramco fabrication (4.7s)
  ok 3 R1-02 Sample-Dashboard fabrication removed + no CTA references (576ms)
  ok 4 R1-03 fundamentals: briefs-known ticker without stocks row → 200 honest-empty (not 404) (209ms)
  ok 5 R1-04 portfolio: no fabricated 32.2% council / stale toast / 847,250 (authed) (5.9s)
  ok 6 R1-06 dead links resolved (277ms)
  ok 7 R1-07 settings: no Saeed/Al-Khalidi identity defaults (95ms)
  7 passed (19.6s)
==END round1-fixes==
```
- **Live spot-checks:** stock-detail served HTML 0 fabricated literals; ABRAAJ_BSE `/fundamentals` → 200 (real P/E 70.13 from scraped ratios); 2222 → 200; ZZZZ → 404; portfolio served HTML 0 of {847,250, councilSynthesis, Action completed}; index 0 "View sample dashboard".

Status per finding: R1-01 ✅ · R1-02 ✅ · R1-03 ✅ · R1-04 ✅ (shown-to-user parts; residual dead `#adjustModal`/`holdingsData`/canned-`processChat`-tail are unreachable — flagged) · R1-05 ✅ (toast removed) · R1-06 ✅ · R1-07 ✅ · R1-08 ✅ (test reconciled).

### New minor finding (R1-09) — anon viewing a PUBLIC stock-detail page fires authed calls → 401 console noise
- stock-detail is meant to be anon-viewable, but it calls watchlist/position/holdings endpoints that 401 for logged-out visitors → 3 console errors. Authed users are clean. Fix = skip the authed calls when not signed in. Folded into the anon-handling item below.

---

# ROUND 2

_Started 2026-06-20. Focus: mobile/responsive, AR↔RTL rendering, per-page console health, and control coverage (the existing 73-test suite already exercises most controls + real-data/honest-empty behavior per page)._

## Findings
- **Mobile/responsive (390×844, all 15 key pages):** zero horizontal overflow (overflow=0px everywhere), zero console errors, zero failed requests, zero page errors. No responsive defects found. Evidence: `test-results/_audit_round2_mobile.json` + `test-results/screens/r2-mobile-*.png`.
- **AR↔RTL (Arabic preference preset):** marketing pages (index/pricing/markets/methodology…) and app pages render `dir=rtl lang=ar` with Arabic content and zero console errors. Evidence: `test-results/_audit_round2_ar.json` + `r2-ar-*.png`.
- **Existing suite** already covers, per page, that controls work + real data renders + honest empty states (alerts filters/rules/chat, scenarios analyze, onboarding import, council-history empty, dashboard/portfolio/stock-detail, auth flows, marketing numbers, currency pegs, i18n). No new blocker/major found in Round 2.

### R2-01 — auth + onboarding pages are English-only — **MINOR → NEEDS FOUNDER REVIEW**
- login.html / signup.html / forgot-password.html / reset-password.html **and onboarding.html** include no `js/i18n.js`, no `.lang-toggle`, no `data-i18n`. A visitor who set Arabic elsewhere lands on these in English/LTR. Not a broken control (no toggle to fail) and no incorrect AR labels — an i18n *scope* gap, like the intentionally-deferred legal.html. The language toggle lives in the main app, and the signup→onboarding flow is pre-toggle, so EN-only is internally consistent. Listed under review.

**Round 2 result: clean — no new blocker/major items.**

---

# ROUND 3 — exhaustive adversarial audit (multi-agent) + fixes

_Started 2026-06-20. A 12-page adversarial audit (independent agents: source-trace + live-API + locale + honest-empty, then per-finding verification) surfaced **12 confirmed blocker/major defects the instrument-based Rounds 1-2 missed** — mostly **interaction bugs** (chat double-wiring, dead filters/toggles/cards, error/empty paths) and **fabrications outside the earlier fake-literal scan**. Marketing-static, dashboard, portfolio, stock-detail re-confirmed CLEAN._

## Findings (all FIXED unless noted) — commit `f92b3a8`, deployed, `tests/round3-fixes.spec.js` 11/11 green
- **R3-B1 (BLOCKER) council-history "Trends Across Reviews"** — hardcoded fabricated per-user analytics ("4 of your last 6 reviews", "7.1→7.4", "Al Rajhi 8.1/10", "SABIC declined 0.5"), never overwritten, shown to every user incl. zero-review/anon. → honest empty-state. ✅
- **R3-B2 (BLOCKER) council-history AI chat** — double-wired (adviser-core real + inline canned), emitted fabricated "stc +0.6 / FAB +0.4 / QNB +0.3" + duplicate "SK" bubble. → removed inline canned handler; real adviser only. ✅
- **R3-B3 (BLOCKER) settings AI chat** — same double-wire emitting canned "All data is encrypted…" + duplicate "SK". → removed inline canned handler. ✅
- **R3-M1 (major) index thesis-dimension/markets contradiction** — "11 Thesis Dimensions" + "7 GCC Markets" vs 12/6 everywhere. → 12 / 6 (+ js/api.js comment). ✅
- **R3-M2 (major) reset-password "[object Object]"** on invalid/expired token (err.detail was the body object). → err.message honest text. ✅
- **R3-M3 (major) news fabricated PIF/Aramco featured story** — flashed every load + persisted on empty/error (renderFeatured only ran on success). → honest loading/empty on all paths; real story on success. ✅
- **R3-M4 (major) council-history dead Date/Sort selects** — read but never applied. → real date-range + sort (newest/oldest, analyst-perspectives via data-created/data-analysts); removed unbacked "Highest conviction" option. ✅
- **R3-M5 (major) scenarios Structured-Trades dead-end** — no consumer. → "Analyze trades" builds an NL scenario and routes to the real adviser. ✅
- **R3-M6 (major) scenarios "Compare Multiple" placebo** (toggle + toast, no logic). → removed. ✅
- **R3-M7 (major) settings fake "SK" profile avatar** — hardcoded identity. → real initials from /auth/me (neutral if none). ✅
- **R3-M8 (major) settings 3 dead "Methodology & Data" cards** (role=button, no handler). → all 4 open methodology.html + keyboard-activatable. ✅
- **R3-M9 (major) onboarding "+NaN%" P&L** for uploaded holdings (no price) + force-green. → guarded "—" + sign-based color. ✅
- **R3-M10 (major) alerts fabricated header/tab counts** ("12 active / 3 new today / 12·3·5") persisted on anon/error. → neutralized + reset on empty/catch; 401→honest sign-in copy. ✅
- **Also neutralized (flash-risk fabrication):** council-history static demo review cards + the detail-modal static template ("June 14 / 7-perspective / Al-Rajhi/SABIC/stc"); settings email default `saeed.khalidi@example.com`. ✅

**Round 3 result: 3 blockers + 10 majors fixed, deployed, regression-tested.**

## Round 3 re-verification (adversarial, 11 pages) — found 2 more of the same class, now FIXED
A full adversarial re-verification confirmed all 11 pages' fixes held + functionality intact, and surfaced 2 more "fabricated count not reset on the anon/error path" defects (the class behind R3-M10), now fixed:
- **R3-V1 (major) council-history stats row** — "12 / 2 days ago / 7 / 5" persisted on anon/401 (setStats only runs on success). → 4 literals neutralized to "—" (setStats fills on success; anon/error stays honest "—"). ✅
- **R3-V2 (major) alerts AI-adviser greeting** — static "You have **3** high-priority alerts" contradicted the neutralized counts. → generic honest greeting, no count. ✅
- Commit `544d0ba`; regression `tests/round3-fixes.spec.js` now 13/13 green. A targeted re-verification of both fixed pages returned **CLEAN**; a comprehensive count-class sweep across all pages found no remaining unhandled instance (other numeric literals are accepted marketing facts/mockups or JS-overwritten + already tested).
- _Non-blocking note:_ council-history suggested-question buttons are double-bound (inline onclick + JS listener); harmless (2nd call no-ops on the cleared input).

**FINAL: zero open blocker/major across Rounds 1-3 + re-verification. Remaining items are all under NEEDS FOUNDER REVIEW.**

---

## NEEDS FOUNDER REVIEW (ambiguous / cosmetic / out-of-scope)
- **R3-m2 methodology example scale:** the "Example Score Breakdown" uses a 0-100 scale while the framework text says dimensions are "1-10". Labeled "Example" (illustrative) — cosmetic copy inconsistency; pick one scale.
- **R3-m4 scenarios "Run Council on This Scenario":** runs a REAL council but on the portfolio-wide prompt (openCouncilModal ignores the scenario text) — under-delivers on the label. Decide: pass scenario context to the council, or relabel.
- **Dead-code purge (not shown):** news.html orphaned `newsStories['featured-1']` JS object (PIF text, unreferenced); scenarios orphan `.multi-compare-toggle` CSS. Harmless; clean when convenient.
- **Auth-page i18n (R2-01):** login/signup/forgot-password/reset-password are English-only (no language toggle). Decide whether auth pages should be bilingual (then they need AR form strings) or stay EN like legal.html.
- **Backend repo backlog:** `C:\projects\alphacouncil` is 8 commits ahead of origin/main with uncommitted edits (router.py, http_cookies.py, main.py, thesis/prompts.py, ticker_names.py) from prior sessions. I avoided deploying these (deployed only the one fundamentals function). They need review + a clean push/deploy or revert.
- **Portfolio dead code (deferred purge):** `#adjustModal` + `holdingsData` mock + `openAdjustModal/confirmAdjust` + the canned `processChat` tail (after its `return`) are unreachable (not shown, not wired) but still in the file. Safe to delete in a dedicated cleanup.
- **Anon on user/app pages:** anon can load dashboard/portfolio/alerts/etc. (honest-empty states) and even public stock-detail, but authed-data fetches fire → 401 console/network noise (R1-09). Cleanest fix = gate user-specific pages (redirect to login) + skip authed calls on public pages for anon. Behavior change — your call.
- **Sample dashboard:** removed the fabricated one + its CTAs. If a public demo is wanted, rebuild as a clearly-labeled "illustrative" preview (no interactive fake AI). Product/marketing decision.
- **Auth-gating user-specific pages:** anon can load dashboard/portfolio/alerts/etc. and sees honest-empty states, but the authed-data fetches fire and 401 → console/network noise for anon. Cleanest fix is to redirect anon to login (behavior change) — your call.
- **Marketing hero mockup `SAR 847,250`** on index.html/features.html (`.mockup-stat-value`): an illustrative product screenshot, not presented as a user's live data. Keep as illustrative, relabel, or replace with a real example — your call.
