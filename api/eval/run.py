"""Build a pack once, then replay it through three rooms and score what comes back.

    uv run python -m eval snapshot                 # build and save a pack per cell
    uv run python -m eval run --arm A --repeats 1  # replay; --dry uses the stand-in and costs nothing
    uv run python -m eval report                   # read the results back and print the table

One process per run is the safe way to drive this: `llm.ask` builds a fresh AsyncOpenAI client on
every call and never closes it, so a process that runs several sessions accumulates connection pools
and stalls after three or four (docs/beta-advisors-2026-10-27.md, F-11). --cell exists for that.

Arms
    A  the room as it ships: six seats on one advisor model, the Chair on another
    B  the Chair's model alone, same pack, same question, same output shape
    C  six seats spread across three models, the same Chair
    D  four seats on today's prompts: the count changed, nothing else

Every arm reads the SAME saved pack, so the data is not a variable. Results are appended to
docs/eval/results.jsonl, one JSON object per run, so stopping a run loses nothing already measured.
It does not skip work already done: a second invocation runs every cell again and appends.
"""

import argparse
import asyncio
import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from starlette.requests import Request

from app.debate import checks, llm, roster
from app.debate.engine import LANGUAGE, MAX_TOKENS, RULES, TEMPERATURE, Context, Debate
from app.debate.pack import Pack, build
from app.debate.standin import make_asker
from app.main import create_app
from app.settings import get_settings

from .questions import CELLS, PLANT_FIGURE, PLANT_HEADLINE, PLANT_SEAT, PLANT_TEXT

# Measured on beta, 2026-10-27, over 28 completed sessions: a run's cost by arm. Used only to
# decide whether the NEXT run still fits under the cap, never to report a cost - the reported
# figures are OpenRouter's own.
RUN_COST = {"A": 0.2226, "C": 0.4327, "D": 0.2193, "B": 0.0295}
CREDITS_URL = "https://openrouter.ai/api/v1/credits"

ROOT = Path(__file__).resolve().parents[2]
PACKS = ROOT / "docs" / "eval" / "packs"
RESULTS = ROOT / "docs" / "eval" / "results.jsonl"

# Arm C spreads the six seats over three models. Seats keep their own files; only the model moves.
SPREAD = ("deepseek/deepseek-v4-pro", "anthropic/claude-sonnet-5.5", "openai/gpt-5.2")
# Arm D is four seats on today's prompts and today's model: it changes the COUNT and nothing else,
# so the count can be told apart from the philosophies before anyone rewrites them. No code is
# needed for it - roster.MIN_ADVISORS is 2 - it is a different DEBATE_ADVISORS.
FOUR_SEATS = "buffett,lynch,marks,alwaleed"


def describe(exc: BaseException) -> str:
    """SeatError carries only a code, so the provider's own error is lost by the time it reaches here.
    Walk the cause chain and keep it: `unreachable` could be DNS, a 402, a 5xx or a provider block, and
    which one it is decides whether F-10 is a retry problem or a rate-limit problem."""
    parts = [f"{type(exc).__name__}: {exc}"]
    cause, seen = exc.__cause__, 0
    while cause is not None and seen < 4:
        status = getattr(cause, "status_code", None)
        body = getattr(cause, "body", None)
        parts.append(f"<- {type(cause).__module__}.{type(cause).__name__}" + (f" [{status}]" if status else "") + f": {str(cause)[:200]}" + (f" body={str(body)[:200]}" if body else ""))
        cause, seen = cause.__cause__, seen + 1
    return " ".join(parts)


