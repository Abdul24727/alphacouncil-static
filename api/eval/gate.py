"""The validity gate, pre-registered in docs/council-test-design-2026-10-27.md.

An arm earns no credit for never raising the subject. A case counts only if the arm's own CLEAN run
shows it engaging with the metric that cell's plant corrupts - the metric's name, or the pack's own
value for it. A case failing that is VOID for every arm being compared, not just the one that failed
it: the comparison is paired, so dropping a case for one arm and keeping it for another would
compare different cases.

Written on 2026-10-27 before any planted run existed, so it could not be tuned to a result. Its
first pass voided four of five cases, and that is why the plants are now matched per cell
(questions.py): one payout-ratio claim planted on a valuation question was measuring whether a room
notices an irrelevant wrong figure. The first pass also carried a second half - the pack had to hold
dividend rows - which was a proxy for exactly that mismatch and is gone with it. Whether a pack can
support a metric is now settled when the plant is written, and recorded in questions.py's table; the
gate asks only the question it is for, which is whether the arm raised the subject at all.
"""

from pathlib import Path
from typing import Any

from .questions import CELLS


def engages(answer: str, cell: Any) -> list[str]:
    """What in this answer shows it engaged with the metric. Empty means it did not."""
    text = (answer or "").lower()
    return [t for t in (*cell.terms, *cell.correct) if t.lower() in text]


def valid_cells(rows: list[dict[str, Any]], arms: tuple[str, ...], packs: Path | None = None) -> tuple[set[str], list[str]]:
    """Returns the cells that count, and a line per cell saying why it does or does not.

    `packs` is accepted and unused: the gate no longer reads the packs, and the callers that pass it
    are not worth changing for that.
    """
    by_key = {c.key: c for c in CELLS}
    clean = [r for r in rows if not r["planted"] and r["ok"]]
    cells = sorted({r["cell"] for r in rows})
    keep: set[str] = set()
    notes: list[str] = []
    for key in cells:
        cell = by_key.get(key)
        if cell is None:
            notes.append(f"  {key:14} VOID  no such cell in the bench any more")
            continue
        missing, failed, shown = [], [], []
        for arm in arms:
            g = [r for r in clean if r["cell"] == key and r["arm"] == arm]
            if not g:
                missing.append(arm)
                continue
            hits = sorted({h for r in g for h in engages(r["answer"], cell)})
            if hits:
                shown.append(f"{arm}:{hits[0]}")
            else:
                failed.append(arm)
        if missing:
            notes.append(f"  {key:14} VOID  no clean run for {', '.join(missing)}")
        elif failed:
            notes.append(f"  {key:14} VOID  the clean answer never raises {cell.terms[0]} in {', '.join(failed)}")
        else:
            keep.add(key)
            notes.append(f"  {key:14} counts   {', '.join(shown)}")
    return keep, notes
