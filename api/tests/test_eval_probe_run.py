"""The safeguards as the RUNNER uses them, not as the helpers offer them.

Round four of the independent review made a point that the rest of this suite had earned:

    The current tests are valuable, but they focus mainly on individual helper functions. The
    critical problems arise where those helpers are connected - or not connected - to the benchmark
    execution paths.

That is exactly what happened. `bound_for` was correct, `Budget.take` accepted a bound, every budget
test passed - and arms B and E called `take()` without one, so two of the four arms ran on a flat
forecast while the suite reported a hard cap. No helper was broken. The wiring was.

So these tests drive the runner. Two kinds, because they can reach different distances:

* **Behavioural** - `run_single` executed with a stand-in model, asserting what the budget actually
  received. These need the saved packs and skip without them.
* **Structural** - the runner's own source read with `ast`, asserting that no call path omits a
  bound and that the stop condition is enforced rather than consulted. Cheap, blunt, and it runs
  anywhere, including inside the verification package where the packs are not on this path.

Nothing here makes a paid call: `llm.ask` is replaced throughout.
"""

import ast
import asyncio
from pathlib import Path

import pytest

from eval.budget import Budget, bound_for

HARNESS = Path(__file__).resolve().parents[1] / "eval"
RUNNER = HARNESS / "probe_run.py"
pytestmark = pytest.mark.skipif(not RUNNER.exists(), reason="the harness is not in this checkout")


# --- structural: the runner cannot route around the bound --------------------------------------


def _calls_named(tree: ast.AST, attr: str) -> list[ast.Call]:
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == attr]


def _source() -> str:
    return RUNNER.read_text(encoding="utf-8")


