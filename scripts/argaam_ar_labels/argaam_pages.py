"""What pair_labels.py and pair_from_gulf.py both read from a saved Argaam statement page.

Every statement line is a `<tr id="trNNN">`, and its label sits in the row's first `<td data-fieldname>`
cell. The row id names the same field on every market and in both languages, which is what lets the two
scripts pair labels. Which saved page to read is each script's own rule, and stays in each script.
"""
from __future__ import annotations

import re
from pathlib import Path

ROW_ID = re.compile(r"^tr\d+$")


def norm(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def page_rows(path: Path) -> dict[str, str]:
    """Row id -> label for every statement line on one saved page; the first label wins for a repeated id."""
    from bs4 import BeautifulSoup  # here, so the scripts' own rules can be tested where bs4 is not installed

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    out: dict[str, str] = {}
    for tr in soup.find_all("tr", id=ROW_ID):
        td = tr.find("td", attrs={"data-fieldname": True})
        if td is None:
            continue
        # The text the reader sees, not the attribute: on an Arabic page `data-fieldname` may be a field
        # key that stays English while the cell's text is Arabic.
        label = norm(td.get_text(" ")) or norm(td.get("data-fieldname"))
        if label:
            out.setdefault(tr["id"], label)
    return out
