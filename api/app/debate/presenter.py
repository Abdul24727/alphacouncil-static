"""The advisors' room on two models: an ANALYST plans the whole room, a PRESENTER writes the advisors' turns.

The owner's direction of 2026-11-06 (docs/council-cost-options-2026-11-06.md, option 2): keep the room's
presentation exactly as it is - the portraits, the rounds, the Chair - and run it on two models at most,
one doing the real work and one presenting it. This is a drop-in for the engine's asker. `Debate` runs
its stages, checks every turn and streams it to the page exactly as before; only where each turn's words
come from changes:

  brief        one ANALYST call (the Chair's model) plans the whole room: the brief, every advisor's
               position in every round, the fault lines and the Chair's answer. The brief is served
               from that plan.
  openings,    one PRESENTER call (the advisors' model) per round writes every advisor's turn from the
  debate,      plan, in each advisor's manner and from their mandate. The plan's leans and challenges
  final        stand; every turn still passes the engine's own checks.
  faultlines,  served from the analyst's plan, in the analyst's words.
  verdict

Four calls a session where the room makes about twenty-one. A turn the engine's checks refuse falls back to
the room's own call for that one turn, so a bad slice costs one ordinary call rather than the session; the
fallbacks are counted in `stats`. A presenter round that fails outright falls back the same way, seat by
seat. A failed analyst ends the session, as a failed Chair does in the room.

Costs: every call's usage is recorded exactly once, never merged with another's (review 64: merging hid an
unknown cost behind a known one). A shared call's usage is returned with ONE turn - the brief for the
analyst, the first advisor served for a presenter round - and the other turns it served carry
`Usage(model="shared")`. When a turn's words come from a fallback, the turn carries the fallback's usage
and the call it superseded goes to `extra`, billed but carried by no displayed turn. The harness records
`extra`; the app does not yet, so its session total would miss those calls - to be fixed before the app
uses this engine (docs/council-cost-options-2026-11-06.md).

Off by default (Settings.debate_engine = "room"). Measured against the room before any decision
(docs/council-cost-options-2026-11-06.md, "The comparison that would decide it").
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from .engine import ANSWER_WORDS, CHAIR_WORDS, LANGUAGE, RULINGS, State
from .llm import Usage
from .roster import Seat

# Room for one call's JSON. The analyst writes the whole room's substance; a presenter round writes every
# advisor's turn at once, and Arabic takes more tokens per word.
MAX_TOKENS = {"analyst": 9_000, "openings": 8_000, "debate": 6_000, "final": 4_000}
TEMPERATURE = {"analyst": 0.3, "presenter": 0.7}
SHARED = "shared"
REPLY = "REPLY with one JSON object in this shape:\n"
PLAN_STAGE = {"openings": "opening", "debate": "challenge", "final": "final"}

# Model call: (role, stage, state, messages, model, max_tokens, temperature, check) -> (checked, usage).
Call = Callable[..., Awaitable[tuple[Any, Usage]]]


def _split(messages: list[dict[str, str]]) -> tuple[str, str, str]:
    """(system, the user message before its reply shape, the reply shape) of one engine turn."""
    system, user = messages[0]["content"], messages[1]["content"]
    head, _, rest = user.partition(REPLY)
    shape = rest.split("\n\nWrite every text value", 1)[0]
    return system, head.rstrip(), shape


def _lean_field(choice: bool, what: str) -> str:
    return f'"lean": "{what}", ' if choice else ""


class PresenterAsker:
    """The engine's asker for one session. `call` makes a model call (metered by the caller); `fallback`
    is the room's own asker, used for a single turn the plan cannot serve."""

    def __init__(self, call: Call, fallback: Call, advisors: list[Seat], chair: Seat, locale: str,
                 models: dict[str, str], pinned: dict[str, dict[str, Any]] | None = None) -> None:
        self.call, self.fallback = call, fallback
        self.advisors, self.chair, self.locale = advisors, chair, locale
        self.models = models
        # Openings already written, which stand as given (the benchmark's planted claim): the analyst is
        # shown them before it plans, so the rest of the room can answer them.
        self.pinned = pinned or {}
        self.plan: dict[str, Any] | None = None
        self.rounds: dict[tuple[str, int | None], asyncio.Future] = {}
        self.claimed: set[tuple[str, int | None]] = set()
        # Billed calls carried by no displayed turn: a plan or a round whose words a fallback replaced, and
        # a presenter round that failed outright. Each is {"stage", "role", "usage"}.
        self.extra: list[dict[str, Any]] = []
        self.stats = {"calls": 0, "fallbacks": 0, "round_failures": 0}

    # --- the engine's entry point ------------------------------------------------------------------

    async def __call__(self, **kw: Any) -> tuple[Any, Usage | None]:
        stage = kw["stage"]
        if stage == "brief":
            usage = await self._analyse(kw)
            return await self._serve(self.plan.get("brief"), kw, usage, "analyst")
        if stage in ("faultlines", "verdict"):
            return await self._serve(self.plan.get(stage), kw, Usage(model=SHARED), "analyst")
        return await self._advisor_turn(kw)

    # --- the analyst ---------------------------------------------------------------------------------

    async def _analyse(self, kw: dict[str, Any]) -> Usage:
        system, head, brief_shape = _split(kw["messages"])
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": self._analyst_prompt(head, brief_shape)}]
        self.stats["calls"] += 1
        plan, usage = await self.call(role="analyst", stage="plan", state=kw.get("state"), messages=messages,
                                      model=self.models["analyst"], max_tokens=MAX_TOKENS["analyst"],
                                      temperature=TEMPERATURE["analyst"], check=self.check_plan)
        self.plan = plan
        return usage

    def _analyst_prompt(self, head: str, brief_shape: str) -> str:
        ids = ", ".join(a.id for a in self.advisors)
        seats = "\n\n".join(
            f"- {a.name} (id {a.id}), lens: {a.info.lens_en}. Datasets they are answerable for: "
            f"{', '.join(a.info.owns)}.\n  Mandate: {a.sections.get('Mandate', '').strip()}\n"
            f"  Principles: {a.sections.get('Investing principles', '').strip()}"
            for a in self.advisors
        )
        pinned = ""
        if self.pinned:
            pinned = "\n\nTHESE OPENINGS ARE ALREADY WRITTEN AND STAND AS GIVEN. Plan the rest of the room in answer to them:\n" + \
                "\n".join(f"- {sid}: {json.dumps(raw, ensure_ascii=False)}" for sid, raw in self.pinned.items())
        low, high = CHAIR_WORDS
        rulings = " | ".join(RULINGS)
        shape = (
            "{\n"
            f'"brief": {brief_shape},\n'
            '"seats": {"<advisor id>": {\n'
            '   "opening": {"lean": "an option id, only in choice mode", "position": "what this advisor answers, '
            "in three to five sentences: what their own datasets show and what they conclude, with the pack's "
            'figures and their [Pn] tags"},\n'
            '   "challenge": {"responds_to": "the id of another advisor whose answer they challenge", "lean": "only '
            'in choice mode", "point": "the disagreement in two or three sentences, with figures and tags", '
            '"concedes": "the point they concede, one sentence, or an empty string"},\n'
            '   "final": {"lean": "only in choice mode", "position": "their final position, two sentences", '
            '"changed": "what changed and why, or an empty string", "would_change": "what data would change it, '
            'one sentence"}}},\n'
            '"faultlines": {"lines": [{"title": "at most 10 words", "between": ["advisor ids"], "text": "one or '
            'two sentences"}], "summary": "one sentence"},\n'
            '"verdict": {"headline": "the room\'s answer in at most 16 words, no figures", '
            f'"answer": "the room\'s complete answer, {low} to {high} words", '
            '"favours": "only in choice mode: which reading the room favours and how firmly", '
            '"rulings": [{"on": "what a fault line was about, one line", "between": ["advisor ids"], '
            f'"verdict": "one of {rulings}", "grounds": "the figure it turns on and why it decides it, or which '
            'figure is missing"}], "gaps": ["what the data does not show that would have settled it"]}\n'
            "}"
        )
        return "\n\n".join([
            head,
            ("YOU ARE ALSO THE ANALYST BEHIND THE WHOLE ROOM. Do all of its reasoning now, in one reply: the brief, "
             "every advisor's position in every round, the fault lines and the room's answer. A presenter will write "
             "each advisor's words from your plan, adding nothing, so everything the room concludes must be in it. "
             "Give each advisor a position that follows from their own datasets and principles; where the data "
             "supports different readings, let them disagree for real, and let the challenges and your rulings "
             "settle what the evidence settles."),
            f"THE ADVISORS (ids {ids}):\n{seats}",
            "THE FAULT LINES (the Chair's step):\n" + self.chair.sections.get("Stage: Fault lines", ""),
            "THE ROOM'S ANSWER (the Chair's step):\n" + self.chair.sections.get("Stage: The answer", ""),
            pinned.strip(),
            REPLY + shape,
            f"Write every text value in {LANGUAGE[self.locale]}.",
        ]).replace("\n\n\n\n", "\n\n")

    def check_plan(self, raw: Any) -> dict[str, Any]:
        """The plan's shape; each part's content is checked by the engine when it is served."""
        if not isinstance(raw, dict):
            raise TypeError("reply with one JSON object")
        for part in ("brief", "seats", "faultlines", "verdict"):
            if not isinstance(raw.get(part), dict):
                raise TypeError(f'"{part}" must be an object')
        ids = {a.id for a in self.advisors}
        seats = raw["seats"]
        missing = sorted(ids - set(seats))
        if missing:
            raise ValueError(f'"seats" must have every advisor; missing: {", ".join(missing)}')
        for sid in ids:
            s = seats[sid]
            if not isinstance(s, dict) or not all(isinstance(s.get(k), dict) for k in ("opening", "challenge", "final")):
                raise ValueError(f'"seats.{sid}" needs "opening", "challenge" and "final" objects')
            if sid not in self.pinned and not str(s["opening"].get("position") or "").strip():
                raise ValueError(f'"seats.{sid}.opening.position" is empty')
            to = s["challenge"].get("responds_to")
            if to not in ids or to == sid:
                raise ValueError(f'"seats.{sid}.challenge.responds_to" must be another advisor\'s id')
        return raw

    # --- the presenter -------------------------------------------------------------------------------

    async def _advisor_turn(self, kw: dict[str, Any]) -> tuple[Any, Usage | None]:
        seat, stage, rnd = kw["seat"], kw["stage"], kw.get("round")
        key = (stage, rnd)
        if key not in self.rounds:
            self.rounds[key] = asyncio.ensure_future(self._present(kw))
        try:
            turns, usage = await asyncio.shield(self.rounds[key])
        except Exception as exc:  # noqa: BLE001 - any failure of the round sends its seats back to the room
            # The round failed outright: every seat falls back to the room's own call, and the round's
            # failed attempts are billed once, as an extra call, by whichever seat gets here first.
            if self._claim(key):
                self.stats["round_failures"] += 1
                self._extra(stage, "presenter", getattr(exc, "usage", None))
            return await self._fall_back(kw)
        owed = usage if self._claim(key) else Usage(model=SHARED)
        value = turns.get(seat.id) if isinstance(turns, dict) else None
        # A malformed value for one advisor (review 64: a string where an object belongs) is that seat's
        # problem alone: an empty slice, refused by the engine's check, falls back for this turn only.
        raw = dict(value) if isinstance(value, dict) else {}
        plan = self._seat_plan(seat.id, stage)
        if "lean" in plan:
            raw["lean"] = plan["lean"]
        if stage == "debate" and plan.get("responds_to"):
            raw["responds_to"] = plan["responds_to"]
        return await self._serve(raw, kw, owed, "presenter")

    def _claim(self, key: tuple[str, int | None]) -> bool:
        if key in self.claimed:
            return False
        self.claimed.add(key)
        return True

    def _seat_plan(self, seat_id: str, stage: str) -> dict[str, Any]:
        return dict(((self.plan or {}).get("seats", {}).get(seat_id) or {}).get(PLAN_STAGE[stage]) or {})

    async def _present(self, kw: dict[str, Any]) -> tuple[dict[str, Any], Usage]:
        stage, state = kw["stage"], kw.get("state")
        choice = bool(state.options()) if state is not None else False
        system, head, _ = _split(kw["messages"])
        common = system.split("\n\nYOUR SEAT:", 1)[0]
        seats = "\n\n".join(
            f"YOUR SEAT: {a.name} (id {a.id}).\n\nTHEIR MANDATE (datasets {', '.join(a.info.owns)}):\n"
            f"{a.sections.get('Mandate', '').strip()}\n\n{a.brief.strip()}"
            for a in self.advisors if not (stage == "openings" and a.id in self.pinned)
        )
        writes = [a for a in self.advisors if not (stage == "openings" and a.id in self.pinned)]
        plans = {a.id: self._seat_plan(a.id, stage) for a in writes}
        low, high = ANSWER_WORDS
        if stage == "openings":
            one = "{" + _lean_field(choice, "as the plan gives it") + \
                f'"headline": "the answer in at most 15 words", "text": "the complete answer, {low} to {high} words"}}'
        elif stage == "debate":
            one = '{"responds_to": "as the plan gives it", ' + _lean_field(choice, "as the plan gives it") + \
                '"headline": "at most 15 words", "text": "120 to 200 words", ' \
                '"concedes": "the point conceded, one sentence, or an empty string"}'
        else:
            one = "{" + _lean_field(choice, "as the plan gives it") + \
                '"text": "the final position, two or three sentences", "changed": "what changed and why, or an empty ' \
                'string", "would_change": "what data would change it, one sentence"}'
        shape = "{" + ", ".join(f'"{a.id}": {one}' for a in writes) + "}"
        user = "\n\n".join([
            head,
            ("YOU WRITE EVERY ADVISOR'S TURN FOR THIS STEP, from the analyst's plan below. Each turn states that "
             "advisor's planned position in the advisor's own manner and from their mandate, as they would say it: "
             "keep the plan's conclusion, lean and figures, cite every figure with its [Pn] tag, and add no figure, "
             "claim or conclusion the plan does not contain."),
            "THE PLAN FOR THIS STEP:\n" + json.dumps(plans, ensure_ascii=False),
            REPLY + shape,
            f"Write every text value in {LANGUAGE[self.locale]}.",
        ])
        messages = [{"role": "system", "content": f"{common}\n\nTHE SEATS YOU WRITE FOR:\n\n{seats}"},
                    {"role": "user", "content": user}]
        ids = {a.id for a in writes}

        def check(raw: Any) -> dict[str, Any]:
            if not isinstance(raw, dict):
                raise TypeError("reply with one JSON object keyed by advisor id")
            missing = sorted(ids - set(raw))
            if missing:
                raise ValueError(f"write a turn for every advisor; missing: {', '.join(missing)}")
            return raw

        self.stats["calls"] += 1
        return await self.call(role="presenter", stage=stage, state=state, messages=messages,
                               model=self.models["presenter"], max_tokens=MAX_TOKENS[stage],
                               temperature=TEMPERATURE["presenter"], check=check)

    # --- serving a turn ------------------------------------------------------------------------------

    async def _serve(self, raw: Any, kw: dict[str, Any], usage: Usage | None, role: str) -> tuple[Any, Usage | None]:
        """The engine's own check on this turn. A turn it refuses - for whatever reason - falls back to the
        room's own call, and the call whose words were refused is kept as an extra, still billed."""
        try:
            if not isinstance(raw, dict):
                raise TypeError("the plan has no object for this turn")
            return kw["check"](dict(raw)), usage
        except Exception:  # noqa: BLE001 - a refused slice is a fallback, never the end of the session
            self._extra(kw["stage"], role, usage)
            return await self._fall_back(kw)

    async def _fall_back(self, kw: dict[str, Any]) -> tuple[Any, Usage | None]:
        """The room's own call for this one turn. Its usage is the turn's; a SeatError carries its own."""
        self.stats["fallbacks"] += 1
        return await self.fallback(**kw)

    def _extra(self, stage: str, role: str, usage: Usage | None) -> None:
        if usage is not None and usage.model != SHARED:
            self.extra.append({"stage": stage, "role": role, "usage": usage})


