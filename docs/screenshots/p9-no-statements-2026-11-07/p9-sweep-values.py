"""Read P9 (/v1/tickers/<slug>/evidence) on beta for every ticker, through the tunnel, GET only, one at a time,
and count REPORTED NUMBERS rather than rows (review 80): a row whose cells after the label are null holds none.
It also counts, per section, the rows with no number at all (review 81).
Writes one JSON line per ticker. Usage: python -I p9-sweep-values.py <out.json>"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

B = "http://127.0.0.1:8200/v1"


def get(path, tries=3):
    """One GET; a timeout (a stalled tunnel) is retried, an HTTP error is recorded as its status."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(B + path, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, None
        except (TimeoutError, urllib.error.URLError):
            if attempt == tries - 1:
                raise


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def numbers(rows):
    return sum(1 for row in rows or [] for v in row[1:] if is_number(v))


def null_rows(rows):
    """Rows with no number after the label: the per-row measure review 81 asked for."""
    return sum(1 for row in rows or [] if not any(is_number(v) for v in row[1:]))


_, uni = get("/tickers")
out = []
for t in uni:
    status, d = get("/tickers/" + urllib.parse.quote(t["slug"], safe="") + "/evidence")
    rec = {"slug": t["slug"], "exchange": t["exchange"], "status": status}
    if d:
        q = d.get("quarters") or {}
        rec.update(
            statement_rows={s["section"]: len(s["rows"]) for s in d["statements"]},
            statement_numbers={s["section"]: numbers(s["rows"]) for s in d["statements"]},
            statement_null_rows={s["section"]: null_rows(s["rows"]) for s in d["statements"]},
            quarter_rows=len(q.get("rows") or []),
            quarter_numbers=numbers(q.get("rows")),
            quarter_null_rows=null_rows(q.get("rows")),
            quarter_columns=(q.get("columns") or [])[1:],
            calcs_valued=sum(1 for c in d["calculations"] if c.get("value") is not None),
            calcs=len(d["calculations"]),
            limitations=[lim.split(":")[0][:60] for lim in d["limitations"]],
        )
    out.append(rec)
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
    f.write("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n]\n")
print("tickers:", len(out), "| non-200:", sum(r["status"] != 200 for r in out))
