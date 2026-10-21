import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from ..auth import User, check_origin, client_ip, current_user, not_signed_in
from ..plans import plan_of
from ..copilot.context import ChatRequest, to_input
from ..copilot.engine import claude_stream
from ..copilot.openai_compat import openai_stream
from ..copilot.standin import standin_stream
from ..copilot.stream import HEADERS, with_keepalive
from .ticker import settings_of

router = APIRouter(prefix="/copilot", tags=["copilot"])


def provider(request: Request) -> str:
    """"openrouter", "anthropic" or "standin", from COPILOT_PROVIDER and which keys exist."""
    wanted = settings_of(request).copilot_provider
    keys = {
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
    }
    if wanted == "auto":
        return next((p for p in ("openrouter", "anthropic") if keys[p]), "standin")
    return wanted if keys.get(wanted) else "standin"


def uses_model(request: Request) -> bool:
    return provider(request) != "standin"


class CopilotStatus(BaseModel):
    model: str
    stand_in: bool
    # A model spends tokens on every question, so it answers signed-in users only.
    sign_in_required: bool


@router.get("/status", operation_id="copilotStatus")
def status(request: Request) -> CopilotStatus:
    real = uses_model(request)
    return CopilotStatus(
        model=settings_of(request).copilot_model if real else "stand-in",
        stand_in=not real,
        sign_in_required=real,
    )


@router.post("/chat", operation_id="copilotChat", response_class=StreamingResponse, dependencies=[Depends(check_origin)])
async def chat(
    request: Request, body: ChatRequest, user: Annotated[User | None, Depends(current_user)]
) -> StreamingResponse:
    """Streams one assistant message in the Vercel AI SDK UI message stream format."""
    real = uses_model(request)
    if real and user is None:
        raise not_signed_in(request, "sign_in_required")  # codes: the web pane words them per language
    limit_key = f"user:{user.id}" if user else f"ip:{client_ip(request)}"
    # Free: 10 questions a day and no Pro-only tools; Pro: 60 an hour (plans.LIMITS).
    plan = await run_in_threadpool(plan_of, request, user)
    request.state.plan = plan
    limiter = request.app.state.copilot_day_limit if plan == "free" else request.app.state.copilot_limit
    if not await run_in_threadpool(limiter.hit, limit_key):
        raise HTTPException(429, "rate_limited_free" if plan == "free" else "rate_limited")
    try:
        chat_input = to_input(body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    s = settings_of(request)
    match provider(request):
        case "openrouter":
            stream = openai_stream(request, chat_input, s)
        case "anthropic":
            stream = claude_stream(request, chat_input, s)
        case _:
            stream = standin_stream(request, chat_input)
    return StreamingResponse(with_keepalive(stream), media_type="text/event-stream", headers=HEADERS)
