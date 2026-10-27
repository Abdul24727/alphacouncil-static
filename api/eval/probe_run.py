"""The discriminating run: nine probes, four arms, scored by probes.py and score.py.

    uv run python -m eval probe --dry                  # the whole plan, no model, no cost
    uv run python -m eval probe --clean --repeats 1    # the controls the validity gate reads
    uv run python -m eval probe --repeats 2            # the planted runs
    uv run python -m eval probe-report                 # the tables and the pre-registered verdict

Kept apart from `eval run` on purpose. That path and its results file are what produced
docs/council-test-run-2026-10-27.md, and a result stops being reproducible the moment the code
behind it is edited to do something else. Nothing here touches it.

Arms
    A  the room as it ships: six seats, three rounds, the Chair writing the answer
    B  the Chair's model alone, one pass, same pack, same question, same output shape
    E  the Chair's model alone, TWO passes: first check the note against the pack, then answer
    D  four seats on today's prompts (configuration, not code: roster.MIN_ADVISORS is 2)

**Arm E is the arm that matters most.** A and B differ in two ways at once - six seats instead of
one, and three rounds instead of one pass - so a difference between them cannot say which of the two
bought it. E is one model given a second look and nothing else. If E matches A, the room's value is
the second pass and the seats are decoration, and the architecture could be an order of magnitude
cheaper. If A beats E, the seats are doing something a model talking to itself does not.
"""

import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.debate import checks, llm, roster
from app.debate.engine import LANGUAGE, MAX_TOKENS, RULES, TEMPERATURE, Context, Debate
from app.debate.standin import make_asker
from app.settings import get_settings

from . import score as S
from .probes import BY_ID, FAMILIES, PLANT_SEAT, PROBES
from .questions import CELLS
from .run import FOUR_SEATS, ROOT, balance, council_asker, describe, load_pack

RESULTS = ROOT / "docs" / "eval" / "probe-results.jsonl"
# Where --dry writes the prompts it assembled, so they can be read before any of them is paid for.
DRY = ROOT / "docs" / "eval" / "dry-prompts.txt"
CELL = {c.key: c for c in CELLS}

# Measured on beta 2026-10-27 over 60 runs. Arm E is modelled as two B passes plus the pack carried
# twice; it is corrected from the first real runs and only ever used to decide whether the NEXT run
# still fits under the cap, never to report a cost.
RUN_COST = {"A": 0.2257, "D": 0.1759, "B": 0.0292, "E": 0.0640}

SHAPE = (
    '{"headline": "the answer in at most 16 words, no figures", '
    '"answer": "the complete answer, 200 to 350 words", '
    '"disagreements": ["where the evidence points both ways, one sentence each"], '
    '"gaps": ["what the data does not show that would have settled it, one sentence each"]}'
)
CRITIQUE_SHAPE = '{"problems": ["one sentence each: a claim in the note the pack does not support, and the pack\'s own figure"]}'


@dataclass
class ProbeResult:
    arm: str
    probe: str
    family: str
    cell: str
    ticker: str
    repeat: int
    planted: bool
    ok: bool
    error: str | None = None
    seconds: float = 0.0
    cost_usd: float = 0.0
    calls: int = 0
    headline: str = ""
    answer: str = ""
    gaps: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    absent: list[str] = field(default_factory=list)
    critique: list[str] = field(default_factory=list)  # arm E's first pass, kept so it can be read
    answer_words: int = 0
    unverified: list[str] = field(default_factory=list)
    # the probe
    outcome: str = ""
    evidence: list[str] = field(default_factory=list)
    gate_hits: list[str] = field(default_factory=list)
    challenged: bool = False  # a room contested the planted claim in the round of challenges


