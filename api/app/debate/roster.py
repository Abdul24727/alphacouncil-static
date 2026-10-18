"""The seats of the debate room, one markdown file each in app/advisors (see the README there).

A file is front matter (`key: value` lines between `---`) and a markdown body whose `## ` headings
are its sections. An advisor's whole body is its brief; the Chair's "Stage: …" sections are the
instructions for each step and its "Scoring" section is the scale every vote uses.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

ADVISORS_DIR = Path(__file__).resolve().parent.parent / "advisors"

ADVISOR_SECTIONS = (
    "Who they are",
    "Investing principles",
    "What they look at first",
    "How they argue and disagree",
    "Blind spots",
    "Voice",
)
CHAIR_SECTIONS = (
    "Who the Chair is",
    "Stage: Brief",
    "Stage: Openings",
    "Stage: Fault lines",
    "Stage: Debate",
    "Stage: Vote",
    "Stage: Verdict",
    "Scoring",
    "Voice",
)
FIELDS = ("id", "name_en", "name_ar", "initials", "lens_en", "lens_ar", "portrait")
SEAT_ID = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")
MIN_ADVISORS, MAX_ADVISORS = 2, 6


class RosterError(ValueError):
    """A seat file is missing, malformed, or the roster setting names too few or too many."""


class SeatInfo(BaseModel):
    """What the screen shows of a seat (and what a session keeps of it)."""

    id: str
    role: Literal["advisor", "chair"]
    name_en: str
    name_ar: str
    initials: str
    lens_en: str
    lens_ar: str
    # Served from web/public/advisors; None until the owner provides the art (initials are drawn).
    portrait: str | None


class Seat(BaseModel):
    info: SeatInfo
    body: str
    sections: dict[str, str]

    @property
    def id(self) -> str:
        return self.info.id

    @property
    def name(self) -> str:
        return self.info.name_en

    @property
    def surname(self) -> str:
        return self.info.name_en.split()[-1]


def parse(text: str) -> tuple[dict[str, str], str]:
    """Front matter and body of a seat file."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text.replace("\r\n", "\n"), re.S)
    if not m:
        raise RosterError("missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if line.strip():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, m.group(2).strip()


def sections_of(body: str) -> dict[str, str]:
    """`## Heading` -> the text under it, up to the next `## `."""
    out: dict[str, str] = {}
    for part in re.split(r"^## ", body, flags=re.M)[1:]:
        heading, _, rest = part.partition("\n")
        out[heading.strip()] = rest.strip()
    return out


@lru_cache
def load(seat_id: str) -> Seat:
    if not SEAT_ID.match(seat_id):
        raise RosterError(f"bad seat id {seat_id!r}")
    path = ADVISORS_DIR / f"{seat_id}.md"
    if not path.is_file():
        raise RosterError(f"no seat file {path.name}")
    meta, body = parse(path.read_text(encoding="utf-8"))
    missing = [f for f in FIELDS if f not in meta or (f != "portrait" and not meta[f])]
    if missing or meta["id"] != seat_id:
        raise RosterError(f"{path.name}: front matter needs {', '.join(missing) or 'id: ' + seat_id}")
    role: Literal["advisor", "chair"] = "chair" if seat_id == "chair" else "advisor"
    sections = sections_of(body)
    wanted = CHAIR_SECTIONS if role == "chair" else ADVISOR_SECTIONS
    absent = [s for s in wanted if not sections.get(s)]
    if absent:
        raise RosterError(f"{path.name}: missing sections {', '.join(absent)}")
    portrait = meta["portrait"] or None
    if portrait and not re.match(r"^[a-z0-9_-]+\.(webp|png|jpg)$", portrait):
        raise RosterError(f"{path.name}: portrait must be a file name in web/public/advisors")
    info = SeatInfo(
        id=seat_id,
        role=role,
        name_en=meta["name_en"],
        name_ar=meta["name_ar"],
        initials=meta["initials"][:3],
        lens_en=meta["lens_en"],
        lens_ar=meta["lens_ar"],
        portrait=f"/advisors/{portrait}" if portrait else None,
    )
    return Seat(info=info, body=body, sections=sections)


def advisors(setting: str) -> list[Seat]:
    """The advisors named by DEBATE_ADVISORS, in seat order."""
    ids = [s.strip() for s in setting.split(",") if s.strip()]
    if len(set(ids)) != len(ids) or "chair" in ids or not MIN_ADVISORS <= len(ids) <= MAX_ADVISORS:
        raise RosterError(f"DEBATE_ADVISORS needs {MIN_ADVISORS} to {MAX_ADVISORS} distinct advisors")
    return [load(i) for i in ids]


def chair() -> Seat:
    return load("chair")
