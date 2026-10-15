"""The Copilot on an OpenAI-compatible endpoint (OpenRouter by default), streamed as UI parts.

Same contract as engine.claude_stream: the same system prompt, tools, validation,
citations and stream parts; only the wire format differs. Provider, endpoint and model
come from the environment (COPILOT_PROVIDER, OPENROUTER_BASE_URL, COPILOT_MODEL); the
key is OPENROUTER_API_KEY and never leaves the process.
"""

import json
import os
from collections.abc import AsyncIterator
from typing import Any

import openai
from fastapi import Request
from starlette.concurrency import run_in_threadpool

from ..settings import Settings
from . import tools
from .context import ChatInput, numbers_in, panel_block, sources
from .engine import MAX_STEPS, SYSTEM, TOOL_RESULT_CHARS, _client_view, _ui_tool
from .stream import Writer


def _tool_defs() -> list[dict[str, Any]]:
    return [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
        for t in tools.ALL_TOOLS
    ]


def _history(chat: ChatInput) -> list[dict[str, Any]]:
    msgs: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM}]
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

    client = openai.AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        default_headers={"X-Title": "AlphaCouncil"},
    )
    messages = _history(chat)

    for _ in range(MAX_STEPS):
        yield w.start_step()
        text, calls, finish = "", {}, None
        try:
            stream = await client.chat.completions.create(
                model=settings.copilot_model,
                messages=messages,
                tools=_tool_defs(),
                tool_choice="auto",
                max_tokens=8_000,
                stream=True,
            )
            async for chunk in stream:
                for choice in chunk.choices:
                    finish = choice.finish_reason or finish
                    delta = choice.delta
                    # OpenRouter passes a model's reasoning as `reasoning` (not in the OpenAI schema).
                    reasoning = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
                    if isinstance(reasoning, str) and reasoning:
                        yield w.reasoning(reasoning)
                    if delta.content:
                        text += delta.content
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

        if finish == "length":
            yield w.error("The answer was cut off. Please ask a narrower question.")
            break
        if not calls:
            yield w.finish_step()
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

            if c["name"] in tools.UI_TOOL_NAMES:
                output = await _ui_tool(request, w, c["name"], args, seen)
                for part in output["parts"]:
                    yield part
                payload = output["ack"]
            else:
                payload = await run_in_threadpool(tools.run, request, c["name"], args)
                numbers_in(payload, seen)
            yield w.tool_result(c["id"], _client_view(payload))
            messages.append(
                {"role": "tool", "tool_call_id": c["id"], "content": json.dumps(payload, ensure_ascii=False, default=str)[:TOOL_RESULT_CHARS]}
            )
        yield w.finish_step()

    yield w.finish()
