"""Research panels of the stock template: council, fundamentals, statements,
corporate actions and insights. Same rules as ticker.py: values come from the
pipeline's databases, missing data is null, nothing is estimated."""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from .. import council, evidence, ratios
from ..freshness import Freshness, assess
from ..market_db import MarketDataUnavailable, reader
from ..plans import require_pro
from .ticker import _flag, _row, get_ticker, load_freshness, resolve, settings_of

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
    # ok | published | missing_inputs | na_sector | undefined_nonpositive
    #   | not_meaningful  the measure has no analogue for this company's sector
    #   | stale           computed from statements that have since been refreshed
    status: str
    sector_percentile: float | None
    # What the number is, so a reader is not left to infer the formula from the name.
    formula: str | None = None
    denominator: str | None = None
    source: str | None = None
    # The operands the pipeline divided, read back from its own audit trail.
    operands: dict[str, Any] | None = None
    # The window and the date behind those operands.
    as_of: evidence.Period | None = None
    # How far this gauge's freshness could be checked: "inputs" where an operand names its
    # line item and the row says which year it read, so a figure corrected inside the same
    # period is caught; "period" where only the year and the window could be compared.
    vintage: str | None = None
    # Why there is no number, or why this one must not be compared.
    note: str | None = None


class GaugeGroup(BaseModel):
    group: str
    metrics: list[GaugeMetric]
    score: float | None  # mean sector percentile of the metrics that have one


class Fundamentals(BaseModel):
    groups: list[GaugeGroup]
    freshness: Freshness | None
    sector: str | None = None  # from the pipeline's own detection, not from a sector name
    # Set when at least one gauge was computed from statements that have since been refreshed.
    # Values for those gauges are withheld rather than shown beside figures they do not match.
    stale: bool = False
    # The peer class the pipeline ranked this ticker inside, by its own vote, and what is known
    # to be wrong with that class's membership. A percentile is a statement about a population:
    # this endpoint reads one company, so it reports the population it was ranked against rather
    # than implying it verified it.
    peer_class: str | None = None
    ranking_note: str | None = None


# Operand keys that are provenance or diagnostics rather than inputs: they are reported in their
# own fields, and repeating them inside `operands` would crowd out the figures.
_NOT_OPERANDS = {
    "fiscal_year", "period", "period_end", "position_at", "sector", "computed_at",
    "missing", "searched", "expected_section", "available_in_section", "note", "year",
}


def _note_of(inputs: dict[str, Any], key: str, status: str) -> str | None:
    """One sentence saying what is missing, in the pipeline's own words plus what it searched."""
    if status == "ok":
        return None
    if inputs.get("note"):
        return str(inputs["note"])
    missing = inputs.get("missing")
    if not missing:
        return None
    searched, available = inputs.get("searched"), inputs.get("available_in_section")
    text = f"{missing} is absent"
    if isinstance(searched, list) and searched:
        text += f"; searched {len(searched)} label(s) including {', '.join(str(x) for x in searched[:3])}"
    if isinstance(available, list):
        text += f"; the {inputs.get('expected_section') or 'section'} carries {len(available)} other labels"
    if key == "payout":
        text += (". A payout matched to the earnings window is in the financial-evidence dataset"
                 " wherever the dividend history supports one")
    return text


