# AlphaCouncil — Pre-Launch Audit Report
**Site:** alphacouncil.tech  ·  **Date:** 2026-07-14  ·  **Phase:** 1 (audit only — no code modified)
**Method:** 7-domain read-only code/infra audit + adversarial verification (multi-agent), a low-concurrency 29-page consistency diff, and hands-on interactive testing of signup, manual stock add, image import, Adviser and Council on a clearly-marked Elite test account (deleted after).

---

## 1. Executive summary

**Verdict: NOT READY — 6 P0 launch blockers must be fixed first.** The platform is well-engineered in the areas that usually sink a launch (payments money-safety, SQL/XSS/IDOR, CSRF, auth token hygiene, backups, full 716-ticker bilingual coverage), so this is a fixable list, not a rewrite. But today the product's entire AI value proposition is non-functional in production (OpenRouter is out of credits, so Adviser, Council, image import and thesis all return errors), the FastAPI backend is exposed to the public internet on a plaintext port with the firewall off, list-view stock data is stamped with a fabricated "as-of" date that hides years-old prices behind a green "not stale" banner, and the legal pack explicitly declares itself non-binding while naming no legal entity. Fix the P0s and the P1s below and this is a **READY AFTER P0–P1 FIXES** launch.

> **Stack reality note (important):** the brief's stated stack is not what is deployed. Actual: **nginx** (not Caddy), **static HTML** served from `/opt/alphacouncil/static-v2` (not Next.js), **custom SQLite + passlib + JWT auth** (not Supabase — so *no RLS exists and the RLS/anon-key audit items are N/A*), **no WeasyPrint/PDF library installed** (no PDF report feature exists), **cron** scheduling (not systemd timers). Moyasar+Tap, Turnstile, Cloudflare, Playwright scrapers and the OpenRouter LLM Council are real. All findings below are against the *deployed* system.

**Tally:** 6 P0 · 8 P1 · ~22 P2 · ~14 P3 · 7 questions (after merging the three audit streams and de-duplicating).

---

## 2. Launch blockers (P0) — fix all before any launch

### P0-1 — All AI features are down: OpenRouter account has insufficient credits *(found via live testing; the code agents could not see this)*
- **Where:** `backend/openrouter.py` `query_model()`; affects `/api/adviser/ask`, `/api/adviser/council/ask`, `/api/portfolio/import-extract` (vision), thesis, AI news.
- **Evidence (live, my test account):** every LLM surface returns an error. Service journal: `Error querying model google/gemini-2.5-flash: Client error '402 Payment Required' … Insufficient credits. Add more using https://openrouter.ai/settings/credits`. Adviser → HTTP 502 leaking that raw text; Council → 502 "The Council could not reach a conclusion"; image import → 502 "Couldn't read the document." The quantitative pipeline is fine (all 716 briefs dated 2026-07-13), but **everything the product sells as "AI Analyst Council / Adviser" is broken right now.**
- **Fix (S):** fund the OpenRouter account; add a credit-balance/health check to `health_digest.py` and an alert; add graceful "AI temporarily unavailable" degradation (see P1-8). **Verify by re-running one Adviser + one Council call.**

### P0-2 — Backend bound to `0.0.0.0:8001` with the host firewall off *(SEC-01 / OBS-01, verified)*
- **Where:** `/etc/systemd/system/alphacouncil-backend.service` `ExecStart … --host 0.0.0.0`; `ufw` inactive.
- **Evidence:** the entire `/api` and `/auth` surface is reachable directly over **plaintext HTTP** from the internet, bypassing nginx TLS, HSTS, security headers and CSP. Confirmed reachable by external curl to port 8001.
- **Fix (S):** bind uvicorn to `127.0.0.1:8001` (nginx already proxies it) **and/or** enable a firewall allowing only 80/443/22. Restart service; re-test that `http://<ip>:8001` no longer answers externally.

### P0-3 — Unauthenticated, unmetered multi-LLM Council endpoint *(SEC-02, verified)*
- **Where:** `backend/main.py` legacy routes `POST /api/conversations` and `POST /api/conversations/{id}/message(/stream)`.
- **Evidence:** these run the full multi-model council with **no auth, no rate limit, no usage cap** — a direct cost-drain / DoS-of-your-wallet vector the moment OpenRouter is funded (P0-1). The new `/api/adviser/*` paths are properly capped; these legacy ones are not.
- **Fix (S):** require auth + the same `_reserve_usage` cap as `/api/adviser/council/ask`, or unmount the legacy router if dead. Re-test that an anonymous POST returns 401.

