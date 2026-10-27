"""The Copilot on an OpenAI-compatible endpoint (OpenRouter by default), streamed as UI parts.

Same contract as engine.claude_stream: the same system prompt, tools, validation,
citations and stream parts; only the wire format differs. Provider, endpoint and model
come from the environment (COPILOT_PROVIDER, OPENROUTER_BASE_URL, COPILOT_MODEL); the
key is OPENROUTER_API_KEY and never leaves the process.
"""

import asyncio
import json
import logging
import os
import time
import weakref
from collections.abc import AsyncIterator
from typing import Any

import openai
from fastapi import Request
from starlette.concurrency import run_in_threadpool

from ..settings import Settings
from . import tools
from .context import AnswerTrace, ChatInput, numbers_in, panel_block, sources
from .engine import MAX_STEPS, SYSTEM, TOOL_RESULT_CHARS, _client_view, _ui_tool
from .stream import Writer

# uvicorn's logger reaches the service journal (journalctl -u acp-api).
log = logging.getLogger("uvicorn.error")

FOLLOW_UP_NUDGE = "Now call suggest_follow_ups with two or three short follow-up questions in the language of my question."


def _tool_defs(specs: list[dict[str, Any]] = tools.ALL_TOOLS) -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in specs
    ]


# Option (e), 2026-10-22: the host OpenRouter picks always looked something up before writing,
# which put first words at 8-9 s. With the page ticker's data already fetched, the first turn
# offers only the display tools and this one, so the model writes at once unless the data is
# missing; then it asks, and the next turn offers every tool. Measured on beta: first words 5.3 s,
# full answers 15.2 s (medians). Tried and dropped the same day (38452ea): offering only
# need_database first and the display tools in a turn after the text. It was slower (first words
# 9.2 s, full 28.7 s, 12 answers): without show_table the model wrote the table's figures into the text, it
# still wrote a follow-ups call before the text, and the follow-ups often needed a third turn.
NEED_DATABASE = "need_database"
NEED_DATABASE_TOOL: dict[str, Any] = {
    "name": NEED_DATABASE,
    "description": (
        "Call this, and write nothing, only when the attached panels and the data already fetched above "
        "do not hold what the question needs (for example another company, price history, news, peers or the council). "
        "The database tools are offered on the next turn."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}
FIRST_TURN_TOOLS = [*tools.UI_TOOLS, NEED_DATABASE_TOOL]
ANSWER_AT_ONCE = (
    " When the attached panels and that fetched data hold what the question needs, write the answer straight away, "
    "with no tool call before it."
)


# Fewer round trips: each one costs a full model turn on OpenAI-compatible providers.
SYSTEM_EXTRA = (
    "\n\nSpeed. When you need several database tools, call them all together in one step. "
    "Calling suggest_follow_ups ends your answer: call it last, after the final text. "
    "Write nothing before or between database tool calls: write the answer once, after the last result. "
    "The page ticker's overview, dividends and fundamentals are already fetched below; call tools only for anything else."
)

# The page ticker's core data, fetched before the model's first turn. Measured on DeepSeek v3.2:
# models answer from the attached panel first, then look these up and answer again, which
# costs a full turn or two. About 7 KB (2,500 tokens) of input for 2222.
PREFETCH = ("get_ticker_overview", "get_dividends", "get_fundamentals")


# One client per event loop, not one per call. Each openai.AsyncOpenAI owns an httpx connection
# pool, and nothing here ever closed them: a debate session makes about 21 calls, so it used to
# leave about 21 pools behind. Sessions back to back then slowed to a stop after three or four
# (docs/beta-advisors-2026-10-27.md, F-11). Keyed by the running loop rather than held in a single
# global because an httpx client binds to the loop that created it, and the tests and the bench
# call asyncio.run more than once in a process; a lone global would be reused across loops and
# fail. The key is the loop itself, and the entry goes when the loop is collected.
_clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, openai.AsyncOpenAI]" = weakref.WeakKeyDictionary()


