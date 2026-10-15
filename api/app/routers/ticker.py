"""Per-ticker data for the stock template panels. Every value comes from the
pipeline's databases; anything missing is returned as null, never estimated."""

import sqlite3

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..freshness import Freshness, assess
from ..market_db import MarketDataUnavailable, reader
from ..settings import Settings
from ..universe import Ticker, Universe

router = APIRouter(prefix="/tickers/{ref}", tags=["ticker"])


class TickerRef(BaseModel):
    ticker_key: str
    symbol: str
    exchange: str
    currency: str | None
    name_en: str | None
    name_ar: str | None
    sector_en: str | None
    sector_ar: str | None
    slug: str


class Quote(BaseModel):
    as_of_date: str | None
    # Freshness of these quote values themselves (briefs.as_of_date), judged by the prices window.
    freshness: Freshness | None
    last_price: float | None
    day_change_pct: float | None
    volume: float | None
    value_traded: float | None
    market_cap_mn: float | None


class Valuation(BaseModel):
    pe: float | None
    pb: float | None
    dividend_yield_pct: float | None
    roe_pct: float | None
    roa_pct: float | None
    ev_ebitda: float | None
    eps_ttm: float | None
    book_value: float | None
    shares_out_mn: float | None


class Returns(BaseModel):
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    return_12m: float | None
    vol_1y: float | None
    max_drawdown: float | None


class Technicals(BaseModel):
    as_of_date: str | None
    rsi_14: float | None
    sma_50: float | None
    sma_200: float | None
    above_50d: bool | None
    above_200d: bool | None
    macd_bull: bool | None
    dist_to_52w_high: float | None
    dist_from_52w_low: float | None


class TickerDetail(BaseModel):
    ticker: TickerRef
    quote: Quote
    valuation: Valuation
    returns: Returns
    technicals: Technicals
    has_price_history: bool
    freshness: list[Freshness]


def ref_of(t: Ticker) -> TickerRef:
    return TickerRef(
        ticker_key=t.ticker_key,
        symbol=t.symbol,
        exchange=t.exchange,
        currency=t.currency,
        name_en=t.name_en,
        name_ar=t.name_ar,
        sector_en=t.sector_en,
        sector_ar=t.sector_ar,
        slug=t.slug,
    )


def resolve(request: Request, ref: str) -> Ticker:
    universe: Universe = request.app.state.universe
    try:
        t = universe.resolve(ref)
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc
    if t is None:
        raise HTTPException(404, f"Unknown ticker: {ref}")
    return t


def settings_of(request: Request) -> Settings:
    return request.app.state.settings


def _row(conn: sqlite3.Connection, sql: str, *args) -> sqlite3.Row | None:
    return conn.execute(sql, args).fetchone()


def _flag(v) -> bool | None:
    return None if v is None else bool(v)


def load_freshness(s: Settings, t: Ticker) -> list[Freshness]:
    with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
        rows = conn.execute(
            "SELECT category, as_of_utc, last_success_utc, max_age_days FROM ticker_freshness"
            " WHERE ticker_key = ? ORDER BY category",
            (t.ticker_key,),
        ).fetchall()
    return [
        assess(
            category=r["category"],
            as_of_utc=r["as_of_utc"],
            last_success_utc=r["last_success_utc"],
            max_age_days=r["max_age_days"],
            exchange=t.exchange,
        )
        for r in rows
    ]


