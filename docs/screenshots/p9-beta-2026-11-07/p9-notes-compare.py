"""Compare beta's P9 notes before and after the P9 release, word for word.
Usage: python -X utf8 p9-notes-compare.py p9-notes-before.json p9-notes-after.json
Prints: which tickers' notes are unchanged, and for those that changed, each distinct before -> after pair with its
count, its tickers and the full text, plus whether anything other than the statement notes changed."""
import json
import sys
from collections import defaultdict

# The notes about the statements themselves: the ones P9's fix rewrites. Every other note must stay as it was.
STATEMENT_NOTES = ("NO FINANCIAL STATEMENTS", "NO ANNUAL STATEMENTS", "NO INCOME STATEMENT", "NO ANNUAL INCOME STATEMENT",
                   "NO CASH FLOW STATEMENT", "ONE INCOME-STATEMENT WINDOW", "The income statement covers a window")


def is_statement_note(note):
    return note.startswith(STATEMENT_NOTES)


def head(note):
    return note.split(":")[0][:60]


before, after = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
print(f"before: {before['started']} to {before['finished']}, {len(before['tickers'])} tickers, health {before['health']}")
print(f"after:  {after['started']} to {after['finished']}, {len(after['tickers'])} tickers, health {after['health']}")
b = {r["slug"]: r for r in before["tickers"]}
a = {r["slug"]: r for r in after["tickers"]}
print("same tickers:", sorted(b) == sorted(a), "| non-200 after:", sum(r["status"] != 200 for r in a.values()))

data_moved = [s for s in a if s in b and (b[s].get("sections"), b[s].get("rows"), b[s].get("quarters"), b[s].get("calcs_valued"))
              != (a[s].get("sections"), a[s].get("rows"), a[s].get("quarters"), a[s].get("calcs_valued"))]
print("tickers whose statement data itself differs between the sweeps (should be 0):", len(data_moved), data_moved[:10])

same = [s for s in a if s in b and b[s].get("limitations") == a[s].get("limitations") and b[s].get("quarters_note") == a[s].get("quarters_note")]
changed = [s for s in a if s in b and s not in same]
print(f"\nnotes word for word unchanged: {len(same)} | changed: {len(changed)}")

other = [s for s in changed if [n for n in b[s]["limitations"] if not is_statement_note(n)]
         != [n for n in a[s]["limitations"] if not is_statement_note(n)]]
print("changed tickers where a note other than the statement notes changed (should be 0):", len(other), other[:10])

groups = defaultdict(list)
for s in changed:
    key = (tuple(b[s]["limitations"]), b[s].get("quarters_note"), tuple(a[s]["limitations"]), a[s].get("quarters_note"))
    groups[key].append(s)
print(f"\n{len(groups)} distinct before -> after pairs among the changed tickers:")
for n, ((bl, bq, al, aq), slugs) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
    r = a[slugs[0]]
    print(f"\n== pair {n}: {len(slugs)} tickers, statements {r['sections']} with {r['rows']} rows, {r['quarters']} quarter rows,"
          f" {r['calcs_valued']} of {r['calcs']} calculations with a value")
    print("   tickers:", " ".join(slugs))
    print("   BEFORE:", " | ".join(head(x) for x in bl), "| quarters note:", "yes" if bq else "none")
    print("   AFTER: ", " | ".join(head(x) for x in al), "| quarters note:", "yes" if aq else "none")
    for x in al:
        if x not in bl:
            print("   NEW NOTE:", x)
    if aq != bq:
        print("   NEW QUARTERS NOTE:", aq)

unchanged_kinds = defaultdict(int)
for s in same:
    unchanged_kinds[" | ".join(head(x) for x in a[s]["limitations"]) or "(no notes)"] += 1
print("\nthe unchanged tickers, by their notes' first words:")
for k, v in sorted(unchanged_kinds.items(), key=lambda kv: -kv[1]):
    print(f"   {v:4d}  {k}")
