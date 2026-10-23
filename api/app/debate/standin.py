"""The room without a model (no OPENROUTER_API_KEY): fixed sentences around database values.

Labelled "stand-in" on the screen, like the Copilot's. It exists so the room can be developed,
tested and shown without spending tokens; its answers go through the same checks as a model's.

It follows the real format: a `choice` session (the question asks the room to choose) frames
options and every seat leans to one; an `open` session has none and the seats answer the question.
"""

import re
from typing import Any

from .engine import State
from .llm import Usage
from .pack import Pack
from .roster import Seat

# Which overview value each advisor looks at first (any other advisor: the dividend yield).
METRIC = {
    "buffett": ("valuation", "roe_pct", "ROE", "العائد على حقوق المساهمين", "%"),
    "lynch": ("valuation", "pe", "P/E", "مكرر الربحية", "x"),
    "dalio": ("returns", "vol_1y_pct", "one-year volatility", "التذبذب خلال سنة", "%"),
    "marks": ("returns", "max_drawdown_pct", "maximum drawdown", "أقصى تراجع", "%"),
}
DEFAULT = ("valuation", "dividend_yield_pct", "dividend yield", "عائد التوزيعات", "%")

OPTIONS = {
    "en": [("The data supports it", "The figures in the pack back the reading."),
           ("Supported only with conditions", "Some figures back it, others cut against it."),
           ("The data argues against it", "The figures in the pack cut against the reading.")],
    "ar": [("البيانات تدعمه", "الأرقام في البيانات تؤيد هذه القراءة."),
           ("مدعوم بشروط فقط", "بعض الأرقام تؤيده وبعضها يعارضه."),
           ("البيانات لا تدعمه", "الأرقام في البيانات تعارض هذه القراءة.")],
}

# A question that asks the room to choose between readings (engine's `choice` mode); anything else is `open`.
CHOICE = re.compile(
    r"\bor\b|\beither\b|\bshould\s+(?:i|we|one)\b|\bwhich\s+(?:of|reading|view)\b|\bأم\b|هل\s+(?:يجب|ينبغي)|أي\s+القراءتين",
    re.I,
)


def mode_for(question: str) -> str:
    return "choice" if CHOICE.search(question) else "open"


def _value(pack: Pack, seat_id: str) -> tuple[str, str, Any, str]:
    group, key, en, ar, unit = METRIC.get(seat_id, DEFAULT)
    overview = pack.data.get("P1") if isinstance(pack.data.get("P1"), dict) else {}
    value = (overview.get(group) or {}).get(key)
    return en, ar, value, unit


def _sentence(pack: Pack, seat: Seat, ar: bool) -> str:
    en_label, ar_label, value, unit = _value(pack, seat.id)
    if value is None:
        return f"لا تُظهر البيانات {ar_label}." if ar else f"The data shows no {en_label}."
    # Two decimals at most, as the rules allow the models (the checks compare at two decimals).
    number = f"{value:.2f}" if isinstance(value, float) and round(value, 2) != value else f"{value}"
    shown = f"{number}{'' if unit == 'x' else unit}"
    return f"{ar_label} {shown} [P1]." if ar else f"The {en_label} is {shown} [P1]."


def _short(seat: Seat, ar: bool) -> str:
    return (seat.info.name_ar if ar else seat.info.name_en).split()[-1]


def _lean(seat_id: str, options: list[str]) -> str | None:
    return options[sum(map(ord, seat_id)) % len(options)] if options else None


def make_asker(pack: Pack, advisors: list[Seat], locale: str, question: str = ""):
    ar = locale == "ar"
    mode = mode_for(question)

    async def ask(*, seat: Seat, stage: str, round: int | None, state: State, check, model: str, **_: Any) -> tuple[dict, Usage]:
        opts = state.options()
        if stage == "brief":
            raw: dict[str, Any] = {
                "mode": mode,
                "question": ("ماذا تقول البيانات عن السؤال المطروح؟" if ar else "What does the data say about the member's question?"),
                "options": (
                    [{"label": label, "detail": detail} for label, detail in OPTIONS["ar" if ar else "en"]] if mode == "choice" else []
                ),
                "focus": [a.info.lens_ar if ar else a.info.lens_en for a in advisors[:3]],
                "weighing": {a.id: a.info.lens_ar if ar else a.info.lens_en for a in advisors},
                "note": "",
            }
        elif stage == "openings":
            lean = _lean(seat.id, opts)
            raw = {
                "lean": lean,
                "headline": (
                    (f"أميل إلى الخيار {lean}." if ar else f"I lean to option {lean}.")
                    if lean
                    else ("هذه قراءتي للأرقام." if ar else "This is how I read the figures.")
                ),
                "text": _sentence(pack, seat, ar) + (" هذا ما أنظر إليه أولاً." if ar else " That is where I look first."),
            }
        elif stage == "faultlines":
            a, b = advisors[0], advisors[1]
            raw = {
                "lines": [{
                    "title": ("الأرقام التي تهم أكثر" if ar else "Which figures matter most"),
                    "between": [a.id, b.id],
                    "text": (f"{_short(a, ar)} و{_short(b, ar)} يقرآن أرقاماً مختلفة." if ar else f"{_short(a, ar)} and {_short(b, ar)} read different figures."),
                }],
                "summary": "",
            }
        elif stage == "debate":
            others = [a for a in advisors if a.id != seat.id]
            to = others[(round or 0) % len(others)]
            raw = {
                "responds_to": to.id,
                "lean": state.lean(seat.id) or _lean(seat.id, opts),
                "headline": (f"ردّ على {_short(to, ar)}." if ar else f"A challenge to {_short(to, ar)}."),
                "text": _sentence(pack, seat, ar) + (f" لا أرى ما يراه {_short(to, ar)}." if ar else f" I do not read it the way {_short(to, ar)} does."),
                "concedes": (f"أوافق {_short(to, ar)} على أهمية الرقم." if ar else f"I grant {_short(to, ar)} that the figure matters."),
            }
        elif stage == "final":
            raw = {
                "lean": state.lean(seat.id) or _lean(seat.id, opts),
                "text": _sentence(pack, seat, ar) + (" هذا موقفي النهائي." if ar else " That is my final position."),
                "changed": "",
                "would_change": ("سلسلة أرباح أطول قد تغيّر موقفي." if ar else "A longer run of earnings would change it."),
            }
        else:
            best = (state.result or {}).get("best") or opts[:1]
            label = next((o["label"] for o in state.brief["options"] if o["id"] == best[0]), best[0]) if best and state.brief else ""
            headline = (
                (f"الأكثر تفضيلاً: {label}" if ar else f"The room favours: {label}")
                if label
                else ("إجابة الغرفة على السؤال" if ar else "The room's answer to the question")
            )
            body = " ".join(_sentence(pack, a, ar) for a in advisors[:3])
            raw = {
                "headline": headline,
                "answer": (("هذه إجابة بديلة بلا نموذج ذكاء اصطناعي. " if ar else "This is a stand-in session without an AI model. ") + body),
                "favours": (("تميل الغرفة إلى هذه القراءة." if ar else "The room leans to this reading.") if label else ""),
                "disagreements": [],
                "gaps": [("لا تتضمن البيانات توقعات للأرباح." if ar else "The data has no earnings forecasts.")],
            }
        return check(raw), Usage(model="stand-in")

    return ask
