"""Read P9 (/evidence) for every ticker on beta through the tunnel, GET only, and keep its notes word for word.
Usage: python -X utf8 p9-notes-sweep.py <out.json>
Records, per ticker: HTTP status, statement sections, statement rows, quarter rows, the quarters' note, every
limitation in full, and how many calculations have a value. Run once before the P9 release and once after it, then
compare with p9-notes-compare.py."""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

B = "http://127.0.0.1:8200/v1"


def get(path, tries=4):
    for n in range(tries):
        try:
            with urllib.request.urlopen(B + path, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception:  # a stalled tunnel: wait and retry
            if n == tries - 1:
                raise
            time.sleep(5)


started = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
_, uni = get("/tickers")
out = []
for t in uni:
    st, d = get("/tickers/" + urllib.parse.quote(t["slug"], safe="") + "/evidence")
    rec = {"slug": t["slug"], "exchange": t["exchange"], "status": st}
    if d:
        rec.update(
            sections=[s["section"] for s in d["statements"]],
            rows=sum(len(s["rows"]) for s in d["statements"]),
            quarters=len(d["quarters"]["rows"]) if d.get("quarters") else 0,
            quarters_note=d["quarters"].get("note") if d.get("quarters") else None,
            calcs_valued=sum(1 for c in d["calculations"] if c.get("value") is not None),
            calcs=len(d["calculations"]),
            limitations=d["limitations"],
        )
    out.append(rec)
_, health = get("/health")
json.dump({"started": started, "finished": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
           "health": health, "tickers": out}, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("started", started, "| tickers:", len(out), "| non-200:", sum(r["status"] != 200 for r in out),
      "| health:", health)
