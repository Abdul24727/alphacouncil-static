import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..auth import User, check_origin, client_ip, current_user
from ..copilot.context import ChatRequest, to_input
from ..copilot.engine import claude_stream
from ..copilot.standin import standin_stream
from ..copilot.stream import HEADERS
from .ticker import settings_of

router = APIRouter(prefix="/copilot", tags=["copilot"])


def model_configured() -> bool:
    """Claude runs when credentials exist; otherwise the labelled stand-in answers."""
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def uses_model(request: Request) -> bool:
    return model_configured() and settings_of(request).copilot_provider != "standin"


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
        raise HTTPException(401, "sign_in_required")  # codes: the web pane words them per language
    if not request.app.state.copilot_limit.hit(f"user:{user.id}" if user else f"ip:{client_ip(request)}"):
        raise HTTPException(429, "rate_limited")
    try:
        chat_input = to_input(body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    s = settings_of(request)
    if real:
        stream = claude_stream(request, chat_input, s)
    else:
        stream = standin_stream(request, chat_input)
    return StreamingResponse(stream, media_type="text/event-stream", headers=HEADERS)
