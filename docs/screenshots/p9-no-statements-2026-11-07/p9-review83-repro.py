"""Review 83's two reproductions, run on whatever api/ code is checked out. No network, no model.
Run from api/: .venv/Scripts/python.exe -X utf8 ../docs/screenshots/p9-no-statements-2026-11-07/p9-review83-repro.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.evidence import Cell, Items, dataset_of  # noqa: E402

print("1. 30 numbered protected income-statement lines from 2024, and one unprotected 2025 figure (Zakat & Tax 555)")
rows = [Cell(label="Net Income", section="Income Statement", fiscal_year=2024, value=float(i + 1), item_index=i,
             period_end="2024-12") for i in range(30)]
rows.append(Cell(label="Zakat & Tax", section="Income Statement", fiscal_year=2025, value=555.0, item_index=30,
                 period_end="2025-12"))
ds = dataset_of(Items(rows, []), ticker_key="X", sector="unknown", currency="SAR")
s = ds.statements[0]
for i, year in enumerate(s.columns[1:], 1):
    print(f"   column {year}: {sum(1 for r in s.rows if len(r) > i and r[i] is not None)} figures shown")
print(f"   rows shown {len(s.rows)}, rows_omitted {s.rows_omitted}, period_end {s.period_end}")
print("   Zakat & Tax 555 shown:", any(r[0] == "Zakat & Tax" and 555.0 in r[1:] for r in s.rows))
for lim in ds.limitations:
    print("   LIMITATION:", lim)

print("\n2. no annual statement, one reported quarter on a line outside the selected quarterly series")
q = Cell(label="Other operating gain", section="Income Statement", fiscal_year=2026, value=12.0, period="Q",
         period_end="2026-06")
ds = dataset_of(Items([], [q]), ticker_key="X", sector="unknown", currency="SAR")
print("   quarters in P9:", ds.quarters)
for lim in ds.limitations:
    print("   LIMITATION:", lim)
print("   claims the SOURCE has no quarterly result:",
      any(lim.startswith("NO FINANCIAL STATEMENTS: the source holds no") for lim in ds.limitations))
