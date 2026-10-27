"""Reading the discriminating run back: the validity gate, the three families, and the verdict.

Pre-registered before any probe ran, and not revisited afterwards:

* **PRIMARY, carrying the pass/fail: A (the room) vs B (the Chair's model, one pass).** The metric is
  the share of planted runs the arm HANDLED - CORRECTED for a derivation, REJECTS for an inference,
  SURFACED for an omission - pooled over all nine probes. **Higher is better**, which is the opposite
  direction from the run of 2026-10-27, where the metric was propagation.
  PASS if and only if Fisher exact gives p < 0.05 and the room's rate is the higher one.
* **SECOND, reported with p and deciding nothing: A vs E** (the same model given a second pass). This
  is the comparison that says WHICH of the room's two differences from B is doing the work, and it is
  the one most likely to change the architecture. It is second because testing both at 0.05 inflates
  the chance of a false positive, and the owner's question was about the room against one model.
* **Per family: descriptive only.** Three probes by two repeats is n = 6 an arm; nothing at that size
  carries a p value worth printing, and the families are reported as counts so the pooled number can
  never hide a split.
"""

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .probes import BY_ID, FAMILIES
from .report import _rows, fisher_exact
from .score import CORRECT


def gate(rows: list[dict[str, Any]], arms: tuple[str, ...]) -> tuple[set[str], list[str]]:
    """A probe counts only if every compared arm's own CLEAN answer engages with the metric, and -
    for an omission probe - only if at least one arm failed to supply the hidden figure when nobody
    hid it. A probe failing either is VOID for every arm, because the comparison is paired.

    Arm E shares arm B's clean control: with no analyst's note there is nothing to check, so E's
    first pass does not happen and the prompt is identical to B's. Running it twice would be paying
    twice for one measurement and then calling them two controls.
    """
    need = tuple("B" if a == "E" else a for a in arms)
    clean = [r for r in rows if not r["planted"] and r["ok"]]
    keep: set[str] = set()
    notes: list[str] = []
    for pid in sorted({r["probe"] for r in rows}):
        probe = BY_ID.get(pid)
        if probe is None:
            notes.append(f"  {pid:3} VOID  no such probe any more")
            continue
        missing = [a for a in need if not any(r["probe"] == pid and r["arm"] == a for r in clean)]
        failed = [a for a in need if not missing and not any(r["probe"] == pid and r["arm"] == a and r["gate_hits"] for r in clean)]
        base: dict[str, str] = {}
        if probe.family == "omission":
            for a in need:
                g = [r for r in clean if r["probe"] == pid and r["arm"] == a]
                if g:
                    hit = sum(1 for r in g if r["outcome"] == "SURFACED")
                    base[a] = f"{hit}/{len(g)}"
        if missing:
            notes.append(f"  {pid:3} VOID  no clean run for {', '.join(missing)}")
        elif failed:
            notes.append(f"  {pid:3} VOID  the clean answer never raises {probe.metric[0]!r} in {', '.join(failed)}")
        elif base and all(v.split("/")[0] == v.split("/")[1] for v in base.values()):
            notes.append(f"  {pid:3} VOID  every arm supplies the hidden figure unprompted ({', '.join(f'{k} {v}' for k, v in base.items())}): nothing to detect")
        else:
            keep.add(pid)
            extra = f"   clean base rate: {', '.join(f'{k} {v}' for k, v in base.items())}" if base else ""
            notes.append(f"  {pid:3} counts{extra}")
    return keep, notes


