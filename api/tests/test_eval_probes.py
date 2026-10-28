"""The pre-registration, enforced: every probe's rubric and expected outcomes, for all eighteen.

The owner's instruction of 2026-10-28 was to pre-register the scoring criteria and expected outcomes
for every new probe BEFORE running model comparisons. This file is that registration in executable
form, which is the only form that cannot quietly stop being true:

* each probe's own pre-registered correct answer (`truth`) must reach its family's CORRECT outcome;
* each probe's plant must score as adopting it;
* no probe's correct answer may carry a wrong-figure marker;
* no planted figure may be a written form of any value in its own pack, because the propagation
  test matches whole numbers and a collision would score a correct answer as having adopted the
  plant;
* every probe must sit on a cell that exists, on a pack that exists, with the plant seat seated in
  both rosters under comparison.

What this file does NOT establish, and what no offline test can: the CLEAN BASE RATE of the twelve
probes added on 2026-10-28. The only model answers on disk were collected on 2026-10-27, before
those probes existed, and eleven of them sit on cells that run never touched. Their detectors are
calibrated against their own truth and plant text and against nothing a model actually wrote. That
is the first thing the live pilot buys, and until it does, a low "handled" rate on a new probe
cannot be told apart from a probe that is simply hard to engage with.

Nothing here makes a model call.
"""

import json
import re

import pytest

from eval import score as S
from eval.probes import PLANT_SEAT, PROBES
from eval.questions import CELLS, PROBE_CELLS

CELL = {c.key: c for c in CELLS + PROBE_CELLS}
NUMBER_ONLY = re.compile(r"-?\d+(?:\.\d+)?")
IDS = [p.id for p in PROBES]


def test_there_are_eighteen_probes_evenly_split():
    """Eighteen because six could only see a 33-point gap between six seats and four, and the only
    prior available puts the gap at zero. Evenly split so the pooled metric cannot be carried by one
    family."""
    assert len(PROBES) == 18, IDS
    families = {}
    for p in PROBES:
        families[p.family] = families.get(p.family, 0) + 1
    assert families == {"derivation": 9, "inference": 9}, families
    assert len(set(IDS)) == 18, "duplicate probe id"


def test_every_probe_tests_a_distinct_failure_mode():
    """The owner's instruction was distinct failure modes rather than variations of one error. A
    cheap structural proxy for that: no two probes may share both a cell and a family, because that
    is what a variation of the same error on the same question looks like."""
    seen = {}
    for p in PROBES:
        key = (p.cell, p.family)
        assert key not in seen, f"{p.id} and {seen[key]} are the same family on the same cell"
        seen[key] = p.id


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_the_pre_registered_correct_answer_scores_as_handling_it(probe):
    """The registration's first claim. A probe whose own correct answer does not score as correct is
    not measuring what it says: it would mark a right answer wrong in every arm equally, which looks
    like a hard probe rather than a broken one."""
    outcome, evidence = S.score(probe, probe.truth, "The pack does not support that")
    assert outcome == S.CORRECT[probe.family], f"{probe.id}: {outcome} - {evidence}"


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_the_plant_scores_as_adopting_it(probe):
    """The second claim, and the one that makes a zero meaningful. If the plant's own text does not
    score as adopted, then an arm that swallowed it whole would still score well and the probe
    cannot detect the failure it was built for."""
    want = "ADOPTED" if probe.family == "derivation" else "ADOPTS"
    outcome, evidence = S.score(probe, probe.text, probe.headline)
    assert outcome == want, f"{probe.id}: {outcome} - {evidence}"


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_the_correct_answer_carries_no_wrong_marker(probe):
    """A correct answer that also trips a wrong-figure marker scores MIXED, not CORRECTED - so this
    is the test that keeps the MIXED outcome from quietly costing every arm its points. D2 failed it
    before `band_metric` existed, and D4 and I9 failed it on the day the twelve were written:
    `right` carried bare words the plant used to deny the same conclusion, and `wrong` carried a
    bare "expensive" that the correct answer needs in order to name what it rejects."""
    _, evidence = S.score(probe, probe.truth, "The pack does not support that")
    assert not [e for e in evidence if e.startswith(("wrong:", "incorrect:"))], f"{probe.id}: {evidence}"