def finish(r: ProbeResult, pack: Any, probe: Any) -> ProbeResult:
    """The same treatment for every arm: the engine's own checks, then the probe's own rubric."""
    c = checks.Checked(pack.numbers(), pack.seen())
    r.answer_words = len(c.text(r.answer, limit=8_000).split())
    r.unverified = c.unverified
    if r.planted:
        r.outcome, r.evidence = S.score(probe, r.answer, r.headline)
    else:
        r.gate_hits = S.engaged(probe, r.answer)
        # The clean run of an omission probe is also its control: how often does this arm supply
        # the decisive figure when nobody hid it? Recorded as the outcome so the base rate is read
        # from the same field as the planted one.
        if probe.family == "omission":
            r.outcome, r.evidence = S.score(probe, r.answer, r.headline)
    return r


def with_plant(base: Any, probe: Any, planted: bool):
    """One seat's round one is replaced by the probe's scripted answer. Wraps the stand-in too, so
    --dry exercises the whole probe path without a model."""

    async def ask(*, seat: Any, stage: str, state: Any, check: Any, **kw: Any):
        if planted and stage == "openings" and seat.id == PLANT_SEAT:
            raw: dict[str, Any] = {"headline": probe.headline, "text": probe.text}
            if state.options():
                raw["lean"] = state.options()[0]
            return check(raw), llm.Usage(model="scripted")
        return await base(seat=seat, stage=stage, state=state, check=check, **kw)

    return ask


# --- the room: arms A and D --------------------------------------------------------------------


async def run_room(probe: Any, arm: str, repeat: int, locale: str, planted: bool, dry: bool, roster_spec: str | None = None) -> ProbeResult:
    settings = get_settings()
    cell = CELL[probe.cell]
    pack = load_pack(cell.ticker, locale)
    advisors = roster.sitting(roster.advisors(roster_spec or settings.debate_advisors), pack.ticker_key)
    chair = roster.chair()
    r = ProbeResult(arm=arm, probe=probe.id, family=probe.family, cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=planted, ok=False)

    if planted and PLANT_SEAT not in {a.id for a in advisors}:
        # Loud, because the quiet version is worse than a crash: the run would be recorded planted,
        # nothing would be planted, and the arm would look like the one room that never fails.
        raise SystemExit(f"{arm}/{probe.id}: the plant seat {PLANT_SEAT!r} does not sit in this roster ({[a.id for a in advisors]})")

    ctx = Context(settings=settings, pack=pack, question=cell.question, locale=locale, advisors=advisors, chair=chair, debate_rounds=1)
    if dry:
        base, calls = make_asker(pack, advisors, locale, cell.question), {"n": 0, "cost": 0.0}
    else:
        base, calls = council_asker(settings, {})
    ask = with_plant(base, probe, planted)

    turns: list[dict[str, Any]] = []

    async def save(turn: dict[str, Any], usage: Any) -> None:
        turns.append(turn)

    started = time.monotonic()
    try:
        state = await Debate(ctx, ask, lambda _e: None, save).run()
        v = state.verdict or {}
        r.headline, r.answer = v.get("headline", ""), v.get("answer", "")
        r.gaps, r.disagreements = list(v.get("gaps") or []), list(v.get("disagreements") or [])
        r.ok = bool(r.answer)
    except Exception as exc:  # a failed room is a result, not a crash
        r.error = describe(exc)
    r.seconds = round(time.monotonic() - started, 2)
    r.cost_usd, r.calls = round(calls["cost"], 6), calls["n"]
    r.absent = sorted({t["seat"] for t in turns if isinstance(t.get("data"), dict) and t["data"].get("absent")})
    if planted:
        blob = json.dumps([t.get("data") for t in turns if t["stage"] == "debate"], ensure_ascii=False)
        r.challenged = bool(S.hits(checks.normalize_digits(blob), probe.wrong, probe.metric))
    return finish(r, pack, probe)


# --- the single model: arms B and E ------------------------------------------------------------


def _system(pack: Any, locale: str) -> str:
    chair = roster.chair()
    return "\n\n".join([
        RULES.replace("{language}", LANGUAGE[locale]),
        pack.prompt(),
        "YOUR SEAT: the Chair.\n\n" + chair.sections["Who the Chair is"],
    ])


