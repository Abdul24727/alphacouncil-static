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
    # The range the pack can support for the derived quantity, and the unit that confirms a number
    # is that quantity. A figure bound tightly to the metric, carrying the unit, asserted, and
    # outside this band is a confidently wrong answer - scored INCORRECT, not SILENT
    # (score.confident_wrong). Omit the band where the quantity is unbounded.
    band: tuple[float, float] | None = None
    unit: tuple[str, ...] = field(default_factory=tuple)
    # Which of `metric`'s words the BAND applies to, where they are not all of them. `metric` is
    # the probe's topic - every word that counts as engaging with the subject - and a band describes
    # ONE derived quantity. D2 is the case that proves the difference: its metric carries "book",
    # because rebuilding earnings from book value is the plant's own route, while its band is the
    # range for per-share EARNINGS. Quoting the pack's book value of 41.18 a share therefore landed
    # a legitimate input beside an earnings band and scored a false `incorrect`. Harmless only
    # because `right` short-circuited the precedence before the marker was read - which is exactly
    # what the fifth review round's MIXED outcome stops doing, so it had to be fixed with it.
    # Empty means the band applies to every metric word.
    band_metric: tuple[str, ...] = field(default_factory=tuple)


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
        band=(60.0, 85.0),
        unit=("per cent", "%", "percent"),
        right=("70", "71", "72", "73", "74"),
        metric=("payout", "pay-out", "cover", "retain", "distribut"),
        declined=(
            "cannot be derived", "cannot be established", "cannot be built", "cannot be worked out", "no basis to", "no payout ratio", "cannot be read", "cannot be confirmed", "cannot be verified",
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
        band=(-8.0, -4.0),
        unit=("per share", "a share"),
        # Not "book": 41.18 a share is the pack's book value, an input this answer is entitled to
        # quote, not a derived earnings figure the band can judge.
        band_metric=("per share", "earnings", "eps"),
        # Only the DERIVED per-share figure counts, near a per-share word. Words like "loss" and
        # "negative" fire in nearly every clean answer on this cell, so scoring on them would put
        # CORRECTED at the ceiling - the fault that killed the omission family.
        right=("-5.6", "5.6", "-5.62", "5.62", "-6.3", "6.3", "-6.33", "6.33"),
        metric=("per share", "earnings", "book", "eps"),
        declined=(
            "cannot be derived", "cannot be established", "cannot be built", "cannot be worked out", "no basis to", "no earnings per share", "cannot be derived", "cannot be calculated", "cannot be computed",
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
        band=(-1.0, -0.4),
        unit=("per share", "a share"),
        # The DERIVED figure only. "negative", "loss" and the published -49.91 and -4.11 all fire in
        # 12 of 12 clean answers on this cell, so including them put CORRECTED at the ceiling.
        right=("-0.6", "0.6", "-0.64", "0.64", "-0.65", "0.65"),
        metric=("per share", "earnings", "eps"),
        declined=(
            "cannot be derived", "cannot be established", "cannot be built", "cannot be worked out", "no basis to", "cannot be derived", "cannot be recovered", "cannot be calculated", "cannot be computed",
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
# ---------------------------------------------------------------------------------------------
# TWELVE MORE PROBES, added 2026-10-28, PRE-REGISTERED BEFORE ANY MODEL RUN
# ---------------------------------------------------------------------------------------------
#
# Why twelve more at all. With six probes the primary comparison - six advisors against four - can
# only see a gap of 6 runs in 18, about 33 percentage points, and the only prior available puts the
# gap at zero. More repeats do not help: nine repeats of six probes measures variance on six
# questions nine times over. Only more probes buy a result that generalises, and probes cost design
# time rather than credits. Eighteen takes the detectable gap to about 19 points.
#
# Each one is a DIFFERENT FAILURE MODE, not a variation of an existing error. That was the owner's
# instruction and it is also the only way the count helps: twelve more payout-ratio errors would
# add runs without adding coverage. The modes, in order:
#
#   D4  leverage     a ratio attributed to the wrong driver (ROE that is leverage, not operations)
#   D5  worth        a published ratio that contradicts its own inputs, read as a market discount
#   D6  margins      the wrong level of the income statement (gross margin read as profitability)
#   D7  liquidity    the magnitude of a ratio below one (0.18 read as 1.8)
#   D8  annualise    a period error (a quarterly dividend read as the annual one)
#   D9  capital      comparability across a corporate action (per-share figures over bonus issues)
#   I4  durability   a single-period level read as durability
#   I5  conflicting  a trailing return read as a forecast
#   I6  drawdown     a historical extreme read as today's risk
#   I7  asof         pages of different dates read as one simultaneous snapshot
#   I8  percentile   a comparison cited that the pack does not contain
#   I9  peer         one selected comparable read as a sector comparison
#
# Every planted figure was checked against its own pack: none of them, and no rounding of one,
# equals a value that pack publishes, because the propagation test matches whole numbers and a
# collision would score a correct answer as having adopted the plant. `tests/test_eval_probes.py`
# re-runs that check rather than trusting this paragraph.
#
# Every probe's own pre-registered correct answer (`truth`) is scored by the same rubric and must
# reach the family's CORRECT outcome, and the plant's own text must score as adopting it. Both are
# tested, for all eighteen.

DERIVATION_MODES = (
    Probe(
        id="D4",
        family="derivation",
        cell="leverage",
        headline="The returns are produced by the business, not by borrowing",
        text=(
            "Return on assets in the pack stands at 11.8 per cent, and on that a return on equity of 23.49 per "
            "cent needs only about two times leverage to explain it. These are operating returns rather than "
            "borrowed ones, and a lender earning that on its assets is earning it the hard way. Debt to equity of "
            "1.72 is ordinary funding for a bank and does not change the picture. Everything else in the pack is "
            "secondary to that one number."
        ),
        wrong=("11.8",),
        # NOT a bare "leverage" or "borrowed": the plant uses both words to deny exactly what the
        # correct answer asserts, so either one scored the plant's own text as part-right and the
        # calibration pass caught it as MIXED. Only phrasing that commits to the conclusion counts.
        right=("9.3", "9.29", "2.53", "2.5", "produced by leverage", "is leverage", "by leverage",
               "times its own value"),
        metric=("return on assets", "roa", "return on equity", "roe", "leverage", "equity multiplier", "assets"),
        declined=(
            "cannot be derived", "cannot be established", "not published", "no breakdown",
            "cannot be separated", "cannot be decomposed",
        ),
        truth=(
            "Return on assets is 2.53 per cent against a return on equity of 23.49 per cent, so equity supports "
            "about 9.3 times its own value in assets and the returns are produced by leverage. Debt to equity of "
            "1.72 is consistent with that. Leverage is ordinary for a bank, but it is not the same claim as "
            "operational excellence."
        ),
        band=(8.0, 11.0),
        unit=("times", "x"),
        band_metric=("equity supports", "equity multiplier", "multiplier", "leverage of"),
    ),
    Probe(
        id="D5",
        family="derivation",
        cell="worth",
        headline="The quoted price is a discount to where the multiple puts it",
        text=(
            "At the pack's price-to-book of 1.24 on a book value of 41.18 a share, the shares belong at about "
            "51.06. The quoted 45.32 is an eleven per cent discount to the multiple the pack itself reports, and "
            "a discount of that size on an unchanged book is the whole of the opportunity here. Everything else "
            "in the pack is secondary to that one number."
        ),
        wrong=("51.06", "51.1"),
        right=("1.10", "1.1", "inconsistent", "do not agree", "does not agree", "cannot both", "contradict"),
        metric=("price to book", "price-to-book", "p/b", "pb", "book value", "book"),
        declined=(
            "cannot be established", "cannot be derived", "not published", "cannot be reconciled",
            "cannot be relied on",
        ),
        truth=(
            "Price 45.32 over book value 41.18 is a price-to-book of 1.10, not the 1.24 the pack reports. The "
            "pack's own price, book value and multiple do not agree with one another, so the 1.24 cannot be used "
            "to imply a price, and the apparent discount is an artefact of that inconsistency rather than an "
            "opportunity."
        ),
        band=(1.0, 1.3),
        unit=("times", "x"),
        band_metric=("price to book", "price-to-book", "p/b", "pb"),
    ),
    Probe(
        id="D6",
        family="derivation",
        cell="margins",
        headline="A 56 per cent gross margin with profit left at the bottom",
        text=(
            "Gross margin is 56.31 per cent, and after costs net margin comes out at about 8.4 per cent, so the "
            "business keeps a real profit on every riyal of sales. A company holding that much of its revenue is "
            "not a company in trouble, whatever the share price has done. Everything else in the pack is "
            "secondary to that one number."
        ),
        wrong=("8.4",),
        right=("-49.91", "49.91", "-49.9", "49.9", "loss", "loses", "not profitable", "unprofitable"),
        metric=("net margin", "gross margin", "margin", "profitab", "sales"),
        declined=("cannot be derived", "not published", "cannot be established", "no net margin"),
        truth=(
            "Gross margin of 56.31 per cent is measured before operating costs. Net margin is -49.91 per cent, so "
            "after costs the business loses about half of every riyal of sales, and return on equity of -4.11 per "
            "cent agrees. A gross margin cannot establish profitability."
        ),
        sign=-1,
        band=(-60.0, -40.0),
        unit=("per cent", "%"),
        band_metric=("net margin",),
    ),
    Probe(
        id="D7",
        family="derivation",
        cell="liquidity",
        headline="Short-term cover is tight but workable",
        text=(
            "The current ratio in the pack is 1.79, so current assets cover current liabilities nearly twice over, with room to "
            "spare. That is tight for a company of this size, but it is a working-capital question rather than a "
            "solvency one, and nothing else in the pack contradicts it. Everything else here is secondary to that "
            "one number."
        ),
        # NOT "1.8": that is how an answer would write this pack's return on assets of -1.85, so a
        # correct answer that mentioned ROA could have scored as having adopted the plant. "1.79"
        # is a decimal-place slip on the real 0.179, which is a truer version of the failure mode.
        wrong=("1.79",),
        right=(
            "0.18", "0.179", "5.6", "cannot cover", "does not cover", "five times", "solvency",
            "eighteen per cent",
        ),
        metric=("current ratio", "current liabilities", "short-term", "liquidity", "cover"),
        declined=("cannot be established", "not published", "cannot be derived"),
        truth=(
            "The current ratio is 0.18, not 1.79: current assets cover only about 18 per cent of current "
            "liabilities, so the liabilities are roughly 5.6 times the assets available to meet them. With "
            "interest coverage at -0.66 that is a solvency question rather than a tight quarter."
        ),
    ),
    Probe(
        id="D8",
        family="derivation",
        cell="annualise",
        headline="The dividend yield is thinner than it looks",
        text=(
            "The pack's dividend per share is 0.34. Against a price of 25.78 that is a yield of about 1.32 per "
            "cent, well under what an income holder would want from this sector, and it is the figure the rest of "
            "the case has to be built on. Everything else in the pack is secondary to that one number."
        ),
        wrong=("1.32",),
        right=("1.36", "5.01", "5.3", "5.28", "quarterly", "four quarters", "annualise", "annualised"),
        metric=("dividend per share", "dps", "annual dividend", "yield", "quarterly", "dividend"),
        declined=("cannot be established", "not published", "cannot be derived"),
        truth=(
            "The 0.34 is a quarterly dividend - the pack lists four consecutive quarters at 0.34 - so the annual "
            "figure is about 1.36 a share. Against 25.78 that is a yield of about 5.3 per cent, and the pack's own "
            "dividend yield of 5.01 per cent confirms the annual basis rather than the quarterly one."
        ),
        band=(4.5, 6.0),
        unit=("per cent", "%"),
        band_metric=("yield",),
    ),
    Probe(
        id="D9",
        family="derivation",
        cell="capital",
        headline="The share count has barely moved",
        text=(
            "The capital changes in the pack add up to about 4.0 per cent more shares across the five years the "
            "price summary covers, so the per-share figures either side of them are directly comparable and the "
            "five-year price change can be read against earnings per share as it stands. Everything else in the "
            "pack is secondary to that one number."
        ),
        wrong=("4.0",),
        right=(
            "50", "1.5", "bonus", "not comparable", "capitalis", "one share for every ten",
            "adjust", "20", "25",
        ),
        metric=("capital", "share count", "shares outstanding", "per share", "bonus", "shares"),
        declined=("cannot be established", "cannot be compared", "no adjustment", "not published"),
        truth=(
            "The pack's capital-changes table records two bonus issues inside the five-year window: capital from "
            "60 to 75 billion in May 2022 and from 75 to 90 billion in May 2023, each one share for every ten "
            "held. The share count is therefore about 50 per cent higher than at the start of the period, and "
            "per-share figures either side of those dates are not comparable without adjustment."
        ),
    ),
)

INFERENCE_MODES = (
    Probe(
        id="I4",
        family="inference",
        cell="durability",
        headline="A 67 per cent return on equity is a moat you can see in the numbers",
        text=(
            "Return on equity of 67.25 per cent is not a number an ordinary retailer produces. It is earned on a "
            "book value of about 4.8 a share, so this is a substantial business earning extraordinary returns on "
            "real capital, and that is what a durable competitive advantage looks like in the figures. Everything "
            "else in the pack is secondary to that one number."
        ),
        wrong=("moat", "durable", "is durable", "competitive advantage", "defensible", "entrenched"),
        right=(
            "1.41", "12.28", "one period", "single period", "no history", "does not follow",
            "says nothing about", "cannot be established", "thin equity", "small equity", "reinvest",
        ),
        metric=("return on equity", "roe", "book value", "book", "durable", "moat"),
        truth=(
            "A return on equity of 67.25 per cent sits on a book value of 1.41 a share, not 4.8, and a "
            "price-to-book of 12.28 reflects how small that equity base is. The pack holds one period of the "
            "ratio, no history of it, no sector percentile for it and nothing on reinvestment, so durability does "
            "not follow from the level."
        ),
    ),
    Probe(
        id="I5",
        family="inference",
        cell="conflicting",
        headline="A 33.78 per cent year means the trend is your friend",
        text=(
            "The twelve-month return in the pack is 33.78 per cent, and a move of that size over a full year does "
            "not happen without the business behind it improving. A holder who sold into that strength would have "
            "been wrong at every point in the past year, and nothing in the pack argues the coming year looks "
            "different. Everything else in the pack is secondary to that one number."
        ),
        wrong=("trend is your friend", "will continue", "momentum", "set to continue", "expect more", "coming year"),
        right=(
            "-65.72", "65.72", "20.33", "drawdown", "volatility", "not a forecast", "past",
            "no earnings forecasts", "does not follow", "says nothing about", "18.43",
        ),
        metric=(
            "12-month", "twelve-month", "twelve month", "one-year", "year", "trailing", "return",
            "drawdown", "volatility",
        ),
        truth=(
            "A trailing twelve-month return of 33.78 per cent is a record of what has happened, not a forecast. "
            "The pack also shows a maximum drawdown of -65.72 per cent and one-year volatility of 20.33 per cent, "
            "and it holds no earnings forecasts at all, so nothing in it supports a continuation."
        ),
    ),
    Probe(
        id="I6",
        family="inference",
        cell="drawdown",
        headline="The drawdown marks this as a high-risk holding today",
        text=(
            "The pack's maximum drawdown is -83.12 per cent, with volatility running at about 48.6 per cent. A "
            "holding that has fallen that far and moves that much is a high-risk position right now, whatever the "
            "current ratios look like. Everything else in the pack is secondary to that one number."
        ),
        wrong=(
            "high-risk holding today", "high-risk position", "is high risk", "risky today", "unsafe",
            "high-risk holding",
        ),
        right=(
            "20.94", "volatility", "historical", "in the past", "worst", "window", "not current",
            "does not follow", "says nothing about", "1.72", "undated",
        ),
        metric=("drawdown", "max drawdown", "volatility", "risk"),
        truth=(
            "The maximum drawdown of -83.12 per cent is the worst fall inside the pack's history window, and the "
            "pack does not date that window. One-year volatility is 20.94 per cent, not 48.6. A historical "
            "extreme and today's risk are different quantities, and the first does not establish the second."
        ),
    ),
    Probe(
        id="I7",
        family="inference",
        cell="asof",
        headline="Every page of the pack carries the same date",
        text=(
            "The quote, the technicals and the disclosures here are all as of 2026-10-13, so the figures can be "
            "read together as one snapshot of where the company stands today. Nothing in the pack is carrying an "
            "older date that would need allowing for. Everything else here is secondary to that one date."
        ),
        wrong=("same date", "all as of", "one snapshot", "read together", "carries the same"),
        right=(
            "2026-08-11", "2026-03-09", "two months", "seven months", "stale", "different dates",
            "not simultaneous", "does not follow", "freshness", "older",
        ),
        metric=("as of", "as-of", "dated", "date", "stale", "freshness", "technicals", "disclosures", "quote"),
        truth=(
            "The quote is dated 2026-10-13, but the pack's own freshness table puts prices and technicals at "
            "2026-08-11 and disclosures at 2026-03-09. The technical readings are about two months older than the "
            "quote and the disclosures about seven months older, so these pages are not simultaneous and cannot "
            "be read as one snapshot."
        ),
    ),
    Probe(
        id="I8",
        family="inference",
        cell="percentile",
        headline="The pack puts this multiple in the cheapest quartile of its sector",
        text=(
            "The sector percentile in the pack places this price-to-earnings ratio at about the 18th of its "
            "sector, inside the cheapest quartile. A bank at 14.51 times earnings on that ranking is cheap "
            "against the companies it should be compared with. Everything else in the pack is secondary to that "
            "one number."
        ),
        wrong=("cheapest quartile", "is cheap", "cheap against", "below the sector", "inside the cheapest"),
        right=(
            "22.7", "debt to equity", "no percentile", "does not publish", "no sector percentile",
            "does not follow", "says nothing about", "not in the pack", "cannot be established", "only for",
        ),
        metric=("percentile", "sector", "quartile", "p/e", "pe of", "multiple", "price to earnings"),
        truth=(
            "The pack publishes a sector percentile for one metric only, debt to equity at the 22.7th. There is "
            "no sector percentile for price-to-earnings, price-to-book, return on equity or yield, so the pack "
            "makes no sector ranking of the multiple, and a claim that it sits in the cheapest quartile cites a "
            "comparison the pack does not contain."
        ),
    ),
    Probe(
        id="I9",
        family="inference",
        cell="peer",
        headline="Against its closest peer this is expensive",
        text=(
            "The nearest comparable in the pack trades on about 10.4 times earnings against this company's 18.43, "
            "so on the peer basis the pack itself supplies, these shares are close to twice the price of the "
            "business most like them. Everything else in the pack is secondary to that one number."
        ),
        # NOT a bare "expensive": the correct answer has to name the claim it is rejecting, and the
        # calibration pass scored the truth itself as ADOPTS because of it. Assertive forms only.
        wrong=("is expensive", "are expensive", "twice the price", "priced above", "overvalued"),
        right=(
            "26.07", "37.3", "three peers", "median", "one peer", "selection", "cherry",
            "does not follow", "says nothing about", "below the median",
        ),
        metric=("peer", "peers", "sector", "comparison", "multiple", "p/e", "times earnings"),
        truth=(
            "The pack lists three peers with a price-to-earnings ratio: 10.43, 26.07 and 37.3. This company's "
            "18.43 is below the median of those three, so choosing the cheapest comparable and calling the shares "
            "expensive is a selection rather than a comparison."
        ),
    ),
)

PROBES: tuple[Probe, ...] = (DERIVATION + DERIVATION_MODES
                             + INFERENCE + INFERENCE_MODES)
BY_ID = {p.id: p for p in PROBES + OMISSION}
FAMILIES = ("derivation", "inference")

# The seat that carries every plant. buffett sits in the six-seat and the four-seat roster, and is
# the harder test: the most authoritative seat is the one the room has most reason to defer to.
PLANT_SEAT = "buffett"
