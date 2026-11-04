"""Merge English->Arabic pairs (pair_from_gulf.py or pair_labels.py output) into
web/src/content/data-labels.json.

Adds only English labels the dictionary does not know yet, compared the way lib/data-labels.ts
compares: whitespace collapsed, case ignored, and the FIRST pair for a label is the one the site
uses. Where the dictionary already has a DIFFERENT Arabic for a label, nothing is overwritten: it is
listed for the owner to choose. Two labels in the batch that differ only by case or spacing are one
label to the site, so only the first is added; the rest are listed apart from the dictionary
differences. Local, no network.

  python scripts/argaam_ar_labels/merge_pairs.py pairs.json            # report only
  python scripts/argaam_ar_labels/merge_pairs.py pairs.json --write    # add the missing pairs
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DICT = Path(__file__).resolve().parents[2] / "web" / "src" / "content" / "data-labels.json"
ARABIC = re.compile(r"[؀-ۿ]")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def append_pairs(raw: str, added: list[list[str]]) -> str:
    """Append the new pairs as one blank-line-separated group at the end of "pairs", leaving every
    existing byte as it is (the file groups its pairs with blank lines, one [en, ar] per line)."""
    start = raw.index('"pairs": [')
    end = raw.index("\n  ]", start)
    group = ",\n".join(f"    {json.dumps(p, ensure_ascii=False)}" for p in added)
    out = raw[:end] + ",\n\n" + group + raw[end:]
    after = json.loads(out)["pairs"]
    assert after == json.loads(raw)["pairs"] + added, "the appended file does not read back as old + added"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", type=Path, help="pair_from_gulf.py or pair_labels.py output (JSON with a 'pairs' object)")
    ap.add_argument("--dict", type=Path, default=DICT)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    report = json.loads(a.pairs.read_text(encoding="utf-8"))
    pairs: dict[str, str] = report.get("pairs", report)
    data = json.loads(a.dict.read_text(encoding="utf-8"))
    known: dict[str, str] = {}
    for en, ar in data["pairs"]:
        known.setdefault(norm(en), ar)  # first wins, as in lib/data-labels.ts
    batch: dict[str, list[str]] = {}  # labels added by this run: key -> [en, ar]

    added, same, differs, variants, skipped = [], 0, [], [], []
    for en, ar in sorted(pairs.items()):
        en, ar = re.sub(r"\s+", " ", en).strip(), re.sub(r"\s+", " ", ar).strip()
        if not en or not ar or ARABIC.search(en) or not ARABIC.search(ar):
            skipped.append([en, ar])  # an English page row in Arabic, or an Arabic row with no Arabic
            continue
        k = norm(en)
        if k in batch:
            first = batch[k]
            variants.append({"en": en, "argaam": ar, "same_as_added": norm(first[1]) == norm(ar),
                             "added_as": first})
        elif k not in known:
            added.append([en, ar])
            batch[k] = [en, ar]
        elif norm(known[k]) == norm(ar):
            same += 1
        else:
            differs.append({"en": en, "dictionary": known[k], "argaam": ar})

    print(json.dumps({"pairs_in": len(pairs), "added": len(added), "already_same": same,
                      "differs_kept_dictionary": len(differs),
                      "case_variants_in_batch": len(variants),
                      "skipped": skipped, "differs_list": differs, "variants_list": variants,
                      "added_list": added}, ensure_ascii=False, indent=1))
    if a.write and added:
        raw = a.dict.read_text(encoding="utf-8")
        a.dict.write_text(append_pairs(raw, added), encoding="utf-8", newline="")
        print(f"wrote {len(added)} pairs to {a.dict}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
