"""The stages of a session: Brief, Openings, Fault lines, Debate, Vote, Verdict.

The Chair (one model) frames the question and writes the brief, the fault lines and the verdict;
the advisors (another model) write openings, replies and votes, all of a round's advisors at
once. Every seat reads the same data pack (pack.py) and nothing else. Every text field passes the
checks in checks.py. The vote count is arithmetic done here, never by a model.

Events go to `emit` as they happen (the router streams them) and every finished turn goes to
`save` (the database), so the screen can follow a session live or replay it later.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ..settings import Settings
from .checks import Checked, advice_in
from .llm import SeatError, Usage
from .pack import Pack
from .roster import Seat

STAGES = ("brief", "openings", "faultlines", "debate", "vote", "verdict")
OPTION_IDS = ("A", "B", "C", "D")
LANGUAGE = {"en": "English", "ar": "Arabic (Modern Standard Arabic)"}

# Mirrors the Copilot's SYSTEM prompt (app/copilot/engine.py): same sources, citations, numbers and scope.
RULES = """You are one seat in AlphaCouncil's advisors' debate room, a simulated panel inside a research terminal for Gulf (GCC) listed equities. A member asked a question about one company; the room debates it in stages and returns a scored assessment of the data, never advice.

Sources. Use only the data pack below. Do not use outside knowledge for any number, price, date, ratio or company fact: no oil prices, interest rates, forecasts, targets or news that are not in the pack. If what you need is not in the pack, say plainly that the data here does not show it; never estimate or fill a gap.

Citations. Every sentence that uses a figure from the pack ends with the tag of the dataset it came from, in square brackets, exactly as given, for example [P1].

Numbers. Quote values exactly as the pack gives them, with units and the listing currency; a value with more than two decimals may be written with two (10.4166 as 10.42), never fewer. Never convert, combine or calculate new figures. Write numbers with Western digits (0-9) and a full stop as the decimal mark, in Arabic too. Dates as YYYY-MM-DD.

Scope. Assess what the data shows. Never tell the member or anyone else to buy, sell or hold anything, give no price targets and no personal investment advice. This holds for every seat, in character or not.

Personas. The advisor seats are simulated, built from each person's publicly documented principles; they are not the people. Never claim to be the person, quote them or describe their private views, holdings or actions. Reason in their manner, in your own words.

Language. Write every text value in {language}. Keep company names as the data gives them. Refer to advisors by surname.

Output. Reply with one JSON object in exactly the shape asked for, and nothing else: no Markdown, no code fence, no comments."""

# Room for the JSON per step; Arabic takes more tokens per word.
MAX_TOKENS = {"brief": 1_200, "openings": 1_000, "faultlines": 900, "debate": 900, "vote": 600, "verdict": 1_600}
TEMPERATURE = {"chair": 0.3, "advisor": 0.7}


@dataclass
class Context:
    settings: Settings
    pack: Pack
    question: str
    locale: str
    advisors: list[Seat]
    chair: Seat
    debate_rounds: int

    @property
    def rounds(self) -> int:
        """Rounds on the screen: the openings, each debate round, the vote."""
        return self.debate_rounds + 2

    def seat(self, seat_id: str) -> Seat:
        return self.chair if seat_id == "chair" else next(a for a in self.advisors if a.id == seat_id)


@dataclass
class State:
    brief: dict[str, Any] | None = None
    openings: dict[str, dict[str, Any]] = field(default_factory=dict)
    faultlines: dict[str, Any] | None = None
    debate: list[dict[str, dict[str, Any]]] = field(default_factory=list)
    votes: dict[str, dict[str, Any]] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    verdict: dict[str, Any] | None = None

    def options(self) -> list[str]:
        return [o["id"] for o in (self.brief or {}).get("options", [])]

    def lean(self, seat_id: str) -> str | None:
        for rnd in reversed(self.debate):
            if seat_id in rnd and not rnd[seat_id].get("absent"):
                return rnd[seat_id]["lean"]
        o = self.openings.get(seat_id)
        return o["lean"] if o and not o.get("absent") else None


# A model call for one seat: (seat, stage, round, messages, model, max_tokens, temperature, check) -> (data, usage).
Asker = Callable[..., Awaitable[tuple[dict[str, Any], Usage]]]
Emit = Callable[[dict[str, Any]], None]
Save = Callable[[dict[str, Any], Usage | None], Awaitable[None]]


def count_votes(options: list[str], votes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Each option's plain average of the advisors' scores, the best-supported option(s) and how
    many advisors put a best-supported option on top (chair.md, Scoring)."""
    present = {s: v for s, v in votes.items() if not v.get("absent")}
    average: dict[str, float | None] = {}
    for o in options:
        xs = [v["scores"][o] for v in present.values() if o in v["scores"]]
        average[o] = sum(xs) / len(xs) if xs else None
    scored = [a for a in average.values() if a is not None]
    top = max(scored) if scored else None
    best = [o for o, a in average.items() if a is not None and a == top]
    return {
        "average": average,
        "best": best,
        "agreement": sum(1 for v in present.values() if v["top"] in best),
        "voters": len(present),
        "scores": {s: v["scores"] for s, v in present.items()},
    }


