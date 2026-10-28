"""The report's judgement calls, which had no tests at all until 2026-10-28.

Three of them carry claims that have been put in front of the owner in writing
(`docs/council-test-plan-final-2026-10-28.md`), so they are tested rather than asserted:

* controls are NOT optional - a probe with no clean run for a compared arm is void for every arm,
  which is why arm D's own control phase has to be paid for;
* the primary comparison is A vs D and is read as a DIFFERENCE, never as PASS;
* the paired reading is printed, because the primary metric sits at a ceiling on half the probes and
  the pooled line on its own would invite a reader to call a tie a finding.

Nothing here makes a model call or reads the network.
"""

import json

import pytest

from eval.probe_report import gate, report
from eval.probes import BY_ID
from eval.score import CORRECT, WRONG


def row(probe: str, arm: str, planted: bool, outcome: str, *, gate_hits=("metric",), ok=True):
    """One result row in the shape `probe_run` writes."""
    p = BY_ID[probe]
    return {
        "arm": arm, "probe": probe, "family": p.family, "cell": p.cell, "ticker": "2222_TADAWUL",
        "repeat": 1, "planted": planted, "ok": ok, "dry": False, "error": None,
        "seconds": 1.0, "cost_usd": 0.01, "bound_usd": 0.4, "calls": 1,
        "headline": "a headline", "answer": "an answer", "gaps": [], "disagreements": [],
        "absent": [], "critique": [], "answer_words": 100, "unverified": [],
        "outcome": outcome, "evidence": [], "gate_hits": list(gate_hits), "challenged": False,
    }


ARMS = ("A", "B", "D")


def test_a_probe_with_no_clean_run_for_a_compared_arm_is_void_for_every_arm():
    """Why arm D's control phase is not an optional saving. Arm E could share arm B's clean control,
    so the old A/B/E plan needed 12; D is a different room and needs its own 6. Skipping them would
    not save $2.58, it would void all six probes - the comparison is paired, so a probe missing one
    arm's control is unreadable for the others too."""
    rows = [row("D1", a, True, "CORRECTED") for a in ARMS]
    rows += [row("D1", a, False, "CORRECTED") for a in ("A", "B")]      # D's control missing
    keep, notes = gate(rows, ARMS)
    assert "D1" not in keep
    assert any("no clean run for D" in n for n in notes), notes

    rows += [row("D1", "D", False, "CORRECTED")]
    keep, notes = gate(rows, ARMS)
    assert "D1" in keep, notes


def test_a_clean_answer_that_never_engages_the_metric_voids_the_probe():
    """The gate's other half: a control that does not reach for the metric cannot establish a base
    rate, so the probe says nothing about what the plant changed."""
    rows = [row("D1", a, True, "CORRECTED") for a in ARMS]
    rows += [row("D1", a, False, "SILENT", gate_hits=()) for a in ARMS]
    keep, notes = gate(rows, ARMS)
    assert "D1" not in keep
    assert any("never raises" in n for n in notes), notes


def _report_text(tmp_path, rows, capsys):
    path = tmp_path / "probe-results.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    report(path)
    return capsys.readouterr().out


def _full_rows(a_outcome: str, d_outcome: str, b_outcome: str, clean: str = "CORRECTED",
               repeats: int = 3):
    """Rows for three derivation probes across the three arms, planted and clean.

    `repeats` is 3 by default for a reason worth recording: at ONE repeat this is n = 3 an arm, and a
    total reversal - 3/3 against 0/3 - gives Fisher p = 0.10 and is correctly reported as no
    measurable difference. The first version of these tests used n = 3 and could not produce a
    detectable difference at all, which is the plan's own power finding arriving uninvited.
    """
    rows = []
    for probe in ("D1", "D2", "D3"):
        for _ in range(repeats):
            for arm, out in (("A", a_outcome), ("D", d_outcome), ("B", b_outcome)):
                rows.append(row(probe, arm, True, out))
        for arm in ("A", "D", "B"):
            rows.append(row(probe, arm, False, clean))
    return rows


def test_the_primary_comparison_is_a_against_d_and_is_never_called_pass(tmp_path, capsys):
    """The owner's revision, and the reading that goes with it. A tie between six seats and four is
    not a PASS and not a FAIL - it is a failure to detect at this sample size, and the report has to
    say which, because the whole six-versus-four decision hangs on not confusing the two."""
    out = _report_text(tmp_path, _full_rows("CORRECTED", "CORRECTED", "DECLINED"), capsys)
    primary = next(line for line in out.splitlines() if "PRIMARY" in line)
    assert "A" in primary and "D" in primary, primary
    assert "no measurable difference" in primary, primary
    assert "NOT equivalence" in primary, primary
    assert "PASS" not in primary, primary
    # and the superiority tests are still there, below it
    assert "second : A" in out and "third  : D" in out, out


def test_a_real_difference_between_six_and_four_is_reported_as_one(tmp_path, capsys):
    """The other direction: when the arms do differ, the primary names which is higher. This is the
    result that would stop a move to four seats."""
    out = _report_text(tmp_path, _full_rows("CORRECTED", "SILENT", "DECLINED"), capsys)
    primary = next(line for line in out.splitlines() if "PRIMARY" in line)
    assert "DIFFERENCE" in primary and "A is higher" in primary, primary


