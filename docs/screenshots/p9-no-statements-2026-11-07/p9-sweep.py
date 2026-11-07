"""Read P9 (/evidence) for every ticker on beta through the tunnel, GET only, one at a time.
Records, per ticker: HTTP status, statement sections, quarter rows, calculations with a value, limitations' first words."""
import json, sys, urllib.request, urllib.error, urllib.parse
B = "http://127.0.0.1:8200/v1"
def get(path):
    try:
        with urllib.request.urlopen(B + path, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None
code, uni = get("/tickers")
out = []
for t in uni:
    st, d = get("/tickers/" + urllib.parse.quote(t["slug"], safe="") + "/evidence")
    rec = {"slug": t["slug"], "exchange": t["exchange"], "status": st}
    if d:
        rec.update(sections=[s["section"] for s in d["statements"]], rows=sum(len(s["rows"]) for s in d["statements"]),
                   quarters=len(d["quarters"]["rows"]) if d.get("quarters") else 0,
                   calcs_valued=sum(1 for c in d["calculations"] if c.get("value") is not None),
                   calcs=len(d["calculations"]), sector=d["sector"],
                   limitations=[l.split(":")[0][:60] for l in d["limitations"]])
    out.append(rec)
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
none = [r for r in out if r.get("rows") == 0]
print("tickers:", len(out), "| non-200:", sum(r["status"] != 200 for r in out), "| no statement rows:", len(none))
from collections import Counter
print("by exchange (no statements):", dict(Counter(r["exchange"] for r in none)))
print("limitations seen on no-statement tickers:", dict(Counter(l for r in none for l in r["limitations"])))
print("examples:", [r["slug"] for r in none[:8]])
