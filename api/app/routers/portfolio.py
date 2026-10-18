"""My Portfolio: holdings, exposure, alerts and the council across holdings.

Values come from the latest close in the pipeline's price file (or the briefs
quote when no file exists). There are no FX rates in our data, so totals and
exposure weights are given per listing currency, never converted.
"""

from collections import defaultdict
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, insert, select, update

from ..auth import User, check_origin, db, require_user
from ..plans import limit, plan_of
from ..appdb import alerts, holdings, random_id, utcnow
from ..market_db import MarketDataUnavailable
from ..prices import PriceStore
from ..universe import Ticker, Universe
from . import ticker_research as research
from .ticker import TickerRef, ref_of

router = APIRouter(prefix="/portfolio", tags=["portfolio"], dependencies=[Depends(check_origin)])
Authed = Annotated[User, Depends(require_user)]


class LastClose(BaseModel):
    as_of: str | None
    close: float | None
    prev_close: float | None
    change_pct: float | None


def last_close(request: Request, t: Ticker) -> LastClose:
    store: PriceStore = request.app.state.prices
    bars = store.latest(t.ticker_key)
    if len(bars) >= 2:
        return LastClose(
            as_of=bars[-1].time,
            close=bars[-1].close,
            prev_close=bars[-2].close,
            change_pct=round((bars[-1].close / bars[-2].close - 1) * 100, 2),
        )
    if bars:
        return LastClose(as_of=bars[-1].time, close=bars[-1].close, prev_close=None, change_pct=None)
    return LastClose(as_of=None, close=None, prev_close=None, change_pct=None)


class Holding(BaseModel):
    id: int
    ticker: TickerRef
    quantity: float
    avg_cost: float | None
    price: LastClose
    market_value: float | None
    day_change_value: float | None
    cost_value: float | None
    pnl: float | None
    pnl_pct: float | None
    weight_pct: float | None  # of its currency group


class Slice(BaseModel):
    label: str
    label_ar: str | None
    value: float
    weight_pct: float


class CurrencyGroup(BaseModel):
    currency: str
    market_value: float
    day_change_value: float
    sectors: list[Slice]
    exchanges: list[Slice]
    holdings_count: int


class SeatTally(BaseModel):
    seat: str
    bullish: int
    neutral: int
    bearish: int
    abstain: int


class Portfolio(BaseModel):
    holdings: list[Holding]
    groups: list[CurrencyGroup]
    council: list[SeatTally]
    unpriced: int  # holdings without any price in our data


def _universe(request: Request) -> Universe:
    return request.app.state.universe


def _slices(pairs: list[tuple[str, str | None, float]], total: float) -> list[Slice]:
    agg: dict[tuple[str, str | None], float] = defaultdict(float)
    for label, label_ar, value in pairs:
        agg[(label, label_ar)] += value
    return sorted(
        (Slice(label=k[0], label_ar=k[1], value=round(v, 2), weight_pct=round(v / total * 100, 2) if total else 0) for k, v in agg.items()),
        key=lambda s: -s.value,
    )


@router.get("", operation_id="getPortfolio")
def get_portfolio(request: Request, user: Authed) -> Portfolio:
    uni = _universe(request)
    with db(request).connect() as conn:
        rows = conn.execute(select(holdings).where(holdings.c.user_id == user.id).order_by(holdings.c.created_at, holdings.c.id)).fetchall()

    items: list[Holding] = []
    for r in rows:
        t = uni.by_key.get(r.ticker_key)
        if t is None:
            continue
        px = last_close(request, t)
        mv = r.quantity * px.close if px.close is not None else None
        dcv = r.quantity * (px.close - px.prev_close) if px.close is not None and px.prev_close is not None else None
        cv = r.quantity * r.avg_cost if r.avg_cost is not None else None
        pnl = mv - cv if mv is not None and cv is not None else None
        items.append(
            Holding(
                id=r.id, ticker=ref_of(t), quantity=r.quantity, avg_cost=r.avg_cost, price=px,
                market_value=round(mv, 2) if mv is not None else None,
                day_change_value=round(dcv, 2) if dcv is not None else None,
                cost_value=round(cv, 2) if cv is not None else None,
                pnl=round(pnl, 2) if pnl is not None else None,
                pnl_pct=round(pnl / cv * 100, 2) if pnl is not None and cv else None,
                weight_pct=None,
            )
        )

    groups: list[CurrencyGroup] = []
    by_cur: dict[str, list[Holding]] = defaultdict(list)
    for h in items:
        if h.market_value is not None:
            by_cur[h.ticker.currency or "?"].append(h)
    for cur, hs in sorted(by_cur.items(), key=lambda kv: -sum(h.market_value or 0 for h in kv[1])):
        total = sum(h.market_value or 0 for h in hs)
        for h in hs:
            h.weight_pct = round((h.market_value or 0) / total * 100, 2) if total else None
        groups.append(
            CurrencyGroup(
                currency=cur,
                market_value=round(total, 2),
                day_change_value=round(sum(h.day_change_value or 0 for h in hs), 2),
                sectors=_slices(
                    [
                        (h.ticker.sector_en, h.ticker.sector_ar, h.market_value or 0)
                        if h.ticker.sector_en
                        else ("Sector unknown", "القطاع غير معروف", h.market_value or 0)
                        for h in hs
                    ],
                    total,
                ),
                exchanges=_slices([(h.ticker.exchange, None, h.market_value or 0) for h in hs], total),
                holdings_count=len(hs),
            )
        )

    tallies = {s: SeatTally(seat=s, bullish=0, neutral=0, bearish=0, abstain=0) for s in ("value", "quality", "income", "momentum", "risk", "news")}
    for h in items:
        try:
            c = research.get_council(request, h.ticker.ticker_key)
        except (HTTPException, MarketDataUnavailable):
            continue
        for seat in c.seats:
            tally = tallies[seat.seat]
            setattr(tally, seat.vote, getattr(tally, seat.vote) + 1)

    return Portfolio(
        holdings=items,
        groups=groups,
        council=list(tallies.values()),
        unpriced=sum(1 for h in items if h.market_value is None),
    )


