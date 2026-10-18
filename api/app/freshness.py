"""Is a ticker's data within its expected update window?

The pipeline writes `ticker_freshness` (screening.sqlite) once per category
per ticker: as_of_utc (what the data describes), last_success_utc (when the
pipeline fetched it) and max_age_days (the allowed age). Its own `is_stale`
flag is frozen at pipeline time, so staleness is recomputed here at request
time against the current clock.
"""

from datetime import UTC, date, datetime, time, timedelta

from pydantic import BaseModel

# Categories that follow the trading calendar: a weekend is not "late".
MARKET_CATEGORIES = {"prices", "technical", "news"}

# Weekday numbers (Mon=0) on which each exchange is closed.
WEEKENDS: dict[str, set[int]] = {
    "ADX": {5, 6},  # UAE: Saturday, Sunday
    "DFM": {5, 6},
}
DEFAULT_WEEKEND = {4, 5}  # Tadawul, QSE, Boursa Kuwait, BHB, MSX: Friday, Saturday

# The pipeline's own price threshold (old backend config PRICE_MAX_AGE_DAYS), used when a
# ticker has no ticker_freshness row of its own.
PRICE_MAX_AGE_DAYS = 2

# Nightly pipeline start (root crontab on the VPS: 00:00 UTC every day).
PIPELINE_RUN_UTC = time(0, 0)

# News and disclosures: the pipeline stamps `as_of_utc` with the time of its fetch, so a light
# judged on it says only that the fetch ran. These categories are dated by their newest item
# instead (the sections each one covers, in evidence.sqlite `items`). A listed company files
# something at least monthly (results, board meetings, dividends): on 2026-10-18, 440 of the 447
# non-Tadawul equities had an item from the last 30 days. So the news light (news and
# disclosures, as its panel shows them) allows 30 calendar days; disclosures keep the pipeline's
# own window. Either is also stale when the fetch itself is late.
NEWS_MAX_AGE_DAYS = 30
ITEM_SECTIONS: dict[str, tuple[str, ...]] = {"news": ("news", "disclosures"), "disclosures": ("disclosures",)}


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


def assess_items(
    *,
    category: str,
    newest_item: str | None,
    last_success_utc: str | None,
    max_age_days: float | None,
    exchange: str,
    now: datetime | None = None,
) -> Freshness:
    """News or disclosures, dated by the newest item. `max_age_days` is the pipeline's window
    for the fetch; the items' own window is NEWS_MAX_AGE_DAYS for news, the same for disclosures.
    No item at all leaves the age unknown, unless the fetch is late."""
    now = now or datetime.now(UTC)
    fetch = assess(category=category, as_of_utc=last_success_utc, last_success_utc=last_success_utc,
                   max_age_days=max_age_days, exchange=exchange, now=now)
    window = NEWS_MAX_AGE_DAYS if category == "news" else max_age_days
    newest = parse_utc(newest_item)
    stale: bool | None = True if fetch.stale else None
    if newest is not None and window is not None:
        stale = bool(fetch.stale) or (now - newest).total_seconds() / 86400 > window
    return Freshness(
        category=category,
        as_of=newest.isoformat() if newest else None,
        updated_at=fetch.updated_at,
        next_at=fetch.next_at,
        max_age_days=window,
        stale=stale,
    )
