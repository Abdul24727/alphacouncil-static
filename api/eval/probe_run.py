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
from .budget import Budget, BudgetExhausted, bound_for, metered
from .probes import BY_ID, FAMILIES, PLANT_SEAT, PROBES
from .questions import CELLS, PROBE_CELLS
from .run import FOUR_SEATS, ROOT, balance, council_asker, describe, load_pack

RESULTS = ROOT / "docs" / "eval" / "probe-results.jsonl"
# A dry run writes HERE, not into the results file. Both used to append to the same place with no
# field telling them apart, so previewing the plan with --dry and then running it for real would
# have mixed 48 stand-in answers into the record and `probe-report` would have scored them as
# findings. Noticed while measuring the plan's bound with --dry, before any paid run existed - so
# nothing was lost, which is the only reason this is a note and not an incident.
DRY_RESULTS = ROOT / "docs" / "eval" / "dry-probe-results.jsonl"
# Where --dry writes the prompts it assembled, so they can be read before any of them is paid for.
DRY = ROOT / "docs" / "eval" / "dry-prompts.txt"
# Both tuples: `eval run` iterates CELLS alone, so the probe-only cells added on 2026-10-28
# cannot change that harness's scope or make its 2026-10-27 results irreproducible.
CELL = {c.key: c for c in CELLS + PROBE_CELLS}

# Measured on beta 2026-10-27 over 60 runs. Arm E is modelled as two B passes plus the pack carried
# twice; it is corrected from the first real runs and only ever used to decide whether the NEXT run
# still fits under the cap, never to report a cost.
RUN_COST = {"A": 0.2257, "D": 0.1759, "B": 0.0292, "E": 0.0640}
# The WORST case per run, not the forecast above. MEASURED, not calculated beside the runner: these
# are the largest reservations `eval probe --dry` actually took over the whole plan, arm by arm,
# with every stand-in call going through the same `metered` wrapper a paid call does. Re-measure
# with:
#
#     uv run python -m eval probe --dry --arm A --arm B --arm D --arm E --repeats 2 --pause 0
#
# which prints the plan's total beside this prediction and says so if they have parted company.
# That command wrote 48 rows while there were six probes; with eighteen it writes 144.
#
# Round three asked for a bound from pricing x input size x output ceiling x retries, and got one
# that was 4-6x the forecast. Round four found three things missing from it - the 2,048-token
# reasoning allowance on every call, the growth of a retried prompt, and the fourth request
# `llm.ask` can issue without counting it as an attempt - plus a token floor of 2 characters that
# was an average rather than a bound. Correcting all four put these at 13-17x the forecast. The
# number got much worse because it got honest; see docs/council-review-response-2026-10-28-round4.md.
#
# RE-MEASURED 2026-10-28 for the fifth review round, which asked for the fourth request to be
# removed rather than priced. It is, so these fell to about 78% of the round-four figures - the
# only legitimate way a bound may fall: the request it was paying for cannot be issued any more.
# Round four's numbers were A 3.7805, D 2.8145, B 0.4066, E 0.8079.
#
# RE-MEASURED AGAIN over the EIGHTEEN probes of 2026-10-28, and essentially unchanged: the bound is
# per RUN, driven by the largest prompt an arm assembles, and the new probes' packs are the same
# five. The exact maxima were A 2.942344, D 2.190313, B 0.314634, E 0.625320, and each is rounded
# UP rather than to nearest, so the published figure covers the measurement instead of sitting a
# hair under it. The previous values were A 2.9423, D 2.1903, B 0.3146, E 0.6252 - under the
# measured maximum in the fourth decimal, which is harmless at this scale and wrong in principle.
RUN_BOUND = {"A": 2.9424, "D": 2.1904, "B": 0.3147, "E": 0.6254}

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
    dry: bool = False
    error: str | None = None
    seconds: float = 0.0
    cost_usd: float = 0.0
    # What the hard cap reserved for this run, summed over its calls. Saved beside the real cost so
    # the bound can be checked against the bill from the record itself rather than recomputed, and
    # so --dry publishes the plan's maximum from the same arithmetic a paid run enforces.
    bound_usd: float = 0.0
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
    """The same treatment for every arm: the engine's own checks, then the probe's own rubric.

    The rubric is applied to CLEAN runs too, for every family. It used to be applied only to the
    planted run and - for `omission` alone - to the clean one, so a derivation or inference control
    carried `outcome: ""`. Three of the measures the owner asked for on 2026-10-28 are unreadable
    without it, and the paired clean-versus-planted comparison read that empty field and silently
    reported a base rate of zero everywhere. Found while building that comparison.

    The rubric means the same thing on a clean run, which is why it transfers rather than needing a
    second scorer:

    * the CORRECT outcome is **clean-control accuracy** - the right answer reached with nothing
      planted. Where it is already high, the planted share cannot separate two arms, and that is a
      fact about the probe which has to be visible.
    * a WRONG outcome is a **false positive**: a figure the arm asserted that nobody planted. On a
      clean run `probe.wrong` cannot have been adopted from anywhere, so a hit is the arm's own
      invention.
    * DECLINED is an **inappropriate refusal** wherever the pack does support the figure - which is
      the case for every derivation probe by construction, since that is what makes it a derivation.
    """
    c = checks.Checked(pack.numbers(), pack.seen())
    r.answer_words = len(c.text(r.answer, limit=8_000).split())
    r.unverified = c.unverified
    r.outcome, r.evidence = S.score(probe, r.answer, r.headline)
    if not r.planted:
        r.gate_hits = S.engaged(probe, r.answer)
    return r


