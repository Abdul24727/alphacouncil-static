"""Reading the discriminating run back: the validity gate, the three families, and the verdict.

**Re-registered 2026-10-28, before any probe ran, on the owner's instruction.** The principal
decision is whether to keep six advisors or move to four, so:

* **PRIMARY: A (six advisors + Chairman) vs D (four + Chairman, existing prompts).** The metric is
  the share of planted runs the arm HANDLED - CORRECTED for a derivation, RESISTS for an inference,
  SURFACED for an omission - pooled over the probes that survive the gate.
  **Read as a difference test, not a pass/fail.** A difference at p < 0.05 is a reason not to drop
  two seats. No measurable difference is NOT equivalence: at n = 18 an arm, Fisher needs a gap of 6
  of 18 before it is visible, so the absence of one is a failure to detect, not a finding of parity.
  Labelling that PASS would be the worst misreading this report could invite, so it does not.
* **SECOND and THIRD, superiority tests: A vs B and D vs B** (the Chair's model, one pass). PASS
  needs p < 0.05 AND the room handling more. These come after the primary but they condition it: if
  neither room beats one model, seat count is not the question and the finding is about the Council.
* **LATER, if arm E is ever run: A vs E** (the same model given a second pass), the comparison that
  says which of the room's two differences from B is doing the work. Deferred by the owner.
* **Per family: descriptive only.** Six probes by three repeats is n = 18 an arm pooled, but far less
  per family; nothing at that size carries a p value worth printing, and the families are reported
  as counts so the pooled number can never hide a split.

**Until 2026-10-28 the primary was A vs B**, which answers a different question - whether the Council
beats one model at all. It is kept as the second comparison rather than dropped.

**The paired reading exists because the primary metric is at a ceiling on half the probes.** On the
clean controls, the three inference probes score RESISTS in every arm and D1 scores CORRECTED in A
and D, so the planted share alone cannot separate two arms there. What is printed is the pair - the
clean control beside the planted run, the change between them, and the wrong-answer rate, whose
clean base rate is zero by construction (score.WRONG).
"""

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .probes import BY_ID, FAMILIES
from .report import _rows, fisher_exact
from .score import CORRECT, WRONG


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

    # --- the paired reading --------------------------------------------------------------------
    #
    # Added 2026-10-28, because "handled" on its own can be read as a result when it is a ceiling.
    # On the answers available, CORRECT's clean base rate is at or near 100% for D1 and for all
    # three inference probes, in EVERY arm: the room derives the payout and resists the planted
    # inference whether or not anything was planted. A metric at its ceiling before the plant
    # arrives separates nothing, and the pooled line above would have shown three arms tied and
    # called it a finding.
    #
    # The design is paired - same pack, same question, plant or no plant - so what is printed here
    # is the pair: the clean control beside the planted run, the CHANGE between them, and the
    # wrong-answer rate, whose clean base rate is zero by construction (score.WRONG). Where the
    # change is zero and the wrong-answer rate is zero, the probe measured nothing in that arm, and
    # that has to be visible rather than inferred.
    print("\nPAIRED: the clean control beside the planted run (same pack, same question)")
    print(f"  {'arm':4}{'clean':>14}{'planted':>14}{'change':>10}{'wrong answers':>16}")
    for arm in arms:
        # arm E shares arm B's clean control, as the gate does
        ctrl_arm = "B" if arm == "E" else arm
        cl = [r for r in clean if r["probe"] in keep and r["arm"] == ctrl_arm]
        pl = [r for r in good if r["arm"] == arm]
        if not pl:
            continue
        ch = sum(1 for r in cl if r["outcome"] == CORRECT[r["family"]])
        ph = sum(1 for r in pl if r["outcome"] == CORRECT[r["family"]])
        wrong = sum(1 for r in pl if r["outcome"] in WRONG[r["family"]])
        clean_rate = ch / len(cl) if cl else None
        planted_rate = ph / len(pl)
        delta = f"{(planted_rate - clean_rate) * 100:+.0f}pp" if clean_rate is not None else "-"
        shown = f"{ch}/{len(cl)}" if cl else "-"
        print(f"  {arm:4}{shown:>14}{f'{ph}/{len(pl)}':>14}{delta:>10}"
              f"{f'{wrong}/{len(pl)}':>16}")
    print("\n  A probe whose clean control already reaches the correct outcome in every arm is at a")
    print("  ceiling: read the wrong-answer column, not 'handled'. Zero in both columns for every")
    print("  arm means the plant changed nothing anywhere, which is a finding about the PROBE.")

    print("\nCLEAN BASE RATE PER PROBE (the correct outcome with nothing planted)")
    pids2 = sorted(keep)
    print(f"  {'arm':4}" + "".join(f"{p:>8}" for p in pids2))
    for arm in arms:
        ctrl_arm = "B" if arm == "E" else arm
        line = f"  {arm:4}"
        for pid in pids2:
            g = [r for r in clean if r["probe"] == pid and r["arm"] == ctrl_arm]
            fam = BY_ID[pid].family
            hit = sum(1 for r in g if r["outcome"] == CORRECT[fam])
            line += f"{(f'{hit}/{len(g)}') if g else '-':>8}"
        print(line)

    def compare(x: str, y: str, label: str, reading: str | None = None) -> None:
        """One comparison. `reading` says how it is to be READ, which is not the same for all of them.

        `superiority` asks whether x does better than y, and no measurable difference is a FAIL -
        the room has not earned its cost. `difference` asks only whether the two differ, because for
        six seats against four a difference is the thing that would STOP a change, and the absence
        of one is not a pass or a fail but a failure to detect at this sample size. Labelling the
        second as PASS would be the worst misreading this report could invite.
        """
        hx, nx = rate(x)
        hy, ny = rate(y)
        if not nx or not ny:
            print(f"  {label}: {x} vs {y}: not enough runs")
            return
        p = fisher_exact(hx, nx - hx, hy, ny - hy)
        line = f"  {label}: {x} {hx}/{nx} vs {y} {hy}/{ny}  Fisher p = {p:.4f}"
        if reading == "superiority":
            line += f"  -> {'PASS' if (p < 0.05 and hx / nx > hy / ny) else 'FAIL'}"
        elif reading == "difference":
            if p < 0.05:
                line += f"  -> DIFFERENCE: {x if hx / nx > hy / ny else y} is higher"
            else:
                line += "  -> no measurable difference (NOT equivalence - read the note)"
        print(line)

    print("\nCOMPARISONS, ranked before the run")
    # RANKED AS THE OWNER PUT IT, 2026-10-28: the principal decision is six advisors or four, so
    # A vs D is primary. It was A vs B until then, which answers a different question - whether the
    # Council beats the Chairman at all - and that is kept directly below, because if neither room
    # beats B then seat count is moot and the finding is about the Council rather than its size.
    if "D" in arms:
        compare("A", "D", "PRIMARY", "difference")
    compare("A", "B", "second ", "superiority")
    if "D" in arms:
        compare("D", "B", "third  ", "superiority")
    for x, y in (("A", "E"), ("E", "B")):
        if x in arms and y in arms:
            compare(x, y, "later  ", None)
    print("\n  PRIMARY is six advisors against four, on identical packs and identical questions.")
    print("  Read it differently from the rest, on purpose:")
    print("    - a DIFFERENCE (p < 0.05) is a reason NOT to drop two seats;")
    print("    - no measurable difference is NOT proof that four match six. It is a failure to")
    print("      detect one at this sample size, and the sample is small by design. An equivalence")
    print("      claim needs a margin fixed in advance and far more runs than this plan buys.")
    print("      What this plan can do is rule out a LARGE loss from dropping two seats.")
    print("  A vs B and D vs B are superiority tests: PASS needs p < 0.05 AND the room handling")
    print("  more. If neither room beats the Chairman alone, seat count is not the question.")
    print("  A vs E, if E was run, is the architecture question: if E matches A, the second pass is")
    print("  doing the work rather than the seats.")

    failed = [r for r in rows if not r["ok"]]
    if failed:
        print(f"\nFAILED RUNS: {len(failed)}")
        for r in failed[:10]:
            print(f"  {r['arm']} {r['probe']} r{r['repeat']}  {r['error']}")