class HoldingIn(BaseModel):
    ticker: str = Field(min_length=1, max_length=40)
    quantity: float = Field(gt=0, le=1e12)
    avg_cost: float | None = Field(default=None, gt=0, le=1e9)


@router.post("/holdings", operation_id="upsertHolding")
def upsert_holding(request: Request, body: HoldingIn, user: Authed) -> Portfolio:
    t = _universe(request).resolve(body.ticker)
    if t is None:
        raise HTTPException(404, f"Unknown ticker: {body.ticker}")
    with db(request).begin() as conn:
        existing = conn.execute(
            select(holdings.c.id).where(holdings.c.user_id == user.id, holdings.c.ticker_key == t.ticker_key)
        ).first()
        if existing:
            conn.execute(update(holdings).where(holdings.c.id == existing.id).values(quantity=body.quantity, avg_cost=body.avg_cost))
        else:
            count = len(conn.execute(select(holdings.c.id).where(holdings.c.user_id == user.id)).fetchall())
            most = limit(request, user, "holdings") or 200
            if count >= most:
                raise HTTPException(400, f"Your plan holds up to {most} positions." + (" Pro holds 200." if plan_of(request, user) == "free" else ""))
            conn.execute(insert(holdings).values(id=random_id(conn, holdings), user_id=user.id, ticker_key=t.ticker_key, quantity=body.quantity, avg_cost=body.avg_cost, created_at=utcnow()))
    return get_portfolio(request, user)


@router.delete("/holdings/{holding_id}", operation_id="deleteHolding")
def delete_holding(request: Request, holding_id: int, user: Authed) -> Portfolio:
    with db(request).begin() as conn:
        conn.execute(delete(holdings).where(holdings.c.id == holding_id, holdings.c.user_id == user.id))
    return get_portfolio(request, user)


# --- alerts -------------------------------------------------------------------------------------


class Alert(BaseModel):
    id: int
    ticker: TickerRef
    kind: Literal["above", "below"]
    price: float
    last: LastClose
    triggered: bool | None  # None when there is no price to compare


class AlertIn(BaseModel):
    ticker: str = Field(min_length=1, max_length=40)
    kind: Literal["above", "below"]
    price: float = Field(gt=0, le=1e9)


@router.get("/alerts", operation_id="listAlerts")
def list_alerts(request: Request, user: Authed) -> list[Alert]:
    uni = _universe(request)
    with db(request).connect() as conn:
        rows = conn.execute(select(alerts).where(alerts.c.user_id == user.id).order_by(alerts.c.created_at, alerts.c.id)).fetchall()
    out = []
    for r in rows:
        t = uni.by_key.get(r.ticker_key)
        if t is None:
            continue
        px = last_close(request, t)
        trig = None if px.close is None else (px.close >= r.price if r.kind == "above" else px.close <= r.price)
        out.append(Alert(id=r.id, ticker=ref_of(t), kind=r.kind, price=r.price, last=px, triggered=trig))
    return out


@router.post("/alerts", operation_id="createAlert")
def create_alert(request: Request, body: AlertIn, user: Authed) -> list[Alert]:
    t = _universe(request).resolve(body.ticker)
    if t is None:
        raise HTTPException(404, f"Unknown ticker: {body.ticker}")
    with db(request).begin() as conn:
        most = limit(request, user, "alerts") or 100
        if len(conn.execute(select(alerts.c.id).where(alerts.c.user_id == user.id)).fetchall()) >= most:
            raise HTTPException(400, f"Your plan has up to {most} alerts." + (" Pro has 100." if plan_of(request, user) == "free" else ""))
        conn.execute(insert(alerts).values(id=random_id(conn, alerts), user_id=user.id, ticker_key=t.ticker_key, kind=body.kind, price=body.price, created_at=utcnow()))
    return list_alerts(request, user)


@router.delete("/alerts/{alert_id}", operation_id="deleteAlert")
def delete_alert(request: Request, alert_id: int, user: Authed) -> list[Alert]:
    with db(request).begin() as conn:
        conn.execute(delete(alerts).where(alerts.c.id == alert_id, alerts.c.user_id == user.id))
    return list_alerts(request, user)
