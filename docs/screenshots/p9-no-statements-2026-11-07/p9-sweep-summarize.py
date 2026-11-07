"""Summarise p9-sweep.py's JSON: which companies' P9 holds no statements, and what P9 told them."""
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1], encoding="utf-8"))
none = [r for r in d if r.get("rows") == 0]
bs = [r for r in d if r.get("rows") and "Income Statement" not in r["sections"]]
print("P9 (/v1/tickers/<slug>/evidence) on beta for every ticker, read 2026-11-07 through the tunnel, GET only (p9-sweep.py).")
print("tickers read:", len(d), "| non-200:", sum(r["status"] != 200 for r in d))
print("statement sections:", dict(Counter(" + ".join(r["sections"]) or "(none at all)" for r in d).most_common()))
print()
print("NO STATEMENT ROWS:", len(none), "tickers; by exchange", dict(Counter(r["exchange"] for r in none)))
print("  their limitations (first words):", dict(Counter(l for r in none for l in r["limitations"])))
print("  calculations with a value:", sum(r["calcs_valued"] for r in none), "of", sum(r["calcs"] for r in none))
print("  slugs:", " ".join(r["slug"] for r in none))
print()
print("BALANCE SHEET BUT NO INCOME STATEMENT:", len(bs), [r["slug"] for r in bs], "| limitations:", [r["limitations"] for r in bs])
