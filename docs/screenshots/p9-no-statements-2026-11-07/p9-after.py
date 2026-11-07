"""What the fixed code (branch `rebuild`) gives for every case review 79 names. No network, no model.
Run from api/: .venv/Scripts/python.exe -X utf8 ../docs/screenshots/p9-no-statements-2026-11-07/p9-after.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.debate.pack import Pack, Source, no_statements_note  # noqa: E402
from app.evidence import Cell, Items, dataset_of  # noqa: E402

here = Path(__file__).resolve().parent


def p9_of(items):
    return dataset_of(items, ticker_key="X_TADAWUL", sector="unknown", currency="SAR", price=26.16)


def show(name, items):
    ds = p9_of(items)
    quarters = ds.quarters.rows if ds.quarters else None
    print(f"\n== {name}")
    print(f"   statements: {[(s.section, s.rows) for s in ds.statements]} | quarters: {quarters}"
          f" | calculations with a value: {sum(c.value is not None for c in ds.calculations)} of {len(ds.calculations)}")
    if ds.quarters:
        print("   QUARTERS NOTE:", ds.quarters.note)
    for lim in ds.limitations:
        print("   LIMITATION:", lim)
    print("   PACK NOTE:", no_statements_note({"P9": ds.model_dump()}))


def cell(label, section, year, value, end=None):
    return Cell(label=label, section=section, fiscal_year=year, value=value, period_end=end)


show("1. empty P9 (4330's case: no statement rows at all)", Items([], []))
show("2. quarterly-only P9 (ALFIRDOU and TAALEEM on 2026-11-07)", Items([], [cell("Net Income", "Income Statement", 2026, 77.0, "2026-06")]))
show("3. all-null statement rows", Items([cell("Net Income", "Income Statement", 2025, None),
                                          cell("Total Assets", "Balance Sheet", 2025, None)], []))
Q77 = cell("Net Income", "Income Statement", 2026, 77.0, "2026-06")
TA900 = cell("Total Assets", "Balance Sheet", 2025, 900.0)
TWO_YEARS = [cell("Net Income", "Income Statement", 2025, 50.0), cell("Net Income", "Income Statement", 2024, 40.0), TA900]
show("4. balance-sheet-only P9 (no income figure at all)", Items([TA900], []))
show("4b. a balance sheet and income-statement quarters (232's case on 2026-11-07)", Items([TA900], [Q77]))
show("5. normal: an income statement and a balance sheet, two years", Items(TWO_YEARS, []))
show("5b. normal, with quarters (the quarters' note is the one it always was)", Items(TWO_YEARS, [Q77]))

print("\n== 6. packs with no P9, and with a P9 error: the note, and that it comes before the data")
for name, data in (("no P9", {"P1": {"quote": 1}}), ("P9 error", {"P1": {"quote": 1}, "P9": {"error": "unavailable"}})):
    pack = Pack(ticker_key="X", slug="x", header="DATA PACK.", fetched_at="2026-11-07", data=data,
                sources={t: Source(title_en=t, title_ar=t, ok=True) for t in data})
    lines = pack.prompt().split("\n")
    first_data = next(i for i, line in enumerate(lines, 1) if line.startswith("[P"))
    print(f"   {name}: line 2 = {lines[1][:110]}... | the data starts at line {first_data}")

print("\n== 7. 4330's pack with beta's P9 as it is today, and the comparison's five frozen packs")
before = json.loads((here / "beta-4330-evidence-before.json").read_text(encoding="utf-8"))
print("   4330:", no_statements_note({"P9": before})[:120], "...")
for path in sorted((here.parents[2] / "docs" / "eval" / "packs").glob("*.json")):
    p = Pack.model_validate_json(path.read_text(encoding="utf-8"))
    print(f"   {path.name}: {p.prompt().split(chr(10))[1][:90]}...")
