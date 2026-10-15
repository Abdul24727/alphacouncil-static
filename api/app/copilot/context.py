"""Turn the useChat request into the Copilot's input."""

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

PANEL_CHARS = 12_000  # per attached panel, after JSON encoding
MAX_PANELS = 8


class AttachedPanel(BaseModel):
    id: str
    title: str
    ticker: str | None = None
    data: Any = None


class ChatRequest(BaseModel):
    """Body sent by the web app's DefaultChatTransport (prepareSendMessagesRequest)."""

    id: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)  # UIMessage[]
    panels: list[AttachedPanel] = Field(default_factory=list)
    locale: Literal["en", "ar"] = "en"
    ticker: str | None = None  # the page's group-1 ticker, if any


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatInput(BaseModel):
    question: str
    history: list[Turn]
    panels: list[AttachedPanel]
    locale: str
    ticker: str | None

    @property
    def tags(self) -> dict[str, AttachedPanel]:
        """Short citation tags the model uses: P1, P2, ..."""
        return {f"P{i + 1}": p for i, p in enumerate(self.panels)}


def _text_of(message: dict[str, Any]) -> str:
    return "".join(p.get("text", "") for p in message.get("parts", []) if p.get("type") == "text")


def to_input(req: ChatRequest) -> ChatInput:
    turns = [
        Turn(role=m["role"], text=_text_of(m))
        for m in req.messages
        if m.get("role") in ("user", "assistant")
    ]
    if not turns or turns[-1].role != "user" or not turns[-1].text.strip():
        raise ValueError("the last message must be a non-empty user message")
    return ChatInput(
        question=turns[-1].text.strip()[:4000],
        history=turns[:-1][-12:],
        panels=req.panels[:MAX_PANELS],
        locale=req.locale,
        ticker=req.ticker,
    )


def panel_block(chat: ChatInput) -> str:
    """Attached panels as data for the model, each under its citation tag."""
    if not chat.panels:
        return "No panels are attached to this question."
    lines = ["Attached panels (data shown on the user's screen; cite with the tag):"]
    for tag, p in chat.tags.items():
        data = json.dumps(p.data, ensure_ascii=False, default=str)
        if len(data) > PANEL_CHARS:
            data = data[:PANEL_CHARS] + " …[truncated]"
        lines.append(f"[{tag}] {p.title}" + (f" (ticker {p.ticker})" if p.ticker else "") + f": {data}")
    return "\n".join(lines)


def sources(chat: ChatInput) -> dict[str, dict[str, str | None]]:
    """Citation tag -> panel, sent to the browser so citation chips can name and find the panel."""
    out: dict[str, dict[str, str | None]] = {tag: {"id": p.id, "title": p.title, "ticker": p.ticker} for tag, p in chat.tags.items()}
    out["DB"] = {"id": None, "title": "Database", "ticker": None}
    return out


def numbers_in(value: Any, out: set[str] | None = None) -> set[str]:
    """Every number in a JSON-like value (absolute, 2 decimals; dates split into parts), for checking model-built tables."""
    out = set() if out is None else out
    if isinstance(value, bool) or value is None:
        return out
    if isinstance(value, (int, float)):
        out.add(f"{abs(float(value)):.2f}")
    elif isinstance(value, str):
        for m in re.findall(r"-?\d[\d,]*\.?\d*", value):
            try:
                out.add(f"{abs(float(m.replace(',', ''))):.2f}")
            except ValueError:
                pass
    elif isinstance(value, dict):
        for v in value.values():
            numbers_in(v, out)
    elif isinstance(value, list):
        for v in value:
            numbers_in(v, out)
    return out


def unverified_cells(rows: list[list[Any]], seen: set[str]) -> list[list[int]]:
    """[row, col] of numeric cells whose value appears nowhere in the data the Copilot read."""
    bad = []
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            nums = numbers_in(cell)
            if nums and not nums <= seen:
                bad.append([i, j])
    return bad
