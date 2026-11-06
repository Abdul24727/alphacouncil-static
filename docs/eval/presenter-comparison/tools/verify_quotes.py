"""Check that every counted claim's quote is an exact substring of the turn it is attributed to:
same probe, arm, planted or clean, stage and seat, in the saved record.

Usage (from this folder): python -X utf8 verify_quotes.py
Reads ../verified-claims.json and ../probe-results.jsonl only. Prints any miss and the totals.
Whitespace runs are collapsed and typographic quotes and dashes folded, nothing else.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent.parent
claims = json.loads((HERE / "verified-claims.json").read_text(encoding="utf-8"))
records = [json.loads(line) for line in (HERE / "probe-results.jsonl").read_text(encoding="utf-8").splitlines()
           if line.strip()]


def text(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ".join(text(x) for x in v)
    if isinstance(v, dict):
        return " ".join(text(x) for x in v.values())
    return ""


def norm(s):
    for a, b in (("’", "'"), ("‘", "'"), ("—", "-"), ("–", "-"), ("…", "...")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s)


missing = 0
for c in claims:
    arm, kind = c["session"].split()
    rec = next(r for r in records if r["probe"] == c["probe"] and r["arm"] == arm and r["planted"] == (kind == "planted"))
    turns = [t for t in rec.get("turns") or [] if t["stage"] == c["stage"] and t.get("seat") == c["seat"]]
    if not any(norm(c["quote"]) in norm(text(t.get("data") or {})) for t in turns):
        missing += 1
        print("MISSING", c["probe"], c["session"], c["stage"], c["seat"], "|", c["quote"][:70])
print(f"{len(claims)} claims checked against their stated turns; {missing} missing")