def _written_forms(ticker: str) -> set:
    """Every way an answer might plausibly write a value this pack publishes."""
    from eval.run import PACKS

    data = json.loads((PACKS / f"{ticker}.en.json").read_text(encoding="utf-8"))
    out: set = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            for v in (node, abs(node)):
                out.update({str(v), f"{v:.0f}", f"{v:.1f}", f"{v:.2f}"})

    walk(data)
    return out


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_no_planted_figure_collides_with_its_own_pack(probe):
    """The constraint `questions.py` states and this enforces: "-15.37 rounded to 15.4 would
    otherwise have scored a CORRECT answer as a propagated error". D7's planted figure was 1.79 only
    because of this check - it was 1.8 first, which is how an answer would write that pack's return
    on assets of -1.85, so a correct answer that mentioned ROA could have scored as having adopted
    the plant."""
    from eval.run import PACKS

    ticker = CELL[probe.cell].ticker
    if not (PACKS / f"{ticker}.en.json").exists():
        pytest.skip(f"no saved pack for {ticker}")
    forms = _written_forms(ticker)
    collisions = [w for w in probe.wrong
                  if NUMBER_ONLY.fullmatch(w) and (w in forms or w.lstrip("-") in forms)]
    assert not collisions, f"{probe.id} plants {collisions}, which {ticker} itself publishes"


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_every_probe_is_wired_to_a_real_cell_and_a_real_pack(probe):
    """Cheap, and it has already earned its place twice in this project: a probe naming a cell that
    does not exist, or a cell naming a ticker with no saved pack, fails at run time after the first
    model call has been paid for."""
    from eval.run import PACKS

    assert probe.cell in CELL, f"{probe.id} names cell {probe.cell!r}, which does not exist"
    cell = CELL[probe.cell]
    assert (PACKS / f"{cell.ticker}.en.json").exists(), f"{probe.id}: no pack for {cell.ticker}"
    assert probe.truth.strip(), f"{probe.id} has no pre-registered correct answer"
    assert probe.metric, f"{probe.id} has no metric words, so nothing can be bound to it"


def test_the_plant_seat_sits_in_both_rosters_under_comparison():
    """Arm A is six seats and arm D is four; a plant carried by a seat that sits in only one of them
    would mark every run of the other `planted=True` with nothing planted - a room that never
    propagates an error because it was never given one. `questions.py` records that this is why the
    plant is Buffett and not Dalio."""
    from app.debate import roster
    from app.settings import get_settings
    from eval.run import FOUR_SEATS

    six = {a.id for a in roster.advisors(get_settings().debate_advisors)}
    four = {a.id for a in roster.advisors(FOUR_SEATS)}
    assert PLANT_SEAT in six and PLANT_SEAT in four, (PLANT_SEAT, six, four)


@pytest.mark.parametrize("probe", PROBES, ids=IDS)
def test_no_advisor_recuses_on_any_probe_ticker(probe):
    """`roster.sitting` drops a seat tied to the company under discussion. On a ticker where one
    recused, arm A would silently be a five-seat room for that probe only, and the comparison the
    whole experiment rests on would not be six against four. 4280 Kingdom Holding is excluded from
    the bench for exactly this reason."""
    from app.debate import roster
    from app.settings import get_settings
    from eval.run import FOUR_SEATS, load_pack

    pack = load_pack(CELL[probe.cell].ticker, "en")
    six = roster.advisors(get_settings().debate_advisors)
    four = roster.advisors(FOUR_SEATS)
    assert len(roster.sitting(six, pack.ticker_key)) == 6, f"{probe.id}: arm A is not six seats"
    assert len(roster.sitting(four, pack.ticker_key)) == 4, f"{probe.id}: arm D is not four seats"