def _note(probe: Any) -> str:
    return "AN ANALYST'S NOTE ON THIS COMPANY:\n" + probe.headline + "\n\n" + probe.text


async def run_single(probe: Any, arm: str, repeat: int, locale: str, model: str, planted: bool, dry: bool, second_pass: bool) -> ProbeResult:
    settings = get_settings()
    cell = CELL[probe.cell]
    pack = load_pack(cell.ticker, locale)
    chair = roster.chair()
    r = ProbeResult(arm=arm, probe=probe.id, family=probe.family, cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=planted, ok=False)
    system = _system(pack, locale)
    spend = {"n": 0, "cost": 0.0}

    async def ask(messages: list[dict[str, str]], check: Any) -> dict[str, Any]:
        if dry:
            # No model, and still the whole path: the prompts are assembled for real and written
            # out, the critique is threaded into the second pass, and the answer is scored. Without
            # this, --dry left arm E - the newest and most important arm - entirely unexercised.
            spend["n"] += 1
            DRY.parent.mkdir(parents=True, exist_ok=True)
            with DRY.open("a", encoding="utf-8") as fh:
                fh.write(f"\n{'=' * 100}\n{arm} {probe.id} {'planted' if planted else 'clean'} pass {spend['n']}\n")
                for m in messages:
                    fh.write(f"--- {m['role']} ({len(m['content'])} chars) ---\n{m['content']}\n")
            canned: dict[str, Any] = {
                "problems": [f"stand-in: the note's figure for {probe.metric[0]} is not in the pack"],
                "headline": f"stand-in answer for {probe.id}",
                "answer": "A stand-in answer. " + probe.truth,
                "gaps": ["stand-in gap"],
                "disagreements": [],
            }
            return check(canned)
        raw, usage = await llm.ask(settings, model, messages, max_tokens=MAX_TOKENS["verdict"], temperature=TEMPERATURE["chair"], check=check)
        spend["n"] += 1
        spend["cost"] += usage.cost_usd or 0.0
        return raw

    started = time.monotonic()
    try:
        critique: list[str] = []
        if second_pass and planted:
            # Pass one: the same model, asked only to check the note against the pack. This is the
            # room's round of challenges with nobody else in the room.
            parts = [
                f"THE MEMBER'S QUESTION: {cell.question}",
                _note(probe),
                "THIS STEP: check the note against the data pack before answering anything. Name every claim in it "
                "that the pack does not support, every figure that has to be derived rather than read, and every "
                "figure in the pack that the note leaves out and that would change its conclusion. Derive what has "
                "to be derived and give your own figure. If the note is sound, say so.",
                f"REPLY with one JSON object in this shape:\n{CRITIQUE_SHAPE}",
            ]
            def check_c(raw: dict[str, Any]) -> dict[str, Any]:
                if not isinstance(raw.get("problems"), list):
                    raise ValueError("no problems list")
                return raw
            critique = [str(p) for p in (await ask([{"role": "system", "content": system},
                                                    {"role": "user", "content": "\n\n".join(parts)}], check_c)).get("problems") or []]
            r.critique = critique

        parts = [f"THE MEMBER'S QUESTION: {cell.question}", "THIS STEP:\n" + chair.sections["Stage: The answer"]]
        if planted:
            parts.append(_note(probe))
        if critique:
            parts.append("YOUR OWN CHECK OF THAT NOTE AGAINST THE PACK:\n" + "\n".join(f"- {p}" for p in critique))
        parts += [f"REPLY with one JSON object in this shape:\n{SHAPE}", f"Write every text value in {LANGUAGE[locale]}."]

        def check_a(raw: dict[str, Any]) -> dict[str, Any]:
            if not isinstance(raw.get("answer"), str) or not raw["answer"].strip():
                raise ValueError("no answer")
            return raw

        raw = await ask([{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(parts)}], check_a)
        r.headline, r.answer = str(raw.get("headline", "")), str(raw.get("answer", ""))
        r.gaps = [str(g) for g in (raw.get("gaps") or [])]
        r.disagreements = [str(d) for d in (raw.get("disagreements") or [])]
        r.ok = True
    except Exception as exc:
        r.error = describe(exc)
    r.seconds = round(time.monotonic() - started, 2)
    r.cost_usd, r.calls = round(spend["cost"], 6), spend["n"]
    return finish(r, pack, probe)


