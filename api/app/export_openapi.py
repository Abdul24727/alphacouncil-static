"""Write the OpenAPI contract that generates web/src/lib/api/schema.d.ts.

    uv run python -m app.export_openapi
"""

import json
from pathlib import Path

from .main import app

OUT = Path(__file__).resolve().parents[1] / "openapi.json"

if __name__ == "__main__":
    OUT.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}")
