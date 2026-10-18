"""Research panels of the stock template: council, fundamentals, statements,
corporate actions and insights. Same rules as ticker.py: values come from the
pipeline's databases, missing data is null, nothing is estimated."""

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from .. import council, ratios
from ..freshness import Freshness, assess
from ..market_db import MarketDataUnavailable, reader
from ..plans import require_pro
from .ticker import _flag, _row, load_freshness, resolve, settings_of

router = APIRouter(prefix="/tickers/{ref}", tags=["ticker"])


def unavailable(exc: MarketDataUnavailable) -> HTTPException:
    return HTTPException(503, f"Market data unavailable: {exc}")


# --- Council --------------------------------------------------------------------------------


class Council(BaseModel):
    seats: list[council.Seat]
    counts: dict[str, int]
    as_of_date: str | None
    freshness: Freshness | None


@router.get("/council", operation_id="getTickerCouncil", dependencies=[Depends(require_pro)])
def get_council(request: Request, ref: str) -> Council:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.briefs_db, immutable=s.market_db_immutable, name="BRIEFS_DB") as conn:
            b = _row(
                conn,
                "SELECT b.as_of_date, b.pe, b.roe_pct, b.dividend_yield_pct, b.vol_1y, b.regime_score,"
                " b.source_run_ts, x.ma_cross_50_200 FROM briefs b"
                " LEFT JOIN ticker_tech_snapshot x ON x.ticker_key = b.ticker_key AND x.status = 'ok'"
                " WHERE b.ticker_key = ?",
                t.ticker_key,
            )
        r = ratios.load(s, [t.ticker_key]).get(t.ticker_key)
        with reader(s.evidence_db, immutable=s.market_db_immutable, name="EVIDENCE_DB") as conn:
            impacts = [
                r["impact"]
                for r in conn.execute(
                    "SELECT n.impact FROM items i JOIN news_ai n ON n.url = i.url"
                    " WHERE i.ticker_key = ? AND i.section = 'news' AND n.impact IS NOT NULL"
                    " AND i.date >= date('now', ?)",
                    (t.ticker_key, f"-{council.THRESHOLDS['news']['window_days']:g} days"),
                )
            ]
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc

    # The same ratios every screen shows (app/ratios.py).
    pe, roe, yld = r["pe"], r["roe_pct"], r["dividend_yield_pct"]
    vol = b["vol_1y"] * 100 if b and b["vol_1y"] is not None else None

    seats = [
        council.value_seat(pe),
        council.quality_seat(roe),
        council.income_seat(yld),
        council.momentum_seat(b["regime_score"] if b else None, _flag(b["ma_cross_50_200"]) if b else None),
        council.risk_seat(vol, yld),
        council.news_seat(impacts),
    ]
    counts = {v: sum(1 for x in seats if x.vote == v) for v in ("bullish", "neutral", "bearish", "abstain")}
    freshness = (
        assess(
            category="prices",
            as_of_utc=b["as_of_date"],
            last_success_utc=b["source_run_ts"],
            max_age_days=2,
            exchange=t.exchange,
        )
        if b and b["as_of_date"]
        else None
    )
    return Council(seats=seats, counts=counts, as_of_date=b["as_of_date"] if b else None, freshness=freshness)


# --- Fundamentals strip (4 groups, sector percentiles) ------------------------------------

GAUGE_GROUPS: list[tuple[str, list[tuple[str, str, bool]]]] = [
    ("valuation", [("pe", "x", False), ("pb", "x", False), ("ev_ebitda", "x", False), ("ps", "x", False)]),
    (
        "profitability",
        [("roe", "%", True), ("roa", "%", True), ("roic", "%", True), ("net_margin", "%", True), ("gross_margin", "%", True)],
    ),
    (
        "health",
        [("debt_equity", "ratio", False), ("current_ratio", "ratio", True), ("interest_coverage", "x", True), ("fcf_yield", "%", True)],
    ),
    ("income", [("div_yield", "%", True), ("payout", "%", False)]),
]


class GaugeMetric(BaseModel):
    key: str
    value: float | None
    unit: str
    higher_is_better: bool
    status: str  # ok | missing_inputs | na_sector | undefined_nonpositive | published
    sector_percentile: float | None


