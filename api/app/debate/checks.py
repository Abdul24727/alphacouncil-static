"""What every line a seat writes goes through before anyone sees it.

1. Digits: Arabic-Indic digits become 0-9 (same value), so the checks below can read them.
2. Citations: a sentence quoting a figure without its tag gets the tag of the dataset the
   figure was read from (the Copilot's context.missing_citations, as in its "autocite").
3. Figures: any figure that appears nowhere in the data pack is listed as unverified, and the
   screen marks it (the Copilot's unverified_cells rule, applied to text).
4. Advice: a sentence that tells someone to buy, sell or hold, or names a price target, is
   removed (legal/ai-financial-disclaimer; the same rule as the Copilot's SYSTEM prompt).
5. Mandate: an opening that cites none of the datasets the seat is answerable for is flagged, so
   a room where every seat argued from the same two figures can be seen rather than guessed at.
   Flagged, never refused: a seat may honestly find its own evidence absent for this company, and
   saying so is covering the mandate - the flag is a question for whoever reads the session, not
   a verdict on the answer.
"""

import re
from typing import Any

from ..copilot.context import FIGURE, TAG, _figures, missing_citations

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬", "01234567890123456789.,")

# Advice in a sentence: someone told to buy, sell or hold, a rating, or a price target. Narrow on
# purpose: "if margins hold", "I hold the view", "selling expenses" and "buyback" are not advice.
SUBJECT = (
    r"\b(?:i|we|you|investors?|members?|one)"
    r"(?:'d|’d|\s+(?:would|should|could|might|must|ought\s+to|can|will))?(?:n't|n’t)?\s+(?:not\s+)?"
)
ADVICE = [
    re.compile(SUBJECT + r"(?:buy|sell|add\s+to|trim|accumulate|short)\b(?!\s*-?\s*(?:back|off)\b)", re.I),
    re.compile(
        SUBJECT + r"hold\s+(?:on\s*to\s+|onto\s+)?(?:it|them|the\s+(?:stock|shares?)|this\s+(?:stock|name|position)|their\s+shares)\b",
        re.I,
    ),
    re.compile(r"\b(?:buy|sell|hold|accumulate)\s+(?:the|this|these|its)?\s*(?:stock|shares?|position)\b", re.I),
    re.compile(r"\b(?:a|rated|rating:?|strong)\s+(?:buy|sell|hold)\b(?!-|\s+on\b)", re.I),
    re.compile(r"\b(?:buy|sell)\s+(?:signal|rating|recommendation|call)\b", re.I),
    re.compile(r"\bprice\s+target\b|\btarget\s+price\b|\b(?:i|we)\s+recommend\b|\byou\s+should\b|\bmy\s+advice\b", re.I),
    re.compile(r"(?:أنصح|ننصح|يُنصح|ينصح|نوصي|أوصي|يوصى|توصية\s+(?:ب|بال)?(?:شراء|بيع|احتفاظ|الشراء|البيع|الاحتفاظ))"),
    re.compile(r"(?:^|[\s،.؛:])(?:اشترِ|اشتر|بِع|احتفظ|احتفظوا|اشتروا|بيعوا)(?=[\s،.؛:!؟]|$)"),
    re.compile(r"(?:السعر\s+المستهدف|سعر\s+مستهدف|(?:شراء|بيع)\s+(?:السهم|الأسهم|أسهم))"),
]
# Option labels and the verdict's headline are short: there any buy / sell / hold word is refused.
ADVICE_SHORT = [
    re.compile(r"(?:^|\W)(?:buy|sell|buying|selling)(?!\s*-?\s*(?:back|off)\b)(?=\W|$)", re.I),
    re.compile(r"^\W*(?:hold|holding|accumulate|avoid|exit|enter)\b", re.I),
    re.compile(r"(?:^|\s)(?:و|ف)?(?:ال|بال|لل)?(?:شراء|بيع|احتفاظ)(?=[\s،.؛:!؟]|$)"),
]

