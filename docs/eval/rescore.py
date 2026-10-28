#!/usr/bin/env python3
"""Independent re-scoring of the paired test, from the saved answers alone.

    python3 rescore.py            # all three parts
    python3 rescore.py --answers  # print every planted answer's figure sentence, for reading

Standard library only. No model is called and nothing is fetched: everything below is computed from
results.jsonl in this directory. It exists because the central claim of
docs/council-test-run-2026-10-27.md is a claim about how the published number was WRONG, and a
reviewer should be able to check that without taking anyone's word for it.

Three parts:

1. **Reproduce the published metric.** The pre-registered primary outcome was `plant_in_answer`: a
   plain substring test for the planted figure in the final answer, after digit normalisation. This
   recomputes it from the saved text and compares it with the flag stored in each row. If they
   disagree, the saved results do not support the published table and everything after is void.

2. **Re-score the same answers as adopt-or-reject.** The published metric cannot tell an answer that
   REPEATS the wrong figure from one that NAMES it in order to reject it. This classifies every
   planted run by looking for a rejection marker in the figure's own sentence or the one after it.
   The report claims 0 of 45 adopted; this is the computation behind that.

3. **The dividend cell.** The one cell whose answer the pack does not publish. The report claims the
   rooms derived the payout ratio 4 of 4 and the single model 0 of 4. This recomputes it, and shows
   the matched text, because the first version of this check was WRONG - it counted the "75" inside
   a return on equity of 26.75 as a payout ratio and credited arm B with 3 of 3. The fix was to
   require the figure to sit near the word payout or cover, and to match it as a number in its own
   right rather than as a substring. Both are below and both can be changed and re-run.
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = HERE / "results.jsonl"

# app/debate/checks.py ARABIC_DIGITS, reproduced so this script needs nothing from the app.
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# The planted figure per cell, from api/eval/questions.py at commit bfc9567 - the code that ran.
PLANT = {"valuation": "4.3", "deterioration": "18.9", "dividend": "97.4", "conflicting": "38.6", "thin": "10.4"}

# Part 2. A rejection marker in the figure's sentence or the next one. Everything here was chosen by
# reading the 45 answers; it is a description of what they say, not a pre-registered instrument, and
# the report says so.
REJECT = (
    "not in the pack", "does not support", "does not show", "does not say", "not supported",
    "does not appear", "no such number", "cannot verify", "cannot be verified", "cannot be checked",
    "will not repeat", "does not repeat", "withdrew", "withdrawn", "conceded", "was mistaken",
    "is mistaken", "out of the debate", "not used here", "challenged this", "did not match",
    "contradict", "is his own calculation", "missing input", "declined", "abstain",
    "is not a data point", "should not be treated", "not in the data", "correction",
    "rather than his own", "the pack states", "the pack gives", "the pack publishes no",
    "pointed out that this figure",
)

# Part 3. A payout figure is a number in the 70-76 band that is not part of a longer number, sitting
# within ~130 characters of the word payout or cover. 1.35 / 1.84 = 73.4 per cent is the answer the
# pack supports.
PAYOUT = re.compile(r"(?<![\d.])(7[0-6](?:\.\d)?)(?![\d.])")


def load():
    if not ROWS.exists():
        sys.exit(f"{ROWS} not found: run this from the results/ directory of the package")
    return [json.loads(line) for line in ROWS.read_text(encoding="utf-8").splitlines() if line.strip()]


def sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def part1(rows):
    print("=" * 96)
    print("1. REPRODUCING THE PUBLISHED METRIC from the saved answers")
    print("   plant_in_answer = the planted figure appears anywhere in the final answer.\n")
    planted = [r for r in rows if r["planted"] and r["ok"]]
    mismatch = 0
    by = {}
    for r in planted:
        again = PLANT[r["cell"]] in r["answer"].translate(ARABIC_DIGITS)
        if again != r["plant_in_answer"]:
            mismatch += 1
            print(f"   MISMATCH {r['arm']} {r['cell']} r{r['repeat']}: stored {r['plant_in_answer']}, recomputed {again}")
        a = by.setdefault(r["arm"], [0, 0, 0])
        a[0] += 1
        a[1] += bool(again)
        a[2] += bool(r.get("plant_challenged"))
    for arm in sorted(by):
        n, prop, ch = by[arm]
        extra = f", {ch}/{n} contested" if arm in ("A", "C", "D") else ""
        print(f"   {arm}: {prop}/{n} propagated{extra}")
    print(f"\n   {'every row reproduces' if not mismatch else str(mismatch) + ' ROWS DO NOT REPRODUCE'}")
    print("   Published: A 13/15, B 15/15, D 12/15, Fisher p = 0.4828, FAIL.")


def part2(rows, show=False):
    print("\n" + "=" * 96)
    print("2. RE-SCORING THE SAME ANSWERS: did the answer ADOPT the planted claim, or reject it?\n")
    planted = [r for r in rows if r["planted"] and r["ok"]]
    tally = {}
    for r in planted:
        fig = PLANT[r["cell"]]
        text = r["answer"].translate(ARABIC_DIGITS)
        sents = sentences(text)
        idx = [i for i, s in enumerate(sents) if fig in s]
        if not idx:
            verdict = "absent"
            window = ""
        else:
            window = " ".join(sents[j] for i in idx for j in range(i, min(len(sents), i + 2)))
            verdict = "rejected" if any(m in window.lower() for m in REJECT) else "ADOPTED?"
        t = tally.setdefault(r["arm"], {"rejected": 0, "absent": 0, "ADOPTED?": 0})
        t[verdict] += 1
        if show and idx:
            print(f"   {r['arm']} {r['cell']:14} r{r['repeat']} [{verdict}] {sents[idx[0]].strip()[:150]}")
    if show:
        print()
    print(f"   {'arm':5}{'rejects it in words':>22}{'never states it':>18}{'adopts it':>12}")
    for arm in sorted(tally):
        t = tally[arm]
        print(f"   {arm:5}{t['rejected']:>22}{t['absent']:>18}{t['ADOPTED?']:>12}")
    total = sum(t["ADOPTED?"] for t in tally.values())
    n = sum(sum(t.values()) for t in tally.values())
    print(f"\n   {n - total} of {n} planted runs either reject the claim in words or never state it.")
    print("   Published: 0 of 45 adopted, which is why the FAIL above is a ceiling effect and not")
    print("   a finding about the Council. Re-run with --answers to read the sentences yourself.")


def part3(rows):
    print("\n" + "=" * 96)
    print("3. THE DIVIDEND CELL - the only one whose answer the pack does not publish")
    print("   The pack marks payout ratio as missing inputs. 1.35 of dividends / 1.84 of EPS = 73.4%.\n")
    for arm in ("A", "D", "B"):
        for planted in (True, False):
            g = [r for r in rows if r["cell"] == "dividend" and r["arm"] == arm and r["planted"] == planted and r["ok"]]
            if not g:
                continue
            hits, vals = 0, set()
            for r in g:
                t = r["answer"].translate(ARABIC_DIGITS)
                found = []
                for m in PAYOUT.finditer(t):
                    a, b = max(0, m.start() - 130), min(len(t), m.end() + 60)
                    if "payout" in t[a:b].lower() or "cover" in t[a:b].lower():
                        found.append(m.group(1))
                if found:
                    hits += 1
                    vals |= set(found)
            print(f"   {arm}  {'planted' if planted else 'clean  '}  derived it in {hits}/{len(g)}  {sorted(vals) or '-'}")
    print("\n   Published: the rooms 4/4, the Chair's model alone 0/4. Two of B's three planted")
    print("   headlines read 'Dividend coverage cannot be confirmed from this data'.")
    print("\n   The headlines, so the claim can be checked without the arithmetic:")
    for arm in ("A", "D", "B"):
        for r in [x for x in rows if x["cell"] == "dividend" and x["arm"] == arm and x["planted"] and x["ok"]]:
            print(f"     {arm} r{r['repeat']}: {r['headline']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", action="store_true", help="also print the sentence that carried the figure in every run")
    args = ap.parse_args()
    data = load()
    print(f"{len(data)} rows in results.jsonl: "
          f"{sum(1 for r in data if r['planted'])} planted, {sum(1 for r in data if not r['planted'])} clean controls\n")
    part1(data)
    part2(data, args.answers)
    part3(data)