class GaugeGroup(BaseModel):
    group: str
    metrics: list[GaugeMetric]
    score: float | None  # mean sector percentile of the metrics that have one


class Fundamentals(BaseModel):
    groups: list[GaugeGroup]
    freshness: Freshness | None


@router.get("/fundamentals", operation_id="getTickerFundamentals", dependencies=[Depends(require_pro)])
def get_fundamentals(request: Request, ref: str) -> Fundamentals:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            gauges = {
                r["gauge_key"]: r
                for r in conn.execute(
                    "SELECT gauge_key, value, status, score FROM fundamentals_gauges WHERE ticker_key = ?",
                    (t.ticker_key,),
                )
            }
        r = ratios.load(s, [t.ticker_key]).get(t.ticker_key)
        fresh = next((f for f in load_freshness(s, t) if f.category == "fundamentals"), None)
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc

    # Ratios shown on Key metrics too: one value everywhere (app/ratios.py).
    published = {
        "pe": r["pe"],
        "pb": r["pb"],
        "roe": r["roe_pct"],
        "roa": r["roa_pct"],
        "div_yield": r["dividend_yield_pct"],
        "ev_ebitda": r["ev_ebitda"],
    }

    groups = []
    for group, metrics in GAUGE_GROUPS:
        rows = []
        for key, unit, hib in metrics:
            g = gauges.get(key)
            # A computed gauge with a value wins (it carries the sector percentile); otherwise
            # the shared published ratio, so Financials and Key metrics agree.
            if g is not None and (g["status"] == "ok" or published.get(key) is None):
                rows.append(
                    GaugeMetric(
                        key=key, value=g["value"], unit=unit, higher_is_better=hib,
                        status=g["status"], sector_percentile=g["score"],
                    )
                )
            else:
                v = published.get(key)
                rows.append(
                    GaugeMetric(
                        key=key, value=v, unit=unit, higher_is_better=hib,
                        status="published" if v is not None else "missing_inputs", sector_percentile=None,
                    )
                )
        scored = [m.sector_percentile for m in rows if m.sector_percentile is not None]
        groups.append(GaugeGroup(group=group, metrics=rows, score=sum(scored) / len(scored) if scored else None))
    return Fundamentals(groups=groups, freshness=fresh)


# --- Statements ------------------------------------------------------------------------------


class StatementRow(BaseModel):
    index: int
    label: str
    values: dict[str, float | None]  # fiscal year -> value


class Statement(BaseModel):
    section: str
    rows: list[StatementRow]


class Statements(BaseModel):
    years: list[int]
    unit: str  # millions of the listing currency
    currency: str | None
    statements: list[Statement]


STATEMENT_ORDER = ["Income Statement", "Balance Sheet"]


@router.get("/statements", operation_id="getTickerStatements", dependencies=[Depends(require_pro)])
def get_statements(request: Request, ref: str, years: int = 5) -> Statements:
    t = resolve(request, ref)
    s = settings_of(request)
    years = max(1, min(years, 10))
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            yrs = [
                r[0]
                for r in conn.execute(
                    "SELECT DISTINCT fiscal_year FROM fundamentals_lineitems WHERE ticker_key = ?"
                    " ORDER BY fiscal_year DESC LIMIT ?",
                    (t.ticker_key, years),
                )
            ]
            rows = []
            if yrs:
                marks = ",".join("?" for _ in yrs)
                rows = conn.execute(
                    "SELECT section, fiscal_year, item_index, line_item_label, value FROM fundamentals_lineitems"
                    f" WHERE ticker_key = ? AND fiscal_year IN ({marks}) ORDER BY section, item_index",
                    (t.ticker_key, *yrs),
                ).fetchall()
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc

    by_section: dict[str, dict[int, StatementRow]] = {}
    for r in rows:
        sec = by_section.setdefault(r["section"] or "Other", {})
        row = sec.setdefault(r["item_index"], StatementRow(index=r["item_index"], label=r["line_item_label"], values={}))
        row.values[str(r["fiscal_year"])] = r["value"]

    def rank(name: str) -> tuple[int, str]:
        return (STATEMENT_ORDER.index(name) if name in STATEMENT_ORDER else 9, name)

    statements = [
        Statement(section=name, rows=[sec[i] for i in sorted(sec)])
        for name, sec in sorted(by_section.items(), key=lambda kv: rank(kv[0]))
    ]
    return Statements(years=sorted(yrs), unit="mn", currency=t.currency, statements=statements)