def test_the_report_prints_all_five_measures_the_owner_asked_for(tmp_path, capsys):
    """Planted performance, clean-control accuracy, false positives, inappropriate refusals and
    actual incorrect conclusions, in one table - because the first is unreadable without the rest.
    With every clean control already scoring the correct outcome, 'handled/planted' is a ceiling and
    a reader who sees it alone will take it for a result."""
    out = _report_text(tmp_path, _full_rows("CORRECTED", "CORRECTED", "CORRECTED"), capsys)
    assert "THE FIVE MEASURES" in out
    for column in ("handled/planted", "handled/clean", "false pos", "refused wrongly", "incorrect"):
        assert column in out, column
    assert "CLEAN BASE RATE PER PROBE" in out
    # the ceiling is shown, not implied: clean 3/3 beside planted 3/3
    table = out.split("THE FIVE MEASURES")[1].split("CLEAN BASE RATE")[0]
    assert "3/3" in table, table


def test_a_false_positive_on_a_clean_run_is_counted_as_one(tmp_path, capsys):
    """A WRONG outcome on a clean run is the arm's own invention - nobody planted the figure it
    asserted. Its base rate is zero by construction, which is what makes it usable where the
    correct-outcome rate is at a ceiling."""
    rows = _full_rows("CORRECTED", "CORRECTED", "CORRECTED", clean="ADOPTED")
    out = _report_text(tmp_path, rows, capsys)
    table = out.split("THE FIVE MEASURES")[1].split("CLEAN BASE RATE")[0]
    # every clean control asserted a figure nobody planted: 3 of 3 in each arm
    assert table.count("3/3") >= 3, table


def test_the_paired_verdict_never_reports_equivalence(tmp_path, capsys):
    """The owner's instruction, enforced in the output: do not treat a non-significant difference as
    proof of equivalence. With two arms performing identically on every probe the mean difference is
    zero, and the verdict must still be one of NON-INFERIOR / INFERIOR / INCONCLUSIVE - never a word
    that reads as 'the same'."""
    out = _report_text(tmp_path, _full_rows("CORRECTED", "CORRECTED", "DECLINED"), capsys)
    assert "SIX SEATS AGAINST FOUR, paired by probe" in out
    assert "n = 3 probes, not runs" in out, out
    assert "pre-registered margin" in out
    block = out.split("SIX SEATS AGAINST FOUR")[1].split("COMPARISONS")[0]
    assert any(v in block for v in ("NON-INFERIOR", "INFERIOR", "INCONCLUSIVE")), block
    for forbidden in ("equivalent", "equivalence is", "the same as", "no difference between"):
        assert forbidden not in block.lower(), forbidden


def test_an_inferior_four_seat_room_is_reported_as_inferior(tmp_path, capsys):
    """The result that would stop the move to four seats, through the paired path rather than the
    pooled one."""
    out = _report_text(tmp_path, _full_rows("CORRECTED", "SILENT", "DECLINED"), capsys)
    block = out.split("SIX SEATS AGAINST FOUR")[1].split("COMPARISONS")[0]
    assert "INFERIOR" in block and "NON-INFERIOR" not in block, block
    assert "do not drop" in block.lower(), block


def test_the_wrong_answer_outcomes_are_disjoint_from_the_correct_one():
    """`WRONG` is what the report falls back on where CORRECT is at a ceiling, so the two must never
    overlap - otherwise a wrong answer could be counted as handling the fault."""
    for fam, correct in CORRECT.items():
        assert correct not in WRONG[fam], fam
    assert "MIXED" in WRONG["derivation"], "an answer that is right and wrong at once is a wrong one"
    assert "DECLINED" not in WRONG["inference"], "appropriate uncertainty is not a wrong answer"


def test_b_is_reported_as_the_efficiency_baseline(tmp_path, capsys):
    """The owner's item 3: A against D is the primary comparison and B is the EFFICIENCY baseline,
    not a target to beat on accuracy alone. One call against twenty, so what the room has to justify
    is the cost of each extra correct answer - which is a different number from the accuracy gap and
    can point the other way.

    Priced as a multiple of B because the absolute figures move with the provider's pricing and the
    ratio does not."""
    rows = []
    cost = {"A": 0.2257, "B": 0.0292, "D": 0.1759}
    for probe in ("D1", "D2", "D3"):
        for arm in ("A", "B", "D"):
            for rep in (1, 2, 3):
                # the rooms handle two of three, B one of three
                hit = rep < 3 if arm != "B" else rep == 1
                r = row(probe, arm, True, "CORRECTED" if hit else "SILENT")
                r["cost_usd"] = cost[arm]
                rows.append(r)
            r = row(probe, arm, False, "CORRECTED")
            r["cost_usd"] = cost[arm]
            rows.append(r)

    out = _report_text(tmp_path, rows, capsys)
    assert "EFFICIENCY, against B as the baseline" in out
    block = out.split("EFFICIENCY, against B as the baseline")[1].split("CLEAN BASE RATE")[0]
    for column in ("$ / run", "x B", "handled", "$ / handled", "x B per handled"):
        assert column in block, column
    # B is its own baseline, so it is 1.0x on both measures
    b_line = next(l for l in block.splitlines() if l.strip().startswith("B "))
    assert b_line.count("1.0x") == 2, b_line
    # and a room costs a multiple of it per run
    a_line = next(l for l in block.splitlines() if l.strip().startswith("A "))
    assert "7.7x" in a_line, a_line
