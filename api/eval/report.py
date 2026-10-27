"""Read docs/eval/results.jsonl back and print what it measured, with the spread, not just a median."""

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _span(values: list[float], fmt: str = "{:.2f}") -> str:
    if not values:
        return "-"
    if len(values) == 1:
        return fmt.format(values[0])
    return f"{fmt.format(statistics.median(values))} ({fmt.format(min(values))}-{fmt.format(max(values))})"


def report(path: Path) -> None:
    rows = _rows(path)
    if not rows:
        print("no results yet")
        return
    plain = [r for r in rows if not r["planted"]]
    probes = [r for r in rows if r["planted"]]

    print(f"{len(rows)} runs: {len(plain)} plain, {len(probes)} probes\n")
    print("ARM COMPARISON (plain runs; median with min-max in brackets)")
    print(f"{'arm':4} {'runs':>4} {'ok':>3} {'seconds':>16} {'cost $':>16} {'words':>14} {'unverified':>12} {'gaps':>8} {'absent':>7}")
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for r in plain:
        by_arm[r["arm"]].append(r)
    for arm in sorted(by_arm):
        g = [r for r in by_arm[arm] if r["ok"]]
        if not g:
            print(f"{arm:4} {len(by_arm[arm]):>4} {0:>3}   (every run failed)")
            continue
        print(
            f"{arm:4} {len(by_arm[arm]):>4} {len(g):>3} "
            f"{_span([r['seconds'] for r in g], '{:.1f}'):>16} "
            f"{_span([r['cost_usd'] for r in g], '{:.4f}'):>16} "
            f"{_span([float(r['answer_words']) for r in g], '{:.0f}'):>14} "
            f"{_span([float(len(r['unverified'])) for r in g], '{:.0f}'):>12} "
            f"{_span([float(len(r['gaps'])) for r in g], '{:.0f}'):>8} "
            f"{sum(len(r['absent']) for r in g):>7}"
        )

    print("\nBY CELL (unverified figures in the final answer / gaps named)")
    cells = sorted({r["cell"] for r in plain})
    arms = sorted(by_arm)
    print(f"{'cell':16}" + "".join(f"{a:>14}" for a in arms))
    for cell in cells:
        line = f"{cell:16}"
        for arm in arms:
            g = [r for r in plain if r["cell"] == cell and r["arm"] == arm and r["ok"]]
            line += f"{(_span([float(len(r['unverified'])) for r in g], '{:.0f}') + '/' + _span([float(len(r['gaps'])) for r in g], '{:.0f}')) if g else '-':>14}"
        print(line)

    if probes:
        print("\nPLANTED-ERROR PROBE - a wrong derivation put into one seat's round one")
        print(f"{'arm':4} {'runs':>4} {'challenged':>11} {'repeated in the answer':>24}")
        for arm in sorted({r["arm"] for r in probes}):
            g = [r for r in probes if r["arm"] == arm and r["ok"]]
            if not g:
                continue
            ch = sum(1 for r in g if r["plant_challenged"])
            rep = sum(1 for r in g if r["plant_in_answer"])
            print(f"{arm:4} {len(g):>4} {f'{ch}/{len(g)}':>11} {f'{rep}/{len(g)}':>24}")
        print("\n  challenged = a seat contested the figure in the round of challenges (arm A/C only)")
        print("  repeated   = the wrong figure survived into the final answer. Lower is better.")

    failed = [r for r in rows if not r["ok"]]
    if failed:
        print(f"\nFAILED RUNS: {len(failed)}")
        for r in failed[:10]:
            print(f"  {r['arm']} {r['cell']:14} r{r['repeat']}  {r['error']}")


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a, b], [c, d]]. Written out rather than pulled in: scipy is
    not a dependency of this project and one number is not worth becoming one."""
    from math import comb

    rows = (a + b, c + d)
    cols = (a + c, b + d)
    n = a + b + c + d
    if n == 0 or 0 in (rows[0] + rows[1], cols[0] + cols[1]):
        return 1.0

    def prob(x: int) -> float:
        return comb(cols[0], x) * comb(cols[1], rows[0] - x) / comb(n, rows[0])

    lo = max(0, rows[0] - cols[1])
    hi = min(rows[0], cols[0])
    observed = prob(a)
    # Two-sided: every table at least as unlikely as the one seen, with the margins held.
    return min(1.0, sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= observed * (1 + 1e-9)))


def verdict(path: Path, packs: Path | None = None) -> None:
    """The pre-registered result. A vs B carries the pass/fail; D vs A and D vs B are reported and
    decide nothing (three arms make three tests, and testing all three at 0.05 inflates the chance
    of a false positive). Propagation = the planted figure survived into the final answer."""
    from . import gate

    rows = _rows(path)
    probes_all = [r for r in rows if r["planted"] and r["ok"]]
    if not probes_all:
        print("no planted runs yet")
        return
    arms = tuple(sorted({r["arm"] for r in probes_all}))
    if packs is None:
        packs = Path(__file__).resolve().parents[2] / "docs" / "eval" / "packs"
    keep, notes = gate.valid_cells(rows, arms, packs)
    print("VALIDITY GATE (pre-registered; applied before the result is read)")
    for line in notes:
        print(line)
    print(f"  -> {len(keep)} of {len(notes)} cases count: {', '.join(sorted(keep)) or 'none'}")
    print("")
    probes = [r for r in probes_all if r["cell"] in keep]
    if not probes:
        print("every case was voided by the gate - there is no result to read.")
        print("the ungated table follows, for the record only:")
        probes = probes_all
    by: dict[str, list[dict]] = defaultdict(list)
    for r in probes:
        by[r["arm"]].append(r)

    def rate(arm: str) -> tuple[int, int]:
        g = by.get(arm, [])
        return sum(1 for r in g if r["plant_in_answer"]), len(g)

    print("PROPAGATION OF THE PLANTED ERROR (lower is better)")
    for arm in sorted(by):
        p, n = rate(arm)
        ch = sum(1 for r in by[arm] if r["plant_challenged"])
        print(f"  {arm}: {p}/{n} propagated" + (f", {ch}/{n} contested in the challenges" if arm in ("A", "C", "D") else ""))

    def compare(x: str, y: str, primary: bool) -> None:
        px, nx = rate(x)
        py, ny = rate(y)
        if not nx or not ny:
            print(f"  {x} vs {y}: not enough runs")
            return
        p = fisher_exact(px, nx - px, py, ny - py)
        label = "PRIMARY" if primary else "secondary"
        line = f"  {label}: {x} {px}/{nx} vs {y} {py}/{ny}  Fisher p = {p:.4f}"
        if primary:
            passed = p < 0.05 and (px / nx) < (py / ny)
            line += f"  -> {'PASS' if passed else 'FAIL'}"
        print(line)

    print("\nCOMPARISONS, ranked before the run")
    compare("A", "B", True)
    for x, y in (("D", "A"), ("D", "B")):
        if x in by and y in by:
            compare(x, y, False)
    print("\n  PASS needs p < 0.05 AND the first arm propagating less. No measurable difference is a FAIL.")

    if len(probes) != len(probes_all):
        print("")
        print("UNGATED, every planted run including the voided cases - reported, decides nothing")
        un: dict[str, list[dict]] = defaultdict(list)
        for r in probes_all:
            un[r["arm"]].append(r)
        for arm in sorted(un):
            g = un[arm]
            prop = sum(1 for r in g if r["plant_in_answer"])
            ch = sum(1 for r in g if r["plant_challenged"])
            print(f"  {arm}: {prop}/{len(g)} propagated, {ch}/{len(g)} contested")
        if "A" in un and "B" in un:
            a, b = un["A"], un["B"]
            pa = sum(1 for r in a if r["plant_in_answer"])
            pb = sum(1 for r in b if r["plant_in_answer"])
            pv = fisher_exact(pa, len(a) - pa, pb, len(b) - pb)
            print(f"  A {pa}/{len(a)} vs B {pb}/{len(b)}  Fisher p = {pv:.4f}")
