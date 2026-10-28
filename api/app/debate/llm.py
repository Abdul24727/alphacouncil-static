"""One model call for one seat: OpenRouter through the Copilot's client, a JSON object back,
and the call's time, tokens and cost (OpenRouter's own figure, from its usage accounting)."""

import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import openai

from ..copilot.openai_compat import host_routing, make_client
from ..settings import Settings

# uvicorn's logger reaches the service journal (journalctl -u acp-api).
log = logging.getLogger("uvicorn.error")

TIMEOUT_S = 120
# Tries per seat per stage. Two was not enough for round one's long answers (docs/beta-advisors-2026-10-27.md, F-1).
ATTEMPTS = 3
# What a retry may add to the prompt, in UTF-8 BYTES rather than characters. `eval.budget` prices a
# retried prompt's growth in bytes - a byte-level BPE tokenizer cannot emit more tokens than the
# input has bytes - while these two were sliced by CHARACTER (`text[:6_000]`). Arabic, which these
# prompts carry, is about two bytes a character before the tokenizer sees it, so a retry could add
# roughly twice what the bound had accounted for, and a bound that can be beaten by ordinary text
# is not a bound. Found by the fifth independent review round, 2026-10-28. Clipping in bytes makes
# the accounted figure true by construction rather than by assumption about the language.
RETRY_ECHO_BYTES = 6_000
# The correction sentence quotes the parser's own message, which has no length of its own: a long
# ValueError text went into the next prompt unbounded. Clipped so the instruction as a whole stays
# inside `eval.budget.RETRY_INSTRUCTION_BYTES`.
RETRY_PROBLEM_BYTES = 200


class SeatError(Exception):
    """The seat gave no usable answer; `code` says why (the screen words it). `usage` carries what the
    failed attempts cost, where there were any: they are real money and belong in the session's total
    (docs/beta-advisors-2026-10-27.md, F-7), even though the turn itself has no answer to show."""

    def __init__(self, code: str, usage: "Usage | None" = None):
        super().__init__(code)
        self.code = code
        self.usage = usage


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


def _clip_bytes(text: str, limit: int) -> str:
    """`text` truncated to at most `limit` UTF-8 bytes, never splitting a character.

    Slicing by character cannot promise this, which is the whole point: `text[:6_000]` is up to
    about 12,000 bytes of Arabic, so the retry growth the spending cap is computed from was an
    undercount for exactly the language this product serves.
    """
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", "ignore")


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


# Models that refuse to answer with reasoning switched off (Claude Sonnet 5.5 on OpenRouter: "Reasoning
# is mandatory for this endpoint"). They get the lowest effort instead, from then on.
#
# SEEDED as of 2026-10-28, where it used to start empty and learn only by being refused. That cost
# one refused request per model per process restart, and once every request this module issues is
# counted against ATTEMPTS - the fifth review round's correction, directly above - that refused
# request would also have cost the chair's FIRST call one of its three attempts at usable JSON,
# which is the shape of failure F-1 was about. Seeding makes the steady state the start state:
# nothing has to be learned by being refused. The runtime path below still works and is still the
# authority; this is only a head start. Remove an entry if the provider starts honouring
# `{"enabled": False}` for that model.
REASONING_REFUSES_OFF = ("anthropic/claude-sonnet-5.5",)
REASONING_REQUIRED: set[str] = set(REASONING_REFUSES_OFF)
REASONING_ROOM = 2_048


def _reasoning(settings: Settings, model: str) -> dict[str, Any] | None:
    if settings.debate_reasoning:
        return None
    return {"effort": "low"} if model in REASONING_REQUIRED else {"enabled": False}


def _refuses_no_reasoning(exc: openai.APIStatusError) -> bool:
    return exc.status_code == 400 and "reasoning" in str(exc.body or exc.message).lower()


async def ask(
    settings: Settings,
    model: str,
    messages: list[dict[str, str]],
    *,
    max_tokens: int,
    temperature: float,
    check: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any], Usage]:
    """Ask once; if the reply is not usable JSON (check raises ValueError), ask again saying why, up to three
    attempts in all: the long answers of round one fail the shape often enough that two was not enough."""
    client = make_client(settings)
    usage = Usage(model=model)
    msgs = list(messages)
    problem = "bad_output"
    attempts = 0
    while attempts < ATTEMPTS:
        extra: dict[str, Any] = {**host_routing(settings), "usage": {"include": True}}
        reasoning = _reasoning(settings, model)
        if reasoning is not None:
            extra["reasoning"] = reasoning
        # Thinking tokens count against max_tokens (Anthropic's budget is 1,024 at least): room for both.
        limit = max_tokens if reasoning == {"enabled": False} else max_tokens + REASONING_ROOM
        started = time.monotonic()
        # Counted BEFORE the request, not after a usable reply comes back. The 400-on-reasoning
        # path below retries with `continue`, and while this line sat after it one `ask` could
        # issue ATTEMPTS + 1 requests - a fourth request that `eval.budget` then had to PRICE
        # (`EXTRA_REQUESTS`) rather than prevent. The fifth review round asked for the configured
        # attempt count to be enforced directly, and counting every request this loop issues is
        # what that means. The ordinary path is unchanged: three requests, three attempts.
        attempts += 1
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=msgs,
                max_tokens=limit,
                temperature=temperature,
                extra_body=extra,
                timeout=TIMEOUT_S,
            )
        except openai.AuthenticationError as exc:
            raise SeatError("credentials", usage) from exc
        except openai.RateLimitError as exc:
            raise SeatError("busy", usage) from exc
        except openai.APITimeoutError as exc:
            raise SeatError("timeout", usage) from exc
        except openai.APIStatusError as exc:
            if _refuses_no_reasoning(exc) and model not in REASONING_REQUIRED:
                REASONING_REQUIRED.add(model)
                continue  # the same request at the lowest effort - and it has cost an attempt
            if exc.status_code == 402:
                # Out of credit at the provider. Its own code, because "unreachable" sent a day of
                # debugging after a network fault that was never there (F-10). Not retried either:
                # asking three times for something unaffordable fails three times.
                log.error("advisors' room: the model provider refused on credit (402): %s", str(exc.body or exc)[:300])
                raise SeatError("no_credit", usage) from exc
            raise SeatError("unreachable", usage) from exc
        except openai.APIConnectionError as exc:
            raise SeatError("unreachable", usage) from exc
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
                {"role": "assistant", "content": _clip_bytes(text, RETRY_ECHO_BYTES) or "(empty)"},
                {
                    "role": "user",
                    "content": f"That reply could not be used ({_clip_bytes(str(exc), RETRY_PROBLEM_BYTES)}). Reply again with only the JSON object in the shape asked for"
                    + (", shorter" if cut else ", with every double quote inside a text value escaped and no line breaks in it")
                    + ".",
                },
            ]
    raise SeatError(problem, usage)