### P0-4 — `briefs.as_of_date` is fabricated (`= now()`), hiding years-old prices on list views *(DATA-01, verified — the exact bug class the brief flagged)*
- **Where:** `build_portfolio_inputs_with_sectors.py:806` (write) → `frontend_api.py` `/api/screening`, `/api/movers`, `/api/ticker-tape`.
- **Evidence:** the rebuild stamps *every* ticker's `as_of_date` with the rebuild timestamp, discarding the real price date. Result (confirmed live): tickers whose last real price is years old (e.g. `AKIC.AD_ADX` last traded 2020-07-05, `METH.AD_ADX` 2023) are served with a `last_price`, a fabricated `day_change_pct`, and a green "as of 13 Jul — not stale" banner. The ticker detail page and the AI council read the *real* `stocks.as_of_date` and correctly withhold — so the truth exists in the code but is bypassed on the list/screener/tape surfaces. **Direct violation of the data-honesty principle.**
- **Fix (M):** carry the real per-ticker price date through to `briefs.as_of_date` (or join `stocks.as_of_date` at read time); drive the freshness banner (P1-1) off that. Re-test that a known-stale ticker shows a stale badge in the screener.

### P0-5 — Legal pack self-declares itself NON-BINDING; no legal entity named *(LEGAL-01 + LEGAL-02)*
- **Where:** `static-v2/legal.html:482,648` ("do not yet constitute a binding legal agreement"); entity absent site-wide.
- **Evidence:** Terms/Privacy/Disclaimer/Refund all carry a "not yet binding" flag, so there is **no enforceable contract, liability waiver, or refund terms** behind a paid product. Separately, **"Insight Lane Establishment" appears on zero pages** — ownership is attributed to the brand "AlphaCouncil" with no commercial registration or address (independently confirmed: `grep` for the entity across all HTML returns nothing; footer shows only "© 2026 AlphaCouncil").
- **Fix (M):** remove the non-binding disclaimer once counsel signs off; insert the correct legal entity (Insight Lane Establishment), CR number and address into ToS/Privacy/footer. **Legal review required before launch.**

### P0-6 — AI "Adviser" serves fabricated holdings + personalized allocation advice *(LEGAL-04, verified; rated P1 by the finder — elevated here for the CMA + data-honesty double-hit)*
- **Where:** `static-v2/alerts.html:1169-1187` (`askAdviserAbout` hardcoded responses); demo cards `alerts.html:613,650`, `council-modal.html`.
- **Evidence:** a hardcoded path renders, in the AI Adviser's voice, **invented portfolio numbers and personalized advice**: *"your banking holdings … represent 32.2% … keep any single sector below 25–30% … Consider reviewing allocation."* This is simultaneously (a) fabricated data shown as if real, and (b) exactly the personalized robo-advisory framing the open CMA licensing question targets.
- **Fix (S):** delete the hardcoded advice/holdings responses; route Adviser answers only through the real, disclaimer-wrapped, data-grounded backend. Re-test the alerts "Ask Adviser" path shows no invented numbers.

---

## 3. Fix before launch (P1)

| ID | Area | Finding | Fix (effort) |
|---|---|---|---|
| **P1-1** DATA-02 | Data honesty | Freshness banner measures *rebuild* recency, not data recency, so it can **never** report stale (`frontend_api.py:158-190`). | Drive off real price date from P0-4. (S) |
| **P1-2** LEGAL-03 | Legal / checkout | `checkout.html` has **no legal links, refund, or auto-renew disclosure** at point of sale. | Add ToS/Privacy/Refund links + auto-renew line to checkout. (S) |
| **P1-3** CON-01 | Broken route | **`watchlist.html` does not exist** — the live URL soft-404s to the marketing landing page (app nav links to it). | Create the page or remove the nav link. (S/M) |
| **P1-4** CON-02 / LEGAL-07 | Trust | `contact.html` ships literal **placeholder contact details** on the live public page ("+966 5X XXX XXXX", "Contact details shown are placeholders"). | Put real support contact details in. (S) |
| **P1-5** OBS-02 | Observability | **Zero active error tracking** — Sentry is referenced but DSN unset *and* the SDK isn't installed; no frontend error capture either. | Install + wire Sentry (or minimal structured logging) backend + frontend. (M) |
| **P1-6** OBS-03 | Observability | **No external uptime monitor** — all alerting runs on the box being monitored, so a box/nginx/cron death is silent. | Add an off-box uptime check on the site + `/healthz/deep`. (S) |
| **P1-7** INT-02 | Data honesty / leak | LLM-down errors are **inconsistent and misleading**: import blames the user's screenshot, Adviser **leaks the raw upstream 402 + openrouter.ai URL** to the client, Council says "could not reach a conclusion." | Single honest "AI temporarily unavailable" message; stop leaking upstream errors. (S) |
| **P1-8** SEO-01 | SEO | Landing page has **no meta description, OpenGraph, Twitter card, or canonical** — poor sharing/indexing for a public launch. | Add head meta to landing (+ key pages). (S) |

