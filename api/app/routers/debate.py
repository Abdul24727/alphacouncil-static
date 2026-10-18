"""Advisors' debate room (app/debate): the room's status, convening a session (streamed live),
and the member's past sessions.

Pro only, with a monthly allowance (plans.LIMITS "debates_per_month"); a failed session does not
count. A session runs as its own task: if the browser goes away it still finishes and is saved,
and the screen picks it up again from GET /debate/sessions/{id}.
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from ..auth import User, check_origin, current_user, require_user
from ..copilot.stream import HEADERS, part, with_keepalive
from ..debate import llm, roster, standin, store
from ..debate.engine import Context, Debate
from ..debate.pack import Source, build
from ..plans import LIMITS, PRO_REQUIRED, Plan, plan_of
from .ticker import TickerRef, ref_of, resolve, settings_of

log = logging.getLogger(__name__)
router = APIRouter(prefix="/debate", tags=["debate"])

# Sessions run as tasks of their own (see the module docstring); kept here so none is collected mid-run.
TASKS: set[asyncio.Task] = set()


def uses_models(request: Request) -> bool:
    """The room runs on OpenRouter whenever its key is set (else the labelled stand-in)."""
    return bool(os.environ.get("OPENROUTER_API_KEY")) and settings_of(request).copilot_provider != "standin"


def seats(request: Request) -> tuple[list[roster.Seat], roster.Seat]:
    try:
        return roster.advisors(settings_of(request).debate_advisors), roster.chair()
    except roster.RosterError as exc:
        log.error("advisors' room: %s", exc)
        raise HTTPException(503, "advisors_unavailable") from exc


def debate_rounds(request: Request) -> int:
    return min(max(settings_of(request).debate_rounds, 1), 2)


def models_of(request: Request) -> dict[str, str]:
    s = settings_of(request)
    if not uses_models(request):
        return {"advisors": "stand-in", "chair": "stand-in"}
    return {"advisors": s.debate_advisor_model, "chair": s.debate_chair_model}


# --- what the browser sees ------------------------------------------------------------------------


class DebateStatus(BaseModel):
    plan: Plan
    signed_in: bool
    stand_in: bool
    # Sessions a month on this plan, used this calendar month (UTC), and when the count restarts.
    limit: int
    used: int
    resets_at: datetime
    running: int | None  # a session of this account still in progress
    seats: list[roster.SeatInfo]  # the advisors in seat order, then the Chair
    rounds: int  # openings + debate rounds + vote
    models: dict[str, str]


class DebateTurn(BaseModel):
    stage: str
    round: int | None
    seat: str
    data: dict[str, Any]
    # unverified: figures found nowhere in the data; cited: citations added; removed: advice sentences dropped.
    flags: dict[str, Any] | None
    seconds: float | None


class DebateSummary(BaseModel):
    id: int
    ticker: TickerRef | None
    ticker_key: str
    question: str
    locale: str
    status: str  # running | done | failed
    created_at: datetime
    seconds: float | None
    result: dict[str, Any] | None


class DebateSession(DebateSummary):
    seats: list[roster.SeatInfo]
    models: dict[str, str]
    rounds: int
    sources: dict[str, Source] | None
    error: str | None
    finished_at: datetime | None
    turns: list[DebateTurn]


class StartBody(BaseModel):
    ticker: str = Field(min_length=1, max_length=40)
    question: str = Field(min_length=3, max_length=300)
    locale: Literal["en", "ar"] = "en"


def _ref(request: Request, ticker_key: str) -> TickerRef | None:
    t = request.app.state.universe.by_key.get(ticker_key)
    return ref_of(t) if t else None


def summary_of(request: Request, row: Any) -> DebateSummary:
    return DebateSummary(
        id=row.id,
        ticker=_ref(request, row.ticker_key),
        ticker_key=row.ticker_key,
        question=row.question,
        locale=row.locale,
        status=row.status,
        created_at=row.created_at,
        seconds=row.seconds,
        result=row.result,
    )


def session_of(request: Request, row: Any, turns: list[Any]) -> DebateSession:
    return DebateSession(
        **summary_of(request, row).model_dump(),
        seats=row.seats,
        models=row.models,
        rounds=row.rounds,
        sources=row.sources,
        error=row.error,
        finished_at=row.finished_at,
        turns=[
            DebateTurn(stage=t.stage, round=t.round, seat=t.seat, data=t.data, flags=t.flags, seconds=t.seconds) for t in turns
        ],
    )


# --- endpoints ---------------------------------------------------------------------------------------


@router.get("/status", operation_id="debateStatus")
def status(request: Request, user: Annotated[User | None, Depends(current_user)]) -> DebateStatus:
    s = settings_of(request)
    advisors, chair = seats(request)
    plan = plan_of(request, user)
    used = running = None
    if user:
        store.expire_stale(s.database_url)
        used = store.used_this_month(s.database_url, user.id)
        running = store.running_for(s.database_url, user.id)
    return DebateStatus(
        plan=plan,
        signed_in=user is not None,
        stand_in=not uses_models(request),
        limit=LIMITS[plan]["debates_per_month"] or 0,
        used=used or 0,
        resets_at=store.next_month(datetime.now(UTC)),
        running=running,
        seats=[a.info for a in advisors] + [chair.info],
        rounds=debate_rounds(request) + 2,
        models=models_of(request),
    )


@router.get("/sessions", operation_id="listDebates")
def list_sessions(request: Request, user: Annotated[User, Depends(require_user)]) -> list[DebateSummary]:
    """The account's sessions, newest first (also after Pro ends: they are the member's own)."""
    url = settings_of(request).database_url
    store.expire_stale(url)
    return [summary_of(request, r) for r in store.list_for(url, user.id)]


@router.get("/sessions/{session_id}", operation_id="getDebate")
def get_session(request: Request, session_id: int, user: Annotated[User, Depends(require_user)]) -> DebateSession:
    url = settings_of(request).database_url
    store.expire_stale(url)
    found = store.get_for(url, user.id, session_id)
    if found is None:
        raise HTTPException(404, "Session not found.")
    return session_of(request, *found)


@router.post("/sessions", operation_id="startDebate", response_class=StreamingResponse, dependencies=[Depends(check_origin)])
async def start(request: Request, body: StartBody, user: Annotated[User, Depends(require_user)]) -> StreamingResponse:
    """Convene the advisors on one question about one stock. Streams the session as SSE events
    (`data: {...}` lines): session, stage, writing, turn, result, error, done."""
    s = settings_of(request)
    url = s.database_url
    plan = await run_in_threadpool(plan_of, request, user)
    if plan != "pro":
        raise HTTPException(403, PRO_REQUIRED)
    request.state.plan = plan
    question = " ".join(body.question.split())
    if len(question) < 3:
        raise HTTPException(422, "question_too_short")
    t = resolve(request, body.ticker)
    advisors, chair = seats(request)

    await run_in_threadpool(store.expire_stale, url)
    # Two clicks at once: only the first gets through.
    if not await run_in_threadpool(request.app.state.debate_start_limit.hit, f"user:{user.id}"):
        raise HTTPException(409, "debate_running")
    if await run_in_threadpool(store.running_for, url, user.id):
        raise HTTPException(409, "debate_running")
    if await run_in_threadpool(store.used_this_month, url, user.id) >= (LIMITS[plan]["debates_per_month"] or 0):
        raise HTTPException(429, "debate_limit")

    pack = await build(request, t, body.locale)
    ctx = Context(
        settings=s, pack=pack, question=question, locale=body.locale, advisors=advisors, chair=chair, debate_rounds=debate_rounds(request)
    )
    models = models_of(request)
    sid = await run_in_threadpool(
        store.create,
        url,
        user_id=user.id,
        ticker_key=t.ticker_key,
        question=question,
        locale=body.locale,
        seats=[a.info.model_dump() for a in advisors] + [chair.info.model_dump()],
        models=models,
        rounds=ctx.rounds,
    )
    sources = {tag: src.model_dump() for tag, src in pack.sources.items()}
    await run_in_threadpool(store.set_sources, url, sid, sources)

    if uses_models(request):

        async def ask(*, messages, model, max_tokens, temperature, check, **_: Any):  # noqa: ANN001, ANN202
            return await llm.ask(s, model, messages, max_tokens=max_tokens, temperature=temperature, check=check)

    else:
        ask = standin.make_asker(pack, advisors, body.locale)

    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    found = await run_in_threadpool(store.get_for, url, user.id, sid)
    queue.put_nowait({"type": "session", "session": session_of(request, *found).model_dump(mode="json")})
    task = asyncio.create_task(run_session(url, sid, ctx, ask, queue.put_nowait, models))
    TASKS.add(task)
    task.add_done_callback(TASKS.discard)
    return StreamingResponse(with_keepalive(_events(queue)), media_type="text/event-stream", headers=HEADERS)


async def _events(queue: asyncio.Queue) -> AsyncIterator[str]:
    while (event := await queue.get()) is not None:
        yield part(event)


async def run_session(url: str, sid: int, ctx: Context, ask: Any, emit: Any, models: dict[str, str]) -> None:
    """Run every stage, save as it goes, close the session with its time and cost."""

    async def save(turn: dict[str, Any], usage: llm.Usage | None) -> None:
        await run_in_threadpool(store.add_turn, url, sid, turn, usage)

    started = time.monotonic()
    debate = Debate(ctx, ask, emit, save)
    status, error = "done", None
    try:
        await debate.run()
    except llm.SeatError as exc:
        status, error = "failed", exc.code
    except Exception:
        log.exception("debate %s failed", sid)
        status, error = "failed", "internal"
    result = debate.state.result
    if result is not None and debate.state.brief:
        result = {
            **result,
            "labels": {o["id"]: o["label"] for o in debate.state.brief["options"]},
            "headline": (debate.state.verdict or {}).get("headline"),
        }
    totals = await run_in_threadpool(store.finish, url, sid, status=status, result=result, error=error, seconds=time.monotonic() - started)
    log.info(
        "debate %s %s%s: %.1f s, %d turns, cost %s USD, tokens %s in / %s out (%s)",
        sid,
        status,
        f" ({error})" if error else "",
        totals["seconds"],
        totals["turns"],
        f"{totals['cost_usd']:.4f}" if totals["cost_usd"] is not None else "n/a",
        totals["prompt_tokens"],
        totals["completion_tokens"],
        ", ".join(f"{k} {v}" for k, v in models.items()),
    )
    if error:
        emit({"type": "error", "code": error})
    emit({"type": "done", "status": status, "seconds": totals["seconds"], "result": result})
    emit(None)
