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
