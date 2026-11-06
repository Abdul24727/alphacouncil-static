"""Reproduce every count in audit.md and RESULT.md from the saved files.

Usage (from this folder): python -X utf8 tally.py
Reads ../verified-claims.json, ../flag-classifications.json (written by classify_flags.py) and
../probe-results.jsonl only.
"""
import collections
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent.parent
claims = json.loads((HERE / "verified-claims.json").read_text(encoding="utf-8"))
flags = json.loads((HERE / "flag-classifications.json").read_text(encoding="utf-8"))
records = [json.loads(line) for line in (HERE / "probe-results.jsonl").read_text(encoding="utf-8").splitlines()
           if line.strip()]

print("WRONG CLAIMS THAT REACH THE READER (verified-claims.json)")
for arm in "AP":
    rs = [r for r in claims if r["session"].startswith(arm)]
    print(f"  {arm}: {len(rs)} | planted {sum(r['session'].endswith('planted') for r in rs)}"
          f" | clean {sum(r['session'].endswith('clean') for r in rs)} | minor {sum(r['minor'] for r in rs)}"
          f" | in the Chair's answer {sum(r['stage'] == 'verdict' for r in rs)}"
          f" | presenter-added {sum(r['presenter_added'] for r in rs)}")
    print("     by category", dict(collections.Counter(r["category"] for r in rs)))
for p in sorted({r["probe"] for r in claims}):
    print("  ", p, {s: sum(1 for r in claims if r["probe"] == p and r["session"] == s)
                    for s in ("A planted", "P planted", "A clean", "P clean")})

print("UNVERIFIED FLAGS (flag-classifications.json; the plant's own opening excluded)")
for s in ("A planted", "A clean", "P planted", "P clean"):
    c = collections.Counter(f["class"] for f in flags if f["session"] == s)
    print(f"  {s}: {sum(c.values())} flags | ok {c['ok']} | wrong {c['wrong']} | invented {c['invented']}"
          f" | asserted wrong or invented {c['wrong'] + c['invented']}")

print("COST (probe-results.jsonl)")
a = [r["cost_usd"] for r in records if r["arm"] == "A"]
p = [r["cost_usd"] for r in records if r["arm"] == "P"]
analyst = []
for r in records:
    if r["arm"] != "P":
        continue
    spent = sum((t.get("usage") or {}).get("cost_usd") or 0 for t in r.get("turns") or []
                if t["stage"] == "brief" and not (t.get("usage") or {}).get("shared"))
    spent += sum(f["usage"]["cost_usd"] for f in r.get("failed_calls") or [] if f["stage"] == "brief")
    analyst.append(spent)
print(f"  A mean ${statistics.mean(a):.4f} | P mean ${statistics.mean(p):.4f} ({statistics.mean(p) / statistics.mean(a):.1%} of A)")
print(f"  P's analyst, every attempt and the failed session included: ${sum(analyst):.6f} in all,"
      f" ${statistics.mean(analyst):.4f} a session ({statistics.mean(analyst) / statistics.mean(a):.1%} of A)")