SENTENCE = re.compile(r"[^\n]+?(?:[.!?؟](?=\s|$)|$)", re.M)


def normalize_digits(text: str) -> str:
    return text.translate(ARABIC_DIGITS)


def advice_in(text: str, short: bool = False) -> bool:
    patterns = ADVICE + (ADVICE_SHORT if short else [])
    return any(p.search(text) for p in patterns)


def drop_advice(text: str) -> tuple[str, int]:
    """The text without sentences that give advice, and how many were removed."""
    kept, removed = [], 0
    for line in text.split("\n"):
        parts = [m.group(0) for m in SENTENCE.finditer(line)] or [line]
        good = [p for p in parts if not advice_in(p)]
        removed += len(parts) - len(good)
        kept.append("".join(good).strip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip(), removed


def add_citations(text: str, cites: list[dict[str, Any]]) -> str:
    """lib/copilot-answer.ts addCitations: each tag goes before the sentence's final stop."""
    out = text
    for c in cites:
        i = out.find(c["sentence"])
        if i < 0 or not c["tags"]:
            continue
        end = i + len(c["sentence"])
        at = end - 1 if re.search(r"[.!?؟]$", c["sentence"]) else end
        out = out[:at] + "".join(f" [{t}]" for t in c["tags"]) + out[at:]
    return out


def tags_in(text: str) -> list[str]:
    """The dataset tags cited in a piece of text, in first-seen order."""
    out: list[str] = []
    for m in TAG.finditer(text):
        tag = m.group(0)[1:-1]
        if tag not in out:
            out.append(tag)
    return out


def uncovered(text: str, owns: list[str]) -> list[str]:
    """The seat's own datasets that this text does not cite."""
    return uncovered_in(set(tags_in(text)), owns)


def uncovered_in(cited: set[str], owns: list[str]) -> list[str]:
    """The seat's own datasets that are not in this set of cited tags.

    Separate from `uncovered` because the set that matters is the one the MODEL wrote, which
    `Checked` records before the engine adds citations of its own."""
    return [t for t in owns if t not in cited]


def unverified_figures(text: str, seen: set[str]) -> list[str]:
    """Figures as written in the text that appear nowhere in the data pack (rounded, converted or invented)."""
    bare = TAG.sub(" ", text)
    out: list[str] = []
    for m in FIGURE.finditer(bare):
        for value in _figures(m.group(0)):
            if value not in seen and m.group(0) not in out:
                out.append(m.group(0))
    return out


class Checked:
    """Runs the checks over every text field of one turn and keeps the tally for its flags."""

    def __init__(self, numbers: dict[str, set[str]], seen: set[str]) -> None:
        self.numbers, self.seen = numbers, seen
        self.unverified: list[str] = []
        self.cited = 0
        self.removed = 0
        # The dataset tags the MODEL wrote, recorded before `add_citations` inserts any of the
        # engine's own. Mandate coverage is measured from this and not from the finished text:
        # `missing_citations` attributes a figure to the first panel that holds it, in DATASETS
        # order, so a figure carried by both P2 and P9 is always tagged `[P2]` - and five of the
        # six seated advisors own P9. Reading coverage off the tagged text made the one
        # instrument for Priority Two read P9 low and P2 high, by construction.
        self.written: set[str] = set()

    def text(self, value: Any, limit: int = 2_000) -> str:
        if not isinstance(value, str):
            return ""
        text = normalize_digits(value).strip()[:limit]
        text, removed = drop_advice(text)
        self.removed += removed
        self.written.update(tags_in(text))
        cites = missing_citations(text, self.numbers, set())
        self.cited += len(cites)
        text = add_citations(text, cites)
        for f in unverified_figures(text, self.seen):
            if f not in self.unverified:
                self.unverified.append(f)
        return text

    def flags(self) -> dict[str, Any]:
        return {"unverified": self.unverified, "cited": self.cited, "removed": self.removed}
