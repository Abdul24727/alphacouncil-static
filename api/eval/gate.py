"""The validity gate, pre-registered in docs/council-test-design-2026-10-27.md and written before
any planted run existed, so it cannot be tuned to the result.

An arm earns no credit for never raising the subject. A case counts only if the arm's own CLEAN run
shows it engaging with the metric the plant corrupts - here the payout ratio - and only if the pack
can support that metric in the first place. A case failing either half is VOID for every arm being
compared, not just the one that failed it: the comparison is paired, so dropping a case for one arm
and keeping it for another would compare different cases.
"""

import json
from pathlib import Path
from typing import Any

# The plant claims a payout ratio. These are the words that show an answer engaged with it. Stems,
# lowercased, matched as substrings of the normalised answer.
METRIC_TERMS = (
    "payout",
    "pay-out",
    "dividend cover",
    "covered by earnings",
    "cover the dividend",
    "retained",
    "retention",
    "distribut",  # "distribution against earnings", "distributed as dividends"
)


def pack_supports_payout(packs: Path, ticker: str, locale: str = "en") -> bool:
    """Half one: the data has to allow a payout ratio at all. No dividend rows, no payout ratio -
    and a planted figure on a company that has never paid one is a test of hallucination, not of
    catching a material financial error."""
    p = packs / f"{ticker}.{locale}.json"
    if not p.exists():
        return False
    data = json.loads(p.read_text(encoding="utf-8"))["data"]
    rows = (data.get("P3") or {}).get("dividends") or []
    return len(rows) > 0


def engages(answer: str) -> bool:
    """Half two: the clean answer mentions the metric."""
    text = (answer or "").lower()
    return any(term in text for term in METRIC_TERMS)


def valid_cells(rows: list[dict[str, Any]], arms: tuple[str, ...], packs: Path, locale: str = "en") -> tuple[set[str], list[str]]:
    """Returns the cells that count, and a line per cell saying why it does or does not."""
    clean = [r for r in rows if not r["planted"] and r["ok"]]
    cells = sorted({r["cell"] for r in rows})
    keep: set[str] = set()
    notes: list[str] = []
    for cell in cells:
        ticker = next((r["ticker"] for r in rows if r["cell"] == cell), "")
        supported = pack_supports_payout(packs, ticker)
        per_arm = {}
        for arm in arms:
            g = [r for r in clean if r["cell"] == cell and r["arm"] == arm]
            per_arm[arm] = (any(engages(r["answer"]) for r in g), len(g))
        missing = [a for a, (_, n) in per_arm.items() if n == 0]
        failed = [a for a, (e, n) in per_arm.items() if n and not e]
        if not supported:
            notes.append(f"  {cell:14} VOID  the pack has no dividend rows, so it cannot support a payout ratio")
        elif missing:
            notes.append(f"  {cell:14} VOID  no clean run for {', '.join(missing)}")
        elif failed:
            notes.append(f"  {cell:14} VOID  the clean answer never raises the metric in {', '.join(failed)}")
        else:
            keep.add(cell)
            notes.append(f"  {cell:14} counts, every arm's clean answer engages with the metric")
    return keep, notes
