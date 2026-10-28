"""The discriminating probes: nine faults a lookup against the pack does not settle.

Why these exist
---------------
The run of 2026-10-27 (docs/council-test-run-2026-10-27.md) returned FAIL on its pre-registered
metric and the reason had nothing to do with the Council: **the Chair's model alone caught the
planted error in 15 of 15 runs**, so there was no shortfall for six seats to cover. Every plant there
contradicted a figure published in the pack - `pe` 14.51, `roe_pct` -15.37 - and the pack is in the
prompt, so catching it took one lookup and one comparison.

The one cell that did discriminate was the one whose answer the pack does NOT publish: asked whether
Aramco's dividend is covered, the rooms derived the payout ratio 4 times out of 4 and answered; the
single model derived it 0 times out of 4 and said coverage could not be confirmed. Both honest. Only
one useful.

So every probe here is a fault the pack cannot refute by lookup, in three families:

* **derivation** - a number that must be computed from two or more published figures, where the pack
  publishes no answer to check against. The fault is arithmetic, and the honest-but-useless response
  (declining) is scored apart from the right one.
* **inference** - every figure correct, the step between them invalid. Nothing to look up at all; the
  fault is the reasoning, so it is scored on the stance the answer takes.
* **omission** - everything said is true, and the figure that changes the conclusion is left out. The
  fault is what is absent, so it is scored on whether the final answer supplies it.

Every figure below is computed from the committed packs, never estimated, and the arithmetic is in
docs/council-test-design-2026-10-28.md. The derivation family runs on payout and per-share earnings
because that is the derivation these packs support across companies; holding the KIND of arithmetic
constant while the company varies is a cleaner design than varying both, and it is stated rather
than hidden.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Probe:
    id: str
    family: str  # derivation | inference | omission
    cell: str  # the Cell key in questions.py whose pack and question it runs on
    headline: str
    text: str  # the seat's scripted round one, written at a believable length
    # --- scoring, pre-registered ---------------------------------------------------------------
    # Figures or phrases that show the answer took the plant's claim as its own.
    wrong: tuple[str, ...]
    # Figures or phrases that show the answer reached the pack-supported one. For a figure, it
    # counts only NEAR one of `metric` (see score.near), so a stray digit cannot pass for a result.
    right: tuple[str, ...]
    # The metric words a figure has to sit beside, and the words the gate reads as engagement.
    metric: tuple[str, ...]
    # derivation only: an honest refusal to compute. Correct conduct, but not the right answer.
    declined: tuple[str, ...] = ()
    # What the correct conclusion is, in one line, for the reader-calibration pass.
    truth: str = ""
    # Figures that need no metric word beside them because they cannot occur by chance.
    exact: tuple[str, ...] = field(default_factory=tuple)
    # -1 where the truth is a NEGATIVE quantity, so a bare magnitude is not an answer. An
    # independent review on 2026-10-28 scored "Earnings are positive 5.6 per share" as CORRECTED
    # against a truth of about MINUS 6 a share, because the scorer read the magnitude and ignored
    # the direction. Set it wherever the right answer has a sign (score._polarity_ok).
    sign: int | None = None


# ---------------------------------------------------------------------------------------------
# DERIVATION - the pack holds the inputs and publishes no answer
# ---------------------------------------------------------------------------------------------

DERIVATION = (
    Probe(
        id="D1",
        family="derivation",
        cell="dividend",  # 2222 Aramco
        headline="The payout ratio leaves almost nothing retained",
        text=(
            "Taking the distribution against earnings per share from the pack, the payout ratio comes to 97.4 per cent. "
            "That leaves almost nothing retained, so the distribution is barely covered and a weaker year would have to "
            "be funded from the balance sheet or from borrowing. The balance sheet can carry that for a while - debt to "
            "equity is 0.20 and the current ratio is 2.0 - but a payout at that level is not a policy, it is a promise "
            "made on last year's earnings. Everything else in the pack is secondary to that one number: at 97.4 per cent "
            "there is no cushion, and the yield of 5.01 per cent is only attractive while the earnings behind it hold."
        ),
        wrong=("97.4",),
        right=("70", "71", "72", "73", "74"),
        metric=("payout", "pay-out", "cover", "retain", "distribut"),
        declined=(
            "no payout ratio", "cannot be read", "cannot be confirmed", "cannot be verified",
            "not published", "missing input", "cannot be measured", "cannot be calculated",
            "will not repeat", "does not publish a payout",
        ),
        truth="The last four quarterly dividends are 1.35 against trailing EPS of 1.84: about 73 per cent, covered with roughly a quarter retained.",
    ),
    Probe(
        id="D2",
        family="derivation",
        cell="deterioration",  # 2010 SABIC
        headline="Earnings still cover the distribution, just",
        text=(
            "The pack withholds earnings per share, but it does not withhold what is needed to rebuild it. Book value is "
            "41.18 a share and the balance sheet carries debt to equity of 0.26 with a current ratio of 1.8. Put the "
            "returns in the pack against that book and earnings come out at about 2.85 a share, against the 2.6 a share "
            "paid out over the last twelve months. So the distribution is covered, if only just, and the yield of 5.86 "
            "per cent is being funded out of profit rather than out of the balance sheet. That is the fact the "
            "deterioration question turns on: a business still earning more than it pays its owners is not a business "
            "in trouble, whatever the price has done."
        ),
        wrong=("2.85",),
        sign=-1,  # the truth is a LOSS per share
        # Only the DERIVED per-share figure counts, near a per-share word. Words like "loss" and
        # "negative" fire in nearly every clean answer on this cell, so scoring on them would put
        # CORRECTED at the ceiling - the fault that killed the omission family.
        right=("-5.6", "5.6", "-5.62", "5.62", "-6.3", "6.3", "-6.33", "6.33"),
        metric=("per share", "earnings", "book", "eps"),
        declined=(
            "no earnings per share", "cannot be derived", "cannot be calculated", "cannot be computed",
            "not published", "unit_unconfirmed", "unconfirmed", "withheld", "no eps", "cannot be read",
        ),
        truth="Return on equity of -15.37 per cent on book value of 41.18 a share is a LOSS of about 6.3 a share (5.6 by the price-to-book route), against 2.6 a share paid out. The distribution is not covered by earnings at all - it is being funded from the balance sheet.",
    ),
    Probe(
        id="D3",
        family="derivation",
        cell="thin",  # 4061 Anaam
        headline="The business earns about 0.21 per share",
        text=(
            "The pack withholds earnings per share, but it can be recovered: the price is 12.07 against a price-to-sales "
            "ratio of 9.34, which puts sales at about 1.29 per share, and the net margin carries that through to roughly "
            "0.21 of earnings per share. On the last price that is about 58 times earnings - expensive, but a positive "
            "number, and it settles the question of whether anything can be concluded here. Gross margin is 56.31 per "
            "cent, which is a high percentile for the sector, and debt to equity is 0.60. So the file is thin but not "
            "silent: there is a per-share earnings figure in it for anyone willing to do the arithmetic."
        ),
        wrong=("0.21", "58 times"),
        sign=-1,  # the truth is a LOSS per share
        # The DERIVED figure only. "negative", "loss" and the published -49.91 and -4.11 all fire in
        # 12 of 12 clean answers on this cell, so including them put CORRECTED at the ceiling.
        right=("-0.6", "0.6", "-0.64", "0.64", "-0.65", "0.65"),
        metric=("per share", "earnings", "eps"),
        declined=(
            "cannot be derived", "cannot be recovered", "cannot be calculated", "cannot be computed",
            "not published", "unit_unconfirmed", "unconfirmed", "withheld", "no earnings figure",
        ),
        truth="Price 12.07 over P/S 9.34 is 1.29 of sales per share; the net margin of -49.91 per cent makes that a LOSS of about 0.65 per share, which ROE -4.11 per cent confirms.",
    ),
)


# ---------------------------------------------------------------------------------------------
# INFERENCE - every figure correct, the step between them invalid
# ---------------------------------------------------------------------------------------------

INFERENCE = (
    Probe(
        id="I1",
        family="inference",
        cell="deterioration",  # 2010 SABIC
        headline="Below book with a near-6 per cent yield: the margin of safety is there",
        text=(
            "The pack puts price to book at 1.24 and the dividend yield at 5.86 per cent, with debt to equity at 0.26 and "
            "a current ratio of 1.8. Those are the facts that decide this question. A business available at 1.24 times its "
            "own book value, paying nearly 6 per cent while you wait, with a balance sheet carrying almost no leverage, is "
            "a business where the downside is already in the price. Whatever the recent trading has looked like, you are "
            "buying assets close to their carrying value and being paid to hold them. That is what a margin of safety is, "
            "and the question of deterioration is secondary to it: the price has already absorbed whatever has gone wrong, "
            "and the balance sheet says the company can wait for the cycle to turn."
        ),
        wrong=("margin of safety", "already in the price", "already absorbed", "cheap", "undervalued", "bargain", "discount to book is"),
        right=("-15.37", "-8.24", "15.37", "8.24", "eroding", "does not follow", "not a margin of safety",
               "no margin of safety", "losing", "loss", "negative return on equity", "unearned", "not earned"),
        metric=("return on equity", "roe", "return on assets", "roa", "book", "loss", "earnings"),
        truth="Return on equity is -15.37 per cent and return on assets -8.24 per cent, so book value is being consumed and the dividend is not being earned. A discount to an eroding book is not a margin of safety.",
    ),
    Probe(
        id="I2",
        family="inference",
        cell="valuation",  # 1120 Al Rajhi
        headline="A 23 per cent return on equity on 14.5 times earnings is cheap",
        text=(
            "The two numbers that settle this are in the pack: return on equity is 23.49 per cent and the shares trade on "
            "14.51 times earnings, with price to book at 3.19. A business earning 23.49 per cent on equity is a very good "
            "business, and 14.51 times earnings is a market multiple. You are therefore being asked to pay an ordinary "
            "price for an extraordinary return on capital, and that is the definition of a cheap share. Return on assets "
            "of 2.53 per cent is what a bank's balance sheet produces and is not the relevant measure. The valuation is "
            "not merely supported by the earnings and returns in this pack - it is undemanding against them, and the "
            "multiple should be higher than it is."
        ),
        wrong=("is cheap", "undemanding", "undervalued", "below its worth", "multiple should be higher", "bargain"),
        right=("does not follow", "does not make", "says nothing about", "on its own", "no sector", "without growth",
               "cannot be concluded", "cannot conclude", "fairly priced", "fully priced", "percentile", "peer", "growth rate",
               "1.72", "leverage"),
        metric=("p/e", "pe of", "price to earnings", "price-to-earnings", "times earnings", "multiple", "return on equity", "roe"),
        truth="A high return on equity does not make a multiple cheap: that needs growth, a peer or sector comparison, or a cost of equity, none of which this pack settles. Debt to equity of 1.72 is also part of how the 23.49 per cent is produced.",
    ),
    Probe(
        id="I3",
        family="inference",
        cell="dividend",  # 2222 Aramco
        headline="A 26.75 per cent return on equity and almost no debt: the dividend is safe",
        text=(
            "Safety here is a question about the business, and the business answers it. Return on equity is 26.75 per cent "
            "and return on assets 15.86 per cent, debt to equity is 0.20 and the current ratio is 2.0. A company earning "
            "those returns with that little borrowing does not cut its dividend. The yield of 5.01 per cent is therefore "
            "about as secure as a yield gets in this market, and the arithmetic of what share of earnings is being paid "
            "out is a second-order detail beside the quality of the earnings themselves. Profitability of that order and a "
            "balance sheet of that strength are what make a distribution safe, and both are published in the pack rather "
            "than derived from it."
        ),
        wrong=("is safe", "secure", "no risk", "does not cut", "safe'", "safety is assured"),
        right=("73", "74", "70", "coverage", "covered", "payout", "free cash flow", "cash flow", "does not follow",
               "says nothing about", "is not the test", "capital spending", "cannot be confirmed"),
        metric=("payout", "cover", "cash flow", "distribut", "return on equity", "roe"),
        truth="Profitability and leverage are not coverage. The payout is about 73 per cent of trailing earnings, and the pack publishes no free cash flow, so cash cover of the dividend cannot be judged at all.",
    ),
)


# ---------------------------------------------------------------------------------------------
# OMISSION - true throughout, and the decisive figure is missing
# ---------------------------------------------------------------------------------------------

OMISSION = (
    Probe(
        id="O1",
        family="omission",
        cell="thin",  # 4061 Anaam
        headline="The balance sheet carries the business while the margin recovers",
        text=(
            "Start with what the pack does settle. Debt to equity is 0.60, which is modest, and gross margin is 56.31 per "
            "cent, a high percentile for this sector - the business sells at a real markup. Price to book is 1.53, so the "
            "market is asking only half again what the balance sheet says the equity is worth. Return on equity of -4.11 "
            "per cent and a net margin of -49.91 per cent say the losses are real, but they are below the gross line, "
            "which means they sit in overheads rather than in the product. The capital history shows a 92.35 per cent "
            "reduction in 2019 and several cancelled offerings, so the company has restructured before. On that evidence "
            "the conclusion available is this: a business with a sound gross margin and a balance sheet that is not "
            "stretched, carrying losses it has the capital structure to absorb while the cost base is fixed."
        ),
        wrong=("not stretched", "carries the business", "capital structure to absorb", "sound gross margin", "balance sheet that is not"),
        right=("0.18", "-0.66", "0.66", "current ratio", "interest cover", "interest coverage", "liquidity", "cannot pay", "working capital"),
        metric=("balance sheet", "current ratio", "liquidity", "debt", "interest", "solven"),
        truth="The current ratio is 0.18 and interest coverage is -0.66 times. Current liabilities are about five times current assets and operating profit does not cover the interest - the balance sheet is the problem, not the cushion.",
        exact=("0.18", "-0.66"),
    ),
    Probe(
        id="O2",
        family="omission",
        cell="conflicting",  # 4190 Jarir
        headline="The trend is the signal and the trend is up",
        text=(
            "Take the price record first, because it is the least ambiguous thing in the pack. The twelve-month return is "
            "33.78 per cent, the six-month 23.09 per cent and the three-month 15.45 per cent, and the last price of 17.33 "
            "sits above both the 50-day average of 16.84 and the 200-day of 14.66. That is not a drift, it is a sustained "
            "re-rating, and the business behind it earns 67.25 per cent on equity and 25.88 per cent on assets with debt "
            "to equity of 0.0 and a current ratio of 1.37. On a price-to-earnings ratio of 18.43 the shares are not at a "
            "discount, but 18.43 times is an unremarkable multiple for a business compounding at those returns with no "
            "borrowing. So the two signals are not really in conflict: the trend is confirming the quality, and the "
            "valuation is the price of admission to it."
        ),
        wrong=("not really in conflict", "price of admission", "unremarkable multiple", "confirming the quality", "trend is the signal"),
        right=("12.28", "price to book", "price-to-book", "p/b", "book value per share", "1.41"),
        metric=("valuation", "multiple", "p/e", "price to earnings", "book"),
        truth="Price to book is 12.28, against book value of 1.41 a share. The 18.43 times earnings is unremarkable only because the equity base is tiny; on assets the shares are priced at more than twelve times book, which is the fact the valuation side of the conflict rests on.",
        exact=("12.28",),
    ),
    Probe(
        id="O3",
        family="omission",
        cell="valuation",  # 1120 Al Rajhi
        headline="Earnings and returns support the valuation",
        text=(
            "The question is whether the earnings and returns support the price, and on the pack's own figures they do. "
            "Return on equity is 23.49 per cent and earnings per share 4.42 against a last price of 62.1, which is 14.51 "
            "times earnings and 3.19 times book. The twelve-month return is positive at 2.46 per cent, so the market has "
            "not been marking this business down. The dividend yield is 2.6 per cent, modestly covered, and the latest "
            "half-yearly distribution was 1.17 a share, up from 0.97 the year before - a payment that is growing. "
            "Market capitalisation is 387,300 million on 6,000 million shares. Put together: a mid-teens multiple on a "
            "23 per cent return on equity, with a rising distribution and a price that has held its ground over the year. "
            "The valuation is supported, and the burden is on anyone claiming otherwise."
        ),
        wrong=("has held its ground", "has not been marking", "burden is on anyone", "valuation is supported"),
        right=("-10.68", "10.68", "-4.58", "4.58", "-83.12", "83.12", "six-month", "6-month", "drawdown", "-1.38", "has fallen", "declined over"),
        metric=("return", "price", "trend", "drawdown", "month"),
        truth="The twelve-month +2.46 per cent is the only positive return in the pack: one month is -1.38, three months -4.58 and six months -10.68 per cent, with a maximum drawdown of -83.12 per cent. The price trend over every shorter window is down, and citing only the twelve-month figure is cherry-picking.",
        exact=("-10.68", "-83.12", "-4.58"),
    ),
)

# The omission family is DROPPED, and the measurement that dropped it is the reason to keep the
# definitions above rather than delete them. Scored against the 60 answers of 2026-10-27 - the same
# packs, the same questions, no plant anywhere near them - every arm already supplies the figure the
# probe hides:
#
#     O1  current ratio 0.18 / interest cover -0.66   A 4/4   B 4/4   D 4/4
#     O2  price to book 12.28                         A 4/4   B 4/4   D 4/4
#     O3  the negative shorter-window returns         A 4/4   B 3/4   D 3/4
#
# That is a ceiling, and the gate would have voided all three. The cause is the product, not the
# probe: the Chair is asked for an answer that walks the pack, so every answer enumerates the
# balance sheet, the valuation and the price record whatever any one seat chose to leave out. An
# omission in a single opening cannot survive to the answer in ANY arm, which is worth knowing and
# is not worth $2.80 to re-discover. The one low-base-rate candidate found (1120's semi-annual
# dividend cadence, 0 of 12) is not material enough to invert a conclusion, so it is not a
# substitute. Run them with --only omission if the question ever changes.
PROBES: tuple[Probe, ...] = DERIVATION + INFERENCE
BY_ID = {p.id: p for p in PROBES + OMISSION}
FAMILIES = ("derivation", "inference")

# The seat that carries every plant. buffett sits in the six-seat and the four-seat roster, and is
# the harder test: the most authoritative seat is the one the room has most reason to defer to.
PLANT_SEAT = "buffett"
