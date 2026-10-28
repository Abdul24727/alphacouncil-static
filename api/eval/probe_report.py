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

import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .probes import BY_ID, FAMILIES
from .report import _rows, fisher_exact
from .score import CORRECT, WRONG


# PRE-REGISTERED 2026-10-28, before any model comparison, at the owner's instruction to "define an
# acceptable non-inferiority margin for four advisors before testing".
#
# Four advisors are NON-INFERIOR to six if the one-sided 95% upper bound on (A - D) is below this
# margin. 15 points is the business judgement, not an arithmetic convenience: a four-seat room costs
# about 30% less per session, and a loss of more than about one answer in seven is more than that
# saving is worth.
#
# WHAT THE PLANNED RUN CAN ACTUALLY ESTABLISH, stated here because the number is uncomfortable.
# Simulated over the probe-level paired design, the upper bound you can expect to beat 80% of the
# time is:
#
#     6 probes x 3 repeats    42 points     18 probes x 6 repeats   15 points
#     18 probes x 2 repeats   26 points     36 probes x 3 repeats   15 points
#     18 probes x 3 repeats   22 points     36 probes x 6 repeats   11 points
#
# So the 18 x 3 plan is UNDERPOWERED against this margin and will most likely return
# "inconclusive". That is not a reason to move the margin to fit the budget - it is the reason the
# verdict below never prints a pass when the bound does not clear the margin, and why a
# non-significant difference is reported as a failure to detect rather than as equivalence.
NON_INFERIORITY_MARGIN = 0.15

# One-sided 95% t critical values by degrees of freedom. A table rather than a dependency: this
# module is importable with no application and no scipy on the path, which is what makes these
# numbers checkable from inside the verification package.
_T95 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833,
        10: 1.812, 11: 1.796, 12: 1.782, 13: 1.771, 14: 1.761, 15: 1.753, 16: 1.746, 17: 1.740,
        19: 1.729, 23: 1.714, 29: 1.699, 35: 1.690, 47: 1.678, 59: 1.671, 119: 1.658}


def t95(df: int) -> float:
    """The one-sided 95% critical value, rounded UP to the nearest tabulated df.

    Rounding up is deliberate: it takes the WIDER interval, so an unlisted df can only make the
    bound more conservative and never fake precision the sample does not have.
    """
    if df < 1:
        return float("inf")
    for key in sorted(_T95):
        if df <= key:
            return _T95[key]
    return 1.645


def paired_rates(rows: list[dict[str, Any]], keep: set[str], arm: str,
                 planted: bool) -> dict[str, float]:
    """This arm's rate of the correct outcome, PER PROBE, over that probe's repeats.

    Aggregating to the probe before comparing is the whole point. Three repeats of one probe are not
    three independent observations of the room: they are one question asked three times, and pooling
    them as if they were independent overstates the precision of every comparison built on them.
    The owner's instruction was a paired analysis that accounts for repeated runs, and this is where
    that accounting happens.
    """
    out: dict[str, float] = {}
    for pid in sorted(keep):
        runs = [r for r in rows
                if r["probe"] == pid and r["arm"] == arm and bool(r["planted"]) == planted and r["ok"]]
        if runs:
            fam = BY_ID[pid].family
            out[pid] = sum(1 for r in runs if r["outcome"] == CORRECT[fam]) / len(runs)
    return out


