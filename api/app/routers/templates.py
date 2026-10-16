"""Data behind the Earnings Season, Dividend Hunter and Sector vs Sector templates."""

import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from .. import ratios
from ..market_db import MarketDataUnavailable, reader
from .market import _uni
from .portfolio import LastClose, last_close
from .ticker import TickerRef, ref_of, settings_of

router = APIRouter(prefix="/templates", tags=["templates"])

RESULT_WORDS = ("result", "financial statement", "earnings", "النتائج", "القوائم المالية")


def _unavailable(exc: MarketDataUnavailable) -> HTTPException:
    return HTTPException(503, f"Market data unavailable: {exc}")


# --- Earnings Season ------------------------------------------------------------------------------


class EarningsEvent(BaseModel):
    ticker: TickerRef
    date: str  # local (Riyadh) calendar date
    title: str
    url: str | None
    upcoming: bool
    price: LastClose


class EarningsSeason(BaseModel):
    window_days: int
    events: list[EarningsEvent]


def _local_date(raw: str) -> str:
    """Events are stamped 21:00 UTC for midnight Riyadh; return the Riyadh calendar date."""
    if len(raw) == 10:
        return raw
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    dt = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return (dt + timedelta(hours=3)).date().isoformat()


@router.get("/earnings-season", operation_id="earningsSeason")
def earnings_season(request: Request, days: int = Query(30, ge=7, le=120)) -> EarningsSeason:
    uni = _uni(request)
    s = settings_of(request)
    today = datetime.now(UTC).date()
    lo, hi = (today - timedelta(days=days)).isoformat(), (today + timedelta(days=days)).isoformat()
    like = " OR ".join("lower(title) LIKE ?" for _ in RESULT_WORDS)
    try:
        with reader(s.evidence_db, immutable=s.market_db_immutable, name="EVIDENCE_DB") as conn:
            rows = conn.execute(
                "SELECT ticker_key, date, title, url FROM items WHERE section = 'events'"
                f" AND date >= ? AND date <= ? AND ({like}) ORDER BY date",
                (lo, hi + "T23:59:59", *(f"%{w}%" for w in RESULT_WORDS)),
            ).fetchall()
    except MarketDataUnavailable as exc:
        raise _unavailable(exc) from exc
    events = []
    for r in rows:
        t = uni.by_key.get(r["ticker_key"])
        if t is None:
            continue
        d = _local_date(r["date"])
        events.append(
            EarningsEvent(ticker=ref_of(t), date=d, title=r["title"], url=r["url"], upcoming=d >= today.isoformat(), price=last_close(request, t))
        )
    return EarningsSeason(window_days=days, events=events)


# --- Dividend Hunter -----------------------------------------------------------------------------


class DividendRow(BaseModel):
    ticker: TickerRef
    price: LastClose
    dividend_yield_pct: float | None
    payments_3y: int
    last_dps: float | None
    last_ex_date: str | None
    next_ex_date: str | None
    payout_pct: float | None


@router.get("/dividend-hunter", operation_id="dividendHunter")
def dividend_hunter(request: Request, min_yield: float = Query(0, ge=0, le=50), limit: int = Query(60, ge=1, le=300)) -> list[DividendRow]:
    uni = _uni(request)
    s = settings_of(request)
    today = datetime.now(UTC).date().isoformat()
    three_years = (datetime.now(UTC).date() - timedelta(days=3 * 365)).isoformat()
    try:
        rv = ratios.load(s)
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            payout = {r["ticker_key"]: r["value"] for r in conn.execute("SELECT ticker_key, value FROM fundamentals_gauges WHERE gauge_key = 'payout' AND status = 'ok'")}
            divs: dict[str, list] = defaultdict(list)
            for r in conn.execute("SELECT ticker_key, ex_date, dps FROM dividends WHERE ex_date IS NOT NULL ORDER BY ex_date DESC"):
                divs[r["ticker_key"]].append(r)
    except MarketDataUnavailable as exc:
        raise _unavailable(exc) from exc

    rows = []
    for t in uni.tickers:
        y = rv.get(t.ticker_key)["dividend_yield_pct"]
        if y is None or y <= 0 or y < min_yield:
            continue
        ds = divs.get(t.ticker_key, [])
        past = [d for d in ds if d["ex_date"] <= today]
        future = [d for d in ds if d["ex_date"] > today]
        rows.append(
            DividendRow(
                ticker=ref_of(t),
                price=last_close(request, t),
                dividend_yield_pct=y,
                payments_3y=sum(1 for d in past if d["ex_date"] >= three_years),
                last_dps=past[0]["dps"] if past else None,
                last_ex_date=past[0]["ex_date"] if past else None,
                next_ex_date=future[-1]["ex_date"] if future else None,
                payout_pct=payout.get(t.ticker_key),
            )
        )
    rows.sort(key=lambda r: -(r.dividend_yield_pct or 0))
    return rows[:limit]