@router.get("", operation_id="getTicker")
def get_ticker(request: Request, ref: str) -> TickerDetail:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            b = _row(
                conn,
                "SELECT as_of_date, last_price, day_change_pct, volume, value_traded, market_cap_raw,"
                " pe, pb, dividend_yield_pct, roe_pct, return_1m, return_3m, return_6m, return_12m,"
                " vol_1y, max_drawdown, has_price_history, source_run_ts FROM briefs WHERE ticker_key = ?",
                t.ticker_key,
            )
            tech = _row(
                conn,
                "SELECT as_of_date, rsi_14, sma_50, sma_200, above_50d, above_200d, macd_bull,"
                " dist_to_52w_high, dist_from_52w_low FROM ticker_tech_snapshot"
                " WHERE ticker_key = ? AND status = 'ok'",
                t.ticker_key,
            )
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            sr = _row(
                conn,
                "SELECT pe, pb, div_yield, roe, roa, ev_ebitda, eps_ttm, book_value, shares_out_mn"
                " FROM scraped_ratios WHERE ticker_key = ?",
                t.ticker_key,
            )
        freshness = load_freshness(s, t)
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc

    b = b or {}
    sr = sr or {}
    tech = tech or {}
    get = lambda row, k: row[k] if row and k in row.keys() else None  # noqa: E731

    prices = next((f for f in freshness if f.category == "prices"), None)
    quote_freshness = (
        assess(
            category="prices",
            as_of_utc=get(b, "as_of_date"),
            last_success_utc=get(b, "source_run_ts"),
            max_age_days=prices.max_age_days if prices else None,
            exchange=t.exchange,
        )
        if get(b, "as_of_date")
        else None
    )

    return TickerDetail(
        ticker=ref_of(t),
        quote=Quote(
            as_of_date=get(b, "as_of_date"),
            freshness=quote_freshness,
            last_price=get(b, "last_price"),
            day_change_pct=get(b, "day_change_pct"),
            volume=get(b, "volume"),
            value_traded=get(b, "value_traded"),
            market_cap_mn=get(b, "market_cap_raw"),
        ),
        # briefs first (the nightly price-derived values), scraped ratios fill gaps.
        valuation=Valuation(
            pe=get(b, "pe") if get(b, "pe") is not None else get(sr, "pe"),
            pb=get(b, "pb") if get(b, "pb") is not None else get(sr, "pb"),
            dividend_yield_pct=(
                get(b, "dividend_yield_pct") if get(b, "dividend_yield_pct") is not None else get(sr, "div_yield")
            ),
            roe_pct=get(b, "roe_pct") if get(b, "roe_pct") is not None else get(sr, "roe"),
            roa_pct=get(sr, "roa"),
            ev_ebitda=get(sr, "ev_ebitda"),
            eps_ttm=get(sr, "eps_ttm"),
            book_value=get(sr, "book_value"),
            shares_out_mn=get(sr, "shares_out_mn"),
        ),
        returns=Returns(
            return_1m=get(b, "return_1m"),
            return_3m=get(b, "return_3m"),
            return_6m=get(b, "return_6m"),
            return_12m=get(b, "return_12m"),
            vol_1y=get(b, "vol_1y"),
            max_drawdown=get(b, "max_drawdown"),
        ),
        technicals=Technicals(
            as_of_date=get(tech, "as_of_date"),
            rsi_14=get(tech, "rsi_14"),
            sma_50=get(tech, "sma_50"),
            sma_200=get(tech, "sma_200"),
            above_50d=_flag(get(tech, "above_50d")),
            above_200d=_flag(get(tech, "above_200d")),
            macd_bull=_flag(get(tech, "macd_bull")),
            dist_to_52w_high=get(tech, "dist_to_52w_high"),
            dist_from_52w_low=get(tech, "dist_from_52w_low"),
        ),
        has_price_history=bool(get(b, "has_price_history")),
        freshness=freshness,
    )


@router.get("/freshness", operation_id="getTickerFreshness")
def get_freshness(request: Request, ref: str) -> list[Freshness]:
    t = resolve(request, ref)
    try:
        return load_freshness(settings_of(request), t)
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc


class PeerRow(BaseModel):
    ticker: TickerRef
    as_of_date: str | None
    last_price: float | None
    day_change_pct: float | None
    market_cap_mn: float | None
    pe: float | None
    dividend_yield_pct: float | None


class Peers(BaseModel):
    basis: str  # "sector_exchange" or "sector_gcc"
    sector_en: str | None
    sector_ar: str | None
    peers: list[PeerRow]


