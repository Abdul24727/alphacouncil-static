"""The stages of a session: Brief, Answers, Fault lines, Challenges, Final word, The answer.

The Chair (one model) writes the brief, the fault lines and the room's answer; the advisors (another
model) write their own complete answers, their challenges and their final word, all of a round's
advisors at once. Every seat reads the same data pack (pack.py) and nothing else. Every text field
passes the checks in checks.py.

A session is `choice` or `open`, decided by the Chair in the brief: `choice` frames two to four
readings of the data and each advisor leans to one, `open` has no options and the advisors answer the
question itself. Where the room leans in a `choice` session is arithmetic done here, never by a model.

Events go to `emit` as they happen (the router streams them) and every finished turn goes to
`save` (the database), so the screen can follow a session live or replay it later.
"""

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ..settings import Settings
from ..copilot.context import TAG, numbers_in
from .checks import Checked, advice_in
from .llm import SeatError, Usage
from .pack import Pack
from .roster import Seat

STAGES = ("brief", "openings", "faultlines", "debate", "final", "verdict")
# Sessions held before the three-round format scored options in a "vote" stage where "final" now sits.
# Nothing writes "vote" any more; store.py keeps those sessions and the screen replays them as they were.
LEGACY_STAGES = ("brief", "openings", "faultlines", "debate", "vote", "verdict")
OPTION_IDS = ("A", "B", "C", "D")
MODES = ("choice", "open")
LANGUAGE = {"en": "English", "ar": "Arabic (Modern Standard Arabic)"}

# The heading of the Chair's section for each step (chair.md "Stage: …"), and the step's name in the prompt.
HEADING = {
    "brief": "Brief",
    "openings": "Answers",
    "faultlines": "Fault lines",
    "debate": "Challenges",
    "final": "Final word",
    "verdict": "The answer",
}

# Mirrors the Copilot's SYSTEM prompt (app/copilot/engine.py): same sources, citations, numbers and scope.
RULES = """You are one seat in AlphaCouncil's advisors' debate room, a simulated panel inside a research terminal for Gulf (GCC) listed equities. A member asked a question about one company; the room answers it in rounds and returns an assessment of the data, never advice.

Sources. Use only the data pack below. Do not use outside knowledge for any number, price, date, ratio or company fact: no oil prices, interest rates, forecasts, targets or news that are not in the pack. If what you need is not in the pack, say plainly that the data here does not show it; never estimate or fill a gap.

Citations. Every sentence that uses a figure from the pack ends with the tag of the dataset it came from, in square brackets, exactly as given, for example [P1].

Numbers. Quote values exactly as the pack gives them, with units and the listing currency; a value with more than two decimals may be written with two (10.4166 as 10.42), never fewer. Never convert, combine or calculate new figures. Write numbers with Western digits (0-9) and a full stop as the decimal mark, in Arabic too. Dates as YYYY-MM-DD.

Scope. Assess what the data shows. Never tell the member or anyone else to buy, sell or hold anything, give no price targets and no personal investment advice. This holds for every seat, in character or not.

Personas. The advisor seats are simulated, built from each person's publicly documented principles; they are not the people. Never claim to be the person, quote them or describe their private views, holdings or actions. Reason in their manner, in your own words.

Language. Write every text value in {language}. Keep company names as the data gives them. Refer to advisors by surname.

Output. Reply with one JSON object in exactly the shape asked for, and nothing else: no Markdown, no code fence, no comments."""

# Room for the JSON per step; Arabic takes more tokens per word. The answers and the Chair's answer
# are long on purpose (chair.md): their limits leave room for the whole text rather than cutting it.
MAX_TOKENS = {"brief": 1_200, "openings": 2_400, "faultlines": 900, "debate": 1_400, "final": 900, "verdict": 2_200}
TEMPERATURE = {"chair": 0.3, "advisor": 0.7}

# The length chair.md asks for, in words: an answer outside it is kept whole and counted in the turn's
# flags (`words`), so check-advisors.mjs can report it. Nothing is ever cut to fit.
ANSWER_WORDS = (250, 400)
CHAIR_WORDS = (200, 350)
WORD = re.compile(r"[^\s]+")


def words_in(text: str) -> int:
    return len(WORD.findall(TAG.sub(" ", text)))


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
        """Rounds on the screen: the answers, each round of challenges, the final word."""
        return self.debate_rounds + 2

    def seat(self, seat_id: str) -> Seat:
        return self.chair if seat_id == "chair" else next(a for a in self.advisors if a.id == seat_id)


