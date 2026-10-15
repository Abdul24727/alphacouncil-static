import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..copilot.context import ChatRequest, to_input
from ..copilot.engine import claude_stream
from ..copilot.standin import standin_stream
from ..copilot.stream import HEADERS
from .ticker import settings_of

router = APIRouter(prefix="/copilot", tags=["copilot"])


def model_configured() -> bool:
    """Claude runs when credentials exist; otherwise the labelled stand-in answers."""
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


class CopilotStatus(BaseModel):
    model: str
    stand_in: bool


@router.get("/status", operation_id="copilotStatus")
def status(request: Request) -> CopilotStatus:
    s = settings_of(request)
    configured = model_configured() and s.copilot_provider != "standin"
    return CopilotStatus(model=s.copilot_model if configured else "stand-in", stand_in=not configured)


@router.post("/chat", operation_id="copilotChat", response_class=StreamingResponse)
async def chat(request: Request, body: ChatRequest) -> StreamingResponse:
    """Streams one assistant message in the Vercel AI SDK UI message stream format."""
    try:
        chat_input = to_input(body)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    s = settings_of(request)
    if model_configured() and s.copilot_provider != "standin":
        stream = claude_stream(request, chat_input, s)
    else:
        stream = standin_stream(request, chat_input)
    return StreamingResponse(stream, media_type="text/event-stream", headers=HEADERS)