def test_no_call_in_the_harness_reserves_without_a_bound():
    """The defect round four found, as a test that fails if it is ever reintroduced. Every
    `.take(...)` anywhere in the harness must pass a bound - a second positional argument or an
    explicit `bound=`. `allow_forecast` is the only way out and no harness path may use it.

    Scanned over the whole package rather than the runner alone, and it asserts that a bounded call
    was actually found: the reservation moved out of `probe_run` into the shared wrapper while this
    was being written, which left the first version of this test passing over an empty list. A test
    that cannot fail is worse than no test, because it is counted.
    """
    bounded = 0
    for path in sorted(HARNESS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for call in _calls_named(tree, "take"):
            kwargs = {k.arg for k in call.keywords}
            where = f"{path.name}:{call.lineno}"
            assert "allow_forecast" not in kwargs, f"{where} opts out of the hard cap"
            assert len(call.args) >= 2 or "bound" in kwargs, f"{where} passes no bound"
            bounded += 1
    assert bounded >= 1, "no reservation call found at all - this test would pass on anything"


def test_the_runner_builds_its_budget_with_both_ceilings():
    """`expect_usd` existed, was tested, was documented, and was never passed to the Budget the run
    used. A ceiling that is not wired is not a ceiling."""
    tree = ast.parse(_source())
    budgets = [n for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Budget"]
    assert budgets, "the runner constructs no Budget at all"
    assert any("expect_usd" in {k.arg for k in b.keywords} for b in budgets), (
        "no Budget is given a forecast ceiling")


def test_the_runner_enforces_the_stop_condition():
    """`should_stop()` could report an overrun while the loop carried on, because the loop checked
    only `budget.refused`. Both have to be read."""
    src = _source()
    assert "should_stop()" in src, "the runner never consults should_stop()"
    assert "budget.refused" in src


def test_every_arm_goes_through_the_one_metering_wrapper():
    """The structural reason the defect is now hard to reintroduce: arms B and E had a metering path
    of their own. There is one wrapper, and both the room and the single-model arms call it."""
    src = _source()
    assert src.count("metered(") >= 2, "the single-model arms do not share the room's wrapper"
    # and the inline bookkeeping the single arms used is gone
    assert "budget.settle(cost)" not in src, "an un-reserved settle remains in the runner"


# --- behavioural: what the budget actually receives ---------------------------------------------


def _why_not_runnable() -> str | None:
    """Why the behavioural tests cannot run here, quoting the actual failure - or None.

    The first version of this guard caught every exception and reported "the saved packs are not on
    this path". That was a guess, and inside the verification package it was the wrong one: the packs
    ARE there, and what fails is importing `eval.run`, because `app.copilot.openai_compat` reaches
    into `app.routers` at module scope and the archive does not carry the application's routes.

    A skip that states the wrong reason is the same fault as a guard that quietly does nothing - it
    is read, and believed, and it sends whoever reads it somewhere else.
    """
    try:
        from eval.run import PACKS
    except Exception as exc:
        return f"the harness does not import here - {type(exc).__name__}: {exc}"
    if not any(PACKS.glob("*.json")):
        return f"no saved packs at {PACKS}"
    return None


_WHY_NOT = _why_not_runnable()
needs_packs = pytest.mark.skipif(_WHY_NOT is not None, reason=_WHY_NOT or "")


class FakeUsage:
    def __init__(self, cost: float = 0.01, prompt_tokens: int = 50) -> None:
        self.cost_usd = cost
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = 10
        self.seconds = 0.1
        self.model = "stand-in"


def _fake_ask(record: list, cost: float = 0.01, prompt_tokens: int = 50):
    """A stand-in `llm.ask` that answers in the shape the probes expect and records the prompt it
    was given, so the reservation can be checked against the real prompt size."""

    async def ask(_settings, model, messages, *, max_tokens, temperature, check):
        record.append({"model": model, "messages": messages, "max_tokens": max_tokens})
        return check({
            "headline": "a stand-in headline",
            "answer": "A stand-in answer with no figures in it at all.",
            "gaps": [],
            "disagreements": [],
            "problems": ["a stand-in problem"],
        }), FakeUsage(cost, prompt_tokens)

    return ask


@needs_packs
@pytest.mark.parametrize("arm,second_pass,passes", [("B", False, 1), ("E", True, 2)])
def test_the_single_model_arms_reserve_their_computed_bound(monkeypatch, arm, second_pass, passes):
    """The test that would have caught it. Arms B and E must reserve the bound computed from their
    own prompt - not the flat per-call forecast, which for these prompts is several times too low.

    Asserted against the prompt the stand-in actually received, so it cannot pass by agreeing with
    a figure this test also guessed.
    """
    from app.debate import llm
    from eval import probe_run
    from eval.probes import BY_ID

    seen: list = []
    monkeypatch.setattr(llm, "ask", _fake_ask(seen))

    budget = Budget(cap_usd=100.00, per_call_usd=0.03, attempts=3)
    r = asyncio.run(probe_run.run_single(
        BY_ID["D1"], arm, 1, "en", "anthropic/claude-sonnet-5.5",
        planted=True, dry=False, second_pass=second_pass, budget=budget))

    assert r.ok, r.error
    assert len(seen) == passes, f"{arm} made {len(seen)} passes"
    assert budget.calls == passes

    expected = 0.0
    for call in seen:
        msgs = [m for m in call["messages"] if isinstance(m, dict)]
        prompt_bytes = sum(len(str(m.get("content", "")).encode("utf-8")) for m in msgs)
        expected += bound_for(call["model"], prompt_bytes, call["max_tokens"], 3, messages=len(msgs))

    assert r.bound_usd == pytest.approx(expected, rel=1e-6)
    # the whole point: the bound is nothing like the flat forecast these arms used to reserve
    assert r.bound_usd > budget.reservation * passes * 3, (
        f"{arm} reserved {r.bound_usd}, barely above the flat forecast "
        f"{budget.reservation * passes}")


@needs_packs
def test_a_charge_above_its_bound_stops_the_single_model_arm(monkeypatch):
    """End to end: a provider that bills more than the bound allowed must leave the run stopped, not
    merely annotated. This is the overrun audit reached through the runner rather than through
    Budget directly."""
    from app.debate import llm
    from eval import probe_run
    from eval.probes import BY_ID

    monkeypatch.setattr(llm, "ask", _fake_ask([], cost=99.0))
    budget = Budget(cap_usd=1000.00, attempts=3)
    asyncio.run(probe_run.run_single(
        BY_ID["D1"], "B", 1, "en", "anthropic/claude-sonnet-5.5",
        planted=True, dry=False, second_pass=False, budget=budget))

    assert budget.overruns, "a charge of $99 against a bound under $1 was not recorded"
    assert budget.should_stop()
    with pytest.raises(Exception):     # BudgetExhausted: admission is closed
        budget.take("another call", 0.01)


@needs_packs
def test_a_prompt_denser_than_the_token_ceiling_stops_the_single_model_arm(monkeypatch):
    """The byte assumption, enforced through the runner. A provider reporting more prompt tokens
    than the prompt had bytes means every bound is too low, and the run must stop on the first
    such call rather than spend the rest of the plan inside a broken guarantee."""
    from app.debate import llm
    from eval import probe_run
    from eval.probes import BY_ID

    monkeypatch.setattr(llm, "ask", _fake_ask([], cost=0.001, prompt_tokens=10_000_000))
    budget = Budget(cap_usd=1000.00, attempts=3)
    asyncio.run(probe_run.run_single(
        BY_ID["D1"], "B", 1, "en", "anthropic/claude-sonnet-5.5",
        planted=True, dry=False, second_pass=False, budget=budget))

    assert budget.overruns and "denser than one token" in budget.overruns[0]
    assert budget.should_stop()


@needs_packs
def test_the_room_meters_its_stand_in_so_dry_reports_a_real_bound(monkeypatch):
    """`--dry` has to take the same reservations a paid run would, or the plan's published maximum
    is a figure computed beside the runner rather than by it. The room's dry path is metered, so a
    dry run of arm A reserves a real bound and spends nothing."""
    from eval import probe_run
    from eval.probes import BY_ID

    budget = Budget(cap_usd=1000.00, attempts=3)
    r = asyncio.run(probe_run.run_room(BY_ID["D1"], "A", 1, "en", planted=True, dry=True,
                                       budget=budget))
    assert r.ok, r.error
    assert r.cost_usd == 0.0, "a dry run spent money"
    assert r.bound_usd > 0.5, f"a dry room run reserved only {r.bound_usd}"
    assert budget.calls >= 10, f"only {budget.calls} calls metered in a six-seat room"
    assert not budget.overruns

@needs_packs
def test_a_second_dry_run_rebuilds_its_outputs_instead_of_doubling_them(monkeypatch, tmp_path):
    """Both dry outputs were opened "a", like the paid record, so previewing the plan twice doubled
    them - taking the committed results file from 48 rows to 96 and the prompt dump from 816K to
    1.6M. That file is committed precisely so the published maximum can be checked against it, so a
    reviewer re-running --dry to verify the bound was corrupting the record they were verifying."""
    from eval import probe_run
    from eval.run import FOUR_SEATS

    results = tmp_path / "dry-probe-results.jsonl"
    prompts = tmp_path / "dry-prompts.txt"
    monkeypatch.setattr(probe_run, "DRY_RESULTS", results)
    monkeypatch.setattr(probe_run, "DRY", prompts)

    def preview() -> tuple[int, int]:
        # A priced model name rather than the settings default, so the test does not depend on
        # which chair model this checkout is configured for. No call is made: dry is True.
        # I3, not D1: D1 was retired on 2026-11-06 (probes.RETIRED); I3 runs on the same pack (2222).
        asyncio.run(probe_run.run(["B"], 1, "en", False, True, "anthropic/claude-sonnet-5.5",
                                  0.0, "I3", FOUR_SEATS, 1.0))
        return (len(results.read_text(encoding="utf-8").strip().splitlines()),
                len(prompts.read_text(encoding="utf-8")))

    first = preview()
    assert first[0] == 1, f"one arm, one probe, one repeat wrote {first[0]} rows"
    second = preview()
    assert second == first, (
        f"a second identical dry run left {second[0]} rows and {second[1]} characters rather than "
        f"{first[0]} and {first[1]}: the dry outputs are appended to, not rebuilt")


@needs_packs
def test_both_phases_of_the_experiment_run_under_one_budget(monkeypatch, tmp_path, capsys):
    """The fifth review round's budget finding. The pre-registered experiment is 54 planted runs
    AND 12 clean controls, and each phase used to be a separate invocation of `eval probe` - so each
    built its own `Budget` with its own cap and the combined spend was bounded by nothing. Two $90
    caps are not a $90 cap, and the figure quoted to whoever authorises the run has to be the figure
    the run is held to.

    `--clean-arms` puts the control phase in the same invocation. This drives both phases and reads
    the run's own summary back: the bound is reported over every run of both phases, totalled from
    one accumulator."""
    import json

    from eval import probe_run
    from eval.run import FOUR_SEATS

    results = tmp_path / "dry-probe-results.jsonl"
    monkeypatch.setattr(probe_run, "DRY_RESULTS", results)
    monkeypatch.setattr(probe_run, "DRY", tmp_path / "dry-prompts.txt")

    # I3, not D1: D1 was retired on 2026-11-06 (probes.RETIRED); I3 runs on the same pack (2222).
    asyncio.run(probe_run.run(["B"], 1, "en", False, True, "anthropic/claude-sonnet-5.5", 0.0,
                              "I3", FOUR_SEATS, 1.0, ["B"]))

    rows = [json.loads(line) for line in results.read_text(encoding="utf-8").strip().splitlines()]
    assert [r["planted"] for r in rows] == [True, False], rows
    out = capsys.readouterr().out
    assert "over 2 runs" in out, out
    # one accumulator across both phases, not one per phase
    assert f"${sum(r['bound_usd'] for r in rows):.4f}" in out, out

# --- fairness of the stimulus across configurations (owner's item 6) ---------------------------


@needs_packs
@pytest.mark.parametrize("probe_id", ["D1", "I1"])
def test_every_arm_is_shown_the_identical_planted_claim(monkeypatch, probe_id):
    """The owner asked for proof that the standalone Chairman receives a fair equivalent of each
    injected claim. It did not, in two ways, and both were invisible until the prompts were read
    side by side:

    1. **Provenance.** The room shows its Chair `THE ADVISORS' ANSWERS:` with the claim attributed to
       a seated colleague; the single-model arm was shown "AN ANALYST'S NOTE ON THIS COMPANY". Same
       words, different authority, and the experiment would have charged the difference to
       configuration.
    2. **Citation tags.** The room's copy went through the engine's checker, which appends the
       `[P1]`-style tags for figures it finds in the pack. The single model's copy did not - so the
       room was shown a better-SOURCED version of the same false claim, which is the direction that
       matters, because tags make a claim look checked.

    Both are closed by `_note` mirroring `engine._line` and running the same `Checked.text`. This
    test reads the prompts the client was actually handed and compares the line character for
    character, because that is the only version of this claim that cannot drift."""
    from eval import probe_run
    from eval.budget import Budget
    from eval.probes import BY_ID, PLANT_SEAT

    probe = BY_ID[probe_id]
    seen: list[list[str]] = []
    real = probe_run.metered

    def spy(ask_fn, budget):
        inner, calls = real(ask_fn, budget)

        async def wrapped(**kw):
            if kw.get("messages"):
                seen.append([m["content"] for m in kw["messages"]])
            return await inner(**kw)

        return wrapped, calls

    monkeypatch.setattr(probe_run, "metered", spy)

    def plant_line(run) -> str:
        seen.clear()
        asyncio.run(run())
        last = "\n".join(seen[-1])
        lines = [l for l in last.splitlines() if l.startswith("- ")and probe.headline[:30] in l]
        assert lines, f"the answer-writing call does not carry the plant at all:\n{last[-2000:]}"
        return lines[0]

    room = plant_line(lambda: probe_run.run_room(
        probe, "A", 1, "en", True, True, budget=Budget(cap_usd=1e6)))
    single = plant_line(lambda: probe_run.run_single(
        probe, "B", 1, "en", "anthropic/claude-sonnet-5.5", True, True,
        second_pass=False, budget=Budget(cap_usd=1e6)))

    assert room == single, (
        f"the arms are shown different versions of the same plant\n  room:   {room!r}\n"
        f"  single: {single!r}")
    # and it really is the plant, attributed, not a paraphrase
    from app.debate import roster
    assert roster.load(PLANT_SEAT).surname in room
    assert "analyst" not in room.lower(), "the old framing is back"


# --- Priority Two and Three: the flags the harness used to discard -----------------------------
#
# Added 2026-11-02. The engine wrote `flags.uncovered` on every opening and `flags.unruled` on
# every verdict, and nothing anywhere read either one - so the funded run would have reported
# Priority One and been silent on the other two while looking like the experiment that measured
# all three. These tests are the consumer, which is the part that was missing.


def test_the_harness_reads_the_two_flags_rather_than_recomputing_them():
    """Structural, and it is the absent turn that matters.

    An absent seat's turn carries `flags: None`, not an empty dict (`engine.py`), so a reader that
    tests truthiness or indexes blindly either crashes or counts a silent seat as fully covered.
    Both are wrong in the same direction: they make a room look healthier the worse it went.
    """
    from eval.probe_run import room_flags

    turns = [
        {"stage": "openings", "seat": "buffett", "flags": {"uncovered": ["P2", "P9"]}},
        {"stage": "openings", "seat": "lynch", "flags": {"uncovered": []}},      # cited all its own
        {"stage": "openings", "seat": "dalio", "flags": None},                   # absent: not measured
        {"stage": "debate", "seat": "buffett", "flags": {"uncovered": ["P2"]}},  # a reply, not a gap
        {"stage": "verdict", "seat": "chair", "flags": {"unruled": ["Whether it is covered"]}},
    ]
    openings, uncovered, unruled = room_flags(turns)

    assert openings == 2, "the absent seat was counted as an opening it never wrote"
    assert uncovered == {"buffett": ["P2", "P9"]}, "a seat that cited all of its own is not a gap"
    assert unruled == ["Whether it is covered"]


def test_a_reply_is_never_counted_against_mandate_coverage():
    """The debate turn above carries an `uncovered` of its own and must not reach the measure.

    Reaching for another seat's dataset in a reply is the debate working. If replies counted, the
    number would fall as the room argued better, which inverts the instrument.
    """
    from eval.probe_run import room_flags

    openings, uncovered, _ = room_flags([
        {"stage": "debate", "seat": "buffett", "flags": {"uncovered": ["P2"]}},
        {"stage": "final", "seat": "lynch", "flags": {"uncovered": ["P7"]}},
    ])
    assert (openings, uncovered) == (0, {})


def test_a_room_that_never_reached_a_verdict_reports_no_rulings_rather_than_crashing():
    from eval.probe_run import room_flags

    assert room_flags([{"stage": "openings", "seat": "buffett", "flags": {"uncovered": []}}])[2] == []


@needs_packs
def test_a_dry_room_measures_coverage_for_every_seat_that_spoke():
    """Behavioural, through the real engine: the wiring, which is what the suite's own preamble says
    these tests exist for. The stand-in writes answers with no citations in them, so every seated
    advisor should come back owing its own datasets - and each seat's list must be a subset of what
    that seat actually owns, which is the check that would have caught the 2026-10-29 fault of
    attributing P9's work to P2."""
    from app.debate import roster
    from eval import probe_run
    from eval.probes import BY_ID

    r = asyncio.run(probe_run.run_room(BY_ID["D1"], "A", 1, "en", planted=True, dry=True,
                                       budget=Budget(cap_usd=1000.00, attempts=3)))
    assert r.ok, r.error
    assert r.absent == [], "a seat went absent, so this run cannot speak to coverage"
    assert r.openings == 6, f"a six-seat room measured {r.openings} openings"
    assert len(r.uncovered) == r.openings, (
        f"the stand-in cites nothing, so every seat should owe its own: {r.uncovered}")
    for seat, missing in r.uncovered.items():
        owns = roster.load(seat).info.owns
        assert set(missing) <= set(owns), f"{seat} was charged with {missing}, but owns {owns}"
    assert isinstance(r.unruled, list)


def test_select_takes_several_ids_and_refuses_retired_or_unknown_ones():
    """The 2026-11-06 pilot runs D2, D4, D5, I1, I2, I3 in one invocation under one cap. A retired
    probe or a typo must stop the run, not shrink it without saying so."""
    from eval import probe_run
    from eval.probes import PROBES, RETIRED

    got = [p.id for p in probe_run.select("D2,D4,D5,I1,I2,I3")]
    assert got == ["D2", "D4", "D5", "I1", "I2", "I3"]
    assert [p.id for p in probe_run.select("D2")] == ["D2"]
    assert {p.family for p in probe_run.select("inference")} == {"inference"}
    assert not {p.id for p in probe_run.select("derivation")} & set(RETIRED)
    assert probe_run.select(None) == list(PROBES)
    for bad in ("D1", "D2,D3", "D2,X9", "omission", ""):
        with pytest.raises(SystemExit):
            probe_run.select(bad)


# --- the turn log (review 61): every displayed turn, its cost, and the time to the first one --------


def test_the_turn_log_keeps_every_turn_with_its_usage_failed_and_scripted_included():
    """A failed seat's attempts are billed (F-7) and arrive as the absent turn's usage; the plant's
    scripted opening costs nothing and says so; a turn with no usage records zeros, not a blank."""
    from app.debate.llm import Usage
    from eval.probe_run import TurnLog

    log = TurnLog(dry=False)
    ok = {"stage": "openings", "round": 1, "seat": "dalio", "data": {"text": "x"}, "flags": {}}
    absent = {"stage": "openings", "round": 1, "seat": "lynch", "data": {"absent": True, "error": "bad_output"}, "flags": None}
    scripted = {"stage": "openings", "round": 1, "seat": "buffett", "data": {"text": "plant"}, "flags": {}}
    asyncio.run(log.save(ok, Usage(model="m", prompt_tokens=100, completion_tokens=50, cost_usd=0.01, seconds=1.234)))
    asyncio.run(log.save(absent, Usage(model="m", cost_usd=0.004)))
    asyncio.run(log.save(scripted, Usage(model="scripted")))
    asyncio.run(log.save({"stage": "verdict", "round": None, "seat": "chair", "data": {}}, None))
    asyncio.run(log.save({"stage": "final", "round": 3, "seat": "marks", "data": {"text": "y"}},
                         Usage(model="m", prompt_tokens=10, completion_tokens=5, cost_usd=None)))

    assert [t["seat"] for t in log.turns] == ["dalio", "lynch", "buffett", "chair", "marks"]
    assert log.turns[0]["usage"] == {"model": "m", "prompt_tokens": 100, "completion_tokens": 50, "cost_usd": 0.01,
                                     "seconds": 1.23, "scripted": False, "shared": False, "simulated": False}
    assert log.turns[1]["data"]["absent"] and log.turns[1]["usage"]["cost_usd"] == 0.004
    assert log.turns[2]["usage"]["scripted"] and log.turns[2]["usage"]["cost_usd"] == 0.0
    # review 62: nothing reported is unknown, and a paid call with tokens but no cost is unknown - never 0.0
    assert log.turns[3]["usage"]["cost_usd"] is None and log.turns[3]["usage"]["model"] is None
    assert log.turns[4]["usage"]["cost_usd"] is None and log.turns[4]["usage"]["prompt_tokens"] == 10
    assert not log.turns[4]["usage"]["scripted"] and not log.turns[4]["usage"]["simulated"]
    known = [t["usage"]["cost_usd"] for t in log.turns if t["usage"]["cost_usd"] is not None]
    assert round(sum(known), 6) == 0.014
    assert ok == {"stage": "openings", "round": 1, "seat": "dalio", "data": {"text": "x"}, "flags": {}}, "the turn was mutated"


def test_the_first_turn_time_is_the_first_turn_a_visitor_sees():
    """Stage events and an absent seat show nothing, so they do not stop the clock; the first real turn
    does, and later turns do not move it."""
    from eval.probe_run import TurnLog

    log = TurnLog(dry=True)
    log.emit({"type": "stage", "stage": "brief"})
    log.emit({"type": "turn", "turn": {"seat": "lynch", "data": {"absent": True}}})
    assert log.first_turn_seconds is None
    log.emit({"type": "turn", "turn": {"seat": "chair", "data": {"question": "q"}}})
    first = log.first_turn_seconds
    assert first is not None and first >= 0
    log.emit({"type": "turn", "turn": {"seat": "dalio", "data": {"text": "x"}}})
    assert log.first_turn_seconds == first


def _fake_paid_room(monkeypatch, fail_seat: str, fail_stage: str):
    """A six-seat room run through the real metering path (`metered`, a Budget) with a fake paid
    model: the named seat fails at the named stage, billed $0.004; the plant's opening is scripted;
    every other call costs $0.01. Returns the result and the plant seat."""
    from app.debate import roster
    from app.debate.llm import SeatError, Usage
    from app.debate.standin import make_asker
    from app.settings import get_settings
    from eval import probe_run
    from eval.budget import metered
    from eval.probes import BY_ID, PLANT_SEAT
    from eval.questions import CELLS, PROBE_CELLS
    from eval.run import load_pack

    probe = BY_ID["I3"]
    cell = {c.key: c for c in CELLS + PROBE_CELLS}[probe.cell]
    pack = load_pack(cell.ticker, "en")
    advisors = roster.sitting(roster.advisors(get_settings().debate_advisors), pack.ticker_key)
    standin = make_asker(pack, advisors, "en", cell.question)
    if fail_seat == "advisor":
        fail_seat = next(a.id for a in advisors if a.id != PLANT_SEAT)

    async def paid(**kw):
        if kw["stage"] == fail_stage and kw["seat"].id == fail_seat:
            raise SeatError("bad_output", usage=Usage(model=kw["model"], cost_usd=0.004))
        checked, _ = await standin(**kw)
        return checked, Usage(model=kw["model"], prompt_tokens=10, completion_tokens=5, cost_usd=0.01)

    monkeypatch.setattr(probe_run, "metered_asker", lambda _settings, budget: metered(paid, budget))
    r = asyncio.run(probe_run.run_room(probe, "A", 1, "en", planted=True, dry=False,
                                       budget=Budget(cap_usd=1000.00, attempts=3)))
    return r, fail_seat, advisors


def _recorded_cost(r) -> float:
    return round(sum(x["usage"]["cost_usd"] for x in r.turns + r.failed_calls if x["usage"]["cost_usd"] is not None), 6)


@needs_packs
def test_a_paid_room_records_every_turn_and_its_cost_adds_up_to_the_run(monkeypatch):
    """The reconciliation the comparison rests on, without a model. One advisor fails its opening
    (billed $0.004), the plant's opening is scripted (free), every other call costs $0.01. Every turn
    is kept, and the turns' costs add up exactly to the run's total."""
    from eval.probes import PLANT_SEAT

    r, failing, advisors = _fake_paid_room(monkeypatch, "advisor", "openings")
    assert r.ok, r.error
    assert r.failed_calls == [], "an advisor's failure is an absent turn, not a separate failed call"
    assert r.absent == [failing]
    stages = [t["stage"] for t in r.turns]
    assert stages.count("brief") == 1 and stages.count("faultlines") == 1 and stages.count("verdict") == 1
    assert stages.count("openings") == len(advisors), "every seat's opening, the absent and scripted ones included"
    assert all("usage" in t for t in r.turns)
    scripted = [t for t in r.turns if t["usage"]["scripted"]]
    assert [(t["seat"], t["stage"]) for t in scripted] == [(PLANT_SEAT, "openings")]
    assert not any(t["usage"]["simulated"] for t in r.turns)
    absent = next(t for t in r.turns if t["seat"] == failing and t["stage"] == "openings")
    assert absent["data"]["absent"] and absent["usage"]["cost_usd"] == 0.004
    assert _recorded_cost(r) == round(r.cost_usd, 6)
    assert r.first_turn_seconds is not None and r.first_turn_seconds <= r.seconds


@needs_packs
@pytest.mark.parametrize("stage", ["brief", "faultlines", "verdict"])
def test_a_failed_chair_call_is_kept_as_billed_and_the_cost_still_adds_up(monkeypatch, stage):
    """Review 62: the engine re-raises a Chair failure before saving any turn, so its billed attempts
    used to vanish from the record. They are kept in `failed_calls` - billed, not displayed - and the
    record still adds up to the run's total, at every Chair stage."""
    r, _, _ = _fake_paid_room(monkeypatch, "chair", stage)
    assert not r.ok and r.error
    assert [(f["stage"], f["seat"], f["error"]) for f in r.failed_calls] == [(stage, "chair", "bad_output")]
    assert r.failed_calls[0]["usage"]["cost_usd"] == 0.004
    assert not any(t["stage"] == stage for t in r.turns), "a failed Chair call is not a displayed turn"
    assert _recorded_cost(r) == round(r.cost_usd, 6)


@needs_packs
def test_a_dry_room_labels_its_turns_simulated_and_a_single_model_times_its_one_answer():
    from eval import probe_run
    from eval.probes import BY_ID

    r = asyncio.run(probe_run.run_room(BY_ID["I3"], "A", 1, "en", planted=False, dry=True,
                                       budget=Budget(cap_usd=1000.00, attempts=3)))
    assert r.ok, r.error
    assert len(r.turns) == 21, len(r.turns)  # 6 seats x 3 rounds and 3 Chair turns
    assert all(t["usage"]["simulated"] and not t["usage"]["scripted"] for t in r.turns)
    assert r.first_turn_seconds is not None

    b = asyncio.run(probe_run.run_single(BY_ID["I3"], "B", 1, "en", "anthropic/claude-sonnet-5.5", False, True,
                                         False, Budget(cap_usd=1000.00, attempts=3)))
    assert b.ok and b.turns == [] and b.first_turn_seconds == b.seconds


# --- arm P: the owner's two-model option (app/debate/presenter.py) ----------------------------------


def _presenter_room(monkeypatch, planted=False, bad_slice=None, fail=None, seen=None):
    """Arm P through run_room on the stand-in, with costs: each room call $0.01, each analyst or
    presenter call $0.05. `bad_slice` empties one advisor's opening so the engine refuses it; `fail`
    ("analyst" or a presenter stage) makes that call fail outright, billed $0.004. `seen` collects the
    analyst's and presenter's messages."""
    from app.debate import presenter, standin
    from app.debate.llm import SeatError, Usage
    from eval import probe_run
    from eval.probes import BY_ID

    real_asker, real_call = standin.make_asker, presenter.make_standin_call

    def costed_asker(*a, **k):
        inner = real_asker(*a, **k)

        async def ask(**kw):
            checked, _ = await inner(**kw)
            return checked, Usage(model=kw["model"], cost_usd=0.01)
        return ask

    def costed_call(standin_ask, advisors, chair):
        inner = real_call(standin_ask, advisors, chair)

        async def call(**kw):
            if seen is not None:
                seen.append((kw["role"], kw["stage"], kw["messages"]))
            if fail in (kw["role"], kw["stage"]):
                raise SeatError("bad_output", usage=Usage(model=kw["model"], cost_usd=0.004))
            checked, _ = await inner(**kw)
            if bad_slice and kw["role"] == "presenter" and kw["stage"] == "openings":
                checked[bad_slice] = {**checked[bad_slice], "text": ""}  # the engine refuses an empty answer
            return checked, Usage(model=kw["model"], cost_usd=0.05)
        return call

    monkeypatch.setattr(probe_run, "make_asker", costed_asker)
    monkeypatch.setattr(probe_run.presenter, "make_standin_call", costed_call)
    return asyncio.run(probe_run.run_room(BY_ID["I3"], "P", 1, "en", planted=planted, dry=True,
                                          budget=Budget(cap_usd=1000.00, attempts=3), engine="presenter"))


@needs_packs
def test_the_presenter_shows_every_stage_of_the_room_from_four_calls(monkeypatch):
    """The page's whole shape - the brief, six openings, the fault lines, six challenges, six final
    words, the answer - from one analyst call and three presenter calls. Each call's cost is on one
    turn and the other turns it served are marked shared, so the record adds up to the run."""
    r = _presenter_room(monkeypatch)
    assert r.ok, r.error
    stages = [t["stage"] for t in r.turns]
    assert {s: stages.count(s) for s in dict.fromkeys(stages)} == {
        "brief": 1, "openings": 6, "faultlines": 1, "debate": 6, "final": 6, "verdict": 1}
    assert r.calls == 4 and r.engine == "presenter"
    assert r.engine_stats == {"calls": 4, "fallbacks": 0, "round_failures": 0}
    assert sum(t["usage"]["shared"] for t in r.turns) == 17
    assert round(r.cost_usd, 6) == 0.2
    assert _recorded_cost(r) == round(r.cost_usd, 6)


@needs_packs
def test_the_presenter_shows_the_analyst_the_planted_opening_and_does_not_rewrite_it(monkeypatch):
    from eval.probes import BY_ID, PLANT_SEAT

    seen = []
    r = _presenter_room(monkeypatch, planted=True, seen=seen)
    assert r.ok, r.error
    analyst = next(m for role, _, m in seen if role == "analyst")
    assert BY_ID["I3"].text in analyst[1]["content"], "the analyst must plan in answer to the plant"
    openings = next(m for role, stage, m in seen if role == "presenter" and stage == "openings")
    shape = openings[1]["content"].split("REPLY with one JSON object in this shape:\n", 1)[1]
    assert f'"{PLANT_SEAT}"' not in shape, "the presenter does not write the pinned opening"
    assert [(t["seat"], t["stage"]) for t in r.turns if t["usage"]["scripted"]] == [(PLANT_SEAT, "openings")]
    assert _recorded_cost(r) == round(r.cost_usd, 6)


@needs_packs
def test_a_turn_the_engine_refuses_falls_back_to_the_room_for_that_turn_only(monkeypatch):
    r = _presenter_room(monkeypatch, bad_slice="dalio")
    assert r.ok, r.error
    assert r.engine_stats["fallbacks"] == 1 and r.calls == 5
    dalio = next(t for t in r.turns if t["seat"] == "dalio" and t["stage"] == "openings")
    assert dalio["data"].get("text") and not dalio["usage"]["shared"]
    assert _recorded_cost(r) == round(r.cost_usd, 6)


@needs_packs
def test_a_failed_presenter_round_falls_back_seat_by_seat_and_bills_the_failure_once(monkeypatch):
    r = _presenter_room(monkeypatch, fail="openings")
    assert r.ok, r.error
    assert r.engine_stats["round_failures"] == 1 and r.engine_stats["fallbacks"] == 6
    assert round(r.cost_usd, 6) == round(0.05 * 3 + 0.004 + 0.01 * 6, 6)
    assert _recorded_cost(r) == round(r.cost_usd, 6)


@needs_packs
def test_a_failed_analyst_ends_the_session_and_its_cost_is_kept(monkeypatch):
    r = _presenter_room(monkeypatch, fail="analyst")
    assert not r.ok and r.error
    assert [(f["stage"], f["usage"]["cost_usd"]) for f in r.failed_calls] == [("brief", 0.004)]
    assert r.turns == []
    assert _recorded_cost(r) == round(r.cost_usd, 6)


def test_the_presenter_is_off_unless_it_is_switched_on():
    from app.settings import Settings

    assert Settings().debate_engine == "room"
