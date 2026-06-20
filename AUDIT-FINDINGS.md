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

### R1-03 — stock-detail fundamentals 404 → console error for screening-listed tickers — **MAJOR** — pending
- **Repro:** `/stock-detail.html?ticker=ABRAAJ_BSE` (in `/api/screening`, summary 200) → `GET /api/ticker/ABRAAJ_BSE/fundamentals` **404** → console error + failed request (DoD violation). POLTRY_BSE (also no fundamentals) returns honest **200-with-nulls** — backend is inconsistent. Page renders honest "—" visually; only the 404 is the defect.
- **Planned fix:** backend `/fundamentals` returns 200 honest-empty for a valid ticker lacking a fundamentals row (consistent with POLTRY).

### R1-04 — portfolio.html ships orphaned fabricated markup — **MAJOR** — pending
- Orphaned `#councilModal` (hardcoded "32.2% banking / SABIC 7.2% / Saudi 51.6% / 5.8/10") + `#adjustModal` + `holdingsData` mock (Aramco 5470 @ 25.40 …) + dead `openAdjustModal/confirmAdjust` + 7 static fabricated `<tr>` holding rows + per-row tx-history. **Not shown** to users (real `onPortfolioReady` overwrites `#holdingsBody`; `openCouncilModal` builds a separate `councilModalOverlay` with a real `/api/adviser/council/ask`; modal-overlay is `opacity:0`) — but fabricated financial content is shipped in the page (rule 2) and flashes pre-hydration.
- **Planned fix:** remove the orphaned modals/mock/handlers; neutralize static metric literals + holding rows.

### R1-05 — stale "Action completed" toast visible by default on portfolio — pending (investigating)
- Full-page screenshot (authed + anon) shows a large "Action completed / Your request has been processed" toast rendered at page bottom with no action taken.

### R1-06 — dead `href="#"` links — **MAJOR** — pending
- forgot-password.html (3 visible), onboarding.html (1), stock-detail.html (1). (news.html's 12 static `#` links are replaced by the real feed render — not user-reachable.)

### R1-07 — settings.html ships fake identity defaults — **MINOR** — pending
- `<input id="firstName" value="Saeed">` / `<input id="lastName" value="Al-Khalidi">`. `loadProfile()` clears+fills from `/auth/me`, but the fake names ship in markup and flash before the async fetch (and the B1 nav check only scanned "SK"/"Sami").

### R1-08 — thesis-auth regression test is brittle — pending (reconcile)
- Test asserts anon `POST /api/thesis/2222 {}` is 200/404 (public cached read). Backend keys the cache on `(model, as_of_date)`; `as_of_date` rolls forward nightly so pre-generated theses go stale → cache miss → anon **401** (by design). The UI handles 401 honestly ("Please log in to generate an AI thesis"); no page-load fetch. So the failure is a brittle assumption, not a user defect.
- **Planned:** reconcile the test to assert the real security invariant; flag the product nuance (logged-out visitors effectively never see a pre-generated thesis) for founder review.

### Verified-OK (audited, no defect)
- Missing-data ticker **POLTRY_BSE**: honest page — real name/BHD price/real price chart, empty gauges, CTAs. ✓
- Anon dashboard/portfolio: honest empty states + "sign in" prompts; `SAR 0` not `847,250`. ✓ (residual: 401 console noise — see NEEDS FOUNDER REVIEW)
- scenarios.html `847,250`/`32.2%` Before-After block is **not rendered** (hidden); not shown to users. (Dead markup — low priority.)
- Marketing platform numbers, currency pegs, alerts/news real feeds: consistent with prior tests.

---

## NEEDS FOUNDER REVIEW (ambiguous / cosmetic / out-of-scope)
- **Sample dashboard:** removed the fabricated one + its CTAs. If a public demo is wanted, rebuild as a clearly-labeled "illustrative" preview (no interactive fake AI). Product/marketing decision.
- **Auth-gating user-specific pages:** anon can load dashboard/portfolio/alerts/etc. and sees honest-empty states, but the authed-data fetches fire and 401 → console/network noise for anon. Cleanest fix is to redirect anon to login (behavior change) — your call.
- **Marketing hero mockup `SAR 847,250`** on index.html/features.html (`.mockup-stat-value`): an illustrative product screenshot, not presented as a user's live data. Keep as illustrative, relabel, or replace with a real example — your call.
