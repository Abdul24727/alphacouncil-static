"""Pair Argaam's English and Arabic statement-line labels by Argaam's own row id.

Argaam's statement grid gives every line a row id that does not change with the page's language
(`<tr id="tr384">` is Cost of Sales on the English page and its Arabic twin on the Arabic page), and
the label sits in the row's first cell (`<td data-fieldname="Cost of Sales">`). So the English label
and the Arabic label of one line are the two labels one row id carries on the two pages.

Read-only. Runs on the server with the pipeline's Python (it needs bs4):

  # the English side only: is each row id one English label everywhere? (a check on the key)
  python pair_labels.py --universe /opt/alphacouncil/backend/argaam/default_universe --check-ids

  # SUPERSEDED (2026-11-03): pairs from saved Saudi Arabic pages. harvest_ar_statements.py never
  # could save them (Argaam's bot challenge; no second sign-in), so use pair_from_gulf.py, which
  # pairs from the Gulf pages the nightly already saves in Arabic. Kept for the record:
  python pair_labels.py --universe … --ar-dir /root/argaam-ar-statements > pairs.json

The English page is the newest harvest run's `financial_statements_quarter.html` (the grid the
nightly parses); the Arabic page is `<ar-dir>/<ticker_key>.html`.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from argaam_pages import page_rows

ENGLISH_PAGE = "financial_statements_quarter.html"


def newest_english_page(ticker_dir: Path) -> Path | None:
    runs = sorted((ticker_dir / "harvest_runs").glob("run_*"), reverse=True)
    for run in runs:
        page = run / ENGLISH_PAGE
        if page.exists() and page.stat().st_size > 0:
            return page
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--universe", required=True, type=Path)
    ap.add_argument("--ar-dir", type=Path, help="folder of <ticker_key>.html Arabic pages")
    ap.add_argument("--check-ids", action="store_true", help="English side only: one label per row id?")
    ap.add_argument("--suffix", default="_TADAWUL")
    a = ap.parse_args()

    tickers = sorted(p for p in a.universe.iterdir() if p.is_dir() and p.name.endswith(a.suffix))
    en_by_id: dict[str, Counter] = defaultdict(Counter)
    pairs: dict[str, Counter] = defaultdict(Counter)  # English label -> Arabic labels seen
    report = {"tickers": len(tickers), "english_pages": 0, "arabic_pages": 0, "unpaired": []}

    for t in tickers:
        page = newest_english_page(t)
        if page is None:
            continue
        en = page_rows(page)
        report["english_pages"] += 1
        for rid, label in en.items():
            en_by_id[rid][label] += 1
        if a.check_ids or not a.ar_dir:
            continue
        ar_page = a.ar_dir / f"{t.name}.html"
        if not ar_page.exists():
            continue
        ar = page_rows(ar_page)
        report["arabic_pages"] += 1
        missing = sorted(set(en) ^ set(ar))
        if missing:  # a row on one page and not the other: report it, pair the rest
            report["unpaired"].append({"ticker": t.name, "row_ids": missing[:20], "count": len(missing)})
        for rid in set(en) & set(ar):
            pairs[en[rid]][ar[rid]] += 1

    ids_with_two_labels = {rid: dict(c) for rid, c in en_by_id.items() if len(c) > 1}
    report["row_ids"] = len(en_by_id)
    report["row_ids_with_more_than_one_english_label"] = len(ids_with_two_labels)
    report["examples"] = dict(list(ids_with_two_labels.items())[:10])
    if a.ar_dir and not a.check_ids:
        report["pairs"] = {en: c.most_common(1)[0][0] for en, c in sorted(pairs.items())}
        report["english_labels_with_more_than_one_arabic"] = {
            en: dict(c) for en, c in sorted(pairs.items()) if len(c) > 1
        }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
