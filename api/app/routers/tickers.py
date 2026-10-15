from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from ..market_db import MarketDataUnavailable
from ..universe import EXCHANGE_ORDER, Universe

router = APIRouter(prefix="/tickers", tags=["tickers"])


class TickerHit(BaseModel):
    ticker_key: str
    symbol: str
    exchange: str
    currency: str | None
    name_en: str | None
    name_ar: str | None
    sector_en: str | None
    sector_ar: str | None
    slug: str


class TickerSearchResponse(BaseModel):
    query: str
    results: list[TickerHit]
    universe_size: int
    universe_as_of: str | None


class UniverseEntry(BaseModel):
    ticker_key: str
    symbol: str
    exchange: str
    slug: str
    name_en: str | None
    name_ar: str | None
    sector_en: str | None
    sector_ar: str | None
    has_prices: bool


@router.get("", operation_id="listTickers")
def list_tickers(request: Request) -> list[UniverseEntry]:
    """The whole universe, Tadawul first. `has_prices`: a daily price file exists."""
    universe: Universe = request.app.state.universe
    try:
        universe.refresh()
    except MarketDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Market data unavailable: {exc}") from exc
    store = request.app.state.prices
    order = {ex: i for i, ex in enumerate(EXCHANGE_ORDER)}
    return [
        UniverseEntry(
            ticker_key=t.ticker_key,
            symbol=t.symbol,
            exchange=t.exchange,
            slug=t.slug,
            name_en=t.name_en,
            name_ar=t.name_ar,
            sector_en=t.sector_en,
            sector_ar=t.sector_ar,
            has_prices=store.path_for(t.ticker_key) is not None,
        )
        for t in sorted(universe.tickers, key=lambda t: (order.get(t.exchange, 99), t.symbol))
    ]


@router.get("/search", operation_id="searchTickers")
def search_tickers(
    request: Request,
    q: str = Query(min_length=1, max_length=64, description="Symbol or company name, English or Arabic"),
    limit: int = Query(8, ge=1, le=25),
) -> TickerSearchResponse:
    universe: Universe = request.app.state.universe
    try:
        hits = universe.search(q, limit)
    except MarketDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=f"Market data unavailable: {exc}") from exc

    return TickerSearchResponse(
        query=q,
        results=[
            TickerHit(
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
            for t in hits
        ],
        universe_size=len(universe.tickers),
        universe_as_of=universe.as_of,
    )
