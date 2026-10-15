# alphacouncil-platform

The rebuilt AlphaCouncil: a research terminal for Gulf markets. See [CLAUDE.md](CLAUDE.md) for the architecture and rules, and [BRAND.md](BRAND.md) for the design system.

## Run locally

```bash
# API (port 8000). First time: cp api/.env.example api/.env and fill in the paths.
cd api && uv sync && uv run uvicorn app.main:app --port 8000 --reload
```

```bash
# Web (port 3100). Proxies /api/v1/* to the API.
cd web && npm install && npm run dev -- -p 3100
```

Open http://localhost:3100. Arabic lives under `/ar`, e.g. http://localhost:3100/ar/home.

## Checks

```bash
cd api && uv run pytest
```

```bash
cd web && npm run typecheck && npm run lint
```

```bash
# Screenshots at 1440px and 390px into docs/screenshots/<phase>/ (needs both servers running)
cd web && node scripts/screenshots.mjs phase-1
```

Each phase's "Done when" has a check script (`web/scripts/check-phase2.mjs` … `check-phase7.mjs`); run one with `BASE_URL=http://localhost:3100 node scripts/check-phase6.mjs`, or against staging through the SSH tunnel with `BASE_URL=http://localhost:3201`. Content scripts: `capture-screens.mjs` retakes the real app screens used on the landing and /templates; `import-legal.py` copies the legal documents from the old site. The pre-launch audit is `docs/pre-launch-audit.md`.

## API contract

The API's OpenAPI schema (`api/openapi.json`) generates the web client types. After changing the API:

```bash
cd api && uv run python -m app.export_openapi && cd ../web && npm run gen:api
```
