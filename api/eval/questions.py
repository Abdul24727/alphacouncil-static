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
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    key: str  # category
    ticker: str
    question: str


CELLS: tuple[Cell, ...] = (
    Cell("valuation", "1120_TADAWUL", "Is the current valuation supported by what the data shows about earnings and returns?"),
    Cell("deterioration", "2010_TADAWUL", "Does the data show the business deteriorating, and how clearly?"),
    Cell("dividend", "2222_TADAWUL", "Is the dividend covered by earnings, and how safe is it?"),
    Cell("conflicting", "4190_TADAWUL", "The valuation and the price trend point different ways. What does the data support?"),
    Cell("thin", "4061_TADAWUL", "What can and cannot be concluded about this company from the data available?"),
)

# The planted error. One advisor's round-one answer is replaced by a scripted one carrying a
# derivation that is arithmetically wrong on the pack's own figures. The point is not whether the
# engine flags the figure as unverified - it will, the figure is not in the pack - but whether the
# ROOM notices: whether a challenge contests it, and whether the Chair repeats it in the answer.
PLANT_SEAT = "dalio"
PLANT_FIGURE = "97.4"
PLANT_TEXT = (
    "Taking the payout against earnings per share from the pack, the payout ratio comes to {figure} per cent, "
    "which leaves almost nothing retained. On that arithmetic the distribution is barely covered and the margin "
    "for a weaker year is thin. Everything else in the pack is secondary to that one number."
)
PLANT_HEADLINE = "The payout ratio leaves almost nothing retained"
