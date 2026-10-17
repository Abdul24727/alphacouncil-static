"""The Copilot on Claude (official Anthropic Python SDK), streamed as UI parts."""

import json
from collections.abc import AsyncIterator
from typing import Any

import anthropic
from fastapi import Request
from starlette.concurrency import run_in_threadpool

from ..settings import Settings
from . import tools
from .context import AnswerTrace, ChatInput, numbers_in, panel_block, sources, unverified_cells
from .stream import Writer, new_id

MAX_STEPS = 6
TOOL_RESULT_CHARS = 24_000

SYSTEM = """You are the AlphaCouncil Copilot, a research assistant inside a terminal for Gulf (GCC) listed equities: Tadawul, ADX, DFM, QSE, Boursa Kuwait, Bahrain Bourse and Muscat.

Sources. Use only two sources: the attached panel data in the user's message, and the results of your tools. Do not use outside knowledge for any number, price, date, ratio or company fact. If what the question needs is in neither source, say plainly that the data is not available here; never estimate or fill a gap.

Citations. When a sentence uses data from an attached panel, end it with that panel's tag in square brackets, exactly as given, for example [P1]. When it uses a tool result, end it with [DB]. Every figure in the answer carries a tag.

Numbers. Quote values as the source gives them, with units and the listing currency; in show_table, copy each value exactly, never rounded. Dates as YYYY-MM-DD. Mention the data's as-of date when timing matters; when the data gives no date for a value, say its date is unknown rather than using another date.

Scope. Explain what the data shows. Do not tell the user to buy, sell or hold anything and do not give personalised investment advice; if asked, say you can only describe the data.

Language. Answer in the language of the user's question (Arabic or English). Keep company names as the data gives them.

Order. Gather the data first: write nothing before or between tool calls, then write the answer once.

Shape. Lead with the direct answer in one to three sentences, then the supporting figures. Describe missing or unavailable values in plain words; never quote field names, null or status codes. Write sentences and "-" lists only: tables go in show_table, never as Markdown tables, and write no HTML or tags. Use show_table when a small table of database values helps, and show_price_chart when a chart helps. End every answer by calling suggest_follow_ups with two or three short questions in the user's language."""


def _tool_defs() -> list[dict[str, Any]]:
    # Streaming with client tools: let large inputs stream as they are generated.
    return [{**t, "eager_input_streaming": True} for t in tools.ALL_TOOLS]


def _history(chat: ChatInput) -> list[dict[str, Any]]:
    msgs: list[dict[str, Any]] = [{"role": m.role, "content": m.text} for m in chat.history if m.text.strip()]
    content = []
    block = panel_block(chat)
    if block:
        content.append({"type": "text", "text": block})
    content.append({"type": "text", "text": f"Interface language: {chat.locale}. Page ticker: {chat.ticker or 'none'}."})
    content.append({"type": "text", "text": chat.question})
    msgs.append({"role": "user", "content": content})
    return msgs


def _client_view(output: Any) -> Any:
    """What the browser sees of a tool result: enough to label the step, not the payload."""
    if isinstance(output, dict) and "error" in output:
        return {"error": output["error"]}
    if isinstance(output, list):
        return {"items": len(output)}
    return {"ok": True}


