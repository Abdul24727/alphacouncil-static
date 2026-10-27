# alphacouncil-platform

Project plan and current step live in PROJECT.md — read it before starting work.

The rebuilt AlphaCouncil: a dense research terminal for Gulf markets (Tadawul, ADX, DFM, QSE, Boursa Kuwait, BHB, MSX).

## Layout

- `web/` — Next.js 16 (App Router) + React + TypeScript. Tailwind v4 with BRAND.md tokens, Radix UI, react-grid-layout, Lightweight Charts, TanStack Query + Zustand, TanStack Table, Vercel AI SDK, next-intl (Arabic RTL + English). Read `web/AGENTS.md` before writing Next.js code.
- `api/` — Python FastAPI (migrated from `llm-council/backend` in the old repo). Postgres for app data, Redis for live prices and cache, WebSocket streams for live panels. Its OpenAPI schema generates the typed client in `web/src/lib/api/`.
- The data pipeline (scrapers, council jobs) stays in the old repo and keeps writing to the same database.

## Data facts (from the Phase 1 survey of the old repo)

- Market data is SQLite written nightly by the pipeline, not Postgres. `/api` opens it read-only by explicit path (`api/.env`, see `.env.example`). The universe is the `briefs` table: 716 rows, `ticker_key` = `SYMBOL_EXCHANGE`, exchange codes TADAWUL, ADX, DFM, QSE, KSE (Boursa Kuwait), BSE (BHB), MSM (MSX).
- Company names are not in any database: Arabic and URL slug come from `argaam/tickers_universe_corrected.csv`, curated Saudi English names from `argaam/tickers_saudi_en_names.csv` (ported in `api/app/names.py`).
- Freshness source for later phases: `ticker_freshness` in `screening.sqlite`. Daily OHLCV lives in per-ticker CSVs on the VPS, not in a database, and is not on this machine.
- The local snapshot `briefs_index.sqlite` also holds real user and billing tables. Read only the ticker tables; never copy the file into this repo.

- Units: `market_cap_*`, statement lines and capital figures are millions of the listing currency; `briefs.return_*`, `vol_1y`, `max_drawdown` are fractions; yields, ROE and tech distances are percents. KWD, BHD, OMR prices need 3 decimals.
- `briefs.pe` is null for every Tadawul row; P/E comes from `scraped_ratios`. Ownership/analyst data in `ticker_insights` is null everywhere (not collected yet). There is no cash-flow statement.
- The council (`api/app/council.py`) is six deterministic seats over database values (thresholds from the old strategy lenses); no LLM, no blended score. Every threshold lives in `THRESHOLDS`; the API returns them with each seat and on `/v1/methodology`, and the UI messages (`stock.council.rules.*`) take them as ICU arguments, so /methodology and the council panel cannot drift from the votes.
- Accounts: sign-up requires the old site's registration acceptance and records it in `consents` (text and document versions in `api/app/legal.py`, tested against `web/src/content/legal`). Settings › Delete account removes the user and everything that cascades from it. The old site's members were imported without a password (`docs/account-import.md`); one without an acceptance accepts on the new-password page. Rate limits key on nginx's `X-Real-IP`, never on `X-Forwarded-For`, and are counted in the app database (`rate_hits`) so all uvicorn workers share them.
- Copilot: the provider and model come from the environment only (`COPILOT_PROVIDER` auto|openrouter|anthropic|standin, `COPILOT_MODEL`; keys `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` live in the server env file, never in git). `app/copilot/openai_compat.py` (OpenRouter or any OpenAI-compatible endpoint) and `engine.py` (Claude) share the prompt, tools and stream format. 60 questions an hour per user or address; with a model configured it answers signed-in users only (`/v1/copilot/status` says `sign_in_required`). Staging runs `deepseek/deepseek-v3.2` on OpenRouter.
- Plan prices: `api/app/pricing.py`, ported from the old backend with the same env variables (PRICE_PRO_SAR, ELITE_ENABLED) the Moyasar checkout uses. The Pro checkout (`api/app/billing.py`, Moyasar) is open on production since 2026-10-18; runbook: `docs/production.md`.

