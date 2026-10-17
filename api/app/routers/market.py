"""Market-wide views: Home overview, Markets table and the Screener's rows."""

from collections import defaultdict

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .. import ratios
from ..freshness import Freshness, assess
from ..market_db import MarketDataUnavailable, reader
from ..universe import EXCHANGE_ORDER, Universe
from .portfolio import LastClose, last_close
from .ticker import READABLE_SQL, TickerRef, merge_by_date, readable_first, ref_of, settings_of

router = APIRouter(tags=["market"])

# Exchange code in briefs -> index key in market_indices (only these three are collected).
INDEX_FOR = {"TADAWUL": "TASI", "ADX": "ADX", "DFM": "DFM"}
INDEX_WINDOW_DAYS = 2


def _uni(request: Request) -> Universe:
    u: Universe = request.app.state.universe
    try:
        u.refresh()
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc
    return u


class Index(BaseModel):
    key: str
    exchange: str
    name_en: str | None
    name_ar: str | None
    level: float | None
    change: float | None
    change_pct: float | None
    freshness: Freshness | None


def _indices(request: Request) -> dict[str, Index]:
    s = settings_of(request)
    if s.market_indices_db is None:
        return {}
    try:
        with reader(s.market_indices_db, immutable=s.market_db_immutable, name="MARKET_INDICES_DB") as conn:
            rows = conn.execute("SELECT market, name_en, name_ar, price, change_, change_pct, fetched_at FROM market_indices").fetchall()
    except MarketDataUnavailable:
        return {}
    by_key = {r["market"]: r for r in rows}
    out = {}
    for exchange, key in INDEX_FOR.items():
        r = by_key.get(key)
        if r is None:
            continue
        out[exchange] = Index(
            key=key,
            exchange=exchange,
            name_en=r["name_en"],
            name_ar=r["name_ar"],
            level=r["price"],
            change=r["change_"],
            change_pct=r["change_pct"],
            freshness=assess(category="prices", as_of_utc=r["fetched_at"], last_success_utc=r["fetched_at"],
                             max_age_days=INDEX_WINDOW_DAYS, exchange=exchange),
        )
    return out


class Mover(BaseModel):
    ticker: TickerRef
    price: LastClose


class Breadth(BaseModel):
    advancers: int
    decliners: int
    unchanged: int


class ExchangeSummary(BaseModel):
    exchange: str
    equities: int
    with_prices: int
    as_of: str | None
    breadth: Breadth
    index: Index | None


class NewsLine(BaseModel):
    ticker: TickerRef
    date: str | None
    title: str | None
    url: str | None
    lang: str | None
    # English headline written for a non-English item (news_ai), when there is one.
    title_en: str | None = None
    summary_en: str | None = None
    summary_ar: str | None = None


class Overview(BaseModel):
    exchanges: list[ExchangeSummary]
    gainers: list[Mover]
    losers: list[Mover]
    news: list[NewsLine]


def _closes(request: Request, uni: Universe) -> dict[str, LastClose]:
    return {t.ticker_key: last_close(request, t) for t in uni.tickers}


def _summaries(request: Request, uni: Universe, closes: dict[str, LastClose]) -> list[ExchangeSummary]:
    idx = _indices(request)
    by_ex: dict[str, list] = defaultdict(list)
    for t in uni.tickers:
        by_ex[t.exchange].append(t)
    out = []
    for ex in sorted(by_ex, key=lambda e: EXCHANGE_ORDER.index(e) if e in EXCHANGE_ORDER else 99):
        ts = by_ex[ex]
        px = [closes[t.ticker_key] for t in ts if closes[t.ticker_key].close is not None]
        latest = max((p.as_of for p in px if p.as_of), default=None)
        # Breadth counts only tickers that traded on the exchange's latest day.
        today = [p for p in px if p.as_of == latest and p.change_pct is not None]
        out.append(
            ExchangeSummary(
                exchange=ex,
                equities=len(ts),
                with_prices=len(px),
                as_of=latest,
                breadth=Breadth(
                    advancers=sum(1 for p in today if p.change_pct > 0),
                    decliners=sum(1 for p in today if p.change_pct < 0),
                    unchanged=sum(1 for p in today if p.change_pct == 0),
                ),
                index=idx.get(ex),
            )
        )
    return out


def _lang(url: str | None) -> str | None:
    return None if not url else "ar" if "/ar/" in url else "en" if "/en/" in url else None