@dataclass
class State:
    brief: dict[str, Any] | None = None
    openings: dict[str, dict[str, Any]] = field(default_factory=dict)
    faultlines: dict[str, Any] | None = None
    debate: list[dict[str, dict[str, Any]]] = field(default_factory=list)
    finals: dict[str, dict[str, Any]] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    verdict: dict[str, Any] | None = None

    @property
    def mode(self) -> str:
        return (self.brief or {}).get("mode") or "open"

    def options(self) -> list[str]:
        """The option ids in a `choice` session; empty in an `open` one."""
        return [o["id"] for o in (self.brief or {}).get("options", [])]

    def lean(self, seat_id: str) -> str | None:
        """The option a seat leans to now: its last turn's lean, latest round first."""
        f = self.finals.get(seat_id)
        if f and not f.get("absent") and f.get("lean"):
            return f["lean"]
        for rnd in reversed(self.debate):
            if seat_id in rnd and not rnd[seat_id].get("absent") and rnd[seat_id].get("lean"):
                return rnd[seat_id]["lean"]
        o = self.openings.get(seat_id)
        return o["lean"] if o and not o.get("absent") and o.get("lean") else None


# A model call for one seat: (seat, stage, round, messages, model, max_tokens, temperature, check) -> (data, usage).
Asker = Callable[..., Awaitable[tuple[dict[str, Any], Usage]]]
Emit = Callable[[dict[str, Any]], None]
Save = Callable[[dict[str, Any], Usage | None], Awaitable[None]]


