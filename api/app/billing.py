"""Pro billing with Moyasar: monthly, renewing until cancelled.

- First payment: in the browser, with Moyasar's payment form. Card details go straight to
  Moyasar and never reach this server; the form saves the card as a token (save_card).
  Moyasar sends the payer back to /billing/return?id=..., and the page asks /billing/confirm,
  which fetches the payment from Moyasar with the secret key and acts only on what Moyasar
  says: paid, the Pro price, in SAR, for this account.
- Renewals: `python -m app.billing renew` (an hourly systemd timer) charges the saved token
  when a period ends, unless cancelled; a reminder goes out 3 days before. A failed renewal is
  retried daily, 3 times, and Pro stays on meanwhile (plans.GRACE); then the plan ends.
- Moyasar's webhook (/api/billing/webhook/moyasar, the address the old site registered) is a
  second path to the same confirmation, for a payer who closed the browser before returning,
  and how refunds made in Moyasar's dashboard end Pro.
- Every payment is recorded once (billing_payments, by Moyasar's id): the return page, the
  webhook and a re-run renewal can never extend Pro twice for one payment.
"""

import calendar
import hmac
import logging
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from . import http, mail, pricing
from .appdb import billing_payments, consents, engine_for, subscriptions, users, utcnow
from .auth import User, check_origin, current_user, require_user, settings_of, site_url
from .legal import CHECKOUT
from .plans import LIMITS, PRO_ONLY, Plan, has_pro, plan_of
from .settings import Settings, get_settings

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

CURRENCY = "SAR"
REMIND_BEFORE = timedelta(days=3)
RETRY_EVERY = timedelta(days=1)
MAX_ATTEMPTS = 3
# given_id for a renewal charge: the same attempt always gets the same id, so a run that
# stopped halfway cannot charge twice (Moyasar keeps one payment per given_id).
_RENEWAL_NS = uuid.UUID("6f1d0f4e-3b0a-4c55-9a43-2f6a5f1b9c21")


def price_halalas() -> int:
    return pricing.price_sar("pro") * 100


def add_month(t: datetime) -> datetime:
    """Same day next month; the 31st becomes the next month's last day."""
    y, m = (t.year + 1, 1) if t.month == 12 else (t.year, t.month + 1)
    return t.replace(year=y, month=m, day=min(t.day, calendar.monthrange(y, m)[1]))


def _aware(t: datetime | None) -> datetime | None:
    return None if t is None else (t if t.tzinfo else t.replace(tzinfo=UTC))


def _secret() -> str:
    return os.environ.get("MOYASAR_SECRET_KEY", "")


def checkout_open(settings: Settings) -> bool:
    return settings.billing_open and bool(settings.moyasar_publishable_key) and bool(_secret())


def moyasar(settings: Settings, method: str, path: str, body: Any = None) -> http.Reply:
    return http.call(method, f"{settings.moyasar_api}{path}", json_body=body, headers=http.basic(_secret()))


# --- what the browser sees ----------------------------------------------------------------------


class PlanInfo(BaseModel):
    plan: Plan
    # Off = early access: everyone has Pro and there is nothing to buy.
    billing_open: bool
    checkout_open: bool
    price_sar: int
    currency: str
    limits: dict[str, int | None]
    pro_only: list[str]


class Summary(BaseModel):
    plan: Plan
    status: str | None  # active | past_due | canceled | expired; None = never paid
    paid_through: datetime | None
    renews: bool
    card_brand: str | None
    card_last4: str | None
    checkout_open: bool
    email_verified: bool


@router.get("/plan", operation_id="billingPlan")
def get_plan(request: Request, user: Annotated[User | None, Depends(current_user)]) -> PlanInfo:
    s, plan = settings_of(request), plan_of(request, user)
    return PlanInfo(
        plan=plan,
        billing_open=s.billing_open,
        checkout_open=checkout_open(s),
        price_sar=pricing.price_sar("pro"),
        currency=CURRENCY,
        limits=LIMITS[plan],
        pro_only=list(PRO_ONLY),
    )


def summary(request: Request, user: User) -> Summary:
    s = settings_of(request)
    with engine_for(s.database_url).connect() as conn:
        sub = conn.execute(select(subscriptions).where(subscriptions.c.user_id == user.id)).first()
    return Summary(
        plan=plan_of(request, user),
        status=sub.status if sub else None,
        paid_through=_aware(sub.current_period_end) if sub else None,
        renews=bool(sub and sub.status in ("active", "past_due") and not sub.cancel_at_period_end and sub.token_id),
        card_brand=sub.card_brand if sub else None,
        card_last4=sub.card_last4 if sub else None,
        checkout_open=checkout_open(s),
        email_verified=user.email_verified,
    )