@router.get("/fundamentals", operation_id="getTickerFundamentals", dependencies=[Depends(require_pro)])
def get_fundamentals(request: Request, ref: str) -> Fundamentals:
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            gauges = {
                r["gauge_key"]: r
                for r in conn.execute(
                    "SELECT gauge_key, value, status, score, inputs_json FROM fundamentals_gauges"
                    " WHERE ticker_key = ?",
                    (t.ticker_key,),
                )
            }
            items = evidence.load_items(conn, t.ticker_key, years=2)
        r = ratios.load(s, [t.ticker_key]).get(t.ticker_key)
        fresh = next((f for f in load_freshness(s, t) if f.category == "fundamentals"), None)
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc

    audit: dict[str, dict] = {}
    for key, row in gauges.items():
        try:
            parsed = json.loads(row["inputs_json"]) if row["inputs_json"] else {}
        except (ValueError, TypeError):
            parsed = {}
        audit[key] = parsed if isinstance(parsed, dict) else {}
    sector = evidence.sector_of(items, audit)
    peer_class = evidence.recorded_peer_class(audit)
    peer_reason = evidence.peer_group_reason(peer_class)

    # Ratios shown on Key metrics too: one value everywhere (app/ratios.py).
    published = {
        "pe": r["pe"],
        "pb": r["pb"],
        "roe": r["roe_pct"],
        "roa": r["roa_pct"],
        "div_yield": r["dividend_yield_pct"],
        "ev_ebitda": r["ev_ebitda"],
    }

    any_stale = False
    groups = []
    for group, metrics in GAUGE_GROUPS:
        rows = []
        for key, unit, hib in metrics:
            g = gauges.get(key)
            inputs = audit.get(key, {})
            definition = evidence.DEFINITIONS.get(key, {})
            common = {
                "key": key, "unit": unit, "higher_is_better": hib,
                "formula": definition.get("formula"),
                "denominator": definition.get("denominator"),
            }
            # A bank has no revenue line and no current/non-current split, so the generic ratios
            # built on them are not missing data — they are measures this company is not read on.
            # Saying "missing" invites the wrong fix: mapping a bank's operating income into the
            # revenue slot, which would put a price-to-sales ratio and a margin on financing
            # income beside industrial companies' and get them compared.
            if sector == "bank" and key in evidence.BANK_UNSUITABLE:
                rows.append(GaugeMetric(
                    **common, value=None, status="not_meaningful", sector_percentile=None,
                    source="not applicable to this company", as_of=None,
                    note=evidence.BANK_UNSUITABLE[key]
                         + ". The measures this company is read on are in the financial-evidence"
                           " dataset.",
                ))
                continue
            stale = evidence.stale_reason(inputs, items) if g is not None else None
            if stale:
                any_stale = True
                rows.append(GaugeMetric(
                    **common, value=None, status="stale", sector_percentile=None,
                    source=definition.get("source"), as_of=_as_of(inputs), note=stale,
                ))
                continue
            # A computed gauge with a value wins (it carries the sector percentile); otherwise
            # the shared published ratio, so Financials and Key metrics agree.
            if g is not None and (g["status"] == "ok" or published.get(key) is None):
                # A percentile means something only for the value it ranked, AND only for the
                # population it ranked it in. The pipeline clears the score when a recomputed
                # value moves, so an absent one here is the sector stage not having run yet; a
                # rank withheld by `peer_reason` is a rank inside a peer class whose membership
                # is known to be wrong, which is a different failure and says so.
                ranked = g["score"] if g["status"] == "ok" else None
                why = [x for x in (_note_of(inputs, key, g["status"]),
                                   peer_reason if ranked is not None else None) if x]
                rows.append(GaugeMetric(
                    **common, value=g["value"], status=g["status"],
                    sector_percentile=None if peer_reason else ranked,
                    source=definition.get("source"),
                    operands={k: v for k, v in inputs.items() if k not in _NOT_OPERANDS} or None,
                    as_of=_as_of(inputs), vintage=evidence.vintage_basis(inputs),
                    note="; ".join(why) or None,
                ))
            else:
                v = published.get(key)
                rows.append(GaugeMetric(
                    **common, value=v, status="published" if v is not None else "missing_inputs",
                    sector_percentile=None, source=definition.get("source"),
                    as_of=_as_of(inputs) if g is not None else None,
                    note=_note_of(inputs, key, "missing_inputs") if v is None else None,
                ))
        scored = [m.sector_percentile for m in rows if m.sector_percentile is not None]
        groups.append(GaugeGroup(group=group, metrics=rows, score=sum(scored) / len(scored) if scored else None))
    return Fundamentals(
        groups=groups, freshness=fresh, sector=sector, stale=any_stale, peer_class=peer_class,
        ranking_note=peer_reason or (evidence.PEER_SHORTFALL_NOTE if peer_class else None),
    )


def _as_of(inputs: dict[str, Any]) -> evidence.Period | None:
    if not inputs.get("period") and not inputs.get("fiscal_year"):
        return None
    return evidence.Period(
        period=inputs.get("period"),
        period_end=inputs.get("period_end") or (f"{inputs['fiscal_year']}-12" if inputs.get("fiscal_year") else None),
        aggregation=None,
        source_columns=[],
    )


# --- Statements ------------------------------------------------------------------------------


class StatementRow(BaseModel):
    index: int
    label: str
    values: dict[str, float | None]  # fiscal year -> value
    # Where this row's aggregation differs from its section's, fiscal year -> the rule that
    # produced it. A share count summed like a flow is the mistake this makes visible.
    rules: dict[str, str] = {}


