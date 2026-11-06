"""F-16's check after the publish, read-only. Runs on the server with the pipeline's Python, on stdin:

    ssh root@alphacouncil.tech '/opt/alphacouncil/pipeline-venv/bin/python -X utf8 - 2026-11-06' \
        < scripts/pipeline-checks/f16_after_publish.py

The argument is the publish day (UTC); it defaults to today. Every item prints PASS or FAIL; the exit
code is the number of FAILs. Nothing is written anywhere. The English-label sweep is the last step of the
checklist and runs from a workstation (docs/pipeline-guard-statement-headings-2026-11-06.md).
"""
import datetime as dt
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path

DAY = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
LOGS = Path("/opt/alphacouncil/logs")
PARSER = Path("/opt/alphacouncil/backend/llm-council/parse_financial_statements.py")
PARSER_MD5 = "9a0b7aa05da2029167c8de1a5fffaf4c"  # the patched parser, applied 2026-11-05 22:44 UTC
# F16_DB points the data checks at another copy (the dry run's, to show they pass on fixed data).
PUBLISHED = Path(os.environ.get("F16_DB", "/var/lib/alphacouncil/screening.sqlite"))
NINE = ["ADAV.AD_ADX", "ADNIC_ADX", "AMCREIT_DFM", "AMLAK_DFM", "DSI_DFM", "DUBAIRES_DFM", "EMSTEEL_ADX", "QIC_ADX", "UPP_DFM"]
# ADNIC's lines under its cash-flow heading carry no figures, so it gets no Cash Flow Statement rows.
WITH_CASH_FLOW = [t for t in NINE if t != "ADNIC_ADX"]
# The cash-flow lines F-16 moves out of the balance sheets (dry run, /tmp/f16/c). "اخرى" (other) is left
# out: it is a balance-sheet line too.
CASH_FLOW_LINES = [
    "( الزيادة ) او النقص في الاستثمارات", "( الزيادة ) او النقص في الممتلكات و المعدات", "إصدار وحدات",
    "اصدار الاسهم", "الاهلاكات", "التدفق النقدي الحر", "التدفق النقدي من الانشطة الاستثمارية",
    "التدفق النقدي من الانشطة التشغيلية", "التدفق النقدي من الانشطة التمويلية", "التوزيعات النقدية",
    "الزيادة ( النقص ) في الديون", "النقد و ما يعادله بداية الفترة", "النقد و ما يعادله في نهاية الفترة",
    "صافي ( الزيادة ) / النقص في الموجودات التشغيلية", "صافي الارباح", "صافي التغير في النقد و ما يعادله",
    "صافي الدخل من العمليات التشغيلية", "صافي الزيادة / ( النقص ) في المطلوبات التشغيلية",
]
fails = 0


def check(ok: bool, what: str, detail: str = "") -> None:
    global fails
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {what}" + (f"  [{detail}]" if detail else ""))


def text(p: Path) -> str:
    """The log and, the logs being rotated at 01:00 UTC, its rotated copy (`<name>.1`)."""
    parts = [q.read_text(encoding="utf-8", errors="replace") for q in (p.with_name(p.name + ".1"), p) if q.exists()]
    return "\n".join(parts)


print(f"F-16 after-publish check for {DAY} (UTC)")

# 1. The patched parser is the one the night ran, and the night's parse step finished.
check(hashlib.md5(PARSER.read_bytes()).hexdigest() == PARSER_MD5, "the parser on disk is the patched one", PARSER_MD5[:8])
run_log = LOGS / f"daily_{DAY.replace('-', '')}.log"
log = text(run_log)
check(bool(log), f"the night's run log exists ({run_log.name})")
check("[OK step 8] parse_financial_statements" in log, "the parse step finished OK")
done = re.findall(r"DONE: (\d+) ticker\(s\), (\d+) line-item-rows", log)
check(bool(done), "the parse step reported its totals", f"{done[-1][0]} tickers, {done[-1][1]} rows" if done else "")
unknown = [ln for ln in log.splitlines() if "UNKNOWN STATEMENT HEADING" in ln]
check(not unknown, "no UNKNOWN STATEMENT HEADING warning in the parse", unknown[0][:160] if unknown else "")
check(bool(re.search(r"ALERT \[OK\]", log)), "the night's run ended with ALERT [OK]")

# 2. That night was published, healthy, and the served file is from it.
pub = [ln for ln in text(LOGS / "db_publish.log").splitlines() if ln.startswith(DAY) and "published. /healthz/deep=ok" in ln]
check(bool(pub), f"published on {DAY} with /healthz/deep=ok", pub[-1][:80] if pub else "")
mtime = dt.datetime.fromtimestamp(PUBLISHED.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
check(mtime.startswith(DAY), "the served screening.sqlite is from that day", mtime)

# 3. The served data: no cash flow left in the nine balance sheets; eight cash-flow statements.
db = sqlite3.connect(f"file:{PUBLISHED}?mode=ro", uri=True)
marks = ",".join("?" * len(NINE))
lines = ",".join("?" * len(CASH_FLOW_LINES))
left = db.execute(f"SELECT ticker_key, COUNT(*) FROM fundamentals_lineitems WHERE section='Balance Sheet' "
                  f"AND ticker_key IN ({marks}) AND line_item_label IN ({lines}) GROUP BY 1", NINE + CASH_FLOW_LINES).fetchall()
check(not left, "no cash-flow line in the nine companies' balance sheets", str(left))
cf = dict(db.execute(f"SELECT ticker_key, COUNT(*) FROM fundamentals_lineitems WHERE section='Cash Flow Statement' "
                     f"AND ticker_key IN ({marks}) GROUP BY 1", NINE).fetchall())
check(all(cf.get(t, 0) > 0 for t in WITH_CASH_FLOW), "the eight have a Cash Flow Statement",
      ", ".join(f"{t.split('_')[0]} {cf.get(t, 0)}" for t in WITH_CASH_FLOW))
check(cf.get("ADNIC_ADX", 0) == 0, "ADNIC has none (its cash-flow lines carry no figures)", str(cf.get("ADNIC_ADX", 0)))
amlak = db.execute("SELECT COUNT(*) FROM fundamentals_lineitems WHERE ticker_key='AMLAK_DFM' AND section='Balance Sheet' "
                   "AND fiscal_year=(SELECT MAX(fiscal_year) FROM fundamentals_lineitems WHERE ticker_key='AMLAK_DFM' AND section='Balance Sheet')").fetchone()[0]
check(amlak < 50, "AMLAK's newest balance sheet is back to its own lines", f"{amlak} rows (50 before, 31 in the dry run)")

print(f"{'ALL PASS' if not fails else f'{fails} FAIL'}")
sys.exit(fails)