@router.get("", operation_id="billingSummary")
def get_summary(request: Request, user: Annotated[User, Depends(require_user)]) -> Summary:
    return summary(request, user)


# --- first payment -------------------------------------------------------------------------------


class CheckoutBody(BaseModel):
    # The checkout acceptance (legal.CHECKOUT), recorded with its document versions.
    accept_terms: bool = False
    locale: str = Field(default="en", pattern="^(en|ar)$")


class CheckoutForm(BaseModel):
    """What Moyasar's payment form is started with. The amount is checked again on confirm."""

    publishable_key: str
    amount: int
    currency: str
    description: str
    callback_url: str
    metadata: dict[str, str]


@router.post("/checkout", operation_id="startCheckout", dependencies=[Depends(check_origin)])
def start_checkout(request: Request, body: CheckoutBody, user: Annotated[User, Depends(require_user)]) -> CheckoutForm:
    s = settings_of(request)
    if not checkout_open(s):
        raise HTTPException(409, "Checkout is not open yet.")
    if not user.email_verified:
        raise HTTPException(403, "Confirm your email address first: we send receipts and renewal reminders there.")
    if not body.accept_terms:
        raise HTTPException(422, f"Please tick: {CHECKOUT['text']}")
    with engine_for(s.database_url).begin() as conn:
        sub = conn.execute(select(subscriptions).where(subscriptions.c.user_id == user.id)).first()
        if sub and sub.status == "active" and not sub.cancel_at_period_end and has_pro(sub.status, sub.current_period_end):
            raise HTTPException(409, "You already have Pro.")
        conn.execute(
            insert(consents).values(
                user_id=user.id,
                kind=CHECKOUT["kind"],
                text_version=CHECKOUT["text_version"],
                documents=CHECKOUT["documents"],
                accepted_at=utcnow(),
            )
        )
    return CheckoutForm(
        publishable_key=s.moyasar_publishable_key or "",
        amount=price_halalas(),
        currency=CURRENCY,
        description=f"AlphaCouncil Pro, monthly, account {user.id}",
        callback_url=f"{site_url(s)}{'/ar' if body.locale == 'ar' else ''}/billing/return",
        metadata={"user_id": str(user.id), "kind": "first"},
    )


