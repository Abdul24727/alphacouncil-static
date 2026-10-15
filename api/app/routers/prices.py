from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..freshness import PRICE_MAX_AGE_DAYS, Freshness, assess
from ..prices import Bar, PriceStore
from .ticker import load_freshness, resolve, settings_of

router = APIRouter(prefix="/tickers/{ref}", tags=["ticker"])


class PriceHistory(BaseModel):
    ticker_key: str
    currency: str | None
    has_history: bool
    bars: list[Bar]  # oldest first; ranges and indicators are cut and computed by the client
    freshness: Freshness | None


def latest_bars(request: Request, ticker_key: str) -> list[Bar] | None:
    store: PriceStore = request.app.state.prices
    return store.bars(ticker_key)


def bar_freshness(request: Request, ticker_key: str, exchange: str, bars: list[Bar]) -> Freshness:
    """Freshness of the price file itself: its last bar, fetched when the file was written."""
    store: PriceStore = request.app.state.prices
    path = store.path_for(ticker_key)
    written = datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat() if path else None
    try:
        window = next((f.max_age_days for f in load_freshness(settings_of(request), _t(request, ticker_key)) if f.category == "prices"), None)
    except Exception:  # noqa: BLE001 - freshness table optional for a price chart
        window = None
    return assess(
        category="prices",
        as_of_utc=bars[-1].time,
        last_success_utc=written,
        max_age_days=window if window is not None else PRICE_MAX_AGE_DAYS,
        exchange=exchange,
    )


def _t(request: Request, ticker_key: str):
    return request.app.state.universe.by_key[ticker_key]


@router.get("/prices", operation_id="getTickerPrices")
def get_prices(request: Request, ref: str) -> PriceHistory:
    t = resolve(request, ref)
    try:
        bars = latest_bars(request, t.ticker_key)
    except OSError as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc
    if not bars:
        return PriceHistory(ticker_key=t.ticker_key, currency=t.currency, has_history=False, bars=[], freshness=None)
    return PriceHistory(
        ticker_key=t.ticker_key,
        currency=t.currency,
        has_history=len(bars) >= 2,
        bars=bars,
        freshness=bar_freshness(request, t.ticker_key, t.exchange, bars),
    )
