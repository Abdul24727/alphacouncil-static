# Pre-launch audit — beta.alphacouncil.tech (Phase 7)

Date: 2026-10-15 · Branch `rebuild` · Checked locally and on the staging server (through the SSH tunnel; the beta hostname has no DNS record yet).

Every issue found is listed here before anything is fixed (plan, Phase 7). Each has a severity and an owner:

- **Blocks testing**: user testing cannot start until it is done.
- **Before launch**: must be done before the new site replaces alphacouncil.tech or takes payments.
- **Later**: worth doing, blocks nothing.
- Owner **Claude**: a code change I can make on `rebuild`. Owner **You**: a decision, an account, or a legal text only you can change.

## Summary

| # | Area | Issue | Severity | Owner | Status |
|---|------|-------|----------|-------|--------|
| T1 | Testing | `beta.alphacouncil.tech` has no DNS record, so testers cannot reach staging (TLS is waiting on it too) | Blocks testing | You | Open |
| T2 | Testing | The Copilot ran as the labelled rule-based stand-in; a real model needed a key on the server | Decision | You | Done: OpenRouter with `deepseek/deepseek-v3.2` (tool calls verified first); the key was pasted in chat, so rotate it after testing |
| S1 | Security | No security headers: no Content-Security-Policy, no frame-ancestors / X-Frame-Options, no X-Content-Type-Options, no Referrer-Policy, no Permissions-Policy; `X-Powered-By: Next.js` was sent; HSTS to add once TLS is on | Before launch | Claude | Fixed (HSTS goes in with TLS) |
| S2 | Security | `POST /v1/copilot/chat` needed no sign-in and had no rate limit: once a key is set, anyone could spend model tokens | Blocks a real Copilot key | Claude | Fixed: 60 questions an hour per user or address; sign-in required once a model is configured |
| S3 | Security | The per-address part of the sign-in and sign-up limit read the first `X-Forwarded-For` entry, which the client writes, so a forged header got a fresh allowance each try (the per-email limit held). *Corrected: the first version of this report said sign-up had no limit; it shares the sign-in limit.* | Before launch | Claude | Fixed: uses nginx's `X-Real-IP`; limits are now counted in the app database, so the API's two workers share them (they were per process, doubling every limit) |
| S4 | Security | No password reset and no e-mail verification (needs a mail service; the domain has no mail records) | Before launch | You (mail), then Claude | Open |
| S5 | Security / legal | No way to delete an account in Settings, although the Privacy Policy says deletion can be requested "through available settings" | Before launch | Claude | Fixed: Settings › Delete account (password asked again) |
| S6 | Correctness | Unknown tickers and templates (`/t/NOPE`, `/templates/nope`) answered HTTP 200 | Later | Claude | Templates now show the not-found page (noindex); unknown tickers still show the in-app "unknown ticker" message |
| P1 | Payments | The new app has no checkout. The old site's Moyasar checkout and monthly renewals are still live (`billing_configured: true`). Existing accounts and subscriptions are not in the new app's database | Before launch | You (migration plan), then Claude | Open |
| P2 | Payments | Pro has no Pro-only features in the new app; /pricing shows a labelled placeholder | Before paid launch | You | Open |
| P3 | Payments | Prices live in two places until the old backend is retired (`api/app/pricing.py` mirrors the old `pricing.py`, same env names); they can drift | Before launch | Claude (check), You (cut-over) | Open |
| P4 | Payments | Open items from the plan: market-data redistribution licence; CMA licensing question | Before paid launch | You | Open |
| D1 | Data | 61 of 690 equities with price files have prices older than 4 days; some stop in 2018 (likely delisted or suspended but still in the universe). They show amber everywhere | Before launch | You (pipeline) | Open |
| D2 | Data | 26 of 716 equities have no price file at all (charts say "Data unavailable") | Later | You (pipeline) | Open |
| D3 | Data | Index levels exist only for TASI, ADX and DFM; QSE, Boursa Kuwait, BHB and MSX show "n/a" | Later | You (pipeline) | Open |
| D4 | Data | Ownership and analyst data are empty for every equity (Ownership tab is "Data unavailable"); no cash-flow statement | Later | You (pipeline) | Open |
| D5 | Data | Some sector labels in `briefs` look wrong (e.g. 1111 "Energy", 1201 "Hotels & Restaurants") | Later | You (pipeline) | Open |
| D6 | Data | Panels said the next update is at 00:00 UTC (pipeline start); the databases are published around 02:30–05:00 UTC | Later | Claude | Fixed: the light now says "next run" |
| D7 | Data | The landing and /templates screens are real but dated (taken 2026-10-15); retake before launch (`scripts/capture-screens.mjs`) | Before launch | Claude | Open |
| L1 | Legal | Every document gives support@ and privacy@alphacouncil.tech; the domain has no mail records, so they bounce | Before launch | You | Open |
| L2 | Legal | Documents link to `https://alphacouncil.tech/contact.html` (old site); the new site has no contact page, so the link breaks at cut-over | Before launch | You (text) / Claude (page) | Open |
| L3 | Legal | Cookie Policy says the session cookie is session-only unless "remember me"; the app always sets a 30-day cookie and has no "remember me". The language choice is a `NEXT_LOCALE` cookie, not local storage | Before launch | You (text) or Claude (behaviour) | Open |
| L4 | Legal | AI & Financial Disclaimer describes the old product ("Adviser interactions", "multi-model or Council responses", "final synthesis"); the council is now rule-based, the Copilot is the AI feature | Before launch | You | Open |
| L5 | Legal | Sign-up did not show or record acceptance of the Terms and Privacy Policy (the old site recorded the versioned registration text) | Before launch | Claude | Fixed: the old site's wording, required, recorded with text and document versions |
| L6 | Legal | Merchant information was on the legal pages but not linked from the site footer | Before launch | Claude | Fixed |
| U1 | UX | The Copilot conversation was cleared when the language was switched (test task 5) | Later | Claude | Fixed: kept for the browser tab |