# --- Sector vs Sector -----------------------------------------------------------------------------


class SectorStats(BaseModel):
    sector_en: str
    sector_ar: str | None
    equities: int
    median_pe: float | None
    median_pb: float | None
    median_yield_pct: float | None
    median_roe_pct: float | None
    median_return_12m: float | None  # fraction
    with_value: dict[str, int]  # how many members had each metric


class SectorMember(BaseModel):
    ticker: TickerRef
    price: LastClose
    market_cap_mn: float | None
    pe: float | None
    dividend_yield_pct: float | None
    return_12m: float | None


class SectorCompare(BaseModel):
    a: SectorStats
    b: SectorStats
    a_members: list[SectorMember]
    b_members: list[SectorMember]


class SectorListItem(BaseModel):
    sector_en: str
    sector_ar: str | None
    equities: int


def _median(vals: list[float]) -> float | None:
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 4) if vals else None


@router.get("/sectors", operation_id="listSectors")
def sectors(request: Request) -> list[SectorListItem]:
    uni = _uni(request)
    groups: dict[str, list] = defaultdict(list)
    for t in uni.tickers:
        if t.sector_en:
            groups[t.sector_en].append(t)
    return sorted(
        (SectorListItem(sector_en=k, sector_ar=v[0].sector_ar, equities=len(v)) for k, v in groups.items()),
        key=lambda s: -s.equities,
    )


@router.get("/sector-vs-sector", operation_id="sectorVsSector")
def sector_vs_sector(request: Request, a: str = Query(min_length=1), b: str = Query(min_length=1)) -> SectorCompare:
    uni = _uni(request)
    s = settings_of(request)
    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            rows = {r["ticker_key"]: r for r in conn.execute("SELECT ticker_key, market_cap_raw, return_12m FROM briefs")}
        rv = ratios.load(s)
    except MarketDataUnavailable as exc:
        raise _unavailable(exc) from exc

    def build(sector: str) -> tuple[SectorStats, list[SectorMember]]:
        members = [t for t in uni.tickers if t.sector_en == sector]
        if not members:
            raise HTTPException(404, f"Unknown sector: {sector}")
        vals = defaultdict(list)
        out = []
        for t in members:
            b_, r_ = rows.get(t.ticker_key), rv.get(t.ticker_key)
            pe, pb, y, roe = r_["pe"], r_["pb"], r_["dividend_yield_pct"], r_["roe_pct"]
            r12 = b_["return_12m"] if b_ else None
            for k, v in (("pe", pe), ("pb", pb), ("yield", y), ("roe", roe), ("r12", r12)):
                if v is not None:
                    vals[k].append(v)
            out.append(SectorMember(ticker=ref_of(t), price=last_close(request, t), market_cap_mn=b_["market_cap_raw"] if b_ else None, pe=pe, dividend_yield_pct=y, return_12m=r12))
        out.sort(key=lambda m: -(m.market_cap_mn or 0))
        stats = SectorStats(
            sector_en=sector,
            sector_ar=members[0].sector_ar,
            equities=len(members),
            median_pe=_median(vals["pe"]),
            median_pb=_median(vals["pb"]),
            median_yield_pct=_median(vals["yield"]),
            median_roe_pct=_median(vals["roe"]),
            median_return_12m=_median(vals["r12"]),
            with_value={k: len(v) for k, v in vals.items()},
        )
        return stats, out

    sa, ma = build(a)
    sb, mb = build(b)
    return SectorCompare(a=sa, b=sb, a_members=ma, b_members=mb)