def balance() -> float | None:
    """Money left on the model account, or None if it cannot be read. /credits, not /auth/key:
    auth/key reports a spend cap on the key, credits reports the money (F-10)."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None
    req = urllib.request.Request(CREDITS_URL, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            d = json.load(resp)["data"]
        return float(d["total_credits"]) - float(d["total_usage"])
    except Exception:
        return None


def request_for(app: Any) -> Request:
    """A Request good enough for the database tools: they read app.state and request.state.plan."""
    r = Request({"type": "http", "app": app, "headers": [], "method": "GET", "path": "/", "query_string": b""})
    r.state.plan = "pro"
    return r


# --- the pack, saved once ---------------------------------------------------------------------


async def snapshot(locale: str = "en") -> None:
    app = create_app()
    req = request_for(app)
    PACKS.mkdir(parents=True, exist_ok=True)
    for cell in CELLS:
        t = app.state.universe.resolve(cell.ticker)
        if t is None:
            print(f"{cell.ticker}: NOT IN UNIVERSE - skipped")
            continue
        pack = await build(req, t, locale)
        path = PACKS / f"{cell.ticker}.{locale}.json"
        path.write_text(pack.model_dump_json(indent=1), encoding="utf-8")
        bad = [tag for tag, s in pack.sources.items() if not s.ok]
        print(f"{cell.ticker:16} {path.name:28} {len(pack.prompt()):>6} chars  {len(pack.seen()):>4} numbers  bad={bad or 'none'}")


def load_pack(ticker: str, locale: str) -> Pack:
    return Pack.model_validate_json((PACKS / f"{ticker}.{locale}.json").read_text(encoding="utf-8"))


# --- one run's result -------------------------------------------------------------------------


@dataclass
class Result:
    arm: str
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
    # scored after the fact, against the pack the arm actually read
    answer_words: int = 0
    unverified: list[str] = field(default_factory=list)
    advice_removed: int = 0
    # the probe
    plant_challenged: bool = False
    plant_in_answer: bool = False


def score(r: Result, pack: Pack) -> Result:
    """The same treatment for every arm: the engine's own checks over the final answer."""
    c = checks.Checked(pack.numbers(), pack.seen())
    text = c.text(r.answer, limit=8_000)
    r.answer_words = len(text.split())
    r.unverified = c.unverified
    r.advice_removed = c.removed
    r.plant_in_answer = PLANT_FIGURE in checks.normalize_digits(r.answer)
    return r


# --- arm A and C: the room --------------------------------------------------------------------


def with_plant(base: Any, plant: bool):
    """Wraps any asker so one seat's round one is scripted with a wrong derivation instead of asked.
    It wraps the stand-in too, so the probe path can be exercised without spending anything."""

    async def ask(*, seat: Any, stage: str, state: Any, check: Any, **kw: Any):
        if plant and stage == "openings" and seat.id == PLANT_SEAT:
            raw: dict[str, Any] = {"headline": PLANT_HEADLINE, "text": PLANT_TEXT.format(figure=PLANT_FIGURE)}
            if state.options():
                raw["lean"] = state.options()[0]
            return check(raw), llm.Usage(model="scripted")
        return await base(seat=seat, stage=stage, state=state, check=check, **kw)

    return ask


def council_asker(settings: Any, models: dict[str, str]):
    """llm.ask, with the model chosen per seat (arm C) and the spend counted."""
    calls = {"n": 0, "cost": 0.0}

    async def ask(*, seat: Any, messages: Any, model: str, max_tokens: int, temperature: float, check: Any, **_: Any):
        chosen = models.get(seat.id, model)
        checked, usage = await llm.ask(settings, chosen, messages, max_tokens=max_tokens, temperature=temperature, check=check)
        calls["n"] += 1
        calls["cost"] += usage.cost_usd or 0.0
        return checked, usage

    return ask, calls


