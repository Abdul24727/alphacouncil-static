"""The council: six seats, each voting bullish, neutral or bearish on one ticker.

Votes are deterministic rules over database values (thresholds carried over
from the old product's strategy lenses, llm-council/backend/frontend_api.py
2410-2496). A seat with no input data abstains; nothing is estimated. There
is no blended score: the ring shows the seats and their counts. /methodology
renders the rules from THRESHOLDS below, so the page and the votes cannot drift.
"""

from typing import Literal

from pydantic import BaseModel

Vote = Literal["bullish", "neutral", "bearish", "abstain"]
SEATS = ("value", "quality", "income", "momentum", "risk", "news")

# Every number a seat votes on. Changing one changes the votes and /methodology together.
THRESHOLDS: dict[str, dict[str, float]] = {
    "value": {"pe_bullish_below": 10, "pe_neutral_below": 16},
    "quality": {"roe_bullish_above": 20, "roe_neutral_above": 12},
    "income": {"yield_bullish_above": 5, "yield_neutral_above": 2.5},
    "momentum": {"regime_bullish_above": 65, "regime_neutral_above": 45},
    "risk": {"vol_bullish_below": 15, "yield_bullish_above": 3, "vol_neutral_below": 25},
    "news": {"window_days": 30},
}

# Which database values each seat reads (names match SeatInput.name).
INPUTS: dict[str, tuple[str, ...]] = {
    "value": ("pe",),
    "quality": ("roe",),
    "income": ("dividend_yield",),
    "momentum": ("regime_score", "golden_cross"),
    "risk": ("volatility_1y", "dividend_yield"),
    "news": ("positive", "negative", "rated_items"),
}


class SeatInput(BaseModel):
    name: str
    value: float | str | None
    unit: str | None = None


class Seat(BaseModel):
    seat: str
    vote: Vote
    inputs: list[SeatInput]
    rule: str
    # The numbers in the rule, so every screen that states it reads them from here.
    thresholds: dict[str, float] = {}


def _band(v: float | None, bull: float, neutral: float, *, higher_is_better: bool) -> Vote:
    if v is None:
        return "abstain"
    if higher_is_better:
        return "bullish" if v > bull else "neutral" if v > neutral else "bearish"
    return "bullish" if v < bull else "neutral" if v < neutral else "bearish"


def _n(x: float) -> str:
    return f"{x:g}"


def value_seat(pe: float | None) -> Seat:
    t = THRESHOLDS["value"]
    bull, neutral = t["pe_bullish_below"], t["pe_neutral_below"]
    vote = "abstain" if pe is None or pe <= 0 else _band(pe, bull, neutral, higher_is_better=False)
    return Seat(
        seat="value",
        thresholds=THRESHOLDS["value"],
        vote=vote,
        inputs=[SeatInput(name="pe", value=pe, unit="x")],
        rule=f"P/E below {_n(bull)} bullish, below {_n(neutral)} neutral, else bearish; no or negative earnings abstains",
    )


def quality_seat(roe_pct: float | None) -> Seat:
    t = THRESHOLDS["quality"]
    bull, neutral = t["roe_bullish_above"], t["roe_neutral_above"]
    return Seat(
        seat="quality",
        thresholds=THRESHOLDS["quality"],
        vote=_band(roe_pct, bull, neutral, higher_is_better=True),
        inputs=[SeatInput(name="roe", value=roe_pct, unit="%")],
        rule=f"ROE above {_n(bull)}% bullish, above {_n(neutral)}% neutral, else bearish",
    )


def income_seat(yield_pct: float | None) -> Seat:
    t = THRESHOLDS["income"]
    bull, neutral = t["yield_bullish_above"], t["yield_neutral_above"]
    vote = "abstain" if yield_pct is None or yield_pct <= 0 else _band(yield_pct, bull, neutral, higher_is_better=True)
    return Seat(
        seat="income",
        thresholds=THRESHOLDS["income"],
        vote=vote,
        inputs=[SeatInput(name="dividend_yield", value=yield_pct, unit="%")],
        rule=f"Dividend yield above {_n(bull)}% bullish, above {_n(neutral)}% neutral, else bearish; no dividend abstains",
    )


def momentum_seat(regime_score: float | None, golden_cross: bool | None) -> Seat:
    t = THRESHOLDS["momentum"]
    bull, neutral = t["regime_bullish_above"], t["regime_neutral_above"]
    if regime_score is None:
        vote: Vote = "abstain"
    elif regime_score > bull and golden_cross:
        vote = "bullish"
    elif regime_score > neutral:
        vote = "neutral"
    else:
        vote = "bearish"
    return Seat(
        seat="momentum",
        thresholds=THRESHOLDS["momentum"],
        vote=vote,
        inputs=[
            SeatInput(name="regime_score", value=regime_score, unit="/100"),
            SeatInput(name="golden_cross", value=None if golden_cross is None else ("yes" if golden_cross else "no")),
        ],
        rule=f"Trend regime above {_n(bull)} with the 50-day above the 200-day bullish, above {_n(neutral)} neutral, else bearish",
    )


def risk_seat(vol_1y_pct: float | None, yield_pct: float | None) -> Seat:
    t = THRESHOLDS["risk"]
    vol_bull, yld_bull, vol_neutral = t["vol_bullish_below"], t["yield_bullish_above"], t["vol_neutral_below"]
    if vol_1y_pct is None:
        vote: Vote = "abstain"
    elif vol_1y_pct < vol_bull and (yield_pct or 0) > yld_bull:
        vote = "bullish"
    elif vol_1y_pct < vol_neutral:
        vote = "neutral"
    else:
        vote = "bearish"
    return Seat(
        seat="risk",
        thresholds=THRESHOLDS["risk"],
        vote=vote,
        inputs=[
            SeatInput(name="volatility_1y", value=vol_1y_pct, unit="%"),
            SeatInput(name="dividend_yield", value=yield_pct, unit="%"),
        ],
        rule=f"1-year volatility below {_n(vol_bull)}% with a yield above {_n(yld_bull)}% bullish, "
        f"below {_n(vol_neutral)}% neutral, else bearish",
    )


def news_seat(impacts: list[str]) -> Seat:
    days = THRESHOLDS["news"]["window_days"]
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
        thresholds=THRESHOLDS["news"],
        vote=vote,
        inputs=[
            SeatInput(name="positive", value=pos),
            SeatInput(name="negative", value=neg),
            SeatInput(name="rated_items", value=len(impacts)),
        ],
        rule=f"Over the last {_n(days)} days of rated news: a majority positive bullish, a majority negative bearish, "
        "otherwise neutral; no rated news abstains",
    )
