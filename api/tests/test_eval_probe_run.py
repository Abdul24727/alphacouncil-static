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
        asyncio.run(probe_run.run(["B"], 1, "en", False, True, "anthropic/claude-sonnet-5.5",
                                  0.0, "D1", FOUR_SEATS, 1.0))
        return (len(results.read_text(encoding="utf-8").strip().splitlines()),
                len(prompts.read_text(encoding="utf-8")))

    first = preview()
    assert first[0] == 1, f"one arm, one probe, one repeat wrote {first[0]} rows"
    second = preview()
    assert second == first, (
        f"a second identical dry run left {second[0]} rows and {second[1]} characters rather than "
        f"{first[0]} and {first[1]}: the dry outputs are appended to, not rebuilt")