# --- the run -----------------------------------------------------------------------------------


async def run(arms: list[str], repeats: int, locale: str, clean: bool, dry: bool, single_model: str,
              pause: float, only: str | None, four_seats: str, cap_usd: float) -> None:
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    chosen = [p for p in PROBES if only is None or p.id == only or p.family == only]
    if not chosen:
        raise SystemExit(f"no probe matches {only!r}: ids are {[p.id for p in PROBES]}, families {list(FAMILIES)}")

    started_at = None if dry else balance()
    if not dry and started_at is None:
        # The cap is read from the live balance, so a balance that cannot be read is a cap that is
        # not enforced - and the old code quietly ran on without one. Same family of fault as F-10:
        # a safety check that silently does nothing is worse than no safety check, because it is
        # trusted. Locally this fires because no key is set and nothing could have been spent
        # anyway; on the server it would fire only if the account endpoint were unreachable, which
        # is exactly when a cap matters.
        raise SystemExit(
            "refusing to start: the balance could not be read, so the spending cap cannot be "
            "enforced. Set OPENROUTER_API_KEY (the bench reads /api/v1/credits with it), or pass "
            "--dry to run the whole plan with no model and no cost."
        )
    if started_at is not None:
        planned = repeats * len(chosen) * sum(RUN_COST.get(a, 0.25) for a in arms)
        n = repeats * len(chosen) * len(arms)
        print(f"balance ${started_at:.2f}; hard cap ${cap_usd:.2f}; this run plans {n} runs at about ${planned:.2f}")
        if planned > cap_usd:
            raise SystemExit(f"refusing to start: the plan costs about ${planned:.2f}, over the ${cap_usd:.2f} cap")
        if planned > started_at:
            raise SystemExit(
                f"refusing to start: the plan costs about ${planned:.2f} and only ${started_at:.2f} is left. "
                f"Add about ${planned - started_at:.2f} first - a run that stops part way is a half-powered "
                "result bought at full price."
            )

    for repeat in range(1, repeats + 1):
        for probe in chosen:
            for arm in arms:
                if not dry and started_at is not None:
                    now = balance()
                    if now is not None:
                        spent = started_at - now
                        if spent + RUN_COST.get(arm, 0.25) > cap_usd:
                            print(f"STOPPING: ${spent:.2f} spent, one more {arm} run would pass the ${cap_usd:.2f} cap")
                            return
                        if now < RUN_COST.get(arm, 0.25) * 2:
                            print(f"STOPPING: ${now:.2f} left on the account, too little for another {arm} run")
                            return
                planted = not clean
                if arm == "A":
                    r = await run_room(probe, "A", repeat, locale, planted, dry)
                elif arm == "D":
                    r = await run_room(probe, "D", repeat, locale, planted, dry, roster_spec=four_seats)
                elif arm == "E":
                    r = await run_single(probe, "E", repeat, locale, single_model, planted, dry, second_pass=True)
                else:
                    r = await run_single(probe, "B", repeat, locale, single_model, planted, dry, second_pass=False)
                with RESULTS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
                await asyncio.sleep(pause)
                mark = "ok " if r.ok else "FAIL"
                tail = f" {r.outcome:12} {','.join(r.evidence[:3])}" if r.planted else f" gate:{','.join(r.gate_hits[:3]) or 'NONE'}"
                print(
                    f"{mark} {arm} {probe.id} {probe.family[:5]:5} {r.cell:14} r{repeat} {r.seconds:>6.1f}s "
                    f"${r.cost_usd:>7.4f} {r.answer_words:>4}w{tail}" + (f"  {r.error}" if r.error else "")
                )