class ConfirmBody(BaseModel):
    payment_id: str = Field(max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/confirm", operation_id="confirmPayment", dependencies=[Depends(check_origin)])
def confirm_payment(
    request: Request, body: ConfirmBody, background: BackgroundTasks, user: Annotated[User, Depends(require_user)]
) -> Summary:
    """The return page's check. Moyasar's answer decides, never the redirect's query string."""
    s = settings_of(request)
    r = moyasar(s, "GET", f"/payments/{body.payment_id}")
    if not r.ok or not isinstance(r.body, dict):
        raise HTTPException(502, "We could not reach the payment provider. If you paid, Pro starts as soon as it confirms.")
    p = r.body
    if (p.get("metadata") or {}).get("user_id") != str(user.id):
        raise HTTPException(403, "This payment belongs to another account.")
    if p.get("status") != "paid":
        reason = ((p.get("source") or {}).get("message") or "").strip()
        raise HTTPException(409, f"The payment was not completed{': ' + reason if reason else '.'}")
    apply_payment(s, p, background)
    return summary(request, user)


# --- applying a paid payment ---------------------------------------------------------------------


def apply_payment(settings: Settings, p: dict, background: BackgroundTasks | None = None) -> bool:
    """Records a paid Pro payment and extends Pro, once per payment id. True if applied now."""
    if p.get("status") != "paid" or p.get("amount") != price_halalas() or p.get("currency") != CURRENCY:
        log.warning("Payment %s not applied: status, amount or currency differ from Pro's.", p.get("id"))
        return False
    meta = p.get("metadata") or {}
    try:
        uid = int(meta.get("user_id", ""))
    except ValueError:
        return False
    kind = meta.get("kind") if meta.get("kind") in ("first", "renewal") else "first"
    src = p.get("source") or {}
    now, old_token = utcnow(), None
    with engine_for(settings.database_url).begin() as conn:
        account = conn.execute(select(users.c.email, users.c.locale).where(users.c.id == uid)).first()
        if account is None:
            return False
        try:
            with conn.begin_nested():  # a second request for the same payment stops here
                conn.execute(
                    insert(billing_payments).values(
                        id=str(p["id"]), user_id=uid, kind=kind, amount=p["amount"], currency=p["currency"], status="paid", created_at=now
                    )
                )
        except IntegrityError:
            return False
        sub = conn.execute(select(subscriptions).where(subscriptions.c.user_id == uid)).first()
        old_end = _aware(sub.current_period_end) if sub else None
        if kind == "renewal" and old_end is not None:
            base = old_end  # renewals continue the period exactly: no drift
        elif sub is not None and sub.status in ("active", "canceled") and old_end and old_end > now:
            base = old_end  # paying again while Pro: the new month starts when this one ends
        else:
            base = now
        end = add_month(base)
        token = src.get("token") if kind == "first" else None
        if token and sub is not None and sub.token_id and sub.token_id != token:
            old_token = sub.token_id  # a new card replaces the old one
        token = token or (sub.token_id if sub else None)
        number = str(src.get("number") or "")
        values = {
            "status": "active",
            "current_period_end": end,
            # Without a saved card (tokenization off at Moyasar) Pro cannot renew by itself.
            "cancel_at_period_end": token is None,
            "token_id": token,
            "card_brand": (src.get("company") or (sub.card_brand if sub else None)),
            "card_last4": (number[-4:] if number[-4:].isdigit() else (sub.card_last4 if sub else None)),
            "renew_attempts": 0,
            "next_attempt_at": None,
            "updated_at": now,
        }
        if sub is None:
            conn.execute(insert(subscriptions).values(user_id=uid, created_at=now, **values))
        else:
            conn.execute(update(subscriptions).where(subscriptions.c.user_id == uid).values(**values))
        conn.execute(update(billing_payments).where(billing_payments.c.id == str(p["id"])).values(period_end=end))
    if old_token:
        moyasar(settings, "DELETE", f"/tokens/{old_token}")
    args = (settings, "receipt", account.email, account.locale)
    fields = _email_fields(settings, account.locale, end, values["card_brand"], values["card_last4"], payment=str(p["id"]), renews=token is not None)
    if background is not None:
        background.add_task(mail.send_billing, *args, **fields)
    else:
        mail.send_billing(*args, **fields)
    return True


def _email_fields(settings: Settings, locale: str, date: datetime, brand: str | None, last4: str | None, **extra: Any) -> dict[str, str]:
    ar = locale == "ar"
    renews = extra.pop("renews", None)
    note = ""
    if renews is True:
        note = " يتجدد تلقائيًا كل شهر حتى تلغيه." if ar else " It renews automatically each month until you cancel."
    elif renews is False:
        note = " لن يتجدد تلقائيًا." if ar else " It will not renew by itself."
    return {
        "amount": f"{pricing.price_sar('pro'):.2f} SAR",
        "card": f"{(brand or 'card').title()} •••• {last4 or '????'}",
        "date": date.date().isoformat(),
        "renews": note,
        "link": f"{site_url(settings)}{'/ar' if ar else ''}/settings#billing",
        **{k: str(v) for k, v in extra.items()},
    }


# --- cancel, resume ----------------------------------------------------------------------------


@router.post("/cancel", operation_id="cancelRenewal", dependencies=[Depends(check_origin)])
def cancel_renewal(request: Request, user: Annotated[User, Depends(require_user)]) -> Summary:
    """Stops renewals. Pro stays on until the paid period ends."""
    with engine_for(settings_of(request).database_url).begin() as conn:
        conn.execute(
            update(subscriptions)
            .where(subscriptions.c.user_id == user.id, subscriptions.c.status.in_(("active", "past_due")))
            .values(cancel_at_period_end=True, status="canceled", next_attempt_at=None, updated_at=utcnow())
        )
    return summary(request, user)


@router.post("/resume", operation_id="resumeRenewal", dependencies=[Depends(check_origin)])
def resume_renewal(request: Request, user: Annotated[User, Depends(require_user)]) -> Summary:
    with engine_for(settings_of(request).database_url).begin() as conn:
        sub = conn.execute(select(subscriptions).where(subscriptions.c.user_id == user.id)).first()
        if not (sub and sub.token_id and sub.status == "canceled" and has_pro(sub.status, sub.current_period_end)):
            raise HTTPException(409, "There is no plan to resume. Subscribe again from the pricing page.")
        conn.execute(
            update(subscriptions)
            .where(subscriptions.c.user_id == user.id)
            .values(cancel_at_period_end=False, status="active", updated_at=utcnow())
        )
    return summary(request, user)


def forget_card(request: Request, user_id: int) -> None:
    """Before an account is deleted: the saved card is deleted at Moyasar, so it can never be
    charged again. A failure is logged; the account is deleted either way."""
    s = settings_of(request)
    with engine_for(s.database_url).connect() as conn:
        row = conn.execute(select(subscriptions.c.token_id).where(subscriptions.c.user_id == user_id)).first()
    if row and row.token_id:
        r = moyasar(s, "DELETE", f"/tokens/{row.token_id}")
        if not r.ok and r.status != 404:
            log.error("Saved card of a deleted account not deleted at Moyasar (HTTP %s).", r.status)


# --- webhook -----------------------------------------------------------------------------------


@router.post("/webhook/moyasar", include_in_schema=False)
def moyasar_webhook(request: Request, payload: Annotated[dict[str, Any], Body()]) -> dict[str, bool]:
    """Moyasar's notifications. Its secret_token must match MOYASAR_WEBHOOK_SECRET; even then
    the payment is fetched again from Moyasar before anything changes."""
    expected = os.environ.get("MOYASAR_WEBHOOK_SECRET", "")
    if not expected or not hmac.compare_digest(str(payload.get("secret_token", "")), expected):
        raise HTTPException(403, "Unknown sender.")
    s = settings_of(request)
    kind, data = str(payload.get("type", "")), payload.get("data") or {}
    pid = str(data.get("id", "")) if isinstance(data, dict) else ""
    if not pid or not pid.replace("-", "").replace("_", "").isalnum():
        return {"ok": True}
    r = moyasar(s, "GET", f"/payments/{pid}")
    if not r.ok or not isinstance(r.body, dict):
        raise HTTPException(502, "Payment provider unreachable; try again.")  # Moyasar retries
    if kind == "payment_paid":
        apply_payment(s, r.body)
    elif kind == "payment_refunded" and r.body.get("status") == "refunded":
        _refunded(s, pid)
    return {"ok": True}


def _refunded(settings: Settings, payment_id: str) -> None:
    """A refund (the 14-day guarantee, made in Moyasar's dashboard) of the payment that paid
    the current period ends Pro now and deletes the saved card."""
    now, token = utcnow(), None
    with engine_for(settings.database_url).begin() as conn:
        pay = conn.execute(select(billing_payments).where(billing_payments.c.id == payment_id)).first()
        if pay is None or pay.status == "refunded":
            return
        conn.execute(update(billing_payments).where(billing_payments.c.id == payment_id).values(status="refunded"))
        sub = conn.execute(select(subscriptions).where(subscriptions.c.user_id == pay.user_id)).first()
        if sub and pay.period_end and _aware(pay.period_end) == _aware(sub.current_period_end):
            token = sub.token_id
            conn.execute(
                update(subscriptions)
                .where(subscriptions.c.user_id == pay.user_id)
                .values(status="expired", current_period_end=now, cancel_at_period_end=True, token_id=None, updated_at=now)
            )
    if token:
        moyasar(settings, "DELETE", f"/tokens/{token}")


# --- renewals (hourly job) -------------------------------------------------------------------------


def run_renewals(settings: Settings, now: datetime | None = None) -> dict[str, int]:
    now = now or utcnow()
    counts = {"reminded": 0, "renewed": 0, "failed": 0, "ended": 0, "unreachable": 0}
    with engine_for(settings.database_url).connect() as conn:
        rows = conn.execute(
            select(subscriptions, users.c.email, users.c.locale)
            .join(users, users.c.id == subscriptions.c.user_id)
            .where(subscriptions.c.status.in_(("active", "past_due", "canceled")))
        ).fetchall()
    for r in rows:
        end = _aware(r.current_period_end)
        renewing = r.status in ("active", "past_due") and not r.cancel_at_period_end and bool(r.token_id)
        if renewing and r.status == "active" and now < end <= now + REMIND_BEFORE and _aware(r.reminded_for) != end:
            mail.send_billing(settings, "reminder", r.email, r.locale, **_email_fields(settings, r.locale, end, r.card_brand, r.card_last4))
            _set(settings, r.user_id, reminded_for=end)
            counts["reminded"] += 1
        if end > now:
            continue
        if renewing:
            if r.next_attempt_at is None or _aware(r.next_attempt_at) <= now:
                counts[_charge(settings, r, now)] += 1
        else:
            _end(settings, r, now)
            counts["ended"] += 1
    return counts


def _set(settings: Settings, user_id: int, **values: Any) -> None:
    with engine_for(settings.database_url).begin() as conn:
        conn.execute(update(subscriptions).where(subscriptions.c.user_id == user_id).values(updated_at=utcnow(), **values))


def _charge(settings: Settings, r: Any, now: datetime) -> str:
    end, attempt = _aware(r.current_period_end), r.renew_attempts + 1
    given = str(uuid.uuid5(_RENEWAL_NS, f"{r.user_id}:{end.isoformat()}:{attempt}"))
    body = {
        "given_id": given,
        "amount": price_halalas(),
        "currency": CURRENCY,
        "description": f"AlphaCouncil Pro, monthly renewal, account {r.user_id}",
        "callback_url": f"{site_url(settings)}/settings",
        "source": {"type": "token", "token": r.token_id},
        "metadata": {"user_id": str(r.user_id), "kind": "renewal"},
    }
    sent = moyasar(settings, "POST", "/payments", body)
    p = sent.body if sent.ok and isinstance(sent.body, dict) else None
    if p is None:
        # Created on an earlier run that stopped halfway? Its id is the given_id.
        again = moyasar(settings, "GET", f"/payments/{given}")
        p = again.body if again.ok and isinstance(again.body, dict) else None
        if p is None and sent.status == 0:
            return "unreachable"  # no answer at all: try again next run, same attempt
    if p and p.get("status") == "paid":
        apply_payment(settings, p)
        return "renewed"
    # Declined, or the bank asked for 3-D Secure (the payer is not there to answer).
    if attempt >= MAX_ATTEMPTS:
        _end(settings, r, now)
        return "ended"
    _set(settings, r.user_id, status="past_due", renew_attempts=attempt, next_attempt_at=now + RETRY_EVERY)
    if attempt == 1:
        from .plans import GRACE

        mail.send_billing(settings, "failed", r.email, r.locale, **_email_fields(settings, r.locale, end + GRACE, r.card_brand, r.card_last4))
    return "failed"


def _end(settings: Settings, r: Any, now: datetime) -> None:
    """The plan ends: cancelled and the period is over, or renewals failed. The saved card is
    deleted at Moyasar; holdings over the Free limits stay, read-only above them."""
    _set(settings, r.user_id, status="expired", cancel_at_period_end=True, token_id=None, next_attempt_at=None)
    if r.token_id:
        moyasar(settings, "DELETE", f"/tokens/{r.token_id}")
    mail.send_billing(settings, "ended", r.email, r.locale, **_email_fields(settings, r.locale, _aware(r.current_period_end), r.card_brand, r.card_last4))


def grant(settings: Settings, email: str, days: int) -> datetime:
    """Complimentary Pro (the owner, a partner, a test account): paid through now + days, with
    no card, so it never renews or charges; it ends by itself."""
    now = utcnow()
    end = now + timedelta(days=days)
    with engine_for(settings.database_url).begin() as conn:
        row = conn.execute(select(users.c.id).where(users.c.email == email.strip().lower())).first()
        if row is None:
            raise SystemExit("no account with that email")
        values = {"status": "active", "current_period_end": end, "cancel_at_period_end": True, "renew_attempts": 0, "next_attempt_at": None, "updated_at": now}
        if conn.execute(select(subscriptions.c.user_id).where(subscriptions.c.user_id == row.id)).first():
            conn.execute(update(subscriptions).where(subscriptions.c.user_id == row.id).values(**values))
        else:
            conn.execute(insert(subscriptions).values(user_id=row.id, created_at=now, **values))
    return end


USAGE = "usage: python -m app.billing renew | python -m app.billing grant <email> <days>"


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args == ["renew"]:
        counts = run_renewals(get_settings())
        print(" ".join(f"{k}={v}" for k, v in counts.items()))
        return 0
    if len(args) == 3 and args[0] == "grant" and args[2].isdigit():
        end = grant(get_settings(), args[1], int(args[2]))
        print(f"Pro through {end.date().isoformat()} (no card; does not renew)")
        return 0
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
