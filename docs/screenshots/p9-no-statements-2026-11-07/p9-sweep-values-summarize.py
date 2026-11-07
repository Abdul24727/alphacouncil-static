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

print(f"P9 on beta for every ticker, read 2026-11-07 through the tunnel, GET only (p9-sweep-values.py): {sys.argv[1].split('/')[-1]}")
print("Classified by reported numbers per company and section (review 80).")
print("tickers read:", len(d), "| non-200:", sum(r["status"] != 200 for r in d))
# What these two lines measure (review 81): whole SECTIONS or quarter SERIES that have rows but no number
# at all. They say nothing about a single all-null row inside a section that has numbers elsewhere.
rows_no_numbers = [r["slug"] for r in d if sum(r["statement_rows"].values()) and not held(r)]
print("companies whose statement sections have rows but no number at all:", len(rows_no_numbers), rows_no_numbers[:10])
qrows_no_numbers = [r["slug"] for r in d if r["quarter_rows"] and not r["quarter_numbers"]]
print("companies whose quarter series has rows but no number at all:", len(qrows_no_numbers), qrows_no_numbers[:10])
if all("statement_null_rows" in r for r in d if r["status"] == 200):
    # The per-row measure, where the sweep recorded it (p9-sweep-rows.json).
    s_null = sum(sum(r["statement_null_rows"].values()) for r in d)
    s_all = sum(sum(r["statement_rows"].values()) for r in d)
    q_null = sum(r["quarter_null_rows"] for r in d)
    q_all = sum(r["quarter_rows"] for r in d)
    print(f"individual statement rows with no number: {s_null} of {s_all}, in"
          f" {sum(1 for r in d if sum(r['statement_null_rows'].values()))} companies")
    print(f"individual quarter rows with no number: {q_null} of {q_all}, in {sum(1 for r in d if r['quarter_null_rows'])} companies")
else:
    print("individual all-null rows: NOT MEASURED in this file (see p9-sweep-rows.json)")
one_window = [r for r in d if "ONE INCOME-STATEMENT WINDOW" in r.get("limitations", []) and r["quarter_numbers"] == 0
              and "Income Statement" in held(r)]
print(f"\nan income statement, one window and no quarterly figure (told 'the single quarters are the history there"
      f" is', review 81): {len(one_window)}: {' '.join(r['slug'] for r in one_window)}")
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