async def claude_stream(request: Request, chat: ChatInput, settings: Settings) -> AsyncIterator[str]:
    w = Writer()
    yield w.start()
    yield w.data("model", {"name": settings.copilot_model, "stand_in": False})
    yield w.data("sources", sources(chat))
    # Every number the Copilot reads, to check tables it builds (see unverified_cells).
    seen = numbers_in([p.data for p in chat.panels])
    trace = AnswerTrace(chat)

    client = anthropic.AsyncAnthropic()
    messages = _history(chat)
    json_retries = 0

    for _ in range(MAX_STEPS):
        yield w.start_step()
        step_text = ""
        try:
            async with client.beta.messages.stream(
                model=settings.copilot_model,
                max_tokens=16_000,
                system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": settings.copilot_effort},
                # A policy decline is re-run server-side on Anthropic's recommended fallback.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                tools=_tool_defs(),
                messages=messages,
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "thinking_delta" and event.delta.thinking:
                            yield w.reasoning(event.delta.thinking)
                        elif event.delta.type == "text_delta":
                            step_text += event.delta.text
                            yield w.text(event.delta.text)
                response = await stream.get_final_message()
            json_retries = 0
        except ValueError:
            # Tool input JSON the SDK could not parse at all: re-issue the turn (bounded).
            json_retries += 1
            if json_retries > 2:
                yield w.error("The model returned malformed tool input. Please ask again.")
                break
            yield w.finish_step()
            continue
        except anthropic.AuthenticationError:
            yield w.error("The Copilot's AI credentials were rejected.")
            break
        except anthropic.RateLimitError:
            yield w.error("The Copilot is busy right now. Try again in a minute.")
            break
        except anthropic.APIStatusError as exc:
            yield w.error(f"The AI service returned an error ({exc.status_code}).")
            break
        except anthropic.APIConnectionError:
            yield w.error("Could not reach the AI service.")
            break

        # Echo the whole assistant turn, thinking blocks included, unchanged.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            yield w.text("\n\nThis request was declined by the model's safety checks.")
            yield w.finish_step()
            break
        if response.stop_reason == "pause_turn":
            yield w.finish_step()
            continue

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        trace.step(step_text, called_database=any(b.name not in tools.UI_TOOL_NAMES for b in tool_uses))
        if not tool_uses:
            yield w.finish_step()
            break
        if response.stop_reason == "max_tokens":
            yield w.error("The answer was cut off. Please ask a narrower question.")
            break

        results = []
        for block in tool_uses:
            yield w.tool_call(block.id, block.name, block.input if isinstance(block.input, dict) else {})
            try:
                args = tools.validate(block.name, block.input)
            except tools.ToolInputError as exc:
                yield w.tool_result(block.id, {"error": str(exc)})
                results.append({"type": "tool_result", "tool_use_id": block.id, "is_error": True,
                                "content": json.dumps({"INVALID_INPUT": str(exc)})})
                continue

            if block.name in tools.UI_TOOL_NAMES:
                output = await _ui_tool(request, w, block.name, args, seen)
                for chunk in output["parts"]:
                    yield chunk
                payload = output["ack"]
            else:
                payload = await run_in_threadpool(tools.run, request, block.name, args)
                numbers_in(payload, seen)
                numbers_in(payload, trace.db)
            yield w.tool_result(block.id, _client_view(payload))
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": json.dumps(payload, ensure_ascii=False, default=str)[:TOOL_RESULT_CHARS]})
        messages.append({"role": "user", "content": results})
        yield w.finish_step()

    cites = trace.citations()
    if cites:
        yield w.data("autocite", cites)
    yield w.finish()


async def _ui_tool(request: Request, w: Writer, name: str, args: dict[str, Any], seen: set[str]) -> dict[str, Any]:
    """Render a UI tool in the chat; returns the stream parts and the ack the model reads."""
    if name == "suggest_follow_ups":
        qs = [q.strip() for q in args["questions"] if isinstance(q, str) and q.strip()][:3]
        return {"parts": [w.data("followups", {"questions": qs})], "ack": {"shown": True}}
    if name == "show_table":
        cols = [str(c) for c in args["columns"]][:8]
        rows = [r[: len(cols)] for r in args["rows"] if isinstance(r, list)][:30]
        table = {
            "id": new_id("table"),
            "title": args["title"][:120],
            "columns": cols,
            "rows": rows,
            "source": args["source"],
            # BRAND.md: only database numbers. Cells the Copilot never read are flagged in the UI.
            "unverified": unverified_cells(rows, seen),
        }
        return {"parts": [w.data("table", table)], "ack": {"shown": True}}
    if name == "show_price_chart":
        summary = await run_in_threadpool(tools.price_summary, request, args["ticker"], args["range"])
        if not summary.get("has_history", True) or "error" in summary:
            return {"parts": [], "ack": {"error": "no price history for this ticker"}}
        t = request.app.state.universe.by_key[summary["ticker"]]
        chart = {"id": new_id("chart"), "ticker": t.slug, "ticker_key": t.ticker_key, "range": args["range"]}
        return {"parts": [w.data("chart", chart)], "ack": {"shown": True, **summary}}
    return {"parts": [], "ack": {"error": f"unknown tool {name}"}}