# --- the pack must still support each band-scored derivation -----------------------------------
#
# The pack fields each band-scored probe's registered derivation rests on, written down because
# `docs/evidence-pipeline-inspection-2026-10-28.md` found some Tadawul gauge values ORPHANED:
# computed from an income statement that is no longer in the database, and not recomputed since.
# 4061's `net_margin` and `ps` are two of them, and D3 and D6 derive their whole answer from them.
# The day 4061 is recomputed those two go to `missing_inputs`, the pack then holds no revenue
# figure for 4061 at all, net margin stops being derivable rather than merely changing, and the
# only remaining per-share route (ROE -4.11% x book 7.76 = -0.32) falls OUTSIDE D3's band. Both
# probes would become unanswerable while the scorer recorded the failure as the arm's.
#
# This is the alarm. It is not a scoring criterion and it changes no registration: it asserts only
# that the inputs the registration already quotes are still present. A probe that loses its inputs
# must be re-registered or retired by the owner BEFORE a paid run, not silently scored.
DERIVATION_INPUTS = {
    "D1": ("valuation.eps_ttm", "dividends>=4"),
    "D2": ("valuation.roe_pct", "valuation.book_value", "valuation.pb"),
    "D3": ("quote.last_price", "gauge.ps", "gauge.net_margin", "valuation.roe_pct"),
    "D4": ("valuation.roe_pct", "valuation.roa_pct", "gauge.debt_equity"),
    "D5": ("quote.last_price", "valuation.book_value", "valuation.pb"),
    "D6": ("gauge.gross_margin", "gauge.net_margin", "valuation.roe_pct"),
    "D8": ("quote.last_price", "valuation.dividend_yield_pct", "dividends>=4"),
}


def _pack_field(pack, path: str):
    """Resolve one DERIVATION_INPUTS key against a loaded pack. Returns the value, or None when
    the field is absent, null, or (for a gauge) carries any status other than `ok`/`published` -
    which is the case this test exists to catch."""
    if path == "dividends>=4":
        rows = (pack.data.get("P3") or {}).get("dividends") or []
        return len(rows) if len(rows) >= 4 else None
    where, key = path.split(".", 1)
    if where in ("quote", "valuation"):
        return ((pack.data.get("P1") or {}).get(where) or {}).get(key)
    if where == "gauge":
        for group in (pack.data.get("P2") or {}).get("groups") or []:
            for metric in group.get("metrics") or []:
                if metric.get("key") == key:
                    if metric.get("status") not in ("ok", "published"):
                        return None
                    return metric.get("value")
        return None
    raise AssertionError(f"unknown derivation input {path!r}")


@pytest.mark.parametrize("probe", [p for p in PROBES if p.band], ids=[p.id for p in PROBES if p.band])
def test_the_pack_still_supports_each_band_scored_derivation(probe):
    from eval.run import load_pack

    inputs = DERIVATION_INPUTS.get(probe.id)
    assert inputs, f"{probe.id} is band-scored but its derivation inputs are not registered"
    pack = load_pack(CELL[probe.cell].ticker, "en")
    missing = [path for path in inputs if _pack_field(pack, path) is None]
    assert not missing, (
        f"{probe.id} on {CELL[probe.cell].ticker}: its registered derivation quotes "
        f"{', '.join(missing)}, which the pack no longer carries. The probe cannot be answered "
        f"from the pack, so a paid run would score every arm's failure as the arm's. "
        f"Re-register or retire it before spending."
    )


def test_every_band_scored_probe_has_registered_derivation_inputs():
    """A new band-scored probe added without an entry above would be guarded by nothing."""
    banded = {p.id for p in PROBES if p.band}
    assert banded == set(DERIVATION_INPUTS), (
        f"band-scored without inputs: {sorted(banded - set(DERIVATION_INPUTS))}; "
        f"registered but no longer band-scored: {sorted(set(DERIVATION_INPUTS) - banded)}"
    )
