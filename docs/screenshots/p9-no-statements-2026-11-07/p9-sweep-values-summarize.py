"""Classify p9-sweep-values.py's output by REPORTED NUMBERS (review 80), not rows."""
import json
import sys
from collections import Counter

d = json.load(open(sys.argv[1], encoding="utf-8"))
ANNUAL = ("Income Statement", "Balance Sheet", "Cash Flow Statement")


def held(r):
    return [s for s in ANNUAL if r["statement_numbers"].get(s, 0) > 0]


groups = {
    "A. no annual statement figure and no quarterly figure": [],
    "B. no annual statement figure, reported quarters": [],
    "C. a partial annual statement (no income-statement figure or no balance-sheet figure)": [],
    "D. an income statement and a balance sheet with figures": [],
}
for r in d:
    h, q = held(r), r["quarter_numbers"] > 0
    if not h:
        groups["A. no annual statement figure and no quarterly figure" if not q else "B. no annual statement figure, reported quarters"].append(r)
    elif "Income Statement" not in h or "Balance Sheet" not in h:
        groups["C. a partial annual statement (no income-statement figure or no balance-sheet figure)"].append(r)
    else:
        groups["D. an income statement and a balance sheet with figures"].append(r)

print("P9 on beta for every ticker, read 2026-11-07 through the tunnel, GET only (p9-sweep-values.py).")
print("Counted by reported numbers: a row whose cells after the label are null holds none (review 80).")
print("tickers read:", len(d), "| non-200:", sum(r["status"] != 200 for r in d))
rows_no_numbers = [r["slug"] for r in d if sum(r["statement_rows"].values()) and not held(r)]
print("statement rows present but no number in them:", len(rows_no_numbers), rows_no_numbers[:10])
qrows_no_numbers = [r["slug"] for r in d if r["quarter_rows"] and not r["quarter_numbers"]]
print("quarter rows present but no number in them:", len(qrows_no_numbers), qrows_no_numbers[:10])
for name, rs in groups.items():
    print(f"\n{name}: {len(rs)}")
    print("  by exchange:", dict(Counter(r["exchange"] for r in rs)))
    print("  with reported quarters:", sum(r["quarter_numbers"] > 0 for r in rs),
          "| calculations with a value:", sum(r["calcs_valued"] for r in rs), "of", sum(r["calcs"] for r in rs))
    print("  limitations P9 gave them (first words):", dict(Counter(lim for r in rs for lim in r["limitations"])))
    if name[0] in "ABC":
        print("  tickers:", " ".join(
            f"{r['slug']}" + (f"[q:{r['quarter_numbers']} numbers, {','.join(r['quarter_columns'])}]" if r["quarter_numbers"] else "")
            + (f"[held:{'+'.join(held(r))}]" if held(r) else "") for r in rs))
