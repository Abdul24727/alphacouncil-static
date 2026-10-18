"""Free and Pro: what each plan allows (the lists on /pricing) and who is on which.

While BILLING_OPEN is off, everyone, signed in or not, has Pro: the early-access promise on
/pricing. With it on, an account has Pro while its subscription is paid up (plus a short grace
period while a failed renewal is retried); everyone else, signed-out visitors included, has Free.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from .appdb import engine_for, subscriptions
from .auth import User, current_user, settings_of

Plan = Literal["free", "pro"]

# The /pricing lists, as numbers. None = no limit of that kind.
LIMITS: dict[str, dict[str, int | None]] = {
    "free": {"holdings": 20, "alerts": 5, "copilot_per_day": 10, "copilot_per_hour": None, "debates_per_month": 0},
    # 20 advisors' sessions a month, like the old site's 20 council reviews.
    "pro": {"holdings": 200, "alerts": 100, "copilot_per_day": None, "copilot_per_hour": 60, "debates_per_month": 20},
}
# Data and tools only Pro has (the web app locks their panels; the API refuses them).
PRO_ONLY = ("council", "financials", "ownership", "calendar", "indicators", "pins", "advisors")

# A failed renewal is retried for this long; Pro stays on meanwhile.
GRACE = timedelta(days=3)
PRO_REQUIRED = "pro_required"


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def has_pro(status: str | None, period_end: datetime | None, now: datetime | None = None) -> bool:
    if status is None or period_end is None:
        return False
    now, end = now or datetime.now(UTC), _aware(period_end)
    if status in ("active", "canceled"):
        return now < end
    if status == "past_due":
        return now < end + GRACE
    return False


def plan_of(request: Request, user: User | None) -> Plan:
    if not settings_of(request).billing_open:
        return "pro"
    if user is None:
        return "free"
    with engine_for(settings_of(request).database_url).connect() as conn:
        row = conn.execute(
            select(subscriptions.c.status, subscriptions.c.current_period_end).where(subscriptions.c.user_id == user.id)
        ).first()
    return "pro" if row and has_pro(row.status, row.current_period_end) else "free"


def limit(request: Request, user: User | None, name: str) -> int | None:
    return LIMITS[plan_of(request, user)][name]


def require_pro(request: Request, user: Annotated[User | None, Depends(current_user)]) -> None:
    """Pro-only data. 403, never 401 (auth.AUTH_FAILED); the web app shows an upgrade prompt."""
    if plan_of(request, user) != "pro":
        raise HTTPException(403, PRO_REQUIRED)
