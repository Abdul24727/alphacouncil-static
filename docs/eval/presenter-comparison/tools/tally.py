"""Total the verified wrong claims of the A-vs-P comparison per arm, session and category.

Usage (from this folder): python -X utf8 tally.py
Reads ../verified-claims.json only.
"""
import collections
import json
from pathlib import Path

rows = json.loads((Path(__file__).parent.parent / "verified-claims.json").read_text(encoding="utf-8"))
for arm in "AP":
    rs = [r for r in rows if r["session"].startswith(arm)]
    print(arm, "claims", len(rs),
          "| planted", sum(r["session"].endswith("planted") for r in rs),
          "| clean", sum(r["session"].endswith("clean") for r in rs),
          "| minor", sum(r["minor"] for r in rs),
          "| in the Chair's answer", sum(r["stage"] == "verdict" for r in rs),
          "| presenter-added", sum(r["presenter_added"] for r in rs),
          "| by category", dict(collections.Counter(r["category"] for r in rs)))
for p in sorted({r["probe"] for r in rows}):
    print(p, {s: sum(1 for r in rows if r["probe"] == p and r["session"] == s)
              for s in ("A planted", "P planted", "A clean", "P clean")})