class Statement(BaseModel):
    section: str
    rows: list[StatementRow]
    # Fiscal year -> the window its figures cover. One section can hold a real fiscal year beside
    # a trailing-twelve-month window, so this cannot be a property of the statement as a whole:
    # without it a December position and a June position sit in one row under nothing but the
    # labels "2025" and "2026", and read as a year-on-year comparison.
    periods: dict[str, evidence.Period] = {}


class Statements(BaseModel):
    years: list[int]
    unit: str  # millions of the listing currency
    currency: str | None
    statements: list[Statement]
    # False against a database parsed before the pipeline recorded reporting modes. Every
    # `periods` entry is then empty, and a figure's window is genuinely unknown — which is a
    # different thing from a figure whose window is a fiscal year.
    period_aware: bool = False


STATEMENT_ORDER = ["Income Statement", "Balance Sheet"]


@router.get("/statements", operation_id="getTickerStatements", dependencies=[Depends(require_pro)])
def get_statements(request: Request, ref: str, years: int = 5) -> Statements:
    t = resolve(request, ref)
    s = settings_of(request)
    years = max(1, min(years, 10))
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            items = evidence.load_items(conn, t.ticker_key, years=years)
            aware = evidence.period_aware(conn)
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc

    by_section: dict[str, dict[int, StatementRow]] = {}
    for c in items.rows:
        sec = by_section.setdefault(c.section, {})
        row = sec.setdefault(c.item_index, StatementRow(index=c.item_index, label=c.label, values={}))
        row.values[str(c.fiscal_year)] = c.value

    def rank(name: str) -> tuple[int, str]:
        return (STATEMENT_ORDER.index(name) if name in STATEMENT_ORDER else 9, name)

    statements = []
    for name, sec in sorted(by_section.items(), key=lambda kv: rank(kv[0])):
        periods = {str(y): items.period(name, y) for y in items.years if items.section_of(name, y)}
        for c in items.rows:
            own = periods.get(str(c.fiscal_year))
            if c.section == name and c.rule and own is not None and c.rule != own.aggregation:
                sec[c.item_index].rules[str(c.fiscal_year)] = c.rule
        statements.append(Statement(section=name, rows=[sec[i] for i in sorted(sec)], periods=periods))
    # Statements keep the pipeline's currency, not a recorded trading currency (universe.py).
    return Statements(
        years=sorted(items.years), unit="mn", currency=t.report_currency,
        statements=statements, period_aware=aware,
    )


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
        currency=t.report_currency,  # dividends, like statements (universe.py)
        dividends=[Dividend(**dict(r)) for r in divs],
        capital_changes=[CapitalChange(**dict(r)) for r in caps],
    )


# --- Financial evidence: reported statements, derived calculations, stated gaps ---------------


@router.get("/evidence", operation_id="getTickerEvidence", dependencies=[Depends(require_pro)])
def get_evidence(request: Request, ref: str) -> evidence.EvidenceDataset:
    """The reported statements for one company, the measures they support, and exactly what is
    missing where a measure cannot be computed.

    Bounded on purpose: this is the dataset a council seat reads inside one prompt, so it carries
    the statement's own leading rows rather than every line, and says how many it left out. The
    unbounded statements are `/statements`.
    """
    t = resolve(request, ref)
    s = settings_of(request)
    try:
        with reader(s.screening_db, immutable=s.market_db_immutable, name="SCREENING_DB") as conn:
            items = evidence.load_items(conn, t.ticker_key, years=2)
            audit: dict[str, dict] = {}
            for row in conn.execute(
                "SELECT gauge_key, inputs_json FROM fundamentals_gauges WHERE ticker_key = ?",
                (t.ticker_key,),
            ):
                try:
                    parsed = json.loads(row["inputs_json"]) if row["inputs_json"] else {}
                except (ValueError, TypeError):
                    parsed = {}
                audit[row["gauge_key"]] = parsed if isinstance(parsed, dict) else {}
            dividends = [
                dict(d)
                for d in conn.execute(
                    "SELECT announce_date, ex_date, pay_date, dps, amount_mn, note FROM dividends"
                    " WHERE ticker_key = ? ORDER BY COALESCE(ex_date, announce_date) DESC LIMIT 24",
                    (t.ticker_key,),
                )
            ]
    except MarketDataUnavailable as exc:
        raise unavailable(exc) from exc
    price = get_ticker(request, ref).quote.last_price
    return evidence.dataset_of(
        items,
        ticker_key=t.ticker_key,
        sector=evidence.sector_of(items, audit),
        currency=t.report_currency,
        peer_class=evidence.recorded_peer_class(audit),
        dividends=dividends,
        price=price,
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