def metered_asker(settings: Any, budget: Budget):
    """The cap applied to every llm.ask. The wrapper itself lives in budget.py with the call
    injected, so it can be tested without importing the application."""

    async def call(*, model: str, messages: Any, max_tokens: int, temperature: float, check: Any, **_: Any):
        return await llm.ask(settings, model, messages, max_tokens=max_tokens, temperature=temperature, check=check)

    return metered(call, budget)


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


async def run_room(probe: Any, arm: str, repeat: int, locale: str, planted: bool, dry: bool, roster_spec: str | None = None, budget: Budget | None = None) -> ProbeResult:
    settings = get_settings()
    cell = CELL[probe.cell]
    pack = load_pack(cell.ticker, locale)
    advisors = roster.sitting(roster.advisors(roster_spec or settings.debate_advisors), pack.ticker_key)
    chair = roster.chair()
    r = ProbeResult(arm=arm, probe=probe.id, family=probe.family, cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=planted, ok=False, dry=dry)

    if planted and PLANT_SEAT not in {a.id for a in advisors}:
        # Loud, because the quiet version is worse than a crash: the run would be recorded planted,
        # nothing would be planted, and the arm would look like the one room that never fails.
        raise SystemExit(f"{arm}/{probe.id}: the plant seat {PLANT_SEAT!r} does not sit in this roster ({[a.id for a in advisors]})")

    ctx = Context(settings=settings, pack=pack, question=cell.question, locale=locale, advisors=advisors, chair=chair, debate_rounds=1)
    # ONE metering path, dry or paid. The engine assembles its real prompts either way and hands
    # them to the asker, so wrapping the stand-in meters the true prompt sizes at no cost - which is
    # what lets --dry report the plan's hard bound as the sum of the reservations a paid run would
    # actually take, rather than as a figure computed alongside the runner and liable to drift.
    if dry:
        base, calls = metered(make_asker(pack, advisors, locale, cell.question), budget) if budget \
            else (make_asker(pack, advisors, locale, cell.question), {"n": 0, "cost": 0.0})
    else:
        base, calls = metered_asker(settings, budget) if budget else council_asker(settings, {})
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
    r.cost_usd, r.calls = round(calls["cost"], 6), int(calls["n"])
    r.bound_usd = round(calls.get("bound", 0.0), 6)
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


def _note(probe: Any, pack: Any) -> str:
    """The planted claim, framed for a single-model arm exactly as the room frames it.

    This read "AN ANALYST'S NOTE ON THIS COMPANY" until 2026-10-28. The content was already
    identical across arms and `finish` already applied one scorer to all of them, but the
    PROVENANCE was not: the room shows its Chair `THE ADVISORS' ANSWERS:` with the claim
    attributed to a seated colleague (`engine._line`), while a single-model arm was shown an
    outside analyst's note. Provenance is exactly the cue that changes how far a reader defers to
    a claim, so the experiment would have attributed part of any difference to configuration when
    it belonged to framing. Checked at the owner's request that the standalone Chairman receive a
    fair equivalent of each injected claim; it did not, and this is the fix.

    Same header, same attribution, same text, one seat where the room has six. What is left
    different between the arms is the configuration itself - five more seats and a round of
    challenges - which is what the comparison exists to measure.
    """
    # Through the SAME checker the engine runs a seat's opening through (engine, the openings
    # stage: Checked.text at 200 for the headline and 4,000 for the text). Without it the room's
    # copy of the plant carried the citation tags the checker adds - '[P1] [P2]' - and the single
    # model's copy did not, so the room was shown a BETTER-SOURCED version of the same false
    # claim. That is the direction that matters: tags make a claim look checked.
    c = checks.Checked(pack.numbers(), pack.seen())
    headline, text = c.text(probe.headline, 200), c.text(probe.text, 4_000)
    return f"THE ADVISORS' ANSWERS:\n- {roster.load(PLANT_SEAT).surname}: {headline} {text}"