@router.get("/market/overview", operation_id="marketOverview")
def overview(request: Request, movers: int = 6, lang: str | None = Query(None, pattern="^(en|ar)$")) -> Overview:
    uni = _uni(request)
    closes = _closes(request, uni)
    summaries = _summaries(request, uni, closes)
    latest_by_ex = {s.exchange: s.as_of for s in summaries}
    # Movers: only tickers that traded on their exchange's latest day.
    live = [
        (t, closes[t.ticker_key])
        for t in uni.tickers
        if closes[t.ticker_key].change_pct is not None and closes[t.ticker_key].as_of == latest_by_ex.get(t.exchange)
    ]
    live.sort(key=lambda tp: tp[1].change_pct)
    n = max(1, min(movers, 20))

    s = settings_of(request)
    news: list[NewsLine] = []
    try:
        select = (
            "SELECT i.id, i.ticker_key, i.date, i.title, i.url, n.headline_en,"
            " coalesce(nullif(i.ai_summary_en, ''), n.summary_en) AS summary_en,"
            " coalesce(nullif(i.ai_summary_ar, ''), n.summary_ar) AS summary_ar"
            " FROM items i LEFT JOIN news_ai n ON n.url = i.url WHERE i.section = 'news'"
            " AND i.date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'"
        )
        with reader(s.evidence_db, immutable=s.market_db_immutable, name="EVIDENCE_DB") as conn:
            rows = conn.execute(f"{select} ORDER BY i.date DESC LIMIT 200").fetchall()
            if lang in READABLE_SQL:
                # The newest items readable in the page's language, however far back they are.
                readable = conn.execute(f"{select} AND {READABLE_SQL[lang]} ORDER BY i.date DESC LIMIT 30").fetchall()
                rows = merge_by_date(rows, readable, key=lambda r: r["id"])
        seen = set()
        candidates: list[NewsLine] = []
        for r in rows:
            t = uni.by_key.get(r["ticker_key"])
            if t is None or r["title"] in seen:
                continue
            seen.add(r["title"])
            lang_of = _lang(r["url"])
            candidates.append(
                NewsLine(
                    ticker=ref_of(t), date=r["date"], title=r["title"], url=r["url"], lang=lang_of,
                    title_en=r["headline_en"] if lang_of != "en" else None,
                    summary_en=r["summary_en"] or None,
                    summary_ar=r["summary_ar"] or None,
                )
            )
        # The page's language first (a headline or summary in it counts).
        news = readable_first(candidates, lang, 10)
    except MarketDataUnavailable:
        pass

    return Overview(
        exchanges=summaries,
        gainers=[Mover(ticker=ref_of(t), price=p) for t, p in reversed(live[-n:]) if p.change_pct > 0],
        losers=[Mover(ticker=ref_of(t), price=p) for t, p in live[:n] if p.change_pct < 0],
        news=news,
    )


@router.get("/market/exchanges", operation_id="marketExchanges")
def exchanges(request: Request) -> list[ExchangeSummary]:
    uni = _uni(request)
    return _summaries(request, uni, _closes(request, uni))


class ScreenerRow(BaseModel):
    ticker: TickerRef
    price: LastClose
    market_cap_mn: float | None
    pe: float | None
    pb: float | None
    dividend_yield_pct: float | None
    roe_pct: float | None
    return_12m: float | None  # fraction
    vol_1y: float | None  # fraction
    rsi_14: float | None


@router.get("/screener", operation_id="screener")
def screener(request: Request) -> list[ScreenerRow]:
    """Every equity with the columns the Screener filters on. Missing values stay null."""
    uni = _uni(request)
    s = settings_of(request)
    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            briefs = {
                r["ticker_key"]: r
                for r in conn.execute(
                    "SELECT ticker_key, market_cap_raw, return_12m, vol_1y FROM briefs"
                )
            }
            tech = {r["ticker_key"]: r["rsi_14"] for r in conn.execute("SELECT ticker_key, rsi_14 FROM ticker_tech_snapshot WHERE status = 'ok'")}
        rv = ratios.load(s)
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc

    order = {ex: i for i, ex in enumerate(EXCHANGE_ORDER)}
    rows = []
    for t in sorted(uni.tickers, key=lambda t: (order.get(t.exchange, 99), t.symbol)):
        b, r = briefs.get(t.ticker_key), rv.get(t.ticker_key)
        rows.append(
            ScreenerRow(
                ticker=ref_of(t),
                price=last_close(request, t),
                market_cap_mn=b["market_cap_raw"] if b else None,
                pe=r["pe"],
                pb=r["pb"],
                dividend_yield_pct=r["dividend_yield_pct"],
                roe_pct=r["roe_pct"],
                return_12m=b["return_12m"] if b else None,
                vol_1y=b["vol_1y"] if b else None,
                rsi_14=tech.get(t.ticker_key),
            )
        )
    return rows
