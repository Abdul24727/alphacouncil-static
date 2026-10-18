# Prompt: audit of AlphaCouncil's data (scraper, integrity, delivery, freshness)

Paste everything below the line into a new agent session.

---

You are auditing the market data behind https://alphacouncil.tech, a research terminal for Gulf (GCC) listed equities (Tadawul, ADX, DFM, QSE, Boursa Kuwait, Bahrain Bourse, Muscat; about 716 tickers). The site shows only numbers from its own database; anything missing must be labelled, never estimated. Your job is to measure how good that data is and report it. **This is a read-only review: change nothing.**

## Where things are

- Server: `ssh root@alphacouncil.tech` (key-based). The site's code: repo `C:\projects\alphacouncil-platform` (branch `rebuild`); `docs/production.md` describes the server layout.
- The data pipeline (scraper) is the old system's code under `/opt/alphacouncil/backend/` (the scraper lives under `argaam/`; the source for most data is Argaam). Find out how and when it runs (cron, systemd timers, its logs, e.g. under `/opt/alphacouncil/logs`).
- Its outputs, which the site reads read-only (paths are in `/etc/alphacouncil-platform/prod/api.env`; read only the path variables):
  - `/var/lib/alphacouncil/briefs_index.sqlite` (quotes, briefs, per-category freshness)
  - `/var/lib/alphacouncil/screening.sqlite` (fundamentals, ratios, gauges, insights such as ownership and seasonality)
  - `/var/lib/alphacouncil/evidence.sqlite` (news, disclosures, events; `news_ai` summaries)
  - `/var/lib/alphacouncil/market_indices.sqlite`
  - price history files under `/opt/alphacouncil/backend/argaam/default_universe/`
  - the universe lists `tickers_universe_corrected.csv` and `tickers_saudi_en_names.csv`
- How the site turns that into numbers: `api/app/` in the repo. Freshness rules are in `freshness.py`; the one rule per ratio is in `ratios.py`; prices and the quote are in `prices.py` and `routers/ticker.py`; sectors are in `universe.py`.

## Rules (strict)

- Read-only. Do not edit, restart, re-run or reschedule anything: no pipeline runs, no cron or nginx changes, no writes to any database or file on the server.
- Open SQLite files read-only (`file:...?mode=ro&immutable=1`). If a heavy query is needed, copy the file to `/tmp` on the server, work on the copy, and delete it afterwards. Never copy databases into the repo or off the server.
- Never print secrets: do not cat env files; grep only the variable names and paths you need.
- `briefs_index.sqlite` also holds the old site's user, account, billing and history tables. **Do not read those tables.** Market-data tables only.
- External spot checks (exchange or Argaam pages) are allowed for a small sample, slowly (one request every few seconds), respecting robots.txt. Do not scrape at scale.
- Report facts with the query or command that produced them. If you cannot measure something, say so; do not estimate.

## What to measure

1. **Scraper performance.** Schedule and run history for the last 30 days (from logs and file or row timestamps): start and end times, duration, runs that failed or were partial, error types (HTTP errors, parse failures, timeouts), retries, and run-to-run variance. Success rate per exchange and per data category (prices, fundamentals, news, disclosures, events, ownership).
2. **Coverage.** For each exchange: tickers in the universe, tickers with price history, with fundamentals, with news or disclosures in the last 30 and 90 days, with ownership data. List tickers that have nothing.
3. **Freshness.** For each category and exchange, the distribution of data age at the time of the review, compared with what is expected given each exchange's trading days and weekends (Tadawul, QSE and Boursa Kuwait trade Sunday to Thursday; ADX and DFM Monday to Friday; check Bahrain and Muscat). Count tickers that are stale beyond `max_age_days`, and why: suspended or delisted, or a scraper gap. Check that the site's freshness lights agree with the data (sample about 20 stock pages against `/api/v1/tickers/{ref}` and `/freshness`).
4. **Integrity.** Price files: gaps on trading days, duplicate dates, zero or negative prices, OHLC inconsistencies (high < low, close outside the range), day-over-day jumps over 30% without a corporate action, splits or bonus shares not adjusted. Fundamentals: impossible or contradictory values (negative equity with a positive P/B, P/E from negative earnings), the same ratio differing across tables, wrong units or currency (fils and baisa for KWD, BHD, OMR), stale statements. News and events: duplicates, wrong ticker mapping, missing dates, the share of English vs Arabic items and of English headlines or summaries. Sectors: misclassified tickers (Tadawul `sector_id` 1 is a known default bucket). Ownership: repeated dates, nameless holders.
5. **Accuracy vs the outside world.** For a random sample of about 30 tickers spread across all seven exchanges, compare the latest close, the date of the close, market cap, the last dividend and the P/E with a public source. Report each match or mismatch with the source and its date.
6. **Delivery (database to API to page).** For the same sample, confirm that what the site shows equals the database: the stock page's key metrics, financials, price chart (last bar) and header price against the database and the API. Note anything shown that is not in the database, or a value that is in the database but missing on the page.

## What to deliver

A report at `docs/data-audit-<date>.md` in the repo (the only file you write), with:

- a one-screen summary: a scorecard for each area (scraper performance, coverage, freshness, integrity, accuracy, delivery) with the key numbers;
- the findings, each with severity (blocker / major / minor), the evidence (query or command plus its output, trimmed), affected tickers, and whether the cause is the pipeline or the web app;
- a prioritised list of fixes, and what to monitor from now on (metrics and thresholds).

Do not fix anything. If you find something that looks urgent (for example the pipeline has stopped), say so at the top of the report and stop there.