def make_client(settings: Settings) -> openai.AsyncOpenAI:
    """The OpenRouter (or OpenAI-compatible) client; the advisors' debate room uses it too.
    The same client comes back for every call on one event loop, so its connections are reused."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop (a synchronous caller): give it its own client rather than cache under no key.
        return _new_client(settings)
    client = _clients.get(loop)
    if client is None:
        client = _new_client(settings)
        _clients[loop] = client
    return client


def _new_client(settings: Settings) -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        default_headers={"X-Title": "AlphaCouncil"},
    )


def host_routing(settings: Settings, *, copilot: bool = False) -> dict[str, Any]:
    """OpenRouter serves a model from several hosts; the default pick can be several times slower.
    For the Copilot, COPILOT_PROVIDER_ORDER names hosts to try first; the others stay as fallbacks.
    Measured 2026-10-22: the latency sort picked a host that always looks up the database before
    writing (an extra round trip, first words after 8-9 s); another wrote first words in 1.8 s."""
    if "openrouter.ai" not in settings.openrouter_base_url:
        return {}
    provider: dict[str, Any] = {}
    if settings.copilot_provider_sort:
        provider["sort"] = settings.copilot_provider_sort
    order = [h.strip() for h in settings.copilot_provider_order.split(",") if h.strip()] if copilot else []
    if order:
        provider.update(order=order, allow_fallbacks=True)
    return {"provider": provider} if provider else {}


def _history(chat: ChatInput, first_turn: str = "lookup") -> list[dict[str, Any]]:
    rule = ANSWER_AT_ONCE if chat.ticker and first_turn in ("answer", "prompt") else ""
    msgs: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM + SYSTEM_EXTRA + rule}]
    msgs += [{"role": m.role, "content": m.text} for m in chat.history if m.text.strip()]
    parts = [panel_block(chat), f"Interface language: {chat.locale}. Page ticker: {chat.ticker or 'none'}.", chat.question]
    msgs.append({"role": "user", "content": "\n\n".join(p for p in parts if p)})
    return msgs


async def openai_stream(request: Request, chat: ChatInput, settings: Settings) -> AsyncIterator[str]:
    w = Writer()
    yield w.start()
    yield w.data("model", {"name": settings.copilot_model, "stand_in": False})
    yield w.data("sources", sources(chat))
    seen = numbers_in([p.data for p in chat.panels])
    trace = AnswerTrace(chat)

    client = make_client(settings)
    messages = _history(chat, settings.copilot_first_turn)
    if chat.ticker:
        async for part in _prefetch(request, w, chat.ticker, messages, seen, trace):
            yield part
    answer_first = bool(chat.ticker) and settings.copilot_first_turn == "answer"
    extra: dict[str, Any] = {"reasoning": {"enabled": True}} if settings.copilot_reasoning else {}
    routing = host_routing(settings, copilot=True)
    followed_up = nudged = False

    for step in range(MAX_STEPS):
        yield w.start_step()
        text, calls, finish, served = "", {}, None, None
        started, first_token = time.monotonic(), None
        try:
            stream = await client.chat.completions.create(
                model=settings.copilot_model,
                messages=messages,
                tools=_tool_defs(FIRST_TURN_TOOLS if answer_first and step == 0 else tools.ALL_TOOLS),
                tool_choice={"type": "function", "function": {"name": "suggest_follow_ups"}} if nudged else "auto",
                parallel_tool_calls=True,
                max_tokens=8_000,
                stream=True,
                # The follow-up turn only needs a quick tool call.
                extra_body=routing if nudged else {**extra, **routing},
            )
            async for chunk in stream:
                served = served or (getattr(chunk, "model_extra", None) or {}).get("provider")
                for choice in chunk.choices:
                    finish = choice.finish_reason or finish
                    delta = choice.delta
                    # OpenRouter passes a model's reasoning as `reasoning` (not in the OpenAI schema).
                    reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
                    if first_token is None and (delta.content or delta.tool_calls or reasoning):
                        first_token = time.monotonic() - started
                    # The follow-up turn only renders its tool call; its text is not part of the answer.
                    if isinstance(reasoning, str) and reasoning and not nudged:
                        yield w.reasoning(reasoning)
                    if delta.content:
                        text += delta.content
                        if not nudged:
                            yield w.text(delta.content)
                    for tc in delta.tool_calls or []:
                        c = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                        c["id"] = tc.id or c["id"]
                        if tc.function:
                            c["name"] += tc.function.name or ""
                            c["arguments"] += tc.function.arguments or ""
        except openai.AuthenticationError:
            yield w.error("The Copilot's AI credentials were rejected.")
            break
        except openai.RateLimitError:
            yield w.error("The Copilot is busy right now. Try again in a minute.")
            break
        except openai.APIStatusError as exc:
            yield w.error(f"The AI service returned an error ({exc.status_code}).")
            break
        except openai.APIConnectionError:
            yield w.error("Could not reach the AI service.")
            break

        log.info(
            "copilot step %d: host %s, %s, first token %s, step %.1f s",
            step,
            served or "unknown",
            ",".join(c["name"] for c in calls.values()) or "text",
            f"{first_token:.1f} s" if first_token is not None else "none",
            time.monotonic() - started,
        )
        if finish == "length":
            yield w.error("The answer was cut off. Please ask a narrower question.")
            break
        if nudged:
            # Only the follow-ups are wanted from the nudge turn.
            calls = {i: c for i, c in calls.items() if c["name"] == "suggest_follow_ups"}
        if not nudged:
            trace.step(text, called_database=any(c["name"] not in tools.UI_TOOL_NAMES for c in calls.values()))
        if not calls:
            yield w.finish_step()
            # SYSTEM asks for follow-ups at the end of every answer; some models stop without
            # them. One short extra turn that must call suggest_follow_ups.
            if not followed_up and not nudged and text.strip() and step < MAX_STEPS - 1:
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": FOLLOW_UP_NUDGE})
                nudged = True
                continue
            break

        ordered = [calls[i] for i in sorted(calls)]
        for c in ordered:
            c["id"] = c["id"] or f"call_{len(messages)}_{c['name']}"
        messages.append(
            {
                "role": "assistant",
                "content": text or None,
                "tool_calls": [
                    {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"] or "{}"}}
                    for c in ordered
                ],
            }
        )

        for c in ordered:
            if c["name"] == NEED_DATABASE:
                # The answer-first turn asked for the database: the next turn offers every tool.
                yield w.tool_call(c["id"], c["name"], {})
                yield w.tool_result(c["id"], {"ok": True})
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps({"ok": True, "note": "The database tools are available now."})})
                continue
            # Streamed arguments arrive as text: parse and validate before running anything.
            try:
                raw = json.loads(c["arguments"] or "{}")
            except ValueError:
                yield w.tool_call(c["id"], c["name"], {})
                yield w.tool_result(c["id"], {"error": "invalid JSON arguments"})
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps({"INVALID_JSON": "arguments were not valid JSON; call the tool again"})})
                continue
            yield w.tool_call(c["id"], c["name"], raw if isinstance(raw, dict) else {})
            try:
                args = tools.validate(c["name"], raw)
            except tools.ToolInputError as exc:
                yield w.tool_result(c["id"], {"error": str(exc)})
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps({"INVALID_INPUT": str(exc)})})
                continue

            if c["name"] == "suggest_follow_ups":
                followed_up = True
            if c["name"] in tools.UI_TOOL_NAMES:
                output = await _ui_tool(request, w, c["name"], args, seen)
                for part in output["parts"]:
                    yield part
                payload = output["ack"]
            else:
                payload = await run_in_threadpool(tools.run, request, c["name"], args)
                numbers_in(payload, seen)
                numbers_in(payload, trace.db)
            yield w.tool_result(c["id"], _client_view(payload))
            messages.append(
                {"role": "tool", "tool_call_id": c["id"], "content": json.dumps(payload, ensure_ascii=False, default=str)[:TOOL_RESULT_CHARS]}
            )
        yield w.finish_step()
        # Follow-ups close the answer: no further model turn after them.
        if nudged or followed_up:
            break

    # Sentences that quote a figure without its tag get the tag of where the figure was read.
    cites = trace.citations()
    if cites:
        yield w.data("autocite", cites)
    yield w.finish()


async def _prefetch(request: Request, w: Writer, ticker: str, messages: list, seen: set[str], trace: AnswerTrace) -> AsyncIterator[str]:
    """Run PREFETCH for the page ticker as one step the model reads as its own tool calls."""
    names = [n for n in PREFETCH if not (n in tools.PRO_TOOLS and getattr(request.state, "plan", "pro") == "free")]
    calls = [{"id": f"prefetch_{name}", "name": name, "args": {"ticker": ticker}} for name in names]
    payloads = await asyncio.gather(*(run_in_threadpool(tools.run, request, c["name"], c["args"]) for c in calls))
    yield w.start_step()
    messages.append(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["args"])}} for c in calls
            ],
        }
    )
    for c, payload in zip(calls, payloads, strict=True):
        numbers_in(payload, seen)
        numbers_in(payload, trace.db)
        yield w.tool_call(c["id"], c["name"], c["args"])
        yield w.tool_result(c["id"], _client_view(payload))
        messages.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(payload, ensure_ascii=False, default=str)[:TOOL_RESULT_CHARS]})
    yield w.finish_step()