def count_leans(options: list[str], finals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Where the room ends up in a `choice` session: how many advisors lean to each option after the
    final word, and which option(s) the most of them lean to. Arithmetic done here, never by a model."""
    present = {s: f["lean"] for s, f in finals.items() if not f.get("absent") and f.get("lean")}
    tally = {o: sum(1 for lean in present.values() if lean == o) for o in options}
    top = max(tally.values(), default=0)
    best = [o for o, n in tally.items() if n == top and n > 0]
    return {"mode": "choice", "tally": tally, "best": best, "voters": len(present), "leans": present}


def count_answers(finals: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """An `open` session has nothing to count: only how many advisors gave a final word."""
    return {"mode": "open", "voters": sum(1 for f in finals.values() if not f.get("absent"))}


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
        roster = (
            "The advisors: "
            + "; ".join(f"{a.name} / {a.info.name_ar}, called {a.surname} / {a.info.short_ar} (id {a.id})" for a in self.ctx.advisors)
            + ". A neutral Chair (رئيس الجلسة) runs the rounds. In Arabic, write the advisors' names in Arabic as given here."
        )
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
            if s.brief["options"]:
                out.append("OPTIONS:\n" + "\n".join(f"{o['id']}. {o['label']}: {o['detail']}" for o in s.brief["options"]))
            else:
                out.append("This session has no options: the room answers the question itself.")
        if s.openings:
            out.append("THE ADVISORS' ANSWERS:\n" + "\n\n".join(self._line(i, t) for i, t in s.openings.items()))
        if s.faultlines:
            lines = [
                f"- {f['title']} ({' vs '.join(self.ctx.seat(x).surname for x in f['between'])}): {f['text']}"
                for f in s.faultlines["lines"]
            ]
            out.append("FAULT LINES:\n" + "\n".join(lines) + (f"\n{s.faultlines['summary']}" if s.faultlines["summary"] else ""))
        for n, rnd in enumerate(s.debate, start=1):
            out.append(f"CHALLENGES, ROUND {n}:\n" + "\n\n".join(self._line(i, t) for i, t in rnd.items()))
        if s.finals:
            out.append("THE FINAL WORD:\n" + "\n\n".join(self._final_line(i, t) for i, t in s.finals.items()))
        if s.result and s.result.get("mode") == "choice":
            tally = ", ".join(f"{o} {n}" for o, n in s.result["tally"].items())
            out.append(
                f"THE COUNT OF THE FINAL LEANS (computed by the engine; do not change it): {tally}; most favoured "
                f"{' and '.join(s.result['best']) or 'none'}, of {s.result['voters']} advisors who gave a final lean."
            )
        return "\n\n".join(out)

    def _line(self, seat_id: str, turn: dict[str, Any]) -> str:
        name = self.ctx.seat(seat_id).surname
        if turn.get("absent"):
            return f"- {name}: (no answer this round)"
        to = f", challenging {self.ctx.seat(turn['responds_to']).surname}" if turn.get("responds_to") else ""
        lean = f" [leans {turn['lean']}]" if turn.get("lean") else ""
        concedes = f" (concedes: {turn['concedes']})" if turn.get("concedes") else ""
        return f"- {name}{to}{lean}: {turn['headline']} {turn['text']}{concedes}"

    def _final_line(self, seat_id: str, turn: dict[str, Any]) -> str:
        name = self.ctx.seat(seat_id).surname
        if turn.get("absent"):
            return f"- {name}: (no final word)"
        lean = f" [leans {turn['lean']}]" if turn.get("lean") else ""
        changed = f" What changed: {turn['changed']}" if turn.get("changed") else " Nothing changed."
        would = f" Would change it: {turn['would_change']}" if turn.get("would_change") else ""
        return f"- {name}{lean}: {turn['text']}{changed}{would}"

    def messages(self, seat: Seat, stage: str, shape: str, extra: str = "") -> list[dict[str, str]]:
        heading = HEADING[stage]
        parts = [f"THE MEMBER'S QUESTION: {self.ctx.question}"]
        if t := self.transcript():
            parts.append(t)
        parts.append(f"THIS STEP ({heading}):\n{self.ctx.chair.sections[f'Stage: {heading}']}")
        if stage != "brief":
            parts.append(
                f"THIS SESSION'S MODE: {self.state.mode}."
                + (" There are no options: answer the question itself and give no lean." if self.state.mode == "open" else "")
            )
        if extra:
            parts.append(extra)
        parts.append(f"REPLY with one JSON object in this shape:\n{shape}")
        parts.append(f"Write every text value in {LANGUAGE[self.ctx.locale]}.")
        return [{"role": "system", "content": self.system(seat)}, {"role": "user", "content": "\n\n".join(parts)}]

    # --- checks on each kind of answer -------------------------------------------------------------

    def _lean(self, value: Any) -> str | None:
        """The option a seat leans to; None in an `open` session, which has no options."""
        options = self.state.options()
        if not options:
            return None
        lean = str(value or "").strip().upper()[:1]
        if lean not in options:
            raise ValueError(f"lean must be one of {', '.join(options)}")
        return lean

    def check_brief(self, raw: dict[str, Any]) -> dict[str, Any]:
        c = Checked(self.numbers, self.seen)
        mode = str(raw.get("mode") or "").strip().lower()
        if mode not in MODES:
            raise ValueError('mode must be "choice" (the question asks the room to choose a reading) or "open"')
        out = []
        if mode == "choice":
            options = [o for o in raw.get("options") or [] if isinstance(o, dict) and str(o.get("label") or "").strip()]
            if not 2 <= len(options) <= 4:
                raise ValueError("a choice session needs two to four options")
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
            "mode": mode,
            "question": question,
            "options": out,
            "focus": [c.text(x, 160) for x in (raw.get("focus") or [])[:4] if isinstance(x, str) and x.strip()],
            "weighing": {a.id: c.text(weighing.get(a.id), 160) for a in self.ctx.advisors},
            "note": c.text(raw.get("note"), 400),
        }
        return {"data": data, "flags": c.flags()}

    def check_opening(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Round 1: an advisor's own complete answer, written without seeing the others'."""
        c = Checked(self.numbers, self.seen)
        # 4,000 characters holds the longest answer chair.md asks for: an over-long one is counted, never cut.
        text = c.text(raw.get("text"), 4_000)
        if not text:
            raise ValueError("the text is empty")
        data = {"lean": self._lean(raw.get("lean")), "headline": c.text(raw.get("headline"), 200), "text": text}
        return {"data": data, "flags": {**c.flags(), "words": words_in(text)}}

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
        """Round 2: the one answer this advisor disagrees with most, challenged with the data."""
        c = Checked(self.numbers, self.seen)
        others = [a.id for a in self.ctx.advisors if a.id != seat_id]
        to = raw.get("responds_to") if raw.get("responds_to") in others else None
        lean = self._lean(raw.get("lean"))
        data = {
            "responds_to": to,
            "lean": lean,
            "changed": lean is not None and self.state.lean(seat_id) not in (None, lean),
            "headline": c.text(raw.get("headline"), 200),
            "text": c.text(raw.get("text"), 2_000),
            "concedes": c.text(raw.get("concedes"), 400),
        }
        if not data["text"]:
            raise ValueError("the text is empty")
        return {"data": data, "flags": c.flags()}

    def check_final(self, seat_id: str, raw: dict[str, Any]) -> dict[str, Any]:
        """Round 3: the final position, what changed in it and what data would change it. No scores."""
        c = Checked(self.numbers, self.seen)
        lean = self._lean(raw.get("lean"))
        text = c.text(raw.get("text"), 900)
        if not text:
            raise ValueError("the text is empty")
        data = {
            "lean": lean,
            "lean_changed": lean is not None and self.state.lean(seat_id) not in (None, lean),
            "text": text,
            # Empty when the advisor's position did not change: the screen says so in its own words.
            "changed": c.text(raw.get("changed"), 500),
            "would_change": c.text(raw.get("would_change"), 500),
        }
        return {"data": data, "flags": c.flags()}

    def check_verdict(self, raw: dict[str, Any]) -> dict[str, Any]:
        # The count of the final leans is the engine's own arithmetic: the Chair may quote it ("3 of 4").
        c = Checked(self.numbers, self.seen | numbers_in(self.state.result or {}))
        headline = TAG.sub("", c.text(raw.get("headline"), 200)).strip()
        if not headline or advice_in(headline, short=True):
            raise ValueError("the headline must state the room's answer from the data, never buy, sell or hold")
        answer = c.text(raw.get("answer"), 4_000)
        if not answer:
            raise ValueError("write the room's complete answer in the `answer` field")
        data = {
            "headline": headline,
            "answer": answer,
            # Only a choice session has a reading to favour; an open one answers the question outright.
            "favours": c.text(raw.get("favours"), 400) if self.state.options() else "",
            "disagreements": [c.text(x, 400) for x in (raw.get("disagreements") or raw.get("split") or [])[:3] if isinstance(x, str) and x.strip()],
            "gaps": [c.text(x, 400) for x in (raw.get("gaps") or [])[:3] if isinstance(x, str) and x.strip()],
        }
        return {"data": data, "flags": {**c.flags(), "words": words_in(answer)}}

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
            '{"mode": "choice" if the member\'s question asks the room to choose between readings, otherwise "open", '
            '"question": "the question restated in one sentence", '
            '"options": [{"id": "A", "label": "a reading of the data, at most 12 words", "detail": "one sentence"}] '
            "(two to four of them in choice mode, an empty list in open mode), "
            '"focus": ["two to four short items the room must weigh"], "weighing": {' + seats_json + "}, "
            '"note": "one sentence, or an empty string"}',
            self.check_brief,
        )
        # A choice session carries a lean through every advisor round; an open one has nothing to lean to.
        choice = bool(s.options())
        opts = ", ".join(s.options())
        lean = ('"lean": "the option you lean to, one of ' + opts + '", ') if choice else ""
        low, high = ANSWER_WORDS

        self.stage("openings", 1)
        s.openings = await self.advisors_round(
            "openings",
            1,
            lambda a: "{"
            + lean
            + '"headline": "your answer in at most 15 words", '
            + f'"text": "your own complete answer to the question, {low} to {high} words"}}',
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
                '{"responds_to": "the id of the advisor whose answer you challenge, one of ' + others + '", '
                + lean
                + '"headline": "at most 15 words", "text": "120 to 200 words", '
                '"concedes": "the point of theirs you concede, one sentence, or an empty string"}'
            )

        for n in range(ctx.debate_rounds):
            self.stage("debate", 2 + n)
            s.debate.append(
                await self.advisors_round(
                    "debate",
                    2 + n,
                    reply_shape,
                    lambda a: lambda raw, a=a: self.check_debate(a.id, raw),
                    "" if n == 0 else "This is the second round of challenges: answer the challenges addressed to you in the first.",
                )
            )

        self.stage("final", ctx.rounds)
        s.finals = await self.advisors_round(
            "final",
            ctx.rounds,
            lambda a: "{"
            + lean
            + '"text": "your final position, two or three sentences", '
            '"changed": "what changed in your position during the room and why, or an empty string if nothing changed", '
            '"would_change": "what data would change it, one sentence"}',
            lambda a: lambda raw, a=a: self.check_final(a.id, raw),
        )
        s.result = count_leans(s.options(), s.finals) if choice else count_answers(s.finals)
        self.emit({"type": "result", "result": s.result})

        self.stage("verdict")
        chair_low, chair_high = CHAIR_WORDS
        s.verdict = await self.chair_turn(
            "verdict",
            '{"headline": "the room\'s answer in at most 16 words, no figures", '
            f'"answer": "the room\'s complete answer, {chair_low} to {chair_high} words", '
            + ('"favours": "one sentence on which reading the room favours and how firmly", ' if choice else "")
            + '"disagreements": ["where the room still splits, one sentence each"], '
            '"gaps": ["what the data does not show that would have settled it, one sentence each"]}',
            self.check_verdict,
        )
        return s
