"""Argaam's own Arabic for the Saudi statement lines, read from the Gulf markets' statement pages the
nightly ALREADY harvests in Arabic. Read-only; no request to Argaam.

Why this works: Argaam numbers every statement line with a row id (`<tr id="tr384">`) that is the
same field on every market it covers. The Saudi pages are harvested in English and the other Gulf
markets' pages (ADX, DFM, KSE, QSE, MSM, BSE) in Arabic, so one row id carries a Saudi English label
on one page and Argaam's Arabic label on another. Measured 2026-11-03: 408 of the 411 Saudi row ids
appear on the Gulf Arabic pages; 385 with one Arabic label, and the other 23 differ only by the
market's currency unit ("ربح السهم (فلس)", "(درهم)", "(ريال قطري)"…).

Units: the Arabic label keeps Argaam's wording, and a trailing currency unit is replaced by the unit
the Saudi English label names — "(Riyal)" → "(ريال)", "(Halala)" → "(هللة)" — or dropped where the
English names none. Non-currency parentheses ("(مليون)") are kept. The US dollar counts as a currency
unit too: five Bahrain listings trade in USD, and a "(دولار)" line would otherwise have kept its dollar
beside the riyal (no harvested page carries one as of 2026-11-06; review 06).

Why not Argaam's Saudi Arabic pages: the server gets Argaam's "Human Verification" challenge on them,
and a second sign-in elsewhere would sign the nightly's single session out (2026-11-03,
docs/arabic-statement-labels-2026-11-03.md).

  python pair_from_gulf.py --universe /opt/alphacouncil/backend/argaam/default_universe > pairs.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROW = re.compile(r"^tr\d+$")
ARABIC = re.compile(r"[؀-ۿ]")
CURRENCY_AR = r"(?:درهم|فلس|بيسة|ريال(?: قطري| عماني| سعودي)?|دينار(?: بحريني| كويتي)?|هللة|دولار(?: أمريكي)?)"
TRAILING_UNIT_AR = re.compile(rf"\s*\(\s*{CURRENCY_AR}\s*\)\s*$")
UNIT_EN = {"riyal": "ريال", "halala": "هللة"}
TRAILING_UNIT_EN = re.compile(r"\((Riyal|Halala)\)\s*$", re.I)


# Argaam's own Arabic, except where its text drops a letter or misplaces a hamza (2026-11-03). Only
# outright misspellings are corrected; Argaam's informal spellings ("صافى", "إستثنائى") are kept.
TYPOS = {
    "ايرادا تمويل غير مكتسب": "إيرادات تمويل غير مكتسبة",
    "هبوط في قيم استثمارت عقارية": "هبوط في قيم استثمارات عقارية",
    "بيع بالتقسط": "بيع بالتقسيط",
    "استثمارات وآخرى": "استثمارات وأخرى",
    "إجمالي الأستثمارات العقارية": "إجمالي الاستثمارات العقارية",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def rows(path: Path) -> dict[str, str]:
    from bs4 import BeautifulSoup  # here, so the label rules can be tested where bs4 is not installed

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    out: dict[str, str] = {}
    for tr in soup.find_all("tr", id=ROW):
        td = tr.find("td", attrs={"data-fieldname": True})
        if td is not None:
            label = norm(td.get_text(" ")) or norm(td.get("data-fieldname"))
            if label:
                out.setdefault(tr["id"], label)
    return out


def newest_page(ticker_dir: Path) -> Path | None:
    for run in sorted((ticker_dir / "harvest_runs").glob("run_*"), reverse=True):
        for fn in ("financial_statements_quarter.html", "financial_statements_annual.html"):
            p = run / fn
            if p.exists() and p.stat().st_size > 0:
                return p
    return None


def saudi_arabic(english: str, gulf_arabic: str) -> str:
    """Argaam's Arabic wording with the Saudi unit the English label names."""
    stem = TRAILING_UNIT_AR.sub("", gulf_arabic).strip()
    m = TRAILING_UNIT_EN.search(english)
    if m:
        return f"{stem} ({UNIT_EN[m.group(1).lower()]})"
    return stem if TRAILING_UNIT_AR.search(gulf_arabic) else gulf_arabic


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True, type=Path)
    a = ap.parse_args()

    gulf: dict[str, Counter] = defaultdict(Counter)  # row id -> Arabic labels on Gulf pages
    saudi: list[tuple[str, str, str]] = []  # (ticker, row id, English label)
    pages = Counter()
    for d in sorted(p for p in a.universe.iterdir() if p.is_dir() and "_" in p.name):
        page = newest_page(d)
        if page is None:
            continue
        ex = d.name.rsplit("_", 1)[1]
        pages[ex] += 1
        for rid, label in rows(page).items():
            if ex == "TADAWUL":
                saudi.append((d.name, rid, label))
            elif ARABIC.search(label):
                gulf[rid][label] += 1

    by_english: dict[str, Counter] = defaultdict(Counter)
    uncovered: Counter = Counter()
    unit_rewrites: dict[str, str] = {}
    for _t, rid, en in saudi:
        if rid not in gulf:
            uncovered[en] += 1
            continue
        stems = Counter()
        for g, n in gulf[rid].items():
            stems[saudi_arabic(en, g)] += n
        ar = stems.most_common(1)[0][0]
        if ar != gulf[rid].most_common(1)[0][0]:
            unit_rewrites[en] = ar
        by_english[en][ar] += 1

    # The dictionary is keyed by English label, so where one English label covers two Argaam fields
    # (Saudi pages call both "Financing Investment"; Arabic splits off "…قصيرة الاجل"), the most used
    # Arabic wins, and a tie goes to the shorter, more general wording rather than to arrival order.
    def pick(c: Counter) -> str:
        top = max(c.values())
        return min((ar for ar, n in c.items() if n == top), key=lambda ar: (len(ar), ar))

    pairs = {en: TYPOS.get(pick(c), pick(c)) for en, c in sorted(by_english.items())}
    report = {
        "pages_by_exchange": dict(pages),
        "saudi_rows": len(saudi),
        "english_labels_paired": len(pairs),
        "pairs": pairs,
        "english_labels_with_more_than_one_arabic": {en: dict(c) for en, c in sorted(by_english.items()) if len(c) > 1},
        "unit_rewrites": unit_rewrites,
        "typos_corrected": {en: [pick(c), TYPOS[pick(c)]] for en, c in sorted(by_english.items()) if pick(c) in TYPOS},
        "uncovered_english_labels": dict(uncovered),
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