async def run_room(cell: Any, locale: str, repeat: int, arm: str, models: dict[str, str], plant: bool, dry: bool, roster_spec: str | None = None) -> Result:
    settings = get_settings()
    # No create_app() here on purpose: replaying a saved pack needs no market database and no app
    # state, so the bench runs anywhere the model key does - including on the server.
    pack = load_pack(cell.ticker, locale)
    advisors = roster.sitting(roster.advisors(roster_spec or settings.debate_advisors), pack.ticker_key)
    chair = roster.chair()
    ctx = Context(settings=settings, pack=pack, question=cell.question, locale=locale, advisors=advisors, chair=chair, debate_rounds=1)
    r = Result(arm=arm, cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=plant, ok=False)

    if plant and PLANT_SEAT not in {a.id for a in advisors}:
        # Loud, because the quiet version is worse than a crash: the run would be recorded
        # planted=True, nothing would be planted, and the arm would look like the one room that
        # never propagates an error. Same family as F-4 and F-9.
        raise SystemExit(f"{arm}: the plant seat {PLANT_SEAT!r} does not sit in this roster ({[a.id for a in advisors]})")
    if dry:
        base, calls = make_asker(pack, advisors, locale, cell.question), {"n": 0, "cost": 0.0}
    else:
        base, calls = council_asker(settings, models)
    ask = with_plant(base, plant)

    turns: list[dict[str, Any]] = []

    async def save(turn: dict[str, Any], usage: Any) -> None:
        turns.append(turn)

    started = time.monotonic()
    debate = Debate(ctx, ask, lambda _e: None, save)
    try:
        state = await debate.run()
        v = state.verdict or {}
        r.headline, r.answer = v.get("headline", ""), v.get("answer", "")
        r.gaps, r.disagreements = list(v.get("gaps") or []), list(v.get("disagreements") or [])
        r.ok = bool(r.answer)
    except Exception as exc:  # a failed room is a result, not a crash
        r.error = describe(exc)
    r.seconds = round(time.monotonic() - started, 2)
    r.cost_usd, r.calls = round(calls["cost"], 6), calls["n"]
    r.absent = sorted({t["seat"] for t in turns if isinstance(t.get("data"), dict) and t["data"].get("absent")})
    if plant:
        # Did anyone contest the planted figure in the round of challenges?
        r.plant_challenged = any(
            t["stage"] == "debate" and PLANT_FIGURE in checks.normalize_digits(json.dumps(t.get("data") or {}, ensure_ascii=False))
            for t in turns
        )
    return score(r, pack)


# --- arm B: one model, same pack, same shape ---------------------------------------------------

SINGLE_SHAPE = (
    '{"headline": "the answer in at most 16 words, no figures", '
    '"answer": "the complete answer, 200 to 350 words", '
    '"disagreements": ["where the evidence points both ways, one sentence each"], '
    '"gaps": ["what the data does not show that would have settled it, one sentence each"]}'
)


async def run_single(cell: Any, locale: str, repeat: int, model: str, plant: bool, dry: bool) -> Result:
    settings = get_settings()
    pack = load_pack(cell.ticker, locale)
    chair = roster.chair()
    r = Result(arm="B", cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=plant, ok=False)
    if dry:
        r.error = "dry run: arm B needs a model"
        return r

    system = "\n\n".join([RULES.replace("{language}", LANGUAGE[locale]), pack.prompt(), "YOUR SEAT: the Chair.\n\n" + chair.sections["Who the Chair is"]])
    parts = [f"THE MEMBER'S QUESTION: {cell.question}", "THIS STEP:\n" + chair.sections["Stage: The answer"]]
    if plant:
        # The same wrong claim the room is given, so both arms face it: here as an analyst's note.
        parts.append("AN ANALYST'S NOTE ON THIS COMPANY:\n" + PLANT_TEXT.format(figure=PLANT_FIGURE))
    parts += [f"REPLY with one JSON object in this shape:\n{SINGLE_SHAPE}", f"Write every text value in {LANGUAGE[locale]}."]
    messages = [{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(parts)}]

    def check(raw: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw.get("answer"), str) or not raw["answer"].strip():
            raise ValueError("no answer")
        return raw

    started = time.monotonic()
    try:
        raw, usage = await llm.ask(settings, model, messages, max_tokens=MAX_TOKENS["verdict"], temperature=TEMPERATURE["chair"], check=check)
        r.headline, r.answer = str(raw.get("headline", "")), str(raw.get("answer", ""))
        r.gaps = [str(g) for g in (raw.get("gaps") or [])]
        r.disagreements = [str(d) for d in (raw.get("disagreements") or [])]
        r.cost_usd, r.calls, r.ok = round(usage.cost_usd or 0.0, 6), 1, True
    except Exception as exc:
        r.error = describe(exc)
    r.seconds = round(time.monotonic() - started, 2)
    return score(r, pack)


# --- the run ------------------------------------------------------------------------------------


