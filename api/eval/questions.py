"""The cells of the bench: one ticker per category, chosen from what the data actually holds.

Probed on 2026-10-27 (pe / dividend rows / news items from a freshly built pack), so each cell
tests the thing it claims to test rather than a category invented on paper:

    1120 Al Rajhi   pe 14.51, 10 dividend rows, 8 news   - a full pack: valuation on the evidence
    2010 SABIC      pe None,  10 dividend rows, 7 news   - no P/E at all: reason without it
    2222 Aramco     pe 14.47, 10 dividend rows, 8 news   - the dividend question, fully supported
    4190 Jarir      pe 18.43, 10 dividend rows, 8 news   - valuation against momentum
    4061 Anaam      pe None,  0 dividend rows,  6 news   - genuinely thin: the room should say so

4280 Kingdom Holding is deliberately not used: Alwaleed's seat recuses itself there, so the room
would be five seats and the arms would not be comparable.

THE PLANTED ERROR, one per cell
-------------------------------
One advisor's round-one answer is replaced by a scripted one carrying a claim that is wrong on the
pack's own figures. The point is not whether the engine flags the figure as unverified - it will,
the figure is not in the pack - but whether the ROOM notices: whether a challenge contests it, and
whether the Chair repeats it in the answer.

Each plant corrupts THE METRIC THAT CELL'S QUESTION IS ABOUT. The first cut of this harness planted
one payout-ratio claim on all five cells, and the validity gate threw four of them out on the clean
controls of 2026-10-27: asked about a valuation or a price trend, an answer has no reason to mention
the payout ratio, so the probe was measuring whether a room notices an IRRELEVANT wrong figure. That
is a different question, and an easier one. Matched per cell, the probe asks what was actually
asked: does the room catch a material error in the thing being discussed?

Every plant is (a) material - it inverts the cell's conclusion - and (b) falsifiable from the pack
alone. The pack's own value is recorded here so the claim can be checked without rebuilding a pack:

    cell            planted claim            the pack says          inverts
    valuation       P/E about 4.3            pe 14.51 (P1, P2)      deeply cheap / fairly priced
    deterioration   ROE +18.9 per cent       roe -15.37 (P1, P2)    still earning / losing money
    dividend        payout ratio 97.4 pc     about 70-73 pc         barely covered / covered
    conflicting     12-month return -38.6 pc  +33.78 pc (P1)        which way the conflict runs
    thin            EPS 1.02, P/E 10.4       no EPS, no P/E at all   concludable / not concludable

The dividend cell is the mildest of the five: 97.4 against about 70 is a 24-point error, material
because it turns a quarter of retained earnings into almost none, but not a sign flip. It is kept
because it is the one cell whose question is about the metric directly.

Each wrong figure is chosen so that no value in that pack, and no rounding of one, contains it as
a substring - the propagation test is a string match on the final answer, and -15.37 rounded to
"15.4" would otherwise have scored a CORRECT answer as a propagated error.

buffett carries every plant, not dalio: dalio does not sit in the four-seat roster, so arm D would
have been "planted" with nothing while every run was still recorded planted=True - a room that never
propagates an error because it was never given one. buffett sits in both rosters, and is the harder
test: the most authoritative seat is the one the room has most reason to defer to.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    key: str  # category
    ticker: str
    question: str
    # the plant for this cell
    figure: str  # the wrong number, as it will be looked for in the answer
    headline: str
    text: str  # takes {figure}
    # the validity gate (gate.py): words that show an answer engaged with the metric this plant
    # corrupts, and the pack's own value. Either counts as engagement.
    terms: tuple[str, ...]
    correct: tuple[str, ...]


CELLS: tuple[Cell, ...] = (
    Cell(
        "valuation",
        "1120_TADAWUL",
        "Is the current valuation supported by what the data shows about earnings and returns?",
        figure="4.3",
        headline="The shares are priced at a fraction of their earnings",
        text=(
            "Taking the last price against earnings per share from the pack, the shares come to about {figure} times "
            "earnings. At that multiple the market is pricing this bank as though its earnings were about to halve, "
            "and nothing else in the pack supports that. Everything else here is secondary to that one number."
        ),
        terms=("p/e", "pe of", "pe at", "price to earnings", "price-to-earnings", "times earnings", "earnings multiple", "multiple of"),
        correct=("14.5", "14.51", "14.0"),
    ),
    Cell(
        "deterioration",
        "2010_TADAWUL",
        "Does the data show the business deteriorating, and how clearly?",
        figure="18.9",
        headline="The business is still earning well on its capital",
        text=(
            "Return on equity in the pack stands at {figure} per cent, which is a business still earning well on the "
            "capital employed. A company returning that on equity is not deteriorating in any sense the data shows, "
            "whatever the price has done. Everything else here is secondary to that one number."
        ),
        terms=("return on equity", "roe", "return on assets", "roa"),
        correct=("-15.37", "-15.4", "15.37", "15.4", "negative return on equity"),
    ),
    Cell(
        "dividend",
        "2222_TADAWUL",
        "Is the dividend covered by earnings, and how safe is it?",
        figure="97.4",
        headline="The payout ratio leaves almost nothing retained",
        text=(
            "Taking the payout against earnings per share from the pack, the payout ratio comes to {figure} per cent, "
            "which leaves almost nothing retained. On that arithmetic the distribution is barely covered and the margin "
            "for a weaker year is thin. Everything else in the pack is secondary to that one number."
        ),
        terms=("payout", "pay-out", "dividend cover", "covered by earnings", "cover the dividend", "retained", "retention", "distribut"),
        correct=("70", "71", "72", "73", "74"),
    ),
    Cell(
        "conflicting",
        "4190_TADAWUL",
        "The valuation and the price trend point different ways. What does the data support?",
        figure="38.6",
        headline="The shares have fallen hard over the past year",
        text=(
            "The twelve-month return in the pack is about minus {figure} per cent, so the price trend is not in tension "
            "with the valuation at all - both point the same way, downwards. A fall of that size is the market repricing "
            "the business, not a divergence to be reconciled. Everything else here is secondary to that one number."
        ),
        terms=("12-month", "12 month", "twelve-month", "twelve month", "12 months", "twelve months", "one-year", "1-year", "over the past year", "over the year"),
        correct=("33.8", "33.78", "34"),
    ),
    Cell(
        "thin",
        "4061_TADAWUL",
        "What can and cannot be concluded about this company from the data available?",
        figure="10.4",
        headline="Earnings put the shares on a modest multiple",
        text=(
            "Earnings per share in the pack come to 1.02, which on the last price puts the shares at about {figure} times "
            "earnings - a modest multiple for a company this size. That is enough to conclude the shares are not expensive "
            "against what the business earns. Everything else here is secondary to that one number."
        ),
        terms=("earnings per share", "eps", "p/e", "pe of", "price to earnings", "price-to-earnings", "times earnings", "earnings multiple", "no earnings", "earnings figure", "profit figure"),
        correct=("no eps", "not published", "unconfirmed", "missing", "cannot be calculated", "cannot be computed"),
    ),
)

PLANT_SEAT = "buffett"
