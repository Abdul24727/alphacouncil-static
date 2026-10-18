"""Debate sessions and their turns in the app database (appdb.debate_sessions / debate_turns)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, insert, select, update

from ..appdb import debate_sessions, debate_turns, engine_for, random_id, utcnow
from .llm import Usage

# A session still "running" after this long lost its worker (a restart): it is marked failed.
STALE_AFTER = timedelta(minutes=15)


def month_start(now: datetime) -> datetime:
    return now.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def next_month(now: datetime) -> datetime:
    start = month_start(now)
    return start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)


def create(url: str, *, user_id: int, ticker_key: str, question: str, locale: str, seats: list[dict], models: dict, rounds: int) -> int:
    with engine_for(url).begin() as conn:
        sid = random_id(conn, debate_sessions)
        conn.execute(
            insert(debate_sessions).values(
                id=sid,
                user_id=user_id,
                ticker_key=ticker_key,
                question=question,
                locale=locale,
                status="running",
                seats=seats,
                models=models,
                rounds=rounds,
            )
        )
    return sid


def set_sources(url: str, sid: int, sources: dict[str, Any]) -> None:
    with engine_for(url).begin() as conn:
        conn.execute(update(debate_sessions).where(debate_sessions.c.id == sid).values(sources=sources))


def add_turn(url: str, sid: int, turn: dict[str, Any], usage: Usage | None) -> None:
    with engine_for(url).begin() as conn:
        conn.execute(
            insert(debate_turns).values(
                session_id=sid,
                stage=turn["stage"],
                round=turn.get("round"),
                seat=turn["seat"],
                data=turn["data"],
                flags=turn.get("flags"),
                model=usage.model if usage else None,
                seconds=usage.seconds if usage else None,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
                cost_usd=usage.cost_usd if usage else None,
            )
        )


def finish(url: str, sid: int, *, status: str, result: dict | None, error: str | None, seconds: float) -> dict[str, Any]:
    """Close the session with its totals (summed from its turns); returns the totals."""
    with engine_for(url).begin() as conn:
        totals = conn.execute(
            select(
                func.sum(debate_turns.c.cost_usd),
                func.sum(debate_turns.c.prompt_tokens),
                func.sum(debate_turns.c.completion_tokens),
                func.count(),
            ).where(debate_turns.c.session_id == sid)
        ).one()
        values = {
            "status": status,
            "result": result,
            "error": error,
            "seconds": round(seconds, 2),
            "cost_usd": totals[0],
            "prompt_tokens": totals[1],
            "completion_tokens": totals[2],
            "finished_at": utcnow(),
        }
        conn.execute(update(debate_sessions).where(debate_sessions.c.id == sid).values(**values))
    return {**values, "turns": totals[3]}


def expire_stale(url: str, now: datetime | None = None) -> None:
    now = now or utcnow()
    with engine_for(url).begin() as conn:
        conn.execute(
            update(debate_sessions)
            .where(debate_sessions.c.status == "running", debate_sessions.c.created_at < now - STALE_AFTER)
            .values(status="failed", error="interrupted", finished_at=now)
        )


def used_this_month(url: str, user_id: int, now: datetime | None = None) -> int:
    """Sessions that count against the month's allowance: running or done (failed ones do not)."""
    start = month_start(now or utcnow())
    with engine_for(url).connect() as conn:
        return conn.execute(
            select(func.count())
            .select_from(debate_sessions)
            .where(
                debate_sessions.c.user_id == user_id,
                debate_sessions.c.status.in_(("running", "done")),
                debate_sessions.c.created_at >= start,
            )
        ).scalar_one()


def running_for(url: str, user_id: int) -> int | None:
    with engine_for(url).connect() as conn:
        return conn.execute(
            select(debate_sessions.c.id)
            .where(debate_sessions.c.user_id == user_id, debate_sessions.c.status == "running")
            .order_by(debate_sessions.c.created_at.desc())
        ).scalar()


def list_for(url: str, user_id: int, limit: int = 50) -> list[Any]:
    with engine_for(url).connect() as conn:
        return conn.execute(
            select(debate_sessions)
            .where(debate_sessions.c.user_id == user_id)
            .order_by(debate_sessions.c.created_at.desc())
            .limit(limit)
        ).fetchall()


def get_for(url: str, user_id: int, sid: int) -> tuple[Any, list[Any]] | None:
    """The session and its turns, only for its owner."""
    with engine_for(url).connect() as conn:
        row = conn.execute(
            select(debate_sessions).where(debate_sessions.c.id == sid, debate_sessions.c.user_id == user_id)
        ).first()
        if row is None:
            return None
        turns = conn.execute(
            select(debate_turns).where(debate_turns.c.session_id == sid).order_by(debate_turns.c.id)
        ).fetchall()
    return row, turns


def stats(url: str, days: int = 30) -> dict[str, Any]:
    """Time and cost of finished sessions (python -m app.debate stats)."""
    since = utcnow() - timedelta(days=days)
    with engine_for(url).connect() as conn:
        rows = conn.execute(
            select(debate_sessions.c.seconds, debate_sessions.c.cost_usd, debate_sessions.c.models, debate_sessions.c.locale)
            .where(debate_sessions.c.status == "done", debate_sessions.c.created_at >= since)
        ).fetchall()
        failed = conn.execute(
            select(func.count()).select_from(debate_sessions).where(debate_sessions.c.status == "failed", debate_sessions.c.created_at >= since)
        ).scalar_one()
    secs = sorted(r.seconds for r in rows if r.seconds is not None)
    costs = sorted(r.cost_usd for r in rows if r.cost_usd is not None)

    def median(xs: list[float]) -> float | None:
        return (xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2) if xs else None

    return {
        "days": days,
        "done": len(rows),
        "failed": failed,
        "seconds_median": median(secs),
        "seconds_max": secs[-1] if secs else None,
        "cost_usd_median": median(costs),
        "cost_usd_mean": sum(costs) / len(costs) if costs else None,
        "cost_usd_total": sum(costs) if costs else None,
        "models": sorted({f"{r.models.get('advisors')} / {r.models.get('chair')}" for r in rows if r.models}),
    }
