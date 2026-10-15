# alphacouncil-platform

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

## Next.js 16 patterns used here

- Locale is in the URL (`[locale]` segment, `localePrefix: "as-needed"`): English keeps `/home`, Arabic is `/ar/home`. `src/proxy.ts` is the old `middleware`.
- `cacheComponents` is on: request data (`params`, `cookies()`, `usePathname()`) must sit behind `<Suspense>`. Use `components/shell/WithPathname` for pathname-dependent UI, and wrap `await params` of dynamic routes in a Suspense child (see `t/[ticker]/page.tsx`).
- Pane sizes persist in localStorage (`ac-layout`) and are applied before paint by `LAYOUT_BOOT_SCRIPT`; they move to per-user server preferences once `/api` has accounts.

## Standing rules

- Work only on git branch `rebuild`. Never push to main, never deploy to alphacouncil.tech.
- Do not touch the live alphacouncil.tech or the old repos (`alphacouncil-static`, `Argaam-council-…`). Read them for reference only.
- Follow BRAND.md exactly. Anything it bans is a bug.
- Never show a number that is not from our database. Missing data = a labelled placeholder or "Data unavailable", never an estimate.
- Before saying a step is done: run the app, screenshot the page at 1440px and 390px wide, and show it.
- If something is unclear or risky, stop and ask instead of guessing.