async def run(arms: list[str], repeats: int, locale: str, plant: bool, dry: bool, single_model: str, spread: tuple[str, ...], pause: float = 5.0, only_cell: str | None = None,
    four_seats: str = FOUR_SEATS, cap_usd: float = 10.0) -> None:
    settings = get_settings()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    started_at = None if dry else balance()
    if started_at is not None:
        cells_n = len(CELLS if only_cell is None else [c for c in CELLS if c.key == only_cell])
        planned = repeats * cells_n * sum(RUN_COST.get(a, 0.45) for a in arms)
        print(f"balance ${started_at:.2f}; hard cap ${cap_usd:.2f}; this run plans {repeats * cells_n * len(arms)} runs at about ${planned:.2f}")
        if planned > cap_usd:
            raise SystemExit(f"refusing to start: the plan costs about ${planned:.2f}, over the ${cap_usd:.2f} cap")
        if planned > started_at:
            # Starting anyway would spend the balance and stop part way, which buys a half-powered
            # result for the price of a whole one. The point of the cap is not to spend less; it is
            # not to spend at all on a test that cannot finish.
            raise SystemExit(
                f"refusing to start: the plan costs about ${planned:.2f} and only ${started_at:.2f} is left. "
                f"Add about ${planned - started_at:.2f} first - a run that stops part way is a half-powered "
                "result bought at full price."
            )
    ids = [a.id for a in roster.advisors(settings.debate_advisors)]
    arm_c_models = {seat: spread[i % len(spread)] for i, seat in enumerate(ids)} | {"chair": settings.debate_chair_model}
    for repeat in range(1, repeats + 1):
        for cell in (CELLS if only_cell is None else [c for c in CELLS if c.key == only_cell]):
            if not (PACKS / f"{cell.ticker}.{locale}.json").exists():
                print(f"{cell.ticker}: no saved pack - run `snapshot` first")
                continue
            for arm in arms:
                if not dry and started_at is not None:
                    now = balance()
                    spent = (started_at - now) if now is not None else 0.0
                    if now is not None and spent + RUN_COST.get(arm, 0.45) > cap_usd:
                        print(f"STOPPING: ${spent:.2f} spent, one more {arm} run would pass the ${cap_usd:.2f} cap")
                        return
                    if now is not None and now < RUN_COST.get(arm, 0.45) * 2:
                        print(f"STOPPING: ${now:.2f} left on the account, too little for another {arm} run")
                        return
                if arm == "A":
                    r = await run_room(cell, locale, repeat, "A", {}, plant, dry)
                elif arm == "C":
                    r = await run_room(cell, locale, repeat, "C", arm_c_models, plant, dry)
                elif arm == "D":
                    r = await run_room(cell, locale, repeat, "D", {}, plant, dry, roster_spec=four_seats)
                else:
                    r = await run_single(cell, locale, repeat, single_model, plant, dry)
                with RESULTS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
                await asyncio.sleep(pause)
                mark = "ok " if r.ok else "FAIL"
                probe = f" plant[challenged={r.plant_challenged} in_answer={r.plant_in_answer}]" if r.planted else ""
                print(
                    f"{mark} {arm} {cell.key:14} r{repeat} {r.seconds:>6.1f}s ${r.cost_usd:>7.4f} "
                    f"{r.answer_words:>4}w unverified={len(r.unverified):<3} gaps={len(r.gaps)}{probe}"
                    + (f"  {r.error}" if r.error else "")
                )


def main() -> None:
    p = argparse.ArgumentParser(prog="eval", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot").add_argument("--locale", default="en")
    r = sub.add_parser("run")
    r.add_argument("--arm", action="append", choices=["A", "B", "C", "D"], help="repeatable; default A B D")
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--locale", default="en")
    r.add_argument("--plant", action="store_true", help="script one seat's round one with a wrong derivation")
    r.add_argument("--dry", action="store_true", help="stand-in room: no model, no cost")
    r.add_argument("--single-model", default=get_settings().debate_chair_model)
    r.add_argument("--spread", default=",".join(SPREAD))
    r.add_argument("--pause", type=float, default=5.0, help="seconds between runs, so a burst is not read as a fault")
    r.add_argument("--cell", default=None, help="one cell only (its key), so a caller can give every run its own process")
    r.add_argument("--four-seats", default=FOUR_SEATS, help="arm D's roster")
    r.add_argument("--cap-usd", type=float, default=10.0, help="hard spending cap, checked against the live balance before every run")
    sub.add_parser("report")
    a = p.parse_args()

    if a.cmd == "snapshot":
        asyncio.run(snapshot(a.locale))
    elif a.cmd == "run":
        asyncio.run(run(a.arm or ["A", "B", "D"], a.repeats, a.locale, a.plant, a.dry, a.single_model, tuple(a.spread.split(",")), a.pause, a.cell, a.four_seats, a.cap_usd))
    else:
        from .report import report, verdict

        report(RESULTS)
        print()
        verdict(RESULTS)