## What passed

- **Arabic and phone (Phase 7 build)**: `web/scripts/check-phase7.mjs` opens 22 pages (site and app) in Arabic and English at 1440px and 390px (88 page views). It checks `lang`/`dir`, the mirrored shell (sidebar right and Copilot left in Arabic), the fonts actually drawn (through Chrome DevTools: only Archivo, Martian Mono and IBM Plex Sans Arabic), numbers left-to-right, nothing wider than the screen, no page errors, and no English left in the Arabic interface. Result in `docs/screenshots/phase-7-sweep-local.txt`.
  - Fixed during the sweep: Arabic text drew in Arial on every page (next/font's Arial fallback came before IBM Plex Sans Arabic); chart months and the chart legend were in English; "vs", "P/E" and "12M" were untranslated on Sector vs Sector; a hydration error on My Portfolio when the shell answered "who am I" before the page hydrated.
  - Fixed from the 1440px and 390px screenshots (things the sweep cannot measure): Arabic small labels were spread apart by Martian Mono's wide spaces and letter-spacing; dates showed English month names ("13 Oct 2026" is now "13 أكتوبر 2026", digits still Latin); numeric table cells hugged the wrong side in Arabic; on the phone the chart legend scrambled label/number pairs and ran under the price scale.
- **Broken links**: 45 internal links on the public pages and 82 in the app, both languages: all resolve. External links go to argaam.com (news sources) and tradingview.com (chart attribution).
- **Dependencies**: `npm audit --omit=dev` and `pip-audit` report no known vulnerabilities.
- **Accounts**: passwords hashed with bcrypt; session cookie HttpOnly, SameSite=Lax, Secure on staging; cookie-authenticated writes check the Origin; sign-in rate-limited; no secrets in the repository; Postgres listens on localhost only with a generated password; staging sits behind basic auth with `X-Robots-Tag: noindex`.
- **Numbers**: the landing's numbers are all database values and match the API (Phase 6 check); /pricing reads the plan configuration; /methodology reads the council thresholds and freshness rules.
- **Legal pages**: the five documents (EN and AR) are the signed-off text, verbatim, with their content hashes (Phase 6 check).
- **Data freshness right now** (staging, live databases, 2026-10-15 03:49 UTC): prices and technical indicators to 2026-10-13 for current equities; fundamentals 2026-10-14; disclosures 2026-10-09 (allowed 120 days); news to 2026-10-14.

## Fixed after this report (owner Claude)

S1, S2, S3, S5, S6 (templates), D6, L5, L6 and U1, on `rebuild`. The Copilot stand-in still answers visitors who are not signed in; once a model key is set, it asks them to sign in. The sign-up acceptance uses the old site's registration text and versions verbatim (`api/app/legal.py`, checked against the documents by a test). Everything marked You stays open for you; D7 (retake the screens) waits until just before launch.

## To start user testing

1. **You**: add the DNS record `beta` → `72.60.91.24` in Cloudflare, DNS only (grey cloud). Then I issue the certificate (`certbot --nginx -d beta.alphacouncil.tech`, which touches only the beta site) and add HSTS.
2. **You**: give the five testers the staging login (the existing staging password; I never handle it).
3. Done: the Copilot runs on OpenRouter (`deepseek/deepseek-v3.2`); a dividend answer takes about 45–70 s and cites the panel it used (Phase 4 check). Testers must be signed in to ask (they are, after task 1).
4. The five tasks were walked by the checks: sign up and add three holdings (Phase 5 check), switch every panel from Aramco to Al Rajhi through the group chip (Phase 2 check), read when Aramco's price was updated (freshness light), ask about a holding's dividend and open the cited panel (Phase 4 check), switch to Arabic (Phase 7 sweep; the conversation now stays).
