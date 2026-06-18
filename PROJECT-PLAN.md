# AlphaCouncil — PROJECT-PLAN.md
**Phase 0 deliverable — full audit + phased remediation plan. No feature code written yet. Awaiting approval.**

Generated 2026-06-18 from a combined audit of the codebase **and** the running site
(https://alphacouncil.tech) by 7 parallel auditors covering every page + the backend.

- Frontend workspace: `C:\projects\alphacouncil-static` (HTML pages with inline `<script>`; shared `adviser-core.js` + `js/api.js`; deploys to VPS `/opt/alphacouncil/static-v2`).
- Backend: `C:\projects\alphacouncil\llm-council\backend` (FastAPI; deploys to VPS `alphacouncil-backend.service`).

---

## 0. Headline findings

1. **The backend is real.** 716 tickers across 7 exchanges, no pure stubs found; the data, auth, portfolio, watchlist, alerts, adviser, council, thesis, news and corporate-actions endpoints all query live DBs. **The work is ~85% frontend**: pages ship hardcoded "demo" data, dead buttons, and stubbed flows even though a real endpoint already exists.
2. **Already fixed this session (verified live):** dashboard Top Gainers/Losers (`/api/movers`), Holdings real names (`name_en`), Watchlist (`/api/watchlist` CRUD), Intelligent Alerts (`/api/alerts`), the 5 "View all" buttons, stock-detail ☆ Watchlist button. These are marked ✅ below and are **not** re-planned.
3. **AED→SAR is already correct** — `backend/portfolio/currency.py` uses a structural USD-peg constant `AED_TO_SAR = 1.0211` server-side (not a stale rate; a prior inverted-rate bug is already fixed). **Gap:** it does **not** convert KWD/QAR/OMR/BHD, so SAR roll-ups for Kuwait/Qatar/Oman/Bahrain holdings are wrong (currently rare, but a real correctness bug).
4. **Constitution discrepancy (must reconcile):** the constitution says *"~435 tickers, Tadawul + ADX/DFM only."* The live system actually serves **716 tickers across 6 GCC markets / 7 exchanges**: TADAWUL 269 (SAR), ADX 102 + DFM 64 (AED), KSE/Kuwait 129 (KWD), QSE/Qatar 55 (QAR), MSM/Oman 58 (OMR), BSE/Bahrain 39 (BHD). Per **Scope Discipline (rule 6)** I have **not** edited the constitution — I recommend updating it; flagged as decision **D0** below. (Caveat: market-index series, `/market-brief`, and beta only exist for TASI/ADX/DFM — the 4 newer markets have no index feed.)

### Cross-cutting fake-data / dead-control patterns (appear on many pages)
- **Fake "AI" shown as live:** `askAboutNews()` (news + stock-detail) and `askAboutDimension()` (stock-detail) inject hardcoded canned "analysis" into the *real* adviser chat. `generateResponse()` is a large dead mock. The Council modal has a static "32.2% banking weight" synthesis + `askAboutReview()` canned text.
- **Fake nav identity:** notification badge literal ("2"/"3"/"5"), user avatar "SK"/"Sami", `aria-label="…Sami…"` hardcoded across most pages (the badge is overwritten by real unread-count on app pages; avatar/name often are not). Note identity mismatch: nav says "Sami", settings says "Saeed Al-Khalidi".
- **"Live" indices bar** literal values + "Live · 14:32 GST" timestamp are static HTML. On app pages `adviser-core.js` replaces values via `/api/ticker-tape` (good); the **timestamp stays fake** and marketing pages never wire it.
- **Dead/placebo controls:** EN/AR language toggles (no handler anywhere), "Export CSV", several modal Save/Run-Again/Create-Rule/Create-Alert buttons that only fire a success toast with no persistence.

---

## 1. Definition of Done (applies to EVERY checklist item — from the constitution)
An item is done only when ALL are true and the **raw evidence** is shown (between `==BEGIN==`/`==END==`):
1. **Real data only** — no placeholder/mock/hardcoded value rendered as live; unavailable data shows an honest empty/unavailable state.
2. **No half-baked** — every control works or is removed; no dead buttons, no TODO/commented-out logic in user-facing paths; visualizations render correctly with real data.
3. **Product correctness** — AED→SAR (and KWD/QAR/OMR/BHD) correct; AR + EN labels both correct where shown; sector/name overrides used, not guesses.
4. **Evidence** — (a) commit hash; (b) service builds/runs; (c) the item's Playwright E2E test passes (raw output); (d) screenshot of the affected UI, visually clean; (e) **zero console errors and zero failed network requests** on the affected page.

---

## 2a. DECISIONS RESOLVED (2026-06-18, founder-approved)
- **D0 ✅ Fix constitution numbers** — DONE: constitution rule 5 updated to 716 tickers / 6 GCC markets / 7 exchanges.
- **D1 ✅ E2E target** — Live site + a dedicated QA account (registered via API; creds in gitignored `.env.test`; Playwright auths programmatically, never the founder's account).
- **D2 → implement real Arabic i18n** — founder did NOT choose to remove the EN/AR toggles, so (consistent with the build-everything-real stance) Phase **B6** becomes "implement real RTL + AR/EN i18n" across the app, persisting `preferred_language`. (Large; sequenced as its own sub-phase.)
- **D3 ✅ scenarios.html — BUILD REAL** — Phase **K** = a real scenario-evaluation engine driven by the user's holdings (new backend), not an honest-preview placeholder.
- **D4 ✅ council-history.html — BUILD REAL** — Phase **J** = persist convened council results + `GET /api/adviser/council/history` + real render.
- **D5 ✅ settings.html — BUILD REAL** — Phase **L** = real Stripe billing + real TOTP 2FA + real session store (each is its own item; Stripe needs founder-supplied keys — flagged, I won't handle secrets).
- **D6 ✅ contact — real endpoint** — Phase **M4** = `POST /api/contact` (store + email), not a mailto fallback.

> Net effect: nothing is descoped. Every page becomes fully real. External-credential blockers (Stripe keys, prod SMTP, Apple/LinkedIn OAuth) are founder actions — I will build everything around them and flag the exact handoff.

## 2. Decision options as originally presented (now resolved above)
- **D0 — Constitution numbers:** approve updating the constitution to "716 tickers / 6 GCC markets / 7 exchanges" (and note index/brief/beta are TASI/ADX/DFM-only)? (Recommended: yes.)
- **D1 — E2E target & test account:** run Playwright against the **live site** with a dedicated **test account** (I'll register `qa+alphacouncil@…`), or stand up a **local** static-server + live-API instance? (Recommended: live site + dedicated QA account; app pages need a real login + seeded holdings. I cannot use your `boss@argaam.com` — I won't handle your password.)
- **D2 — AR/EN:** implement real Arabic i18n (RTL + translated labels; backend already stores `preferred_language` and returns `name_ar`) **or** remove the EN/AR toggles for now so they aren't dead controls? (Recommended: remove toggles in Phase 1, schedule full i18n as its own later phase — real i18n across ~14 pages is large.)
- **D3 — scenarios.html:** it is 100% mock with **no** backend. Build a real scenario-evaluation engine (large) **or** reduce it to an honest, non-fabricated "coming soon"/manual-input preview that invents no numbers? (Recommended: honest preview now; real engine as a later phase.)
- **D4 — council-history.html:** build council-result **persistence** + a `GET /api/adviser/council/history` endpoint + render real history (medium) **or** gate the page as "coming soon" until then? (Recommended: build persistence — it's modest and makes the Council feature whole.)
- **D5 — settings.html billing / 2FA / sessions:** these are placebos with no backend. **Remove** them for launch **or** build real ones (Stripe billing, TOTP 2FA, session store — each large)? (Recommended: remove/disable for launch, schedule separately.)
- **D6 — contact form:** add a real `POST /api/contact` (store + email) **or** switch to a `mailto:` fallback? (Recommended: real endpoint.)

---

## 3. Phased plan
Ordered so shared/foundational work lands before the pages that depend on it. Each `[ ]` is one commit-able item. Per-item rows use **State** (working/broken/missing/stubbed/fake-data) → **Work** → **Acceptance** (on top of the global DoD §1).

### PHASE A — Test & evidence harness (foundational; blocks all Phase-1 execution) — ✅ DONE (commit pending)
> Evidence: baseline `7b26974`; Playwright 1.61.0 + Chromium; `smoke.spec.js` green; QA account id 58 registered + 3 holdings seeded; `auth.spec.js` green (0 console errors / 0 failed requests / 0 page errors). Harness caught a real bug on first authed run (`AlphaCouncil.log is not a function`, dashboard.html) — fixed (dead debug line removed) + deployed.
- [x] **A1 — Git baseline.** State: working dir is non-git per env; canonical repos unknown. Work: confirm/initialise git in `alphacouncil-static` (+ backend repo), commit current state as the baseline so every later item has a real commit hash. Acceptance: `git log` shows the baseline commit; subsequent items each produce a hash.
- [x] **A2 — Playwright harness.** State: missing (no tests exist anywhere). Work: add Playwright config, a login fixture (per D1), helpers to (a) capture a screenshot, (b) assert **zero console errors** and **zero failed (4xx/5xx) network requests**, (c) seed/cleanup test holdings via the real API. Acceptance: `npx playwright test` runs green on one smoke test (loads `index.html`, asserts no console errors).
- [x] **A3 — QA account + seed.** State: missing. Work: register a dedicated QA user via `/api/auth/register`; provide a seed routine that adds a known multi-currency holding set (a TADAWUL, an ADX/AED, a QSE/QAR) so currency + rendering are testable. Acceptance: fixture logs in and GET `/api/portfolio/holdings` returns the seeded set.

### PHASE B — Shared foundations (used by every app page)
- [ ] **B1 — Real nav identity everywhere.** State: fake-data (badge "2/3/5", avatar "SK", aria "Sami" hardcoded in markup on dashboard/portfolio/news/alerts/scenarios/council-history/settings/stock-detail). Work: drive avatar initials + name from `/auth/me`, badge from `/api/alerts/unread-count` (extend the `adviser-core.js` logic to set avatar/name on all pages); remove static literals. Acceptance: signed-out → neutral/hidden; signed-in → real initials/name/count; no "Sami"/"SK"/"3" literal in any shipped page.
- [ ] **B2 — Remove fake "AI shown as live."** State: fake-data (user-reachable). Work: rewrite `askAboutNews()` + `askAboutDimension()` (`adviser-core.js`) to call real `/api/adviser/ask` with the headline/dimension as the question; delete dead `generateResponse()`; remove the Council modal's static "32.2%" synthesis + `askAboutReview()` canned text (send a real question instead). Acceptance: every adviser-chat bubble originates from `/api/adviser/ask` (or an honest error); grep finds no "32.2%"/"SAR 847,250"/canned-template strings in user paths.
- [ ] **B3 — Honest indices bar.** State: partial (values replaced by `/api/ticker-tape` on app pages; "Live · HH:MM GST" timestamp is static; marketing pages never wire it). Work: render the timestamp from the feed's real `fetched_at` (or drop "Live"); on marketing pages either wire `/api/ticker-tape` or mark the strip illustrative. Acceptance: timestamp reflects real data freshness; no "Live" label over static numbers anywhere.
- [x] **B4 — Multi-currency SAR roll-up (backend).** ✅ DONE — `currency.py` now carries all six GCC pegs (AED 1.0211, QAR 1.0302, BHD 9.9734, OMR 9.7530, KWD ~12.22) + suffix rules (_QSE/_KSE/_MSM/_BSE); `resolve_currency` accepts all valid currencies from the snapshot; `frontend_api.py` import-confirm widened. Deployed + restarted; QA QNBK re-seeds as QAR; `currency.spec.js` (2 tests) green. State: broken for KWD/QAR/OMR/BHD (`to_sar` only handles SAR/AED). Work: add USD-peg constants for KWD/QAR/OMR/BHD to `currency.py`, extend `to_sar` + `resolve_currency` + the `Currency` type; verify per-ticker native P&L unaffected. Acceptance: a QAR + a KWD holding roll into the SAR total at the correct peg; E2E asserts the portfolio SAR total for the seeded multi-currency set.
- [ ] **B5 — Delete dead/duplicate code (prevents fake-data regressions).** State: dead. Work: remove dashboard `#councilModal`/`#stockModal` (~170 lines fake), portfolio `holdingsData` mock + orphaned row fns, backend unused `auth/router.py`, and `council-modal.html` (dead prototype superseded by the real modal in `adviser-core.js`). Acceptance: pages render identically; grep shows the dead symbols gone; no console errors.
- [ ] **B6 — EN/AR toggle decision (per D2).** State: stubbed (toggles no-op site-wide). Work: implement real i18n **or** remove the toggles. Acceptance: no dead language control; if implemented, Arabic flips RTL + labels and persists `preferred_language`.

### PHASE C — Auth completeness (gates onboarding & account)
- [ ] **C1 — Build `reset-password.html` (MISSING).** State: broken end-to-end — reset emails link to `/reset-password?token=…` but no such page exists; backend `POST /auth/reset-password` is real. Work: build the page (token from query → new-password form → POST), with strength meter + success/expired-token states. Acceptance: emailed link opens a working form; valid token sets a new password and logs in; expired/used token shows an honest error.
- [ ] **C2 — signup: stop discarding inputs.** State: fake-data — first/last name + "Primary GCC market" are collected but never sent; `preferred_language` hardcoded `'en'`. Work: send/store name + market + language (extend `/auth/register` + `users`), or remove the inputs (per D2 for language). Acceptance: a field shown to the user is persisted and reflected in `/auth/me`, or it isn't shown.
- [ ] **C3 — login: remove dead 2FA.** State: stubbed/security-risk — 2FA UI accepts any 6-digit code client-side (gated off by `has2FA=false`, not reachable, but shipped). Work: remove the dead 2FA branch (real TOTP is out of scope → D5). Also fix login footer `href="#"` dead links → real `legal.html`. Acceptance: no client-only auth-bypass code in the bundle; footer links resolve.
- [ ] **C4 — Verify prod email delivery.** State: environment-dependent — without SMTP creds, reset/verification emails only console-log. Work: confirm MailerSend/SMTP env is set on prod; if not, surface it. Acceptance: a real reset email is received end-to-end (or the gap is explicitly reported).

### PHASE D — stock-detail.html (highest-value data page; mostly fake today)
Real already: header/price (`/api/ticker/{key}`), on-demand Thesis (`/api/thesis`), Council, Adviser, Add-to-Portfolio, ☆ Watchlist ✅.
- [ ] **D1 — Price chart + timeframe/overlays.** State: broken — permanent "Interactive chart loads here" placeholder; tabs/SMA/EMA/Volume buttons are no-op. Backend `/api/ticker/{key}/price-history` is **real**. Work: render a real chart from price-history for the selected timeframe; wire overlays or remove them. Acceptance: chart draws real OHLC/line for 1M/3M/6M/1Y/5Y; overlays toggle real series; empty state if no history.
- [ ] **D2 — Recent News (per-ticker).** State: fake-data (hardcoded Aramco headlines on every ticker). Backend `/api/ticker/{key}/news` is **real**. Work: render from the news endpoint; "Ask Adviser" passes the real headline (via B2). Acceptance: news matches the ticker; honest empty state; links go to real article URLs.
- [ ] **D3 — Dividends & Corporate Actions.** State: fake-data. Backend `/api/ticker/{key}/corporate` is **real** (dividends, capital changes, M&A, beta). Work: render real rows or hide the section. Acceptance: real dividend history/actions or honest empty.
- [ ] **D4 — Key-Facts gauges + Technical table + Ownership.** State: fake-data (ring scores + EV/EBITDA/ROA/D-E/payout hardcoded; 5/6 technical rows hardcoded; ownership %s hardcoded with mis-scaled bars). Backend `/api/ticker/{key}/fundamentals` + `…/tech` provide real values (some null). Work: bind every metric to real data or render "—"; fix bar widths; real ownership or remove. Acceptance: no invented metric; every gauge/row is real-or-"—".
- [ ] **D5 — Signal banner + "Your Position".** State: fake-data — "HOLD/High Confidence" hardcoded; position 320 sh/SAR 9,248 shown to everyone; Adjust/Record-Sale toast-only. Work: derive signal from real score (or remove); show the **signed-in user's** real holding for this ticker or hide; wire or remove Adjust/Sale. Acceptance: signal from real data; position is user-specific or absent; no no-op buttons.
- [ ] **D6 — Analyst Forecast (price target + earnings trend).** State: fake-data (invented targets/analyst count/earnings beats). Backend `/api/ticker/{key}/insights` has analyst/estimate data. Work: render from insights or remove the section. Acceptance: real targets/estimates or section gone.
- [ ] **D7 — Set Alert + dimension explanations.** State: stubbed — "Alert Created" persists nothing; dimension-card explanations are canned and bound to cards removed at runtime. Work: make Set-Alert honest (label not-yet-active or wire a real create-alert endpoint) and route dimension insight through real thesis/adviser (B2). Acceptance: no false "created" confirmation; explanations are real or absent.

### PHASE E — dashboard.html (finish what this session started)
Real already: movers ✅, holdings names ✅, watchlist ✅, intelligent alerts ✅, view-all buttons ✅, bell badge ✅, search ✅, adviser/council ✅, ticker tape ✅.
- [ ] **E1 — Metrics row.** State: fake-data — "SAR 847,250 / +SAR 38,912 / 3.2% / 64 Moderate" literals persist when logged-out or on fetch failure; Risk Score has no data source. Work: skeleton until real; compute from holdings; remove Risk Score or back it with a real metric. Acceptance: logged-out/no-holdings never shows the 847,250 literal; values match `/api/portfolio/holdings`.
- [ ] **E2 — Portfolio Snapshot quick-stats.** State: fake-data — "7/4/5/2" never updated. Work: compute count/distinct-sectors/gainers/losers from real holdings, or remove the card. Acceptance: counts derive from real data or card gone.
- [ ] **E3 — "AI Analyst Council" sidebar card.** State: fake-data — hardcoded "banking 32.2%… Materials 7.2%" synthesis. Work: replace with a neutral CTA (like stock-detail) or a real portfolio-council summary. Acceptance: no invented percentages; button still convenes the real Council.
- [ ] **E4 — Greeting/date + Thesis column + dead controls.** State: fake-data/stubbed — "Good morning, Sami" + wrong static date + "Last sync 2 min ago"; Holdings "Thesis Score" column renders "—" for all; sidebar tabs are cosmetic no-ops. Work: dynamic greeting/date/user; real thesis score per row or drop the column; wire or remove the tabs. Acceptance: real name/date; no dead column/tabs.

### PHASE F — portfolio.html (depends B4 for currency)
Real already: holdings table + metrics (after load), watchlist section ✅, council/adviser-council button.
- [ ] **F1 — Sector & Country allocation charts.** State: fake-data (Banking 32.2%, Saudi 51.6% hardcoded; Country card omits Kuwait/Oman/Bahrain). Work: compute allocations client-side from real holdings (sector + exchange, SAR-weighted via B4). Acceptance: bars sum to 100% of the real portfolio; all held markets represented; flags from real thresholds.
- [ ] **F2 — Alerts panel + News panel.** State: fake-data (3 static alerts; 3 static news). Backends `/api/alerts` + `/api/news/for-holdings` are **real**. Work: render both from the API with honest empty states. Acceptance: real alerts/news or empty state.
- [ ] **F3 — Add Holding modal (BUG) + Import flow.** State: broken — the modal's own confirm writes to a mock + invents a price; the header button path is correct. Import upload zone is **dead** though `/api/portfolio/import-extract`+`import-confirm` are real. Work: make the modal POST via `API.addHolding`; wire the upload zone to extract→review→confirm. Acceptance: confirming the modal persists a real holding; uploading a statement extracts real rows the user confirms and persists.
- [ ] **F4 — Commentary, transaction-history, Export CSV, adviser chat.** State: fake-data/dead — static commentary; per-row Add-Lot/Partial-Sale persist nothing; "Export CSV" no-op; sidebar chat is canned. Work: remove the transaction UI (no backend) or build it; implement CSV export of real holdings; route chat through real adviser (B2); real-or-remove metric sub-labels + Thesis column. Acceptance: no control that claims persistence it lacks; CSV downloads real data; chat is real.

### PHASE G — onboarding.html (depends F3 import)
- [ ] **G1 — Upload flow (CRITICAL: silent data loss).** State: broken/fake — upload discards the file and injects `simulatedHoldings` with no `tickerKey`, so "ready!" persists **zero** holdings. Work: real base64 → `import-extract` → editable review → `import-confirm`. Acceptance: after upload+finish, `/api/portfolio/holdings` returns the imported positions.
- [ ] **G2 — Profile persistence + success tiles + FX.** State: stubbed/fake — profile answers never saved; "+8.4%/3.2%/72" tiles hardcoded; onboarding uses its own invented FX table. Work: persist profile to `/api/adviser/risk-profile` (or mark cosmetic); compute/remove the tiles; use the backend as the single FX source. Acceptance: profile persists; tiles real-or-gone; onboarding SAR total == portfolio page total for the same holdings.

### PHASE H — news.html
Real already: feed (`/api/news/latest`, `/api/news/for-holdings`) ✅.
- [ ] **H1 — Top Stories sidebar + "Summarize" + tab/badge wiring.** State: fake-data/buggy — sidebar Top Stories hardcoded; "Summarize today's news" injects a canned string; duplicate tab handlers (one reloads, one just toasts); ticker-badge click binds only to pre-render static nodes. Work: populate Top Stories from the feed; route Summarize through real adviser (B2); delete the legacy toast tab handler; delegate badge clicks. Acceptance: sidebar real; Summarize is a real model answer; one tab handler; badges on real cards navigate.

### PHASE I — alerts.html
Real already: feed + Load-more + mark-read ✅; ticker search + All/High/Unread filters ✅.
- [ ] **I1 — Filters + per-card actions + Rules.** State: broken/stubbed — analyst-type `<select>` filters by a CSS class the real cards don't have (hides everything); "My holdings only" toggle no-op; snooze/dismiss/mark-read are DOM-only; the "Alert Rules" sidebar (create/edit/delete) is a mockup with no backend. Work: map filters to real `kind`/`source`; wire or remove "holdings only"; render intended per-card actions backed by real endpoints (or remove); build a real alert-rules CRUD or clearly disable the panel ("coming soon"); route the sidebar chat through real adviser. Acceptance: every filter/control acts on real cards or is removed; no control claims persistence it lacks.

### PHASE J — council-history.html (per D4)
- [ ] **J1 — Real history.** State: fake-data — entire list/stats/trends/detail-modal hardcoded; no history endpoint exists (`council_usage` stores counts only). Work: persist each convened council result + add `GET /api/adviser/council/history`; render real list/stats/detail with empty state; wire sort/date filters; make Export/Compare/Ask-Adviser real or remove. Acceptance: fresh account → empty state; after a convening the entry appears on reload, scoped to that account; each card opens its own data.

### PHASE K — scenarios.html (per D3)
- [ ] **K1 — De-fabricate.** State: fake-data — 100% mock (every before/after number hardcoded); Analyze/Save/Clone/Delete persist nothing; honest "Preview" banner present but the page still renders invented figures. Work: per D3 — either a real scenario-eval engine driven by the user's holdings, or an honest input-only preview that invents no numbers and clearly states it's not yet computing. Acceptance: no fabricated metric presented as result; any number shown is either real-computed or absent.

### PHASE L — settings.html (per D5)
- [ ] **L1 — Make real-or-remove.** Real already: email display, plan name/price/CTA, **risk tolerance** (save/load), logout. State: placebo — profile save (name/market/language), notifications toggles, billing (USD $49 + fake VISA + fake invoices), 2FA (client-only theatre), active sessions, data export, delete-account, change-password, avatar upload all do nothing. Work (per D5): remove/disable the unbacked sections for launch (billing/2FA/sessions), and wire the cheap real ones — profile-name save, language persist (D2), a real export and a real delete-account, change-password. Acceptance: every visible control persists/acts, or is removed; no security-looking control that secures nothing; no USD billing artifacts.

### PHASE M — marketing pages (index, features, how-it-works, markets, methodology, pricing, about, contact, legal)
- [ ] **M1 — Reconcile platform numbers.** State: fake-data/inconsistent — stock count "700+" vs "1,200+" vs per-market sum 815; "7 GCC markets" (should be 6); thesis dims "11" vs "12". Work: set the true figures everywhere (716 tickers, 6 markets/7 exchanges, correct dimension count) from one source. Acceptance: identical correct numbers site-wide.
- [ ] **M2 — index testimonials + ticker.** State: fake-data — fabricated investor testimonials (Ahmad/Fatima/Khalid) under "What investors are saying"; static ticker strip. Work: remove/clearly label testimonials; wire the ticker to `/api/ticker-tape` or mark illustrative. Acceptance: no fabricated testimonial presented as real; ticker honest.
- [ ] **M3 — markets.html real coverage.** State: fake-data — invented per-market counts/market-caps; "Real-time … OHLCV" overstated (nightly pipeline). Work: real per-market counts (from `/api/screening`), cite or soften market-caps, change "real-time"→"end-of-day/daily". Acceptance: counts match prod; freshness claim accurate.
- [ ] **M4 — contact + pricing + emails (per D6).** State: stubbed/inconsistent — contact form has no submit target ("isn't fully wired"); placeholder phone "+966 5X…"; support email differs (`hello@…tech` vs `enterprise@…com`, wrong TLD); pricing FAQ uses stale tier name "Explorer". Work: real `POST /api/contact` (or mailto); real channels; unify email + domain; "Explorer"→"Free"; optional `?plan=` preselect. Acceptance: contact submission delivers; one correct support email; tier names consistent.
- [ ] **M5 — legal.html.** State: self-flagged template pending counsel. Work: out of engineering scope — note for legal review; keep the honest disclaimer. Acceptance: disclaimer present; tracked as a non-engineering gap.

### PHASE N — backend hardening (supporting; low user-visibility)
- [ ] **N1 — Gate costly public endpoints.** State: risk — `POST /api/thesis/{key}` (paid LLM gen, 60–200s) and `DELETE /api/thesis/cache/{key}` are unauthenticated. Work: auth/tier-gate + rate-limit. Acceptance: anonymous abuse blocked; legit cached reads still public.
- [ ] **N2 — evidence/search 503.** State: broken on prod (FTS DB not available to that router). Work: fix or confirm unused and remove. Acceptance: returns results or is removed; no 503 surfaced to any UI.
- [ ] **N3 — OAuth completeness.** State: Apple/LinkedIn `configured=false` (env creds unset; UI already honestly "coming soon"). Work: enable when the founder supplies creds (founder action — I won't handle secrets). Acceptance: provider goes live once creds set; otherwise stays honestly gated.

---

## 4. Suggested execution order (dependency-respecting)
A (harness) → B (shared) → C (auth) → D (stock-detail) → E (dashboard) → F (portfolio) → G (onboarding) → H (news) → I (alerts) → J (council-history) → K (scenarios) → L (settings) → M (marketing) → N (backend hardening).

Rationale: tests must exist first (A); shared identity/anti-fake/currency/cleanup (B) unblock every page; auth (C) unblocks the signed-in journeys; then pages in value order; backend hardening last as it isn't user-visible. Items already done this session are pre-checked and excluded.

---

## 5. Coverage map (every page → its phase)
| Page | Phase(s) | Worst current issue |
|---|---|---|
| dashboard.html | E (+B) | metrics row + snapshot + council card still fake |
| stock-detail.html | D (+B) | chart placeholder; news/dividends/gauges/position fake |
| portfolio.html | F (+B4) | allocation charts, alerts, news fake; Add/Import broken |
| onboarding.html | G | upload flow loses data silently |
| news.html | H | Top Stories + Summarize fake |
| alerts.html | I | filters break real cards; Rules mockup |
| council-history.html | J | entire page fabricated; no backend |
| council-modal.html | B5 | dead prototype → delete |
| scenarios.html | K | 100% mock; no backend |
| settings.html | L | most controls placebo (2FA/billing/sessions) |
| login.html | C3, B1 | dead 2FA accepts any code; dead footer links |
| signup.html | C2 | name/market/language discarded |
| forgot-password.html | C1 | reset-password page missing → dead-end |
| reset-password.html | C1 | **missing entirely** |
| index/features/how-it-works/markets/methodology/pricing/about/contact/legal | M | inconsistent stats; fake testimonials; dead contact form |
| adviser-core.js / js/api.js | B | canned "AI" in real chat; dead mocks |
| backend | B4, N | multi-currency roll-up; ungated costly endpoints |

---

**Status: PHASE 0 complete. No feature code written. Awaiting your approval of this plan + decisions D0–D6 before starting PHASE 1 (which begins with the test harness, then proceeds in the order above, with tests + screenshots + commit + check-off per item).**