---

## 4. Fix within first week (P2) — condensed

**Security/transport:** SEC-03 Turnstile only on signup (login/forgot/reset/contact unprotected) · SEC-04 stateless JWT not invalidated on password change/reset/logout · SEC-05 email verification effectively optional (register issues a 30-day session immediately; 17/20 real users unverified) · SEC-CSP nginx CSP has no `default-src`/`script-src` (no XSS mitigation).
**Payments:** PAY-01 Tap webhook has no signature/amount check (dormant) · PAY-03 concurrent webhook+redirect can write duplicate payment audit rows (entitlement still single-granted) · PAY-04 paid sub with no saved token is shown "Renews <date>" but silently excluded from auto-renewal (data-honesty).
**Data:** DATA-03 list endpoints expose no per-row data age · COV-01 40 of 687 scored stocks carry >1-week-old (some 3–6yr) prices · DB-01 user DB in rollback-journal mode, not WAL.
**Frontend/consistency:** FE-02/SEO-02/SEO-03 nginx `try_files … /index.html` causes **soft-404s** and fake `robots.txt`/`sitemap.xml` (both return landing HTML, 200) · FE-05 hardcoded "Live market indices" figures ship in raw HTML (repopulated by feed, but visible pre-JS) · CON-03 two divergent "Markets" pages share one title · CON-06 `markets-app.html` has no footer/disclaimer while peers do · CON-08 several app pages skip the shared stylesheet (self-styled drift) · CON-10 several pages use i18n namespaces with no dictionary entries · PERF-01 `gzip_types` commented out → CSS/JS uncompressed.
**Legal/trust:** LEGAL-05 demo cards contain advice-flavored fabricated allocation copy · LEGAL-06 competitor brand **`argaam_token`** in the published Privacy Policy (and it's the real cookie name) · CON-09 old dark-violet/purple palette persists site-wide vs the warm-ivory/ink-navy/bronze target.
**Interactive (my testing):** INT-03 manual add-holding **accepts non-existent tickers** ("ZZZZ" stored with null name/price/value; no validation) · INT-04 negative/zero shares & negative cost return a **raw HTTP 500** instead of a clean 400 (no numeric input validation; body is plain "Internal Server Error", no stack leak).
**Launch:** LAUNCH-01 the live `static-v2` frontend is **not version-controlled** and has no deploy/rollback script (partly mitigated — I pushed a `vps-production-sync-20260714` branch, but the box still deploys by rsync, not git).

## 5. Backlog (P3) — condensed
SEC-06 passwords use `sha256_crypt` not the bcrypt the docstrings claim · SEC-07 contact form rate limit is a single global counter · SEC-02 Turnstile fails **open** if the secret is ever emptied · SEC-03 dead demo bundle `alphacouncil-core.js` served with unescaped rendering · PAY-06 embedded-flow metadata (user_id, plan) client-set (server re-verifies, so low risk) · DATA-04 `/api/market-indices` no staleness flag + covers only 3 of 7 exchanges · FE-03 dashboard "View all" points to marketing `markets.html` not the app screener · FE-04 missing i18n key `lgl.footer_refund`, `lg.continue_linkedin` · FE-06 HTML served without charset in Content-Type · FE-07 stale `_qa_backup_*` dirs + duplicate dead assets served publicly · LEGAL-09 Refund policy not linked from home/pricing footers · SEO-04 no favicon, OG/Twitter, or hreflang despite AR/EN · CON-11..16 council-modal not i18n'd, per-page footer namespaces, low i18n coverage on content pages, login loads an extra font bundle.

---

## 6. Page-by-page sweep (live browser + consistency diff)

| Page | Status | Notes |
|---|---|---|
| Landing (`index`) | ✅ renders, no console errors | Title "Your AI **Adviser**" (naming risk); violet "AI Analyst Council" icon; no meta/OG/canonical; EN+AR RTL both clean. |
| Pricing | ✅ | Strong "Analysis & Education, Not Advice" section; Free/Pro SAR 79/Elite SAR 399; no mobile overflow. |
| Signup | ✅ | Turnstile renders (site key `0x4AAAAAADoxyhgLIaK5NH5B`); consent line "analysis, not financial advice"; **client validation works** (empty→"Missing details"; weak password→blocked, no server call); market values are exchange codes (my earlier fix). |
| Login | ✅ | **No Turnstile** (rate-limit only); forgot-password link present; loads an extra JetBrains-Mono font bundle. |
| Forgot/Reset password | ✅ | `forgot-password` title says "Reset Password" (mismatch). |
| Stock detail | ✅ **good data honesty** | Price "As of 2026-07-13" + freshness pills (PRICES 2d/FUND 1d/NEWS 1d); PHASE-8 gauges **enabled & rendering**; invalid ticker → honest "Stock not found". **Legal risk:** categorical green **"BUY"** badge. |
| Markets / markets-app | ✅ (holdings-bar overflow fixed earlier) | Two divergent "Markets" pages, same title; markets-app has no footer. |
| Portfolio (manual add) | ⚠️ | Valid add enriches correctly + CSRF enforced (403 w/o token); **but** bogus ticker accepted (INT-03) and negative/zero inputs → 500 (INT-04). |
| Image import | ⚠️ | Validation robust (415/400/413/401) **but vision extract fails** (P0-1 OpenRouter 402). |
| Adviser / Council | ❌ | Both 502 from OpenRouter 402 (P0-1); different misleading messages (P1-7); caps enforced pre-call (good). |
| Legal | ⚠️ | Non-binding (P0-5), no entity (P0-5), argaam_token leak; ToS/Privacy/Refund/14-day all present. |
| Contact | ⚠️ | Placeholder details on live page (P1-4). |
| 404 / robots / sitemap | ❌ | Unknown URLs return **200 landing** (soft-404); robots.txt & sitemap.xml don't exist. `/.env` correctly 404s. |
| Arabic (RTL) | ✅ | Clean shaping, Arabic-Indic numerals, no mojibake; `<title>` stays English (no hreflang). |

---

## 7. QUESTIONS (need your decision)

1. **Turnstile pairing (SEC-08):** the signup site key `0x4AAAAAADoxyhgLIaK5NH5B` and the `.env` secret can't be validated as a pair from outside — please confirm in the Cloudflare dashboard that they're one widget and that `alphacouncil.tech` **and** `www.` are in its domain allowlist. (This is the exact class that once blocked all signups.)
2. **Payments sandbox (PAY-02):** all keys are `sk_test/pk_test`, `BILLING_LIVE=false` — **no customer can pay until a go-live key swap.** Intended for launch day? When do you want the live-key cutover?
3. **"Adviser" naming (LEGAL-08):** product name "AI Adviser" + "decisive READ" copy + the "BUY" signal badge sit close to the CMA robo-advisory line. Rename/soften, or is this cleared with counsel?
4. **Design palette (FE-01/CON-09):** deployed is dark navy/teal/**violet**, not the brief's warm-ivory/ink-navy/bronze. Is the warm-ivory system still the target (big visual change), or is the current dark theme the real design?
5. **Upgrade proration (PAY-05):** upgrades charge the full new-plan price with no credit for the unused current period. Intended?
6. **CORS (SEC-04):** production CORS allows credentials with `localhost` dev origins baked in — safe to strip for launch?
7. **"Argaam" demo copy (CON-17):** the "Argaam" news-source label on `features.html`/`legal.html` — intentional attribution or leftover to remove?

---

## 8. Proposed Phase 2 fix order

**Wave 1 — unblock & secure (do first):** P0-2 (bind localhost/firewall) → P0-3 (lock legacy council endpoint) → P0-1 (fund OpenRouter + credit alert) → P1-7 (honest AI-down errors). *These are small and mostly independent; Wave 1 makes the site safe and the AI either working or honestly degraded.*
**Wave 2 — data honesty:** P0-4 (real `as_of_date`) → P1-1 (freshness banner off real date) → INT-03/INT-04 (portfolio input validation) → P0-6 & LEGAL-05 (remove fabricated advice/holdings).
**Wave 3 — legal & checkout:** P0-5 (binding legal + entity) → P1-2 (checkout legal links) → P1-4 (real contact details). *Gated on your counsel + entity details.*
**Wave 4 — routes, SEO, observability polish:** P1-3 (watchlist) → P1-5/P1-6 (Sentry + uptime) → P1-8/SEO-02/03 (meta, robots, sitemap, real 404) → P2 batch.

**I have not changed any code.** Tell me which findings to fix (and your answers to §7) and I'll start Phase 2 in this order, one finding per commit, re-testing signup + payment(test) + ticker-detail after each P0/P1.
