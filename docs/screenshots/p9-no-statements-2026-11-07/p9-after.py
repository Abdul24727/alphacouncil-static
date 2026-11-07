"""What the fixed code (branch `rebuild`) gives for the reproduced cases. No network, no model.
Run from api/: .venv/Scripts/python.exe ../docs/screenshots/p9-no-statements-2026-11-07/p9-after.py"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.debate.pack import Pack, Source  # noqa: E402
from app.evidence import Items, dataset_of  # noqa: E402

here = Path(__file__).resolve().parent
print("1. P9 for a company with no statement rows (4330's case), from the fixed evidence.dataset_of:")
ds = dataset_of(Items([], []), ticker_key="4330_TADAWUL", sector="unknown", currency="SAR")
print("   statements:", ds.statements, "| quarters:", ds.quarters,
      "| calculations with a value:", sum(c.value is not None for c in ds.calculations), "of", len(ds.calculations))
for lim in ds.limitations:
    print("   LIMITATION:", lim)

print("\n2. The pack the room reads for 4330, with beta's P9 as it is today (before the fix reaches it):")
before = json.loads((here / "beta-4330-evidence-before.json").read_text(encoding="utf-8"))
pack = Pack(ticker_key="4330_TADAWUL", slug="4330", header="DATA PACK. (header as built live)",
            fetched_at="2026-11-07", data={"P9": before}, sources={"P9": Source(title_en="P9", title_ar="P9", ok=True)})
print("   " + pack.prompt().split("\n")[1])

print("\n3. The comparison's frozen packs (P1 to P8, no P9):")
for path in sorted((here.parents[2] / "docs" / "eval" / "packs").glob("*.json")):
    p = Pack.model_validate_json(path.read_text(encoding="utf-8"))
    line = p.prompt().split("\n")[1]
    print(f"   {path.name}: {line[:80]}...")
