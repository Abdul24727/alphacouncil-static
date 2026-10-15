"""Vercel AI SDK UI message stream (SSE, protocol v1), written from Python.

The web app's `useChat` reads this stream directly; see
web/node_modules/ai/docs/04-ai-sdk-ui/50-stream-protocol.mdx for the parts.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

HEADERS = {
    "x-vercel-ai-ui-message-stream": "v1",
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",  # nginx: do not buffer the stream
}


def part(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False, default=str)}\n\n"


DONE = "data: [DONE]\n\n"

# An SSE comment line: the client's parser drops it, proxies see bytes flowing.
KEEPALIVE = ": keepalive\n\n"


async def with_keepalive(parts: AsyncIterator[str], every_s: float = 10.0) -> AsyncIterator[str]:
    """Pass the parts through, adding a comment whenever nothing was sent for `every_s`.

    A model can think for a while between parts (or between tool steps); the web app's
    rewrite proxy drops a response that stays silent for 30 s.
    """
    it = aiter(parts)
    pending: asyncio.Task | None = None
    try:
        while True:
            if pending is None:
                pending = asyncio.ensure_future(anext(it))
            done, _ = await asyncio.wait({pending}, timeout=every_s)
            if not done:
                yield KEEPALIVE
                continue
            try:
                chunk = pending.result()
            except StopAsyncIteration:
                return
            pending = None
            yield chunk
    finally:
        if pending is not None and not pending.done():
            pending.cancel()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class Writer:
    """Collects parts for one assistant message; tracks open text/reasoning blocks."""

    def __init__(self) -> None:
        self.message_id = new_id("msg")
        self._text_id: str | None = None
        self._reasoning_id: str | None = None

    def start(self) -> str:
        return part({"type": "start", "messageId": self.message_id})

    def start_step(self) -> str:
        return part({"type": "start-step"})

    def finish_step(self) -> str:
        return self.close_blocks() + part({"type": "finish-step"})

    def text(self, delta: str) -> str:
        out = self.close_reasoning()
        if self._text_id is None:
            self._text_id = new_id("text")
            out += part({"type": "text-start", "id": self._text_id})
        return out + part({"type": "text-delta", "id": self._text_id, "delta": delta})

    def reasoning(self, delta: str) -> str:
        out = self.close_text()
        if self._reasoning_id is None:
            self._reasoning_id = new_id("reasoning")
            out += part({"type": "reasoning-start", "id": self._reasoning_id})
        return out + part({"type": "reasoning-delta", "id": self._reasoning_id, "delta": delta})

    def close_text(self) -> str:
        if self._text_id is None:
            return ""
        out = part({"type": "text-end", "id": self._text_id})
        self._text_id = None
        return out

    def close_reasoning(self) -> str:
        if self._reasoning_id is None:
            return ""
        out = part({"type": "reasoning-end", "id": self._reasoning_id})
        self._reasoning_id = None
        return out

    def close_blocks(self) -> str:
        return self.close_text() + self.close_reasoning()

    def tool_call(self, call_id: str, name: str, input: dict[str, Any]) -> str:
        return self.close_blocks() + part(
            {"type": "tool-input-available", "toolCallId": call_id, "toolName": name, "input": input}
        )

    def tool_result(self, call_id: str, output: Any) -> str:
        return part({"type": "tool-output-available", "toolCallId": call_id, "output": output})

    def data(self, kind: str, data: Any) -> str:
        return part({"type": f"data-{kind}", "data": data})

    def error(self, text: str) -> str:
        return self.close_blocks() + part({"type": "error", "errorText": text})

    def finish(self) -> str:
        return self.close_blocks() + part({"type": "finish"}) + DONE