def non_inferiority(x_rates: dict[str, float], y_rates: dict[str, float],
                    margin: float) -> tuple[str, float, float, float, int]:
    """Is y non-inferior to x within `margin`, on the probes both arms answered?

    Paired by PROBE, because both arms saw the identical pack and the identical question - which is
    what makes the pairing legitimate and what removes probe difficulty from the difference.

    Returns (verdict, mean difference, upper bound, margin, n probes). The verdict is deliberately
    one of three, never two: a bound that clears the margin is non-inferiority, a difference that
    excludes zero on the wrong side is inferiority, and anything else is INCONCLUSIVE. There is no
    outcome here that reads as "equivalent", because this design cannot establish equivalence.
    """
    shared = sorted(set(x_rates) & set(y_rates))
    diffs = [x_rates[k] - y_rates[k] for k in shared]
    n = len(diffs)
    if n < 2:
        return "NOT ENOUGH PROBES", 0.0, float("inf"), margin, n
    mean = statistics.mean(diffs)
    sd = statistics.stdev(diffs)
    upper = mean + t95(n - 1) * sd / math.sqrt(n) if sd > 0 else mean
    if upper < margin:
        return "NON-INFERIOR", mean, upper, margin, n
    lower = mean - t95(n - 1) * sd / math.sqrt(n) if sd > 0 else mean
    if lower > 0:
        return "INFERIOR", mean, upper, margin, n
    return "INCONCLUSIVE", mean, upper, margin, n


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
    # THE FIVE MEASURES, side by side. The owner asked for planted-error performance reported
    # alongside clean-control accuracy, false positives, inappropriate refusals and actual
    # incorrect conclusions - and the reason to put them in one table is that the first number is
    # unreadable without the rest:
    #
    #   handled (planted)  the pre-registered primary metric
    #   handled (clean)    the same rubric with nothing planted. Where this is already high the
    #                      planted figure is at a ceiling and cannot separate two arms.
    #   false positive     a WRONG outcome on a CLEAN run: a figure the arm asserted that nobody
    #                      planted, so it is the arm's own invention. Base rate zero by
    #                      construction.
    #   refused wrongly    DECLINED on a clean run. For a derivation probe the pack supports the
    #                      figure by construction - that is what makes it a derivation - so a
    #                      refusal there is a refusal to answer something answerable, which is a
    #                      cost to the member even though it is not a wrong answer.
    #   incorrect          a WRONG outcome on a planted run: the failure that reaches the member.
    print("\nTHE FIVE MEASURES (same packs, same questions, plant or no plant)")
    head = f"  {'arm':4}{'handled/planted':>17}{'handled/clean':>15}{'false pos':>11}{'refused wrongly':>17}{'incorrect':>11}"
    print(head)
    for arm in arms:
        ctrl = "B" if arm == "E" else arm           # arm E shares arm B's control, as the gate does
        pl = [r for r in good if r["arm"] == arm]
        cl = [r for r in clean if r["probe"] in keep and r["arm"] == ctrl and r["ok"]]
        if not pl:
            continue

        def share(rows_in: list[dict[str, Any]], want: str) -> str:
            if not rows_in:
                return "-"
            if want == "correct":
                n = sum(1 for r in rows_in if r["outcome"] == CORRECT[r["family"]])
            elif want == "wrong":
                n = sum(1 for r in rows_in if r["outcome"] in WRONG[r["family"]])
            else:
                n = sum(1 for r in rows_in if r["outcome"] == "DECLINED")
            return f"{n}/{len(rows_in)}"

        print(f"  {arm:4}{share(pl, 'correct'):>17}{share(cl, 'correct'):>15}"
              f"{share(cl, 'wrong'):>11}{share(cl, 'declined'):>17}{share(pl, 'wrong'):>11}")
    print("\n  Read 'handled/clean' first. Where it is already high, 'handled/planted' is a ceiling")
    print("  and the arms cannot be separated on it - use 'incorrect', whose clean base rate is")
    print("  zero by construction. A high 'refused wrongly' is the cost of caution, not of error.")

    # B IS THE EFFICIENCY BASELINE, not a target to beat on accuracy alone. One model answering
    # once is what the room has to justify its cost against, so the question is not only whether a
    # room handles more but what each extra correct answer costs. Printed as a multiple of B
    # because the absolute figures move with the provider's pricing and the ratio does not.
    print("\nEFFICIENCY, against B as the baseline (planted runs)")
    base = [r for r in good if r["arm"] == "B"]
    base_cost = sum(r["cost_usd"] for r in base) / len(base) if base else 0.0
    base_hit, base_n = rate("B") if "B" in arms else (0, 0)
    print(f"  {'arm':4}{'$ / run':>11}{'x B':>8}{'handled':>10}{'$ / handled':>14}{'x B per handled':>17}")
    for arm in arms:
        g = [r for r in good if r["arm"] == arm]
        if not g:
            continue
        per_run = sum(r["cost_usd"] for r in g) / len(g)
        hit, n = rate(arm)
        per_hit = (per_run * n / hit) if hit else None
        base_per_hit = (base_cost * base_n / base_hit) if base_hit else None
        mult = f"{per_run / base_cost:.1f}x" if base_cost else "-"
        mult_hit = (f"{per_hit / base_per_hit:.1f}x"
                    if per_hit is not None and base_per_hit else "-")
        print(f"  {arm:4}{per_run:>11.4f}{mult:>8}{f'{hit}/{n}':>10}"
              f"{(f'{per_hit:.4f}' if per_hit is not None else 'never'):>14}{mult_hit:>17}")
    print("\n  A room that handles more but costs more per correct answer has not earned its seats,")
    print("  and a room that handles the same for more money has lost the argument outright. On a")
    print("  dry run these costs are all zero and the columns are meaningless.")

    print("\nCLEAN BASE RATE PER PROBE (the correct outcome with nothing planted)")
    pids2 = sorted(keep)
    print(f"  {'arm':4}" + "".join(f"{pid:>8}" for pid in pids2))
    for arm in arms:
        ctrl = "B" if arm == "E" else arm
        line = f"  {arm:4}"
        for pid in pids2:
            g = [r for r in clean if r["probe"] == pid and r["arm"] == ctrl and r["ok"]]
            fam = BY_ID[pid].family
            hit = sum(1 for r in g if r["outcome"] == CORRECT[fam])
            line += f"{(f'{hit}/{len(g)}') if g else '-':>8}"
        print(line)

    # --- the paired, probe-level comparison ----------------------------------------------------
    #
    # Three repeats of one probe are ONE question asked three times, not three independent
    # observations, so every rate here is computed per probe first and the comparison is paired
    # across probes. The owner's instruction was a paired analysis that accounts for repeated runs;
    # pooling the runs instead would overstate the precision of the primary comparison, which is
    # the one the whole decision rests on.
    if "D" in arms and "A" in arms:
        a_rates = paired_rates(rows, keep, "A", planted=True)
        d_rates = paired_rates(rows, keep, "D", planted=True)
        verdict, mean, upper, margin, n_probes = non_inferiority(a_rates, d_rates, NON_INFERIORITY_MARGIN)
        print(f"\nSIX SEATS AGAINST FOUR, paired by probe (n = {n_probes} probes, not runs)")
        print(f"  mean difference A - D      {mean * 100:+.1f} points")
        print(f"  one-sided 95% upper bound  {upper * 100:+.1f} points"
              if upper != float("inf") else "  one-sided 95% upper bound  -")
        print(f"  pre-registered margin      {margin * 100:.0f} points")
        print(f"  -> {verdict}")
        if verdict == "INCONCLUSIVE":
            print("     The bound does not clear the margin and the difference does not exclude")
            print("     zero. This is a FAILURE TO DETECT at this sample size, not equivalence:")
            print("     18 probes x 3 repeats can be expected to bound at about 22 points, so it")
            print("     cannot establish a 15-point margin. Do not read it as four matching six.")
        elif verdict == "NON-INFERIOR":
            print(f"     Four seats lose less than {margin * 100:.0f} points against six, on these probes.")
        elif verdict == "INFERIOR":
            print("     Six seats handle measurably more. This is the result that says do not drop")
            print("     two seats.")

    def compare(x: str, y: str, label: str, reading: str | None = None) -> None:
        """One comparison. `reading` says how it is to be READ, which is not the same for all of them.

        `superiority` asks whether x does better than y, and no measurable difference is a FAIL -
        the room has not earned its cost. `difference` asks only whether the two differ, because for
        six seats against four a difference is the thing that would STOP a change, and the absence
        of one is not a pass or a fail but a failure to detect at this sample size. Labelling the
        second as PASS would be the worst misreading this report could invite.

        These pool the runs. The paired block above is the one that accounts for repeats, and it is
        the one the six-against-four decision should be read from; these are kept for continuity
        with the earlier rounds, which reported them.
        """
        hx, nx = rate(x)
        hy, ny = rate(y)
        if not nx or not ny:
            print(f"  {label}: {x} vs {y}: not enough runs")
            return
        pval = fisher_exact(hx, nx - hx, hy, ny - hy)
        line = f"  {label}: {x} {hx}/{nx} vs {y} {hy}/{ny}  Fisher p = {pval:.4f}"
        if reading == "superiority":
            line += f"  -> {'PASS' if (pval < 0.05 and hx / nx > hy / ny) else 'FAIL'}"
        elif reading == "difference":
            if pval < 0.05:
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
    print("  A vs B and D vs B ask whether either room beats the Chairman at all. B is the")
    print("  EFFICIENCY BASELINE: one call against twenty, so a room that cannot beat it on")
    print("  accuracy has not earned its cost, and seat count stops being the question. Read these")
    print("  beside the efficiency table above, which prices each correct answer.")
    print("  A vs E, if E was run, is the architecture question: if E matches A, the second pass is")
    print("  doing the work rather than the seats.")
    print("\n  The Fisher lines above pool the runs and are reported for continuity with the earlier")
    print("  rounds. The PAIRED block above them is the one to read for the six-against-four")
    print("  decision: it aggregates each probe before comparing, so three repeats of one question")
    print("  count as one question answered three times rather than three independent findings.")

    failed = [r for r in rows if not r["ok"]]
    if failed:
        print(f"\nFAILED RUNS: {len(failed)}")
        for r in failed[:10]:
            print(f"  {r['arm']} {r['probe']} r{r['repeat']}  {r['error']}")
