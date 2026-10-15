"""Merge a JSON fragment of UI strings into messages/en.json and messages/ar.json.

    python -I -X utf8 scripts/merge-messages.py path/to/fragment.json

The fragment has the shape {"en": {...}, "ar": {...}}; top-level keys replace
the same keys in each messages file, so both languages stay in step.
"""

import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1] / "messages"
fragment = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if set(fragment) != {"en", "ar"} or set(fragment["en"]) != set(fragment["ar"]):
    sys.exit("fragment must have matching 'en' and 'ar' sections")

for locale, extra in fragment.items():
    path = root / f"{locale}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(extra)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{path.name}: {', '.join(extra)}")
