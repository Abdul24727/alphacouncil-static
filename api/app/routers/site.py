"""Public pages: plan prices for /pricing and the rules behind /methodology.

Both come from the code and databases that do the work (pricing.py is the checkout's
configuration, council.THRESHOLDS are the votes' thresholds, ticker_freshness holds
each category's allowed age), so the public pages cannot drift from the product.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .. import council, pricing
from ..freshness import DEFAULT_WEEKEND, MARKET_CATEGORIES, PIPELINE_RUN_UTC, PRICE_MAX_AGE_DAYS, WEEKENDS
from ..market_db import MarketDataUnavailable, reader
from .market import _uni
from .ticker import settings_of

router = APIRouter(tags=["site"])


class Plan(BaseModel):
    id: str
    name: str
    name_ar: str
    price_sar: int
    currency: str
    interval: str
    rank: int
    paid: bool


class Plans(BaseModel):
    plans: list[Plan]
    currency: str
    interval: str
    provider: str
    # This app has no checkout yet; payments still run through the old site's Moyasar flow.
    checkout_open: bool


@router.get("/plans", operation_id="plans")
def plans() -> Plans:
    return Plans(
        plans=[Plan(**p) for p in pricing.public_plans()],
        currency=pricing.CURRENCY,
        interval=pricing.INTERVAL,
        provider=pricing.PROVIDER,
        checkout_open=False,
    )


class SeatRule(BaseModel):
    seat: str
    inputs: list[str]
    thresholds: dict[str, float]


class FreshnessRule(BaseModel):
    category: str
    max_age_days: float | None
    tickers: int
    # Ages count trading days (weekends excluded) rather than calendar days.
    trading_days: bool


class ExchangeCalendar(BaseModel):
    exchange: str
    equities: int
    weekend: list[int]  # weekday numbers, Monday = 0


class Methodology(BaseModel):
    seats: list[SeatRule]
    freshness: list[FreshnessRule]
    price_max_age_days: int
    pipeline_run_utc: str
    exchanges: list[ExchangeCalendar]
    equities: int


@router.get("/methodology", operation_id="methodology")
def methodology(request: Request) -> Methodology:
    s = settings_of(request)
    uni = _uni(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            rows = conn.execute(
                "SELECT category, max_age_days, COUNT(*) AS n FROM ticker_freshness"
                " GROUP BY category, max_age_days ORDER BY category, max_age_days"
            ).fetchall()
    except MarketDataUnavailable as exc:
        raise HTTPException(503, f"Market data unavailable: {exc}") from exc

    counts: dict[str, int] = {}
    for t in uni.tickers:
        counts[t.exchange] = counts.get(t.exchange, 0) + 1

    return Methodology(
        seats=[
            SeatRule(seat=seat, inputs=list(council.INPUTS[seat]), thresholds=council.THRESHOLDS[seat])
            for seat in council.SEATS
        ],
        freshness=[
            FreshnessRule(
                category=r["category"],
                max_age_days=r["max_age_days"],
                tickers=r["n"],
                trading_days=r["category"] in MARKET_CATEGORIES,
            )
            for r in rows
        ],
        price_max_age_days=PRICE_MAX_AGE_DAYS,
        pipeline_run_utc=PIPELINE_RUN_UTC.strftime("%H:%M"),
        exchanges=[
            ExchangeCalendar(exchange=ex, equities=n, weekend=sorted(WEEKENDS.get(ex, DEFAULT_WEEKEND)))
            for ex, n in sorted(counts.items(), key=lambda kv: -kv[1])
        ],
        equities=len(uni.tickers),
    )