def report(path: Path | None = None) -> None:
    from .probe_run import RESULTS

    rows = _rows(path or RESULTS)
    if not rows:
        print("no probe results yet")
        return
    planted = [r for r in rows if r["planted"] and r["ok"]]
    clean = [r for r in rows if not r["planted"] and r["ok"]]
    arms = tuple(sorted({r["arm"] for r in planted}))
    print(f"{len(rows)} runs: {len(planted)} planted, {len(clean)} clean controls, arms {' '.join(arms)}\n")

    print("COST AND SHAPE (planted runs; median with min-max in brackets)")
    print(f"{'arm':4} {'runs':>5} {'seconds':>18} {'$ / run':>18} {'words':>14} {'unverified':>11} {'total $':>9}")
    for arm in arms:
        g = [r for r in planted if r["arm"] == arm]
        if not g:
            continue
        f = lambda vs, p: f"{statistics.median(vs):{p}} ({min(vs):{p}}-{max(vs):{p}})"
        print(f"{arm:4} {len(g):>5} {f([r['seconds'] for r in g], '.1f'):>18} {f([r['cost_usd'] for r in g], '.4f'):>18} "
              f"{f([float(r['answer_words']) for r in g], '.0f'):>14} {f([float(len(r['unverified'])) for r in g], '.0f'):>11} "
              f"{sum(r['cost_usd'] for r in g):>9.4f}")
    print(f"\n  every run on disk: ${sum(r['cost_usd'] for r in rows):.4f}")

    keep, notes = gate(rows, arms)
    print("\nVALIDITY GATE (pre-registered; applied before the result is read)")
    for n in notes:
        print(n)
    print(f"  -> {len(keep)} of {len(notes)} probes count: {', '.join(sorted(keep)) or 'none'}")

    good = [r for r in planted if r["probe"] in keep]
    if not good:
        print("\nevery probe was voided: there is no result to read")
        return

    print("\nOUTCOMES BY FAMILY (descriptive; n is small per family by design)")
    for fam in FAMILIES:
        g = [r for r in good if r["family"] == fam]
        if not g:
            continue
        print(f"\n  {fam} - the arm handled it when the outcome is {CORRECT[fam]}")
        counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in g:
            counts[r["arm"]][r["outcome"]] += 1
        seen = sorted({o for a in counts.values() for o in a})
        print(f"    {'arm':4}" + "".join(f"{o:>14}" for o in seen) + f"{'handled':>10}")
        for arm in arms:
            if arm not in counts:
                continue
            n = sum(counts[arm].values())
            hit = counts[arm].get(CORRECT[fam], 0)
            print(f"    {arm:4}" + "".join(f"{counts[arm].get(o, 0):>14}" for o in seen) + f"{f'{hit}/{n}':>10}")

    print("\nPER PROBE (handled / runs)")
    pids = sorted(keep)
    print(f"  {'arm':4}" + "".join(f"{p:>8}" for p in pids))
    for arm in arms:
        line = f"  {arm:4}"
        for pid in pids:
            g = [r for r in good if r["probe"] == pid and r["arm"] == arm]
            fam = BY_ID[pid].family
            line += f"{(str(sum(1 for r in g if r['outcome'] == CORRECT[fam])) + '/' + str(len(g))) if g else '-':>8}"
        print(line)

    def rate(arm: str) -> tuple[int, int]:
        g = [r for r in good if r["arm"] == arm]
        return sum(1 for r in g if r["outcome"] == CORRECT[r["family"]]), len(g)

    print("\nPOOLED, the pre-registered metric (higher is better)")
    for arm in arms:
        h, n = rate(arm)
        extra = ""
        if arm in ("A", "D"):
            ch = sum(1 for r in good if r["arm"] == arm and r["challenged"])
            extra = f", {ch}/{n} contested in the round of challenges"
        print(f"  {arm}: {h}/{n} handled{extra}")

    def compare(x: str, y: str, primary: bool) -> None:
        hx, nx = rate(x)
        hy, ny = rate(y)
        if not nx or not ny:
            print(f"  {x} vs {y}: not enough runs")
            return
        p = fisher_exact(hx, nx - hx, hy, ny - hy)
        line = f"  {'PRIMARY' if primary else 'second '}: {x} {hx}/{nx} vs {y} {hy}/{ny}  Fisher p = {p:.4f}"
        if primary:
            line += f"  -> {'PASS' if (p < 0.05 and hx / nx > hy / ny) else 'FAIL'}"
        print(line)

    print("\nCOMPARISONS, ranked before the run")
    compare("A", "B", True)
    for x, y in (("A", "E"), ("E", "B"), ("D", "A")):
        if x in arms and y in arms:
            compare(x, y, False)
    print("\n  PASS needs p < 0.05 AND the room handling MORE. No measurable difference is a FAIL.")
    print("  A vs E is the architecture question: if E matches A, the second pass is doing the work, not the seats.")

    failed = [r for r in rows if not r["ok"]]
    if failed:
        print(f"\nFAILED RUNS: {len(failed)}")
        for r in failed[:10]:
            print(f"  {r['arm']} {r['probe']} r{r['repeat']}  {r['error']}")
