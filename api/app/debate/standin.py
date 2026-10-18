"""The room without a model (no OPENROUTER_API_KEY): fixed sentences around database values.

Labelled "stand-in" on the screen, like the Copilot's. It exists so the room can be developed,
tested and shown without spending tokens; its answers go through the same checks as a model's.
"""

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


def _value(pack: Pack, seat_id: str) -> tuple[str, str, Any, str]:
    group, key, en, ar, unit = METRIC.get(seat_id, DEFAULT)
    overview = pack.data.get("P1") if isinstance(pack.data.get("P1"), dict) else {}
    value = (overview.get(group) or {}).get(key)
    return en, ar, value, unit


def _sentence(pack: Pack, seat: Seat, ar: bool) -> str:
    en_label, ar_label, value, unit = _value(pack, seat.id)
    if value is None:
        return f"لا تُظهر البيانات {ar_label}." if ar else f"The data shows no {en_label}."
    shown = f"{value}{'' if unit == 'x' else unit}"
    return f"{ar_label} {shown} [P1]." if ar else f"The {en_label} is {shown} [P1]."


def _lean(seat_id: str, options: list[str]) -> str:
    return options[sum(map(ord, seat_id)) % len(options)]


def make_asker(pack: Pack, advisors: list[Seat], locale: str):
    ar = locale == "ar"

    async def ask(*, seat: Seat, stage: str, round: int | None, state: State, check, model: str, **_: Any) -> tuple[dict, Usage]:
        opts = state.options()
        if stage == "brief":
            raw: dict[str, Any] = {
                "question": ("ماذا تقول البيانات عن السؤال المطروح؟" if ar else "What does the data say about the member's question?"),
                "options": [{"label": label, "detail": detail} for label, detail in OPTIONS["ar" if ar else "en"]],
                "focus": [a.info.lens_ar if ar else a.info.lens_en for a in advisors[:3]],
                "weighing": {a.id: a.info.lens_ar if ar else a.info.lens_en for a in advisors},
                "note": "",
            }
        elif stage == "openings":
            lean = _lean(seat.id, opts)
            raw = {
                "lean": lean,
                "headline": (f"أميل إلى الخيار {lean}." if ar else f"I lean to option {lean}."),
                "text": _sentence(pack, seat, ar) + (" هذا ما أنظر إليه أولاً." if ar else " That is where I look first."),
            }
        elif stage == "faultlines":
            a, b = advisors[0], advisors[1]
            raw = {
                "lines": [{
                    "title": ("الأرقام التي تهم أكثر" if ar else "Which figures matter most"),
                    "between": [a.id, b.id],
                    "text": (f"{a.surname} و{b.surname} يقرآن أرقاماً مختلفة." if ar else f"{a.surname} and {b.surname} read different figures."),
                }],
                "summary": "",
            }
        elif stage == "debate":
            others = [a for a in advisors if a.id != seat.id]
            to = others[(round or 0) % len(others)]
            raw = {
                "responds_to": to.id,
                "lean": state.lean(seat.id) or opts[0],
                "headline": (f"ردّ على {to.surname}." if ar else f"A reply to {to.surname}."),
                "text": _sentence(pack, seat, ar) + (f" لا أرى ما يراه {to.surname}." if ar else f" I do not read it the way {to.surname} does."),
            }
        elif stage == "vote":
            lean = state.lean(seat.id) or opts[0]
            raw = {"scores": {o: 7 if o == lean else 4 for o in opts}, "top": lean,
                   "reason": ("هذا ما تُظهره الأرقام التي نظرت إليها." if ar else "That is what the figures I looked at show.")}
        else:
            best = (state.result or {}).get("best") or opts[:1]
            label = next((o["label"] for o in state.brief["options"] if o["id"] == best[0]), best[0]) if state.brief else best[0]
            raw = {
                "headline": (f"الأكثر دعماً: {label}" if ar else f"Best supported: {label}"),
                "summary": ("هذه إجابة بديلة بلا نموذج ذكاء اصطناعي." if ar else "This is a stand-in session without an AI model."),
                "why": [{"seat": a.id, "point": _sentence(pack, a, ar)} for a in advisors[:3]],
                "watch_out": {"seat": advisors[-1].id, "point": _sentence(pack, advisors[-1], ar)},
                "disagreements": [],
                "gaps": [("لا تتضمن البيانات توقعات للأرباح." if ar else "The data has no earnings forecasts.")],
            }
        return check(raw), Usage(model="stand-in")

    return ask
