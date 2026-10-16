"""One value per valuation ratio, whichever screen shows it.

P/E, P/B, dividend yield, ROE and ROA each exist in three pipeline tables (`stocks`,
computed from statements; `scraped_ratios`, published TTM; `briefs`, the nightly
digest), refreshed at different times. Key metrics, the Financials tab, the screener,
peers, templates and the council all read them through `RatioSources`, so one ticker
shows one number everywhere.

Rules: `stocks` first, then `scraped_ratios`, then `briefs` (P/E has no `stocks`
column). A ratio that is not meaningful is null, never a number: P/E when earnings
are zero or negative, P/B and ROE when book value is negative, EV/EBITDA where the
fundamentals gauge marks it not applicable to the sector.
"""

from collections.abc import Iterable
from typing import Any

from .market_db import reader
from .settings import Settings

NOT_APPLICABLE = {"na_sector", "undefined_nonpositive"}


def _get(row: Any, key: str) -> Any:
    return row[key] if row is not None and key in row.keys() else None


def _first(*values: Any) -> Any:
    return next((v for v in values if v is not None), None)


class RatioSources:
    """The three tables' rows (and the EV/EBITDA gauge status) for some or all tickers."""

    def __init__(self, briefs: dict, scraped: dict, stocks: dict, ev_gauge: dict):
        self.briefs, self.scraped, self.stocks, self.ev_gauge = briefs, scraped, stocks, ev_gauge

    def get(self, ticker_key: str) -> dict[str, float | None]:
        b, sc, st = self.briefs.get(ticker_key), self.scraped.get(ticker_key), self.stocks.get(ticker_key)
        pe = _first(_get(sc, "pe"), _get(b, "pe"))
        pb = _first(_get(st, "pb"), _get(sc, "pb"), _get(b, "pb"))
        book = _get(sc, "book_value")
        negative_equity = (pb is not None and pb < 0) or (book is not None and book < 0)
        roe = _first(_get(st, "roe_pct"), _get(sc, "roe"), _get(b, "roe_pct"))
        ev_ebitda = _get(sc, "ev_ebitda")
        return {
            "pe": pe if pe is not None and pe > 0 else None,
            "pb": pb if pb is not None and pb > 0 and not negative_equity else None,
            "dividend_yield_pct": _first(_get(st, "dividend_yield_pct"), _get(sc, "div_yield"), _get(b, "dividend_yield_pct")),
            # ROE over negative equity reads as a high positive return: not meaningful.
            "roe_pct": None if negative_equity else roe,
            "roa_pct": _first(_get(st, "roa_pct"), _get(sc, "roa")),
            "ev_ebitda": None if self.ev_gauge.get(ticker_key) in NOT_APPLICABLE else ev_ebitda,
        }


def load(s: Settings, ticker_keys: Iterable[str] | None = None) -> RatioSources:
    """All tickers, or just `ticker_keys`. Raises MarketDataUnavailable like any market read."""
    keys = list(ticker_keys) if ticker_keys is not None else None
    where = f" WHERE ticker_key IN ({','.join('?' * len(keys))})" if keys else ""
    args = tuple(keys) if keys else ()

    def rows(conn, sql: str, extra: str = "") -> dict:
        if keys is not None and not keys:
            return {}
        clause = where + (f" AND {extra}" if where and extra else f" WHERE {extra}" if extra else "")
        return {r["ticker_key"]: r for r in conn.execute(sql + clause, args)}

    with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
        briefs = rows(conn, "SELECT ticker_key, pe, pb, dividend_yield_pct, roe_pct FROM briefs")
    with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
        scraped = rows(conn, "SELECT ticker_key, pe, pb, div_yield, roe, roa, ev_ebitda, book_value FROM scraped_ratios")
        stocks = rows(conn, "SELECT ticker_key, pb, roe_pct, roa_pct, dividend_yield_pct FROM stocks")
        ev_gauge = {
            k: r["status"]
            for k, r in rows(conn, "SELECT ticker_key, status FROM fundamentals_gauges", "gauge_key = 'ev_ebitda'").items()
        }
    return RatioSources(briefs, scraped, stocks, ev_gauge)
