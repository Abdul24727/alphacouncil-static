"""One model call for one seat: OpenRouter through the Copilot's client, a JSON object back,
and the call's time, tokens and cost (OpenRouter's own figure, from its usage accounting)."""

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import openai

from ..copilot.openai_compat import host_routing, make_client
from ..settings import Settings

TIMEOUT_S = 120


class SeatError(Exception):
    """The seat gave no usable answer; `code` says why (the screen words it)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class Usage:
    model: str
    seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float | None = None

    def add(self, usage: Any) -> None:
        if usage is None:
            return
        self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
        self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
        extra = getattr(usage, "model_extra", None) or {}
        cost = getattr(usage, "cost", None) if getattr(usage, "cost", None) is not None else extra.get("cost")
        if isinstance(cost, (int, float)):
            self.cost_usd = (self.cost_usd or 0.0) + float(cost)


def parse_json(text: str) -> dict[str, Any]:
    """The JSON object in a reply, with or without a Markdown fence around it."""
    t = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip())
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("no JSON object")
    obj = json.loads(t[i : j + 1])
    if not isinstance(obj, dict):
        raise ValueError("not a JSON object")
    return obj


async def ask(
    settings: Settings,
    model: str,
    messages: list[dict[str, str]],
    *,
    max_tokens: int,
    temperature: float,
    check: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any], Usage]:
    """Ask once; if the reply is not usable JSON (check raises ValueError), ask once more saying why."""
    client = make_client(settings)
    usage = Usage(model=model)
    msgs = list(messages)
    extra = {**host_routing(settings), "usage": {"include": True}}
    if not settings.debate_reasoning:
        extra["reasoning"] = {"enabled": False}
    problem = "bad_output"
    for _ in range(2):
        started = time.monotonic()
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_body=extra,
                timeout=TIMEOUT_S,
            )
        except openai.AuthenticationError as exc:
            raise SeatError("credentials") from exc
        except openai.RateLimitError as exc:
            raise SeatError("busy") from exc
        except openai.APITimeoutError as exc:
            raise SeatError("timeout") from exc
        except (openai.APIStatusError, openai.APIConnectionError) as exc:
            raise SeatError("unreachable") from exc
        finally:
            usage.seconds += time.monotonic() - started
        usage.add(getattr(resp, "usage", None))
        choice = resp.choices[0] if resp.choices else None
        text = (choice.message.content if choice and choice.message else None) or ""
        try:
            return check(parse_json(text)), usage
        except (ValueError, KeyError, TypeError) as exc:
            cut = choice is not None and choice.finish_reason == "length"
            problem = "cut_off" if cut else "bad_output"
            msgs = msgs + [
                {"role": "assistant", "content": text[:6_000] or "(empty)"},
                {
                    "role": "user",
                    "content": f"That reply could not be used ({exc}). Reply again with only the JSON object in the shape asked for"
                    + (", shorter" if cut else "")
                    + ".",
                },
            ]
    raise SeatError(problem)