# --- Corporate: dividends and capital changes -----------------------------------------------


class Dividend(BaseModel):
    announce_date: str | None
    ex_date: str | None
    pay_date: str | None
    dps: float | None
    amount_mn: float | None
    note: str | None


class CapitalChange(BaseModel):
    date: str | None
    change_type: str | None
    capital_before_mn: float | None
    capital_after_mn: float | None
    change_pct: float | None
    note: str | None


class Corporate(BaseModel):
    currency: str | None
    dividends: list[Dividend]
    capital_changes: list[CapitalChange]


@router.get("/corporate", operation_id="getTickerCorporate", dependencies=[Depends(require_pro)])
def get_corporate(request: Request, ref: str) -> Corporate:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            divs = conn.execute(
                "SELECT announce_date, ex_date, pay_date, dps, amount_mn, note FROM dividends"
                " WHERE ticker_key = ? ORDER BY COALESCE(ex_date, announce_date) DESC LIMIT 16",
                (t.ticker_key,),
            ).fetchall()
            caps = conn.execute(
                "SELECT date, change_type, capital_before_mn, capital_after_mn, change_pct, note FROM capital_changes"
                " WHERE ticker_key = ? ORDER BY date DESC LIMIT 12",
                (t.ticker_key,),
            ).fetchall()
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc
    return Corporate(
        currency=t.currency,
        dividends=[Dividend(**dict(r)) for r in divs],
        capital_changes=[CapitalChange(**dict(r)) for r in caps],
    )


# --- Insights: performance, seasonality, ownership --------------------------------------------


class Insights(BaseModel):
    updated_at: str | None
    performance: dict | None  # {as_of, 1w, 1m, 3m, 6m, ytd, 1y} in percent
    # {years: [{year, monthly_pct[12], partial}], average[12], years_back}: cumulative % from
    # the year's first close at each month end.
    seasonality: dict | None
    ownership: dict | None  # null until the pipeline collects it
    analysts: dict | None


@router.get("/insights", operation_id="getTickerInsights", dependencies=[Depends(require_pro)])
def get_insights(request: Request, ref: str) -> Insights:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            r = _row(conn, "SELECT updated_at, data_json FROM ticker_insights WHERE ticker_key = ?", t.ticker_key)
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc
    data = json.loads(r["data_json"]) if r and r["data_json"] else {}
    performance = data.get("performance")
    seasonality = data.get("seasonality")
    # The pipeline carries the last close forward into months that have not
    # happened yet; blank those so the current year shows only real month ends.
    as_of = (performance or {}).get("as_of")
    if seasonality and as_of:
        last_year, last_month = int(as_of[:4]), int(as_of[5:7])
        for year in seasonality.get("years", []):
            if year.get("year") == last_year:
                year["monthly_pct"] = [v if i < last_month else None for i, v in enumerate(year.get("monthly_pct", []))]
    return Insights(
        updated_at=r["updated_at"] if r else None,
        performance=performance,
        seasonality=seasonality,
        ownership=_ownership(data.get("ownership")),
        analysts=data.get("analysts"),
    )


def _ownership(o: dict | None) -> dict | None:
    """The pipeline's ownership block, with one foreign-ownership point per day (it can repeat
    a day; the later entry wins) and holder rows without a name dropped (some are "0.00 %")."""
    if not o:
        return o
    o = dict(o)
    if o.get("foreign_series"):
        by_date = {p["date"]: p for p in o["foreign_series"] if p.get("date")}
        o["foreign_series"] = [by_date[d] for d in sorted(by_date)]
    named = lambda h: any(ch.isalpha() for ch in str(h.get("name") or ""))  # noqa: E731
    for key in ("major_holders", "recent_changes"):
        if o.get(key):
            o[key] = [h for h in o[key] if named(h)]
    return o
