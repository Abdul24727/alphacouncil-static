"""Per-ticker data for the stock template panels. Every value comes from the
pipeline's databases; anything missing is returned as null, never estimated."""

import sqlite3

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .. import ratios
from ..freshness import PRICE_MAX_AGE_DAYS, Freshness, assess
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
    # Freshness of these quote values themselves, judged by the prices window.
    freshness: Freshness | None
    # "prices_file" whenever the ticker has a daily price file; "briefs" otherwise.
    source: str
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
    from .prices import bar_freshness, latest_bars  # local import: prices imports this module

    # The daily price file is the record of prices: when it exists, the quote is its last
    # close, dated by that bar (briefs stamps old prices with the run date). Without a file,
    # the briefs price is dated only by the pipeline's own price record, never by the run date.
    bars = latest_bars(request, t.ticker_key)
    if bars:
        last = bars[-1]
        prev = bars[-2] if len(bars) >= 2 else None
        quote = Quote(
            as_of_date=last.time,
            source="prices_file",
            freshness=bar_freshness(request, t.ticker_key, t.exchange, bars),
            last_price=last.close,
            day_change_pct=round((last.close / prev.close - 1) * 100, 2) if prev else None,
            volume=last.volume,
            value_traded=last.turnover,
            market_cap_mn=get(b, "market_cap_raw"),
        )
    else:
        # An old briefs row proves the price is at least that old (stale); a recent one is
        # only the run date, so without the pipeline's price record the age is unknown.
        rec = prices if prices and prices.as_of else None
        if rec is None and get(b, "as_of_date"):
            from_briefs = assess(
                category="prices",
                as_of_utc=get(b, "as_of_date"),
                last_success_utc=get(b, "source_run_ts"),
                max_age_days=PRICE_MAX_AGE_DAYS,
                exchange=t.exchange,
            )
            rec = from_briefs if from_briefs.stale else None
        quote = Quote(
            as_of_date=rec.as_of[:10] if rec else None,
            source="briefs",
            freshness=rec,
            last_price=get(b, "last_price"),
            day_change_pct=get(b, "day_change_pct"),
            volume=get(b, "volume"),
            value_traded=get(b, "value_traded"),
            market_cap_mn=get(b, "market_cap_raw"),
        )
    try:
        r = ratios.load(s, [t.ticker_key]).get(t.ticker_key)
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc

    return TickerDetail(
        ticker=ref_of(t),
        quote=quote,
        # The same values every other screen shows (app/ratios.py).
        valuation=Valuation(
            pe=r["pe"],
            pb=r["pb"],
            dividend_yield_pct=r["dividend_yield_pct"],
            roe_pct=r["roe_pct"],
            roa_pct=r["roa_pct"],
            ev_ebitda=r["ev_ebitda"],
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
        # Same rule as /prices: a chart needs at least two bars in the price file.
        has_price_history=bool(bars) and len(bars) >= 2,
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
        "SELECT ticker_key, as_of_date, last_price, day_change_pct, market_cap_raw"
        " FROM briefs WHERE sector_en = ? AND ticker_key != ? {extra}"
        " ORDER BY market_cap_raw IS NULL, market_cap_raw DESC"
    )

    def same_sector(found) -> list:
        # The universe drops sector labels it knows are wrong (universe.py): those rows are not peers.
        return [r for r in found if (p := universe.by_key.get(r["ticker_key"])) and p.sector_en == t.sector_en][:limit]

    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            rows = same_sector(conn.execute(sql.format(extra="AND exchange = ?"), (t.sector_en, t.ticker_key, t.exchange)).fetchall())
            basis = "sector_exchange"
            if len(rows) < 3:
                rows = same_sector(conn.execute(sql.format(extra=""), (t.sector_en, t.ticker_key)).fetchall())
                basis = "sector_gcc"
        rv = ratios.load(s, [r["ticker_key"] for r in rows])
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
                pe=rv.get(r["ticker_key"])["pe"],
                dividend_yield_pct=rv.get(r["ticker_key"])["dividend_yield_pct"],
            )
        )
    return Peers(basis=basis, sector_en=t.sector_en, sector_ar=t.sector_ar, peers=peers)


class NewsItem(BaseModel):
    id: str
    section: str  # news | disclosures | events
    date: str | None  # ISO; disclosures and events carry 21:00 UTC = midnight Riyadh
    title: str | None
    # English headline written for a non-English item (news_ai), when there is one.
    title_en: str | None = None
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


