"""Is a ticker's data within its expected update window?

The pipeline writes `ticker_freshness` (screening.sqlite) once per category
per ticker: as_of_utc (what the data describes), last_success_utc (when the
pipeline fetched it) and max_age_days (the allowed age). Its own `is_stale`
flag is frozen at pipeline time, so staleness is recomputed here at request
time against the current clock.
"""

from datetime import UTC, datetime, time, timedelta

from pydantic import BaseModel

# Categories that follow the trading calendar: a weekend is not "late".
MARKET_CATEGORIES = {"prices", "technical", "news"}

# Weekday numbers (Mon=0) on which each exchange is closed.
WEEKENDS: dict[str, set[int]] = {
    "ADX": {5, 6},  # UAE: Saturday, Sunday
    "DFM": {5, 6},
}
DEFAULT_WEEKEND = {4, 5}  # Tadawul, QSE, Boursa Kuwait, BHB, MSX: Friday, Saturday

# Nightly pipeline start (root crontab on the VPS: 00:00 UTC every day).
PIPELINE_RUN_UTC = time(0, 0)


class Freshness(BaseModel):
    category: str
    as_of: str | None
    updated_at: str | None
    next_at: str | None
    max_age_days: float | None
    stale: bool | None


def parse_utc(value: str | None) -> datetime | None:
    """ISO timestamps or dates, plus the pipeline's run stamps ("20260807_000115")."""
    if not value:
        return None
    dt: datetime | None = None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(value[: len("20260807_000115") if "_" in fmt else 10], fmt)
                break
            except ValueError:
                continue
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def trading_days_between(start: date, end: date, exchange: str) -> int:
    """Trading days after `start` up to and including `end`."""
    closed = WEEKENDS.get(exchange, DEFAULT_WEEKEND)
    days, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() not in closed:
            days += 1
    return days


def next_run(now: datetime) -> datetime:
    today_run = datetime.combine(now.date(), PIPELINE_RUN_UTC, tzinfo=UTC)
    return today_run if today_run > now else today_run + timedelta(days=1)


def assess(
    *,
    category: str,
    as_of_utc: str | None,
    last_success_utc: str | None,
    max_age_days: float | None,
    exchange: str,
    now: datetime | None = None,
) -> Freshness:
    now = now or datetime.now(UTC)
    as_of = parse_utc(as_of_utc)
    updated = parse_utc(last_success_utc) or as_of

    stale: bool | None = None
    if as_of is not None and max_age_days is not None:
        if category in MARKET_CATEGORIES:
            age = trading_days_between(as_of.date(), now.date(), exchange)
        else:
            age = (now - as_of).total_seconds() / 86400
        stale = age > max_age_days

    return Freshness(
        category=category,
        as_of=as_of.isoformat() if as_of else None,
        updated_at=updated.isoformat() if updated else None,
        next_at=next_run(now).isoformat(),
        max_age_days=max_age_days,
        stale=stale,
    )