def make_asker(call: Call, fallback: Call, advisors: list[Seat], chair: Seat, locale: str,
               models: dict[str, str], pinned: dict[str, dict[str, Any]] | None = None) -> PresenterAsker:
    return PresenterAsker(call, fallback, advisors, chair, locale, models, pinned)


def make_standin_call(standin: Call, advisors: list[Seat], chair: Seat) -> Call:
    """The analyst and the presenter without a model, built from the room's own stand-in
    (`standin.make_asker`), so a dry run takes the presenter's real prompts through the same metering
    a paid run does, and the screen shows the presenter's shape without an AI model."""
    def same(raw: Any) -> Any:
        return raw

    async def turn(seat: Seat, stage: str, rnd: int | None, state: Any, model: str) -> dict[str, Any]:
        raw, _ = await standin(seat=seat, stage=stage, round=rnd, state=state, check=same, model=model)
        return raw

    async def call(*, role: str, stage: str, state: Any, model: str, check: Callable[[Any], Any], **_: Any):
        if role == "analyst":
            tmp = State()
            brief = await turn(chair, "brief", None, tmp, model)
            tmp.brief = {**brief, "options": [{"id": oid, **o} for oid, o in zip("ABCD", brief.get("options") or [])]}
            seats: dict[str, Any] = {}
            for a in advisors:
                op = await turn(a, "openings", 1, tmp, model)
                ch = await turn(a, "debate", 2, tmp, model)
                fi = await turn(a, "final", 3, tmp, model)
                seats[a.id] = {
                    "opening": {"lean": op.get("lean"), "position": op.get("text", "")},
                    "challenge": {"responds_to": ch.get("responds_to"), "lean": ch.get("lean"),
                                  "point": ch.get("text", ""), "concedes": ch.get("concedes", "")},
                    "final": {"lean": fi.get("lean"), "position": fi.get("text", ""),
                              "changed": fi.get("changed", ""), "would_change": fi.get("would_change", "")},
                }
            plan = {"brief": brief, "seats": seats,
                    "faultlines": await turn(chair, "faultlines", None, tmp, model),
                    "verdict": await turn(chair, "verdict", None, tmp, model)}
            return check(plan), Usage(model="stand-in")
        rnd = {"openings": 1, "debate": 2, "final": 3}[stage]
        out = {a.id: await turn(a, stage, rnd, state, model) for a in advisors}
        return check(out), Usage(model="stand-in")

    return call