class Debate:
    def __init__(self, ctx: Context, ask: Asker, emit: Emit, save: Save) -> None:
        self.ctx, self.ask, self.emit, self.save = ctx, ask, emit, save
        self.state = State()
        self.numbers = ctx.pack.numbers()
        self.seen = ctx.pack.seen()
        self.writing: set[str] = set()

    # --- prompts ---------------------------------------------------------------------------------

    def system(self, seat: Seat) -> str:
        # Everything up to the data pack is the same for every seat, so the host can reuse it.
        roster = "The advisors: " + "; ".join(f"{a.name} (id {a.id})" for a in self.ctx.advisors) + ". A neutral Chair runs the rounds."
        head = "\n\n".join([RULES.replace("{language}", LANGUAGE[self.ctx.locale]), roster, self.ctx.pack.prompt()])
        if seat.info.role == "chair":
            you = "YOUR SEAT: the Chair.\n\n" + seat.sections["Who the Chair is"] + "\n\nVoice: " + seat.sections["Voice"]
        else:
            you = f"YOUR SEAT: {seat.name} (id {seat.id}).\n\n{seat.body}"
        return f"{head}\n\n{you}"

    def transcript(self) -> str:
        s, out = self.state, []
        if s.brief:
            out.append("THE CHAIR'S BRIEF: " + s.brief["question"])
            out.append("OPTIONS:\n" + "\n".join(f"{o['id']}. {o['label']}: {o['detail']}" for o in s.brief["options"]))
        if s.openings:
            out.append("OPENINGS:\n" + "\n".join(self._line(i, t) for i, t in s.openings.items()))
        if s.faultlines:
            lines = [
                f"- {f['title']} ({' vs '.join(self.ctx.seat(x).surname for x in f['between'])}): {f['text']}"
                for f in s.faultlines["lines"]
            ]
            out.append("FAULT LINES:\n" + "\n".join(lines) + (f"\n{s.faultlines['summary']}" if s.faultlines["summary"] else ""))
        for n, rnd in enumerate(s.debate, start=1):
            out.append(f"DEBATE ROUND {n}:\n" + "\n".join(self._line(i, t) for i, t in rnd.items()))
        if s.votes:
            out.append(
                "VOTES:\n"
                + "\n".join(
                    f"- {self.ctx.seat(i).surname}: "
                    + ", ".join(f"{o} {v['scores'][o]}" for o in s.options() if o in v["scores"])
                    + f"; top {v['top']}. {v['reason']}"
                    for i, v in s.votes.items()
                    if not v.get("absent")
                )
            )
        if s.result:
            avg = ", ".join(f"{o} {a:g}" for o, a in s.result["average"].items() if a is not None)
            out.append(
                f"THE COUNT (computed by the engine; do not change it): average scores {avg}; best supported "
                f"{' and '.join(s.result['best']) or 'none'}; {s.result['agreement']} of {s.result['voters']} advisors put it on top."
            )
        return "\n\n".join(out)

    def _line(self, seat_id: str, turn: dict[str, Any]) -> str:
        name = self.ctx.seat(seat_id).surname
        if turn.get("absent"):
            return f"- {name}: (no answer this round)"
        to = f", answering {self.ctx.seat(turn['responds_to']).surname}" if turn.get("responds_to") else ""
        return f"- {name}{to} [leans {turn['lean']}]: {turn['headline']} {turn['text']}"

    def messages(self, seat: Seat, stage: str, shape: str, extra: str = "") -> list[dict[str, str]]:
        heading = {"brief": "Brief", "openings": "Openings", "faultlines": "Fault lines", "debate": "Debate", "vote": "Vote", "verdict": "Verdict"}[stage]
        parts = [f"THE MEMBER'S QUESTION: {self.ctx.question}"]
        if t := self.transcript():
            parts.append(t)
        parts.append(f"THIS STEP ({heading}):\n{self.ctx.chair.sections[f'Stage: {heading}']}")
        if stage in ("vote", "verdict"):
            parts.append("SCORING:\n" + self.ctx.chair.sections["Scoring"])
        if extra:
            parts.append(extra)
        parts.append(f"REPLY with one JSON object in this shape:\n{shape}")
        parts.append(f"Write every text value in {LANGUAGE[self.ctx.locale]}.")
        return [{"role": "system", "content": self.system(seat)}, {"role": "user", "content": "\n\n".join(parts)}]

    # --- checks on each kind of answer -------------------------------------------------------------

    def _lean(self, value: Any) -> str:
        lean = str(value or "").strip().upper()[:1]
        if lean not in self.state.options():
            raise ValueError(f"lean must be one of {', '.join(self.state.options())}")
        return lean

    def check_brief(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        options = [o for o in raw.get("options") or [] if isinstance(o, dict) and str(o.get("label") or "").strip()]
        if not 2 <= len(options) <= 4:
            raise ValueError("give two to four options")
        out = []
        for oid, o in zip(OPTION_IDS, options):
            label = c.text(o.get("label"), 140)
            if not label or advice_in(label, short=True):
                raise ValueError(f"option {oid} must be a reading of the data, not an action such as buy, sell or hold")
            out.append({"id": oid, "label": label, "detail": c.text(o.get("detail"), 400)})
        question = c.text(raw.get("question"), 400)
        if not question:
            raise ValueError("restate the question")
        weighing = raw.get("weighing") if isinstance(raw.get("weighing"), dict) else {}
        data = {
            "question": question,
            "options": out,
            "focus": [c.text(x, 160) for x in (raw.get("focus") or [])[:4] if isinstance(x, str) and x.strip()],
            "weighing": {a.id: c.text(weighing.get(a.id), 160) for a in self.ctx.advisors},
            "note": c.text(raw.get("note"), 400),
        }
        return {"data": data, "flags": c.flags()}

    def check_opening(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        data = {"lean": self._lean(raw.get("lean")), "headline": c.text(raw.get("headline"), 200), "text": c.text(raw.get("text"))}
        if not data["text"]:
            raise ValueError("the text is empty")
        return {"data": data, "flags": c.flags()}

    def check_faultlines(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        ids = {a.id for a in self.ctx.advisors}
        lines = []
        for f in (raw.get("lines") or raw.get("fault_lines") or [])[:3]:
            if not isinstance(f, dict) or not str(f.get("title") or "").strip():
                continue
            between = [x for x in (f.get("between") or []) if x in ids]
            lines.append({"title": c.text(f.get("title"), 140), "between": list(dict.fromkeys(between)), "text": c.text(f.get("text"), 600)})
        if not lines:
            raise ValueError("name at least one fault line")
        return {"data": {"lines": lines, "summary": c.text(raw.get("summary"), 400)}, "flags": c.flags()}

    def check_debate(self, seat_id: str, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        others = [a.id for a in self.ctx.advisors if a.id != seat_id]
        to = raw.get("responds_to") if raw.get("responds_to") in others else None
        lean = self._lean(raw.get("lean"))
        data = {
            "responds_to": to,
            "lean": lean,
            "changed": self.state.lean(seat_id) not in (None, lean),
            "headline": c.text(raw.get("headline"), 200),
            "text": c.text(raw.get("text")),
        }
        if not data["text"]:
            raise ValueError("the text is empty")
        return {"data": data, "flags": c.flags()}

    def check_vote(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        given = raw.get("scores") if isinstance(raw.get("scores"), dict) else {}
        scores: dict[str, int] = {}
        for o in self.state.options():
            v = given.get(o)
            if isinstance(v, str) and v.strip().replace(".", "", 1).isdigit():
                v = float(v)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= 10:
                raise ValueError(f"score every option from 0 to 10 (option {o})")
            scores[o] = int(round(v))
        high = max(scores.values())
        top = str(raw.get("top") or "").strip().upper()[:1]
        if scores.get(top) != high:  # the named top must be a highest score
            top = next(o for o, v in scores.items() if v == high)
        return {"data": {"scores": scores, "top": top, "reason": c.text(raw.get("reason"), 600)}, "flags": c.flags()}

    def check_verdict(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        ids = {a.id for a in self.ctx.advisors}
        headline = c.text(raw.get("headline"), 200)
        if not headline or advice_in(headline, short=True):
            raise ValueError("the headline must state the room's assessment of the data, never buy, sell or hold")

        def credited(x: Any) -> dict[str, Any] | None:
            if not isinstance(x, dict) or not str(x.get("point") or "").strip():
                return None
            return {"seat": x.get("seat") if x.get("seat") in ids else None, "point": c.text(x.get("point"), 500)}

        data = {
            "headline": headline,
            "summary": c.text(raw.get("summary"), 900),
            "why": [w for w in (credited(x) for x in (raw.get("why") or [])[:5]) if w and w["point"]],
            "watch_out": credited(raw.get("watch_out")),
            "disagreements": [c.text(x, 400) for x in (raw.get("disagreements") or [])[:3] if isinstance(x, str) and x.strip()],
            "gaps": [c.text(x, 400) for x in (raw.get("gaps") or [])[:3] if isinstance(x, str) and x.strip()],
        }
        return {"data": data, "flags": c.flags()}

    # --- running -----------------------------------------------------------------------------------

    def set_writing(self, seats: set[str]) -> None:
        self.writing = seats
        self.emit({"type": "writing", "seats": sorted(seats, key=self._order)})

    def _order(self, seat_id: str) -> int:
        ids = [a.id for a in self.ctx.advisors]
        return ids.index(seat_id) if seat_id in ids else -1

    async def turn(self, seat: Seat, stage: str, rnd: int | None, shape: str, check: Callable, extra: str = "") -> dict[str, Any]:
        """One seat's answer for one step, checked, saved and sent to the screen."""
        role = seat.info.role
        model = self.ctx.settings.debate_chair_model if role == "chair" else self.ctx.settings.debate_advisor_model
        try:
            checked, usage = await self.ask(
                seat=seat,
                stage=stage,
                round=rnd,
                state=self.state,
                messages=self.messages(seat, stage, shape, extra),
                model=model,
                max_tokens=MAX_TOKENS[stage],
                temperature=TEMPERATURE[role],
                check=check,
            )
        except SeatError as exc:
            if role == "chair":
                raise
            turn = {"stage": stage, "round": rnd, "seat": seat.id, "data": {"absent": True, "error": exc.code}, "flags": None}
            await self.save(turn, None)
            self.emit({"type": "turn", "turn": turn})
            return turn["data"]
        turn = {"stage": stage, "round": rnd, "seat": seat.id, **checked, "seconds": round(usage.seconds, 2)}
        await self.save(turn, usage)
        self.emit({"type": "turn", "turn": turn})
        return checked["data"]

    async def chair_turn(self, stage: str, shape: str, check: Callable, extra: str = "") -> dict[str, Any]:
        self.set_writing({"chair"})
        try:
            return await self.turn(self.ctx.chair, stage, None, shape, check, extra)
        finally:
            self.set_writing(set())

    async def advisors_round(
        self, stage: str, rnd: int, shape_of: Callable[[Seat], str], check_of: Callable[[Seat], Callable], extra: str = ""
    ) -> dict[str, dict[str, Any]]:
        """Every advisor at once; each answer goes out as soon as it lands."""
        self.set_writing({a.id for a in self.ctx.advisors})

        async def one(a: Seat) -> tuple[str, dict[str, Any]]:
            data = await self.turn(a, stage, rnd, shape_of(a), check_of(a), extra)
            self.set_writing(self.writing - {a.id})
            return a.id, data

        results = dict(await asyncio.gather(*(one(a) for a in self.ctx.advisors)))
        if sum(1 for d in results.values() if not d.get("absent")) < 2:
            raise SeatError("too_few")
        # Seat order, whatever order they finished in.
        return {a.id: results[a.id] for a in self.ctx.advisors}

    def stage(self, stage: str, rnd: int | None = None) -> None:
        self.emit({"type": "stage", "stage": stage, "round": rnd, "rounds": self.ctx.rounds})

    async def run(self) -> State:
        s, ctx = self.state, self.ctx
        seats_json = ", ".join(f'"{a.id}": "what {a.surname} weighs first, at most 14 words"' for a in ctx.advisors)

        self.stage("brief")
        s.brief = await self.chair_turn(
            "brief",
            '{"question": "the question restated in one sentence", "options": [{"id": "A", "label": "a reading of the data, at most 12 words", '
            '"detail": "one sentence"}], "focus": ["two to four short items the room must weigh"], "weighing": {' + seats_json + "}, "
            '"note": "one sentence, or an empty string"}',
            self.check_brief,
        )
        opts = ", ".join(s.options())

        self.stage("openings", 1)
        s.openings = await self.advisors_round(
            "openings",
            1,
            lambda a: '{"lean": "one of ' + opts + '", "headline": "your position in at most 15 words", "text": "80 to 140 words"}',
            lambda a: self.check_opening,
        )

        self.stage("faultlines")
        s.faultlines = await self.chair_turn(
            "faultlines",
            '{"lines": [{"title": "at most 10 words", "between": ["advisor ids"], "text": "one or two sentences"}], "summary": "one sentence"}',
            self.check_faultlines,
        )

        def reply_shape(a: Seat) -> str:
            others = ", ".join(x.id for x in ctx.advisors if x.id != a.id)
            return (
                '{"responds_to": "the id of the advisor you answer, one of ' + others + '", "lean": "one of ' + opts + '", '
                '"headline": "at most 15 words", "text": "60 to 120 words"}'
            )

        for n in range(ctx.debate_rounds):
            self.stage("debate", 2 + n)
            s.debate.append(
                await self.advisors_round(
                    "debate",
                    2 + n,
                    reply_shape,
                    lambda a: lambda raw, a=a: self.check_debate(a.id, raw),
                    "" if n == 0 else "This is the second debate round: answer the replies addressed to you in the first.",
                )
            )

        self.stage("vote", ctx.rounds)
        score_shape = ", ".join(f'"{o}": 0' for o in s.options())
        s.votes = await self.advisors_round(
            "vote",
            ctx.rounds,
            lambda a: '{"scores": {' + score_shape + '}, "top": "the option you score highest", "reason": "one or two sentences"}',
            lambda a: self.check_vote,
        )
        s.result = count_votes(s.options(), s.votes)
        self.emit({"type": "result", "result": s.result})

        self.stage("verdict")
        s.verdict = await self.chair_turn(
            "verdict",
            '{"headline": "the room\'s assessment of the data in one line", "summary": "two or three sentences", '
            '"why": [{"seat": "advisor id", "point": "one sentence"}], "watch_out": {"seat": "advisor id", "point": "one sentence"}, '
            '"disagreements": ["one sentence each"], "gaps": ["what the data does not show, one sentence each"]}',
            self.check_verdict,
        )
        return s