## Next.js 16 patterns used here

- With Cache Components, Next keeps the previous route mounted but hidden (React `<Activity>`), so the DOM can hold two copies of a panel. Anything that finds panels (citations, tests) must pick the visible one (`:visible`, `checkVisibility()`).

- Locale is in the URL (`[locale]` segment, `localePrefix: "as-needed"`): English keeps `/home`, Arabic is `/ar/home`. `src/proxy.ts` is the old `middleware`.
- `cacheComponents` is on: request data (`params`, `cookies()`, `usePathname()`) must sit behind `<Suspense>`. Use `components/shell/WithPathname` for pathname-dependent UI, and wrap `await params` of dynamic routes in a Suspense child (see `t/[ticker]/page.tsx`).
- Dev mode does not enforce the prerender rules: run `npx next build` before deploying. Every segment under `[locale]` calls `setRequestLocale(locale)`, or next-intl falls back to request headers and the build fails.
- Public pages (`/`, `/pricing`, `/methodology`, `/legal/*`) are the `(site)` route group: server components that read the API through `lib/api/server.ts` (it calls `connection()` first, so callers sit behind `<Suspense>`). Every digit on them is wrapped in `<Db>` (`data-db`); `scripts/check-phase6.mjs` fails any other. /markets and /templates stay in the app shell (no sign-in needed) and are linked from the site.
- `next.config.ts` sends a Content-Security-Policy (no nonces, so shells stay prerendered) and the usual hardening headers. Anything loaded from another origin needs a CSP change first.
- Legal texts are copied verbatim from the old site by `scripts/import-legal.py` into `src/content/legal/`; never edit that JSON by hand.
- Fonts: globals.css lists the bare faces first (`--face-*`, set in `[locale]/layout.tsx`), then next/font's variables. next/font's metric fallbacks are local Arial, which has Arabic letters: listed earlier, they draw every Arabic glyph in Arial.
- Metadata: every page's `generateMetadata` goes through `lib/seo.ts` (`localizedMetadata`, `privateMetadata`), which sets the canonical, hreflang and cards on https://alphacouncil.tech. Next replaces `openGraph`/`twitter` per segment instead of merging, so never set them partially. robots.txt, sitemap.xml and the cards: docs/production.md, "Search engines and link previews".
- Landing and /templates images are real app screens: `node scripts/capture-screens.mjs` (point BASE_URL at the staging tunnel for live data) writes `src/assets/screens/`.
- Pane sizes persist in localStorage (`ac-layout`) and are applied before paint by `LAYOUT_BOOT_SCRIPT`; signed-in users' panes, chart and display settings sync to `/v1/me/prefs` (lib/prefs-sync.ts).

## Standing rules

- Work only on git branch `rebuild`. Never push to main.
- Remote `origin` = the owner's private GitHub repository `https://github.com/Abdul24727/alphacouncil-static` (its other branches hold the old static site; push `rebuild` only, never force).
- alphacouncil.tech runs this app (since 2026-10-17). Release only beta → production with `scripts/deploy-staging.sh` then `scripts/deploy-production.sh`, and only with the owner's go-ahead for that release.
- Do not change the old repos (`alphacouncil-static`, `Argaam-council-…`) or the old pipeline on the server (`/opt/alphacouncil/backend`): read them for reference only, unless the owner approves a specific change (PROJECT.md, Goal 2).
- Follow BRAND.md exactly. Anything it bans is a bug.
- Never show a number that is not from our database. Missing data = a labelled placeholder or "Data unavailable", never an estimate.
- Before saying a step is done: run the app, screenshot the page at 1440px and 390px wide, and show it.
- If something is unclear or risky, stop and ask instead of guessing.
- Run a chat to the end of its room: hand over at about 80% of context, not when a goal finishes or the
  obvious work runs out (owner, 2026-10-27). The full rule, and the `/goal` wording a handover block must
  print, are in `~/.claude/CLAUDE.md`; they override the `project-loop` skill's budget gate and template.