@router.get("/peers", operation_id="getTickerPeers")
def get_peers(request: Request, ref: str, limit: int = 8) -> Peers:
    """Same sector on the same exchange, largest first; across the GCC if fewer than 3."""
    t = resolve(request, ref)
    s = settings_of(request)
    universe: Universe = request.app.state.universe
    limit = max(1, min(limit, 20))
    if not t.sector_en:
        return Peers(basis="sector_exchange", sector_en=None, sector_ar=None, peers=[])

    sql = (
        "SELECT ticker_key, as_of_date, last_price, day_change_pct, market_cap_raw, pe, dividend_yield_pct"
        " FROM briefs WHERE sector_en = ? AND ticker_key != ? {extra}"
        " ORDER BY market_cap_raw IS NULL, market_cap_raw DESC LIMIT ?"
    )
    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            rows = conn.execute(sql.format(extra="AND exchange = ?"), (t.sector_en, t.ticker_key, t.exchange, limit)).fetchall()
            basis = "sector_exchange"
            if len(rows) < 3:
                rows = conn.execute(sql.format(extra=""), (t.sector_en, t.ticker_key, limit)).fetchall()
                basis = "sector_gcc"
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc

    peers = []
    for r in rows:
        p = universe.by_key.get(r["ticker_key"])
        if p is None:
            continue
        peers.append(
            PeerRow(
                ticker=ref_of(p),
                as_of_date=r["as_of_date"],
                last_price=r["last_price"],
                day_change_pct=r["day_change_pct"],
                market_cap_mn=r["market_cap_raw"],
                pe=r["pe"],
                dividend_yield_pct=r["dividend_yield_pct"],
            )
        )
    return Peers(basis=basis, sector_en=t.sector_en, sector_ar=t.sector_ar, peers=peers)


class NewsItem(BaseModel):
    id: str
    section: str  # news | disclosures | events
    date: str | None  # ISO; disclosures and events carry 21:00 UTC = midnight Riyadh
    title: str | None
    url: str | None
    lang: str | None
    snippet: str | None
    summary_en: str | None
    summary_ar: str | None
    impact: str | None


def _lang_of(url: str | None) -> str | None:
    if not url:
        return None
    return "ar" if "/ar/" in url else "en" if "/en/" in url else None


def _items(request: Request, ref: str, sections: tuple[str, ...], limit: int, upcoming: bool = False) -> list[NewsItem]:
    t = resolve(request, ref)
    s = settings_of(request)
    limit = max(1, min(limit, 50))
    marks = ",".join("?" for _ in sections)
    order = "ASC" if upcoming else "DESC"
    when = "AND i.date >= date('now', '-1 day')" if upcoming else ""
    try:
        with reader(s.evidence_db, immutable=s.market_db_immutable, name="EVIDENCE_DB") as conn:
            rows = conn.execute(
                "SELECT i.id, i.section, i.date, i.title, i.url, i.snippet, i.ai_summary_en, i.ai_summary_ar,"
                " n.headline_en, n.summary_en AS n_summary_en, n.summary_ar AS n_summary_ar, n.impact"
                " FROM items i LEFT JOIN news_ai n ON n.url = i.url"
                f" WHERE i.ticker_key = ? AND i.section IN ({marks})"
                " AND i.date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'"
                f" {when} ORDER BY i.date {order} LIMIT ?",
                (t.ticker_key, *sections, limit),
            ).fetchall()
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc
    return [
        NewsItem(
            id=r["id"],
            section=r["section"],
            date=r["date"],
            title=r["title"],
            url=r["url"],
            lang=_lang_of(r["url"]),
            snippet=r["snippet"] or None,
            summary_en=r["ai_summary_en"] or r["n_summary_en"],
            summary_ar=r["ai_summary_ar"] or r["n_summary_ar"],
            impact=r["impact"],
        )
        for r in rows
    ]


@router.get("/news", operation_id="getTickerNews")
def get_news(request: Request, ref: str, limit: int = 12) -> list[NewsItem]:
    """Latest news and disclosures touching this ticker."""
    return _items(request, ref, ("news", "disclosures"), limit)


@router.get("/events", operation_id="getTickerEvents")
def get_events(request: Request, ref: str, limit: int = 20, upcoming: bool = False) -> list[NewsItem]:
    """Corporate calendar: dividends, assemblies, results dates."""
    return _items(request, ref, ("events",), limit, upcoming=upcoming)