async def run_single(probe: Any, arm: str, repeat: int, locale: str, model: str, planted: bool, dry: bool, second_pass: bool, budget: Budget) -> ProbeResult:
    settings = get_settings()
    cell = CELL[probe.cell]
    pack = load_pack(cell.ticker, locale)
    chair = roster.chair()
    r = ProbeResult(arm=arm, probe=probe.id, family=probe.family, cell=cell.key, ticker=cell.ticker, repeat=repeat, planted=planted, ok=False, dry=dry)
    system = _system(pack, locale)

    async def call(*, model: str, messages: Any, max_tokens: int, temperature: float, check: Any, **_: Any):
        if dry:
            # No model, and still the whole path: the prompts are assembled for real and written
            # out, the critique is threaded into the second pass, and the answer is scored. Without
            # this, --dry left arm E - the newest and most important arm - entirely unexercised.
            DRY.parent.mkdir(parents=True, exist_ok=True)
            with DRY.open("a", encoding="utf-8") as fh:
                fh.write(f"\n{'=' * 100}\n{arm} {probe.id} {'planted' if planted else 'clean'} pass {int(spend['n']) + 1}\n")
                for m in messages:
                    fh.write(f"--- {m['role']} ({len(m['content'])} chars) ---\n{m['content']}\n")
            canned: dict[str, Any] = {
                "problems": [f"stand-in: the note's figure for {probe.metric[0]} is not in the pack"],
                "headline": f"stand-in answer for {probe.id}",
                "answer": "A stand-in answer. " + probe.truth,
                "gaps": ["stand-in gap"],
                "disagreements": [],
            }
            return check(canned), llm.Usage(model="stand-in")
        return await llm.ask(settings, model, messages, max_tokens=max_tokens, temperature=temperature, check=check)

    # The SAME wrapper arms A and D use. These two arms used to meter themselves inline, and that is
    # how they came to call budget.take() with no bound at all - reserving a flat $0.09 where the
    # real upper bound is several times that, which an independent review found on 2026-10-28. The
    # fix is structural rather than a corrected argument: there is one metering path now, so there
    # is nowhere left to forget the bound.
    asker, spend = metered(call, budget)

    async def ask(messages: list[dict[str, str]], check: Any) -> dict[str, Any]:
        raw, _usage = await asker(messages=messages, model=model, max_tokens=MAX_TOKENS["verdict"],
                                  temperature=TEMPERATURE["chair"], check=check)
        return raw

    started = time.monotonic()
    try:
        critique: list[str] = []
        if second_pass and planted:
            # Pass one: the same model, asked only to check the note against the pack. This is the
            # room's round of challenges with nobody else in the room.
            parts = [
                f"THE MEMBER'S QUESTION: {cell.question}",
                _note(probe, pack),
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
            parts.append(_note(probe, pack))
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
    r.cost_usd, r.calls = round(spend["cost"], 6), int(spend["n"])
    r.bound_usd = round(spend.get("bound", 0.0), 6)
    return finish(r, pack, probe)


# --- the run -----------------------------------------------------------------------------------


async def run(arms: list[str], repeats: int, locale: str, clean: bool, dry: bool, single_model: str,
              pause: float, only: str | None, four_seats: str, cap_usd: float,
              clean_arms: list[str] | None = None) -> None:
    out = DRY_RESULTS if dry else RESULTS
    out.parent.mkdir(parents=True, exist_ok=True)
    if dry:
        # REBUILT, not appended to. .gitignore has always said this of the prompt dump - "rebuilt
        # by any dry run" - and the results file has to be rebuilt too, because it is committed so
        # that the published hard bound can be checked against it. Both were opened "a", like the
        # paid record, so every preview of the plan doubled them: a second --dry took the committed
        # results from 48 rows to 96 and the prompt dump from 816K to 1.6M, which means a reviewer
        # re-running --dry to verify the bound was corrupting the record they were verifying. Found
        # 2026-10-28 by running --dry to re-check the bound before quoting it to the owner. Done
        # once here rather than at each open, which would leave only the last probe's rows. The
        # PAID record still appends: a run that stops part way has bought what it already wrote.
        out.write_text("", encoding="utf-8")
        DRY.parent.mkdir(parents=True, exist_ok=True)
        DRY.write_text("", encoding="utf-8")
    chosen = [p for p in PROBES if only is None or p.id == only or p.family == only]
    if not chosen:
        raise SystemExit(f"no probe matches {only!r}: ids are {[p.id for p in PROBES]}, families {list(FAMILIES)}")

    # (arms, repeats, planted) for each phase of ONE experiment. `--clean-arms` adds the validity
    # gate's control phase to the same run instead of leaving it to a second command with a second
    # cap; without it this is the single phase it always was.
    phases: list[tuple[list[str], int, bool]] = [(arms, repeats, not clean)]
    if clean_arms:
        phases.append((clean_arms, 1, False))
    planned = sum(reps * len(chosen) * sum(RUN_COST.get(a, 0.25) for a in ph) for ph, reps, _ in phases)
    worst = sum(reps * len(chosen) * sum(RUN_BOUND.get(a, 1.50) for a in ph) for ph, reps, _ in phases)
    n = sum(reps * len(chosen) * len(ph) for ph, reps, _ in phases)

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
        print(f"balance ${started_at:.2f}; {n} runs")
        print(f"  forecast   ${planned:.2f}   from the measured history of 2026-10-27")
        print(f"  hard bound ${worst:.2f}   pricing x prompt size x output ceilings x {Budget(0).attempts} retries")
        print(f"  cap        ${cap_usd:.2f}   enforced against the BOUND, per call")
        if worst > cap_usd:
            # The distinction the second review round asked for, enforced rather than described. A
            # cap set to the forecast is not a guarantee: it would refuse this run on its first
            # call, because one room run alone bounds at about six times its forecast. A cap that
            # IS a guarantee has to cover the worst case, and then it never binds in a normal run.
            raise SystemExit(
                f"refusing to start: the cap is ${cap_usd:.2f} but this plan's worst case is "
                f"${worst:.2f}, so the cap could not be honoured as a hard cap - it would refuse a "
                f"call part way through.\n"
                f"  Either raise --cap-usd to at least ${worst:.0f} (the run is still only expected "
                f"to cost ${planned:.2f}; the cap is there to make a catastrophe impossible, not to "
                f"predict the bill),\n"
                f"  or shorten the plan with --repeats or --only."
            )
        if planned > started_at:
            raise SystemExit(
                f"refusing to start: the plan costs about ${planned:.2f} and only ${started_at:.2f} is left. "
                f"Add about ${planned - started_at:.2f} first - a run that stops part way is a half-powered "
                "result bought at full price."
            )

    # What this process has actually been charged, summed from the per-call costs the provider
    # returns with every response. It does not lag, and it does not depend on the account endpoint
    # being reachable - which the balance does. Both caps apply; either one stops the run.
    spent_local = 0.0
    bound_local = 0.0
    # One cap for the whole run, applied per CALL rather than per run, so retries and calls
    # in flight are covered. It needs no provider endpoint: it is arithmetic over what this
    # process has been billed (budget.py).
    #
    # BOTH ceilings are passed. The forecast ceiling is 1.5x the measured history - high enough not
    # to trip on ordinary variance, low enough to stop a retry storm or a repriced model long before
    # the hard cap would. The third review round found it was never passed to the Budget at all:
    # this function computed `planned` and then built `Budget(cap_usd)`, so the second ceiling
    # existed in the class, in its tests and in the documentation, and nowhere in a run. A control
    # that is described but not wired is worse than one that was never claimed.
    #
    # In dry mode the cap is set out of reach on purpose: --dry's job is to report the plan's hard
    # bound, and it can only do that if every stand-in call takes the same reservation a paid call
    # would. Nothing is spent either way.
    budget = Budget(
        max(worst, cap_usd) * 10 if dry else cap_usd,
        expect_usd=None if dry else round(planned * 1.5, 4),
    )

    # TWO PHASES, ONE BUDGET. The pre-registered experiment is 54 planted runs and 12 clean
    # controls (docs/council-test-design-2026-10-28.md), and until the fifth independent review
    # round each phase was a separate invocation of this command - so each built its own Budget
    # with its own cap and the combined spend was bounded by nothing at all. Two $94 caps are not
    # a $94 cap. Both phases now run inside one Budget, and `planned`, `worst` and `n` above are
    # summed over both, so the figure quoted to whoever authorises the run is the figure the run
    # is actually held to.
    for phase_arms, phase_repeats, planted in phases:
        if len(phases) > 1:
            label = "planted" if planted else "clean controls"
            runs_here = phase_repeats * len(chosen) * len(phase_arms)
            print()
            print(f"--- {label}: arms {','.join(phase_arms)}, {phase_repeats} repeat(s), {runs_here} runs ---")
        for repeat in range(1, phase_repeats + 1):
            for probe in chosen:
                for arm in phase_arms:
                    if not dry and started_at is not None:
                        if spent_local + RUN_COST.get(arm, 0.25) > cap_usd:
                            print(f"STOPPING: ${spent_local:.2f} charged so far, one more {arm} run would pass the ${cap_usd:.2f} cap")
                            return
                        now = balance()
                        if now is None:
                            # FAIL CLOSED. The old code checked `if now is not None`, so a single failed
                            # balance read silently skipped the cap and the loop spent on. Found by an
                            # independent review, 2026-10-28. A guard that stops guarding when its
                            # input is missing is the F-10 fault again: trusted, and doing nothing.
                            print(f"STOPPING: the balance could not be read before the next {arm} run, "
                                  f"so the cap cannot be checked. ${spent_local:.2f} charged so far.")
                            return
                        spent = started_at - now
                        if spent + RUN_COST.get(arm, 0.25) > cap_usd:
                            print(f"STOPPING: ${spent:.2f} spent, one more {arm} run would pass the ${cap_usd:.2f} cap")
                            return
                        if now < RUN_COST.get(arm, 0.25) * 2:
                            print(f"STOPPING: ${now:.2f} left on the account, too little for another {arm} run")
                            return
                    if arm == "A":
                        r = await run_room(probe, "A", repeat, locale, planted, dry, budget=budget)
                    elif arm == "D":
                        r = await run_room(probe, "D", repeat, locale, planted, dry, roster_spec=four_seats, budget=budget)
                    elif arm == "E":
                        r = await run_single(probe, "E", repeat, locale, single_model, planted, dry, second_pass=True, budget=budget)
                    else:
                        r = await run_single(probe, "B", repeat, locale, single_model, planted, dry, second_pass=False, budget=budget)
                    spent_local += r.cost_usd
                    bound_local += r.bound_usd
                    # should_stop() is ENFORCED here, not consulted. It used to be neither: the loop
                    # checked only `budget.refused`, so a recorded overrun - a charge above its own
                    # bound, or a prompt denser than the token ceiling, either of which means the cap
                    # has stopped being a guarantee - left the run going. Found by an independent
                    # review, 2026-10-28. `Budget.take` now refuses on the same condition, so this is
                    # the second of two gates rather than the only one.
                    stop = budget.should_stop()
                    if stop or budget.refused:
                        print(f"STOPPING: {stop or f'the per-call cap refused a call ({budget})'}. "
                              f"Nothing further is attempted.")
                        with out.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
                        return
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
                    await asyncio.sleep(pause)
                    mark = "ok " if r.ok else "FAIL"
                    tail = f" {r.outcome:12} {','.join(r.evidence[:3])}" if r.planted else f" gate:{','.join(r.gate_hits[:3]) or 'NONE'}"
                    print(
                        f"{mark} {arm} {probe.id} {probe.family[:5]:5} {r.cell:14} r{repeat} {r.seconds:>6.1f}s "
                        f"${r.cost_usd:>7.4f} {r.answer_words:>4}w{tail}" + (f"  {r.error}" if r.error else "")
                    )

    # The plan's maximum, measured rather than asserted: every stand-in call above took the same
    # reservation a paid call would, so this total IS the sum of the reservations the runner would
    # enforce. Priority 6 of the third review round asked for exactly this agreement, and the drift
    # line below is what keeps it - RUN_BOUND is a published constant, and a published constant that
    # nothing checks is a comment.
    if dry:
        print(f"\nplan bound ${bound_local:.4f} over {n} runs, measured from the reservations taken")
        print(f"  RUN_BOUND predicts ${worst:.4f}")
        # One-sided on purpose. RUN_BOUND holds each arm's WORST run, so the prediction should sit a
        # little above a plan's total and that is correct. The dangerous direction is the other one:
        # a measured total above the published maximum means the figure quoted to whoever authorised
        # the spend was too low, and that is a failure of the guarantee rather than a rounding note.
        if bound_local > worst:
            print(f"  TOO LOW: the published maximum is ${worst:.2f} and this plan reserves "
                  f"${bound_local:.2f}. Update RUN_BOUND before quoting a maximum to anyone.")
        elif worst > bound_local * 1.2:
            print(f"  loose by {(worst / bound_local - 1) * 100:.0f}%: still a bound, but it asks for "
                  f"more headroom than the plan needs. Worth re-measuring.")
        else:
            print("  consistent: the published maximum covers this plan and is not padded")
