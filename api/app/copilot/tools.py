"""Copilot tools: read-only database queries plus three UI tools.

Database tools reuse the same functions the panels call, so the Copilot sees
exactly what the screen shows. UI tools (`show_table`, `show_price_chart`,
`suggest_follow_ups`) only render something in the chat and return an ack.
"""

from typing import Any

from fastapi import HTTPException, Request

from ..routers import prices as prices_router
from ..routers import ticker as ticker_router
from ..routers import ticker_research as research
from ..routers.tickers import search_tickers

TICKER = {"type": "string", "description": "Ticker symbol or key, e.g. 2222, 1120, FAB, 2010_KSE"}

RANGES = {"1M": 23, "3M": 66, "6M": 130, "1Y": 260, "5Y": 1300}


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


DATABASE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_tickers",
        "description": "Find GCC-listed equities by symbol or company name (English or Arabic).",
        "input_schema": _schema({"query": {"type": "string"}}, ["query"]),
    },
    {
        "name": "get_ticker_overview",
        "description": "Quote, valuation ratios, returns, technicals and data freshness for one ticker.",
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_dividends",
        "description": "Dividend history (ex-date, pay date, per-share amount) and capital changes for one ticker.",
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_fundamentals",
        "description": "Fundamentals strip: valuation, profitability, financial health and income metrics with sector percentiles.",
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_council",
        "description": "The AlphaCouncil's six seats (value, quality, income, momentum, risk, news), each vote, its inputs and rule.",
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_news",
        "description": "Latest news and disclosures touching one ticker, newest first.",
        "input_schema": _schema({"ticker": TICKER, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, ["ticker"]),
    },
    {
        "name": "get_peers",
        "description": "Same-sector peers with price, change, P/E and market cap.",
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_financial_statements",
        "description": (
            "Reported financial statements for one ticker with the period each figure covers,"
            " the date it was struck, the currency, the unit and the rule that aggregated it;"
            " the single quarters behind any reconstructed annual figure; measures computed from"
            " those figures with their formula and operands; and what is missing where a measure"
            " cannot be computed. Reported figures, computed figures and gaps are separate."
        ),
        "input_schema": _schema({"ticker": TICKER}, ["ticker"]),
    },
    {
        "name": "get_price_summary",
        "description": "Summary of daily closes over a range: first and last close, change, high, low, average volume.",
        "input_schema": _schema({"ticker": TICKER, "range": {"type": "string", "enum": list(RANGES)}}, ["ticker", "range"]),
    },
]

UI_TOOLS: list[dict[str, Any]] = [
    {
        "name": "show_table",
        "description": "Show a small table in the chat (the user can pin it to a dashboard). Only database values.",
        "input_schema": _schema(
            {
                "title": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
                "rows": {
                    "type": "array",
                    "maxItems": 30,
                    "items": {"type": "array", "items": {"type": ["string", "number", "null"]}},
                },
                "source": {"type": "string", "description": "Citation tag of the panel or tool the values came from"},
            },
            ["title", "columns", "rows", "source"],
        ),
    },
    {
        "name": "show_price_chart",
        "description": "Show a price chart for a ticker in the chat (the user can pin it to a dashboard).",
        "input_schema": _schema({"ticker": TICKER, "range": {"type": "string", "enum": list(RANGES)}}, ["ticker", "range"]),
    },
    {
        "name": "suggest_follow_ups",
        "description": "Offer 2-3 short follow-up questions the user may ask next. Call once, at the end of every answer.",
        "input_schema": _schema(
            {"questions": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3}},
            ["questions"],
        ),
    },
]

ALL_TOOLS = DATABASE_TOOLS + UI_TOOLS
UI_TOOL_NAMES = {t["name"] for t in UI_TOOLS}


class ToolInputError(ValueError):
    """The model sent input that does not match the tool's schema."""


def validate(name: str, args: Any) -> dict[str, Any]:
    """Minimal schema check (the stream's tolerant parser can hand back partial input)."""
    spec = next((t for t in ALL_TOOLS if t["name"] == name), None)
    if spec is None:
        raise ToolInputError(f"unknown tool {name}")
    if not isinstance(args, dict):
        raise ToolInputError("input must be an object")
    schema = spec["input_schema"]
    for key in schema["required"]:
        if key not in args:
            raise ToolInputError(f"missing {key}")
    for key, value in args.items():
        prop = schema["properties"].get(key)
        if prop is None:
            raise ToolInputError(f"unexpected {key}")
        kind = prop.get("type")
        if kind == "string" and not isinstance(value, str):
            raise ToolInputError(f"{key} must be a string")
        if kind == "integer" and not isinstance(value, int):
            raise ToolInputError(f"{key} must be an integer")
        if kind == "array" and not isinstance(value, list):
            raise ToolInputError(f"{key} must be an array")
        if "enum" in prop and value not in prop["enum"]:
            raise ToolInputError(f"{key} must be one of {prop['enum']}")
    return args


def _dump(model: Any) -> Any:
    if isinstance(model, list):
        return [_dump(m) for m in model]
    return model.model_dump() if hasattr(model, "model_dump") else model


def price_summary(request: Request, ticker: str, range_: str) -> dict[str, Any]:
    t = ticker_router.resolve(request, ticker)
    bars = prices_router.latest_bars(request, t.ticker_key)
    if not bars:
        return {"ticker": t.ticker_key, "has_history": False}
    window = bars[-RANGES[range_] :]
    vols = [b.volume for b in window if b.volume is not None]
    return {
        "ticker": t.ticker_key,
        "currency": t.currency,
        "range": range_,
        "from": window[0].time,
        "to": window[-1].time,
        "first_close": window[0].close,
        "last_close": window[-1].close,
        "change_pct": round((window[-1].close / window[0].close - 1) * 100, 2),
        "high_close": max(b.close for b in window),
        "low_close": min(b.close for b in window),
        "average_volume": round(sum(vols) / len(vols)) if vols else None,
        "trading_days": len(window),
    }


# Data only Pro has (plans.PRO_ONLY): on the Free plan the model is told so and says it.
PRO_TOOLS = {"get_dividends", "get_fundamentals", "get_council", "get_financial_statements"}


def run(request: Request, name: str, args: dict[str, Any]) -> Any:
    """Execute a database tool. Errors come back as data so the model can say what is missing."""
    if name in PRO_TOOLS and getattr(request.state, "plan", "pro") == "free":
        return {"error": "This data is part of AlphaCouncil Pro; the user is on the Free plan. Say so and suggest Pro."}
    try:
        match name:
            case "search_tickers":
                return _dump(search_tickers(request, q=args["query"][:64], limit=6).results)
            case "get_ticker_overview":
                return _dump(ticker_router.get_ticker(request, args["ticker"]))
            case "get_dividends":
                return _dump(research.get_corporate(request, args["ticker"]))
            case "get_fundamentals":
                return _dump(research.get_fundamentals(request, args["ticker"]))
            case "get_financial_statements":
                return _dump(research.get_evidence(request, args["ticker"]))
            case "get_council":
                return _dump(research.get_council(request, args["ticker"]))
            case "get_news":
                items = ticker_router.get_news(request, args["ticker"], limit=args.get("limit", 8))
                return [{k: v for k, v in _dump(i).items() if k != "snippet"} for i in items]
            case "get_peers":
                return _dump(ticker_router.get_peers(request, args["ticker"]))
            case "get_price_summary":
                return price_summary(request, args["ticker"], args["range"])
    except HTTPException as exc:
        return {"error": exc.detail}
    return {"error": f"unknown tool {name}"}
