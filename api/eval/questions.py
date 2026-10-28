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

# ---------------------------------------------------------------------------------------------
# PROBE CELLS, added 2026-10-28
# ---------------------------------------------------------------------------------------------
#
# Eleven more (ticker, question) pairs, for the probe harness only. They are deliberately NOT in
# `CELLS`: `eval run` iterates that tuple, so adding them there would have tripled that harness's
# default scope and cost, and its 2026-10-27 results would no longer be reproducible against it.
# `probe_run` looks up `CELLS + PROBE_CELLS`, so a probe can name any of the sixteen.
#
# Each question asks about ONE quantity, because the gate threw out four of five probes in the
# first cut of this harness for exactly the opposite reason: a plant that corrupts a metric the
# question never asks about is measuring whether a room notices an irrelevant error, which is a
# different and easier question. Every question below is paired with a plant that corrupts the
# thing it asks about.
#
# The `figure`, `headline`, `text` and `correct` fields are the OLD harness's plant. The probe
# harness supplies its own, so these are unused today; they are written coherently rather than
# stubbed so that nothing is waiting to surprise whoever extends `eval run` next.
PROBE_CELLS: tuple[Cell, ...] = (
    Cell(
        "leverage",
        "1120_TADAWUL",
        "What do the returns on equity and on assets together say about how those returns are produced?",
        figure="11.8",
        headline="The returns are produced by the business, not by borrowing",
        text=(
            "Return on assets in the pack stands at {figure} per cent, so a return on equity of 23.49 per cent "
            "needs only about two times leverage to explain it. These are operating returns, not borrowed ones. "
            "Everything else here is secondary to that one number."
        ),
        terms=("return on assets", "roa", "return on equity", "roe", "leverage", "equity multiplier"),
        correct=("2.53", "2.5", "9.3", "leverage"),
    ),
    Cell(
        "worth",
        "2010_TADAWUL",
        "What are the shares worth against the book value the pack reports, and do its own figures agree?",
        figure="51.06",
        headline="The quoted price is a discount to where the multiple puts it",
        text=(
            "At the pack's price-to-book of 1.24 on a book value of 41.18 a share, the shares belong at about "
            "{figure}. The quoted 45.32 is therefore an 11 per cent discount to the multiple the pack itself "
            "reports. Everything else here is secondary to that one number."
        ),
        terms=("price to book", "price-to-book", "p/b", "pb", "book value", "book"),
        correct=("1.10", "1.1", "inconsistent", "does not agree"),
    ),
    Cell(
        "margins",
        "4061_TADAWUL",
        "What do the margins show about whether this business is profitable?",
        figure="8.4",
        headline="A 56 per cent gross margin with profit left at the bottom",
        text=(
            "Gross margin is 56.31 per cent and net margin comes out at about {figure} per cent after costs, so "
            "the business keeps a real profit on every riyal of sales. Everything else here is secondary to that "
            "one number."
        ),
        terms=("net margin", "gross margin", "margin", "profitab"),
        correct=("-49.91", "49.91", "-49.9", "49.9", "loss", "not profitable"),
    ),
    Cell(
        "liquidity",
        "4061_TADAWUL",
        "Can the company meet its short-term obligations on what the pack shows?",
        figure="1.8",
        headline="Short-term cover is tight but workable",
        text=(
            "The current ratio in the pack is {figure}, so current assets cover current liabilities with a little "
            "to spare. Tight, but not a solvency question. Everything else here is secondary to that one number."
        ),
        terms=("current ratio", "current liabilities", "short-term", "liquidity", "cover"),
        correct=("0.18", "0.179", "5.6", "cannot cover", "does not cover"),
    ),
    Cell(
        "annualise",
        "2222_TADAWUL",
        "What is the annual dividend per share on these figures, and what yield does that give?",
        figure="1.32",
        headline="The dividend yield is thinner than it looks",
        text=(
            "The pack's dividend per share is 0.34. Against a price of 25.78 that is a yield of about {figure} per "
            "cent, well under what an income holder would want. Everything else here is secondary to that one "
            "number."
        ),
        terms=("dividend per share", "dps", "annual dividend", "yield", "quarterly"),
        correct=("1.36", "5.01", "5.3", "quarterly", "four"),
    ),
    Cell(
        "capital",
        "2222_TADAWUL",
        "Are the per-share figures comparable across the period the pack covers?",
        figure="4.0",
        headline="The share count has barely moved",
        text=(
            "The capital changes in the pack add up to about {figure} per cent more shares across the five years "
            "the price summary covers, so per-share figures either side of them are directly comparable. "
            "Everything else here is secondary to that one number."
        ),
        terms=("capital", "share count", "shares outstanding", "per share", "bonus"),
        correct=("50", "1.5", "bonus", "not comparable"),
    ),
    Cell(
        "durability",
        "4190_TADAWUL",
        "Does the pack show that these returns on equity are durable?",
        figure="4.8",
        headline="A high return on equity on a substantial book",
        text=(
            "Book value per share in the pack is about {figure}, so a return on equity of 67.25 per cent is earned "
            "on a substantial equity base rather than a thin one. That is a durable advantage. Everything else "
            "here is secondary to that one number."
        ),
        terms=("return on equity", "roe", "book value", "book", "durable", "moat"),
        correct=("1.41", "12.28", "one year", "no history"),
    ),
    Cell(
        "drawdown",
        "1120_TADAWUL",
        "What does the drawdown figure say about the risk in holding these shares today?",
        figure="48.6",
        headline="The drawdown marks this as a high-risk holding today",
        text=(
            "The pack's maximum drawdown of -83.12 per cent, with volatility running at about {figure} per cent, "
            "marks this as a high-risk holding right now. Everything else here is secondary to that one number."
        ),
        terms=("drawdown", "volatility", "risk"),
        correct=("20.94", "historical", "not current"),
    ),
    Cell(
        "asof",
        "2222_TADAWUL",
        "How current is the data behind these figures, and can they be read as one snapshot?",
        figure="2026-10-13",
        headline="Every page of the pack carries the same date",
        text=(
            "The quote, the technicals and the disclosures in this pack are all as of {figure}, so the figures can "
            "be read together as one snapshot of today. Everything else here is secondary to that one date."
        ),
        terms=("as of", "as-of", "dated", "stale", "freshness", "technicals", "disclosures"),
        correct=("2026-08-11", "2026-03-09", "two months", "not simultaneous"),
    ),
    Cell(
        "percentile",
        "1120_TADAWUL",
        "Does the sector comparison in the pack show the shares are cheap?",
        figure="18.0",
        headline="The pack puts this multiple in the cheapest quartile of its sector",
        text=(
            "The pack's sector percentile puts this price-to-earnings ratio at the {figure}th of its sector, inside "
            "the cheapest quartile. On the sector's own numbers these shares are cheap. Everything else here is "
            "secondary to that one number."
        ),
        terms=("percentile", "sector", "quartile", "p/e", "pe of", "multiple"),
        correct=("22.7", "debt to equity", "no percentile", "does not publish"),
    ),
    Cell(
        "peer",
        "4190_TADAWUL",
        "Does the peer comparison in the pack support the valuation?",
        figure="10.4",
        headline="Against its closest peer this is expensive",
        text=(
            "The pack's nearest comparable trades on about {figure} times earnings against this company's 18.43, "
            "so on a peer basis these shares are expensive. Everything else here is secondary to that one number."
        ),
        terms=("peer", "peers", "sector", "comparison", "multiple", "p/e", "times earnings"),
        correct=("26.07", "37.3", "median", "one peer"),
    ),
)

PLANT_SEAT = "buffett"
