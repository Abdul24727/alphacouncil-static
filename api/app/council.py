"""The council: six seats, each voting bullish, neutral or bearish on one ticker.

Votes are deterministic rules over database values (thresholds carried over
from the old product's strategy lenses, llm-council/backend/frontend_api.py
2410-2496). A seat with no input data abstains; nothing is estimated. There
is no blended score: the ring shows the seats and their counts. The rules
are published on /methodology.
"""

from typing import Literal

from pydantic import BaseModel

Vote = Literal["bullish", "neutral", "bearish", "abstain"]
SEATS = ("value", "quality", "income", "momentum", "risk", "news")


class SeatInput(BaseModel):
    name: str
    value: float | str | None
    unit: str | None = None


class Seat(BaseModel):
    seat: str
    vote: Vote
    inputs: list[SeatInput]
    rule: str


def _band(v: float | None, bull: float, neutral: float, *, higher_is_better: bool) -> Vote:
    if v is None:
        return "abstain"
    if higher_is_better:
        return "bullish" if v > bull else "neutral" if v > neutral else "bearish"
    return "bullish" if v < bull else "neutral" if v < neutral else "bearish"


def value_seat(pe: float | None) -> Seat:
    vote = "abstain" if pe is None or pe <= 0 else _band(pe, 10, 16, higher_is_better=False)
    return Seat(
        seat="value",
        vote=vote,
        inputs=[SeatInput(name="pe", value=pe, unit="x")],
        rule="P/E below 10 bullish, below 16 neutral, else bearish; no or negative earnings abstains",
    )


def quality_seat(roe_pct: float | None) -> Seat:
    return Seat(
        seat="quality",
        vote=_band(roe_pct, 20, 12, higher_is_better=True),
        inputs=[SeatInput(name="roe", value=roe_pct, unit="%")],
        rule="ROE above 20% bullish, above 12% neutral, else bearish",
    )


def income_seat(yield_pct: float | None) -> Seat:
    vote = "abstain" if yield_pct is None or yield_pct <= 0 else _band(yield_pct, 5, 2.5, higher_is_better=True)
    return Seat(
        seat="income",
        vote=vote,
        inputs=[SeatInput(name="dividend_yield", value=yield_pct, unit="%")],
        rule="Dividend yield above 5% bullish, above 2.5% neutral, else bearish; no dividend abstains",
    )


def momentum_seat(regime_score: float | None, golden_cross: bool | None) -> Seat:
    if regime_score is None:
        vote: Vote = "abstain"
    elif regime_score > 65 and golden_cross:
        vote = "bullish"
    elif regime_score > 45:
        vote = "neutral"
    else:
        vote = "bearish"
    return Seat(
        seat="momentum",
        vote=vote,
        inputs=[
            SeatInput(name="regime_score", value=regime_score, unit="/100"),
            SeatInput(name="golden_cross", value=None if golden_cross is None else ("yes" if golden_cross else "no")),
        ],
        rule="Trend regime above 65 with the 50-day above the 200-day bullish, above 45 neutral, else bearish",
    )


def risk_seat(vol_1y_pct: float | None, yield_pct: float | None) -> Seat:
    if vol_1y_pct is None:
        vote: Vote = "abstain"
    elif vol_1y_pct < 15 and (yield_pct or 0) > 3:
        vote = "bullish"
    elif vol_1y_pct < 25:
        vote = "neutral"
    else:
        vote = "bearish"
    return Seat(
        seat="risk",
        vote=vote,
        inputs=[
            SeatInput(name="volatility_1y", value=vol_1y_pct, unit="%"),
            SeatInput(name="dividend_yield", value=yield_pct, unit="%"),
        ],
        rule="1-year volatility below 15% with a yield above 3% bullish, below 25% neutral, else bearish",
    )


def news_seat(impacts: list[str]) -> Seat:
    pos = sum(1 for i in impacts if i == "positive")
    neg = sum(1 for i in impacts if i == "negative")
    if not impacts:
        vote: Vote = "abstain"
    elif pos > neg and pos * 2 > len(impacts):
        vote = "bullish"
    elif neg > pos and neg * 2 > len(impacts):
        vote = "bearish"
    else:
        vote = "neutral"
    return Seat(
        seat="news",
        vote=vote,
        inputs=[
            SeatInput(name="positive", value=pos),
            SeatInput(name="negative", value=neg),
            SeatInput(name="rated_items", value=len(impacts)),
        ],
        rule="Over the last 30 days of rated news: a majority positive bullish, a majority negative bearish, "
        "otherwise neutral; no rated news abstains",
    )