# An item reads in a language when it is written in it, or carries a headline or summary in it
# (news_ai / the pipeline's summaries). SQL form for `items i LEFT JOIN news_ai n`.
READABLE_SQL = {
    "en": "(i.url LIKE '%/en/%' OR n.headline_en IS NOT NULL OR length(i.ai_summary_en) > 0 OR length(n.summary_en) > 0)",
    "ar": "(i.url LIKE '%/ar/%' OR length(i.ai_summary_ar) > 0 OR length(n.summary_ar) > 0)",
}


def reads_in(item, lang: str | None) -> bool:
    if item.lang == lang:
        return True
    if lang == "en":
        return bool(item.title_en or item.summary_en)
    return lang == "ar" and bool(item.summary_ar)


def readable_first(items: list, lang: str | None, limit: int) -> list:
    """prefer_language, where an item with a headline or summary in the page's language counts
    (the market-wide feed: a reader gains nothing from the newest items in a language they do
    not read when the archive has readable ones)."""
    return prefer_language(items, lang, limit, key=lambda i: lang if reads_in(i, lang) else i.lang)


def merge_by_date(first: list, more: list, key, newest_first: bool = True) -> list:
    """Two row sets from the same table, without repeats, in date order."""
    seen = {key(r) for r in first}
    rows = list(first) + [r for r in more if key(r) not in seen]
    return sorted(rows, key=lambda r: r["date"] or "", reverse=newest_first)


def prefer_language(items: list, lang: str | None, limit: int, key=lambda i: i.lang) -> list:
    """Items in `lang` first (newest first), topped up with the other language only when there
    are not `limit` of them; the result stays in date order."""
    if lang not in ("en", "ar"):
        return items[:limit]
    chosen = [i for i in items if key(i) == lang][:limit]
    if len(chosen) < limit:
        picked = {id(i) for i in chosen}
        chosen += [i for i in items if id(i) not in picked][: limit - len(chosen)]
    order = {id(i): n for n, i in enumerate(items)}
    return sorted(chosen, key=lambda i: order[id(i)])


def _items(
    request: Request, ref: str, sections: tuple[str, ...], limit: int, upcoming: bool = False, lang: str | None = None
) -> list[NewsItem]:
    t = resolve(request, ref)
    s = settings_of(request)
    limit = max(1, min(limit, 50))
    marks = ",".join("?" for _ in sections)
    order = "ASC" if upcoming else "DESC"
    when = "AND i.date >= date('now', '-1 day')" if upcoming else ""
    select = (
        "SELECT i.id, i.section, i.date, i.title, i.url, i.snippet, i.ai_summary_en, i.ai_summary_ar,"
        " n.headline_en, n.summary_en AS n_summary_en, n.summary_ar AS n_summary_ar, n.impact"
        " FROM items i LEFT JOIN news_ai n ON n.url = i.url"
        f" WHERE i.ticker_key = ? AND i.section IN ({marks})"
        " AND i.date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'"
    )
    try:
        with reader(s.evidence_db, immutable=s.market_db_immutable, name="EVIDENCE_DB") as conn:
            rows = conn.execute(
                f"{select} {when} ORDER BY i.date {order} LIMIT ?",
                # Room to prefer the page's language among recent items (a story published in both
                # languages shows once). A company's latest items are never dropped for older ones
                # that merely have a summary in the page's language: the web app shows that summary.
                (t.ticker_key, *sections, limit * 4 if lang else limit),
            ).fetchall()
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc
    items = [
        NewsItem(
            id=r["id"],
            section=r["section"],
            date=r["date"],
            title=r["title"],
            title_en=r["headline_en"] if _lang_of(r["url"]) != "en" else None,
            url=r["url"],
            lang=_lang_of(r["url"]),
            snippet=r["snippet"] or None,
            summary_en=r["ai_summary_en"] or r["n_summary_en"],
            summary_ar=r["ai_summary_ar"] or r["n_summary_ar"],
            impact=r["impact"],
        )
        for r in rows
    ]
    return prefer_language(items, lang, limit)


@router.get("/news", operation_id="getTickerNews")
def get_news(request: Request, ref: str, limit: int = 12, lang: str | None = Query(None, pattern="^(en|ar)$")) -> list[NewsItem]:
    """Latest news and disclosures touching this ticker; `lang` puts the page's language first."""
    return _items(request, ref, ("news", "disclosures"), limit, lang=lang)


@router.get("/events", operation_id="getTickerEvents")
def get_events(request: Request, ref: str, limit: int = 20, upcoming: bool = False) -> list[NewsItem]:
    """Corporate calendar: dividends, assemblies, results dates."""
    return _items(request, ref, ("events",), limit, upcoming=upcoming)
