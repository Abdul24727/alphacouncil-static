"""Pro billing: checkout, confirmation, the Free/Pro gates, renewals, webhook, refunds."""

import re
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

ORIGIN = {"Origin": "http://testserver"}
EMAIL = "payer@alphamail.co"
PRO = 7900


class FakeMoyasar:
    """Payments and saved cards in memory; renewals succeed unless `decline` is set."""

    def __init__(self):
        self.payments, self.tokens, self.decline, self.created = {}, {"token_card1"}, False, []

    def pay(self, pid, user_id, kind="first", amount=PRO, status="paid", token="token_card1", currency="SAR"):
        self.payments[pid] = {
            "id": pid, "status": status, "amount": amount, "currency": currency,
            "metadata": {"user_id": str(user_id), "kind": kind},
            "source": {"type": "creditcard", "company": "visa", "number": "4111-11XX-XXXX-1111", "token": token, "message": "Insufficient funds" if status == "failed" else "APPROVED"},
        }
        return self.payments[pid]

    def __call__(self, settings, method, path, body=None):
        from app import http

        if method == "GET" and path.startswith("/payments/"):
            p = self.payments.get(path.split("/")[-1])
            return http.Reply(200, p) if p else http.Reply(404, {"message": "not found"})
        if method == "POST" and path == "/payments":
            self.created.append(body)
            assert body["source"] == {"type": "token", "token": body["source"]["token"]} and body["amount"] == PRO
            p = self.pay(body["given_id"], body["metadata"]["user_id"], "renewal", status="failed" if self.decline else "paid", token=None)
            return http.Reply(201, p)
        if method == "DELETE" and path.startswith("/tokens/"):
            self.tokens.discard(path.split("/")[-1])
            return http.Reply(204, None)
        raise AssertionError((method, path))


@pytest.fixture
def moyasar(client, monkeypatch):
    from app import billing, mail

    fake = FakeMoyasar()
    monkeypatch.setattr(billing, "moyasar", fake)
    s = client.app.state.settings
    monkeypatch.setattr(s, "billing_open", True)
    monkeypatch.setattr(s, "moyasar_publishable_key", "pk_test_x")
    monkeypatch.setattr(s, "smtp_host", "smtp.test")
    monkeypatch.setenv("MOYASAR_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("MOYASAR_WEBHOOK_SECRET", "hook-secret")
    fake.mail = []
    monkeypatch.setattr(mail, "deliver", lambda settings, msg: fake.mail.append(msg))
    return fake


def verified_user(client, moyasar, email=EMAIL):
    client.post("/v1/auth/signup", json={"email": email, "password": "correct horse battery", "accept_terms": True}, headers=ORIGIN)
    token = re.search(r"#token=([\w-]+)", moyasar.mail[-1].get_content()).group(1)
    client.post("/v1/auth/verify-email", json={"token": token}, headers=ORIGIN)
    return client.get("/v1/auth/me").json()["user"]["id"]


def checkout(client):
    return client.post("/v1/billing/checkout", json={"accept_terms": True}, headers=ORIGIN)


def subscription(client, uid):
    from app.appdb import engine_for, subscriptions

    with engine_for(client.app.state.settings.database_url).connect() as conn:
        return conn.execute(select(subscriptions).where(subscriptions.c.user_id == uid)).first()


def set_sub(client, uid, **values):
    from app.appdb import engine_for, subscriptions

    with engine_for(client.app.state.settings.database_url).begin() as conn:
        conn.execute(update(subscriptions).where(subscriptions.c.user_id == uid).values(**values))


def renew(client, now=None):
    from app.billing import run_renewals

    return run_renewals(client.app.state.settings, now)


def aware(t):
    return t if t.tzinfo else t.replace(tzinfo=UTC)


# --- plans and gates ----------------------------------------------------------------------------


def test_early_access_gives_everyone_pro_until_billing_opens(client, monkeypatch):
    assert client.get("/v1/billing/plan").json()["plan"] == "pro"
    assert client.get("/v1/tickers/2222/council").status_code == 200
    monkeypatch.setattr(client.app.state.settings, "billing_open", True)
    plan = client.get("/v1/billing/plan").json()
    assert plan["plan"] == "free" and plan["price_sar"] == 79 and plan["limits"]["holdings"] == 20
    for path in ("council", "fundamentals", "statements", "corporate", "insights", "events"):
        r = client.get(f"/v1/tickers/2222/{path}")
        assert r.status_code == 403 and r.json()["detail"] == "pro_required", path
    assert client.get("/v1/tickers/2222").status_code == 200  # the overview stays free


def test_free_plan_limits_holdings_and_alerts(client, moyasar, monkeypatch):
    from app import plans

    verified_user(client, moyasar)
    # The fixture universe is small: a Free limit of 2 holdings shows the same rule as 20.
    monkeypatch.setitem(plans.LIMITS["free"], "holdings", 2)
    codes = [client.post("/v1/portfolio/holdings", json={"ticker": t, "quantity": 1}, headers=ORIGIN) for t in ("2222", "1120", "2010")]
    assert [c.status_code for c in codes] == [200, 200, 400] and "Pro holds 200" in codes[2].json()["detail"]
    alerts = [client.post("/v1/portfolio/alerts", json={"ticker": "2222", "kind": "above", "price": i + 1}, headers=ORIGIN).status_code for i in range(6)]
    assert alerts == [200] * 5 + [400]


def test_free_copilot_cannot_read_pro_data(client, moyasar):
    from types import SimpleNamespace

    from app.copilot import tools

    req = SimpleNamespace(app=client.app, state=SimpleNamespace(plan="free"))
    assert "Pro" in tools.run(req, "get_council", {"ticker": "2222"})["error"]


# --- checkout and confirmation ----------------------------------------------------------------------


def test_checkout_needs_open_billing_a_confirmed_email_and_the_terms(client, moyasar, monkeypatch):
    client.post("/v1/auth/signup", json={"email": EMAIL, "password": "correct horse battery", "accept_terms": True}, headers=ORIGIN)
    assert checkout(client).status_code == 403  # email not confirmed
    token = re.search(r"#token=([\w-]+)", moyasar.mail[-1].get_content()).group(1)
    client.post("/v1/auth/verify-email", json={"token": token}, headers=ORIGIN)
    assert client.post("/v1/billing/checkout", json={}, headers=ORIGIN).status_code == 422
    form = checkout(client).json()
    assert form["amount"] == PRO and form["currency"] == "SAR" and form["publishable_key"] == "pk_test_x"
    assert form["callback_url"] == "http://testserver/billing/return" and form["metadata"]["kind"] == "first"
    monkeypatch.setattr(client.app.state.settings, "billing_open", False)
    assert checkout(client).status_code == 409


def test_a_paid_payment_starts_pro_once(client, moyasar):
    uid = verified_user(client, moyasar)
    moyasar.pay("pay_1", uid)
    s = client.post("/v1/billing/confirm", json={"payment_id": "pay_1"}, headers=ORIGIN).json()
    assert s["plan"] == "pro" and s["renews"] and s["card_brand"] == "visa" and s["card_last4"] == "1111"
    end = aware(subscription(client, uid).current_period_end)
    assert timedelta(days=27) < end - datetime.now(UTC) < timedelta(days=32)
    # The return page asked twice, and the webhook too: still one month.
    client.post("/v1/billing/confirm", json={"payment_id": "pay_1"}, headers=ORIGIN)
    client.post("/v1/billing/webhook/moyasar", json={"secret_token": "hook-secret", "type": "payment_paid", "data": {"id": "pay_1"}})
    assert aware(subscription(client, uid).current_period_end) == end
    assert client.get("/v1/tickers/2222/council").status_code == 200
    assert [m["Subject"] for m in moyasar.mail][-1] == "Your AlphaCouncil Pro receipt"


def test_confirm_trusts_only_moyasar(client, moyasar):
    uid = verified_user(client, moyasar)
    moyasar.pay("pay_other", uid + 1)
    assert client.post("/v1/billing/confirm", json={"payment_id": "pay_other"}, headers=ORIGIN).status_code == 403
    moyasar.pay("pay_failed", uid, status="failed")
    r = client.post("/v1/billing/confirm", json={"payment_id": "pay_failed"}, headers=ORIGIN)
    assert r.status_code == 409 and "Insufficient funds" in r.json()["detail"]
    moyasar.pay("pay_cheap", uid, amount=100)
    client.post("/v1/billing/confirm", json={"payment_id": "pay_cheap"}, headers=ORIGIN)
    assert subscription(client, uid) is None
    assert client.post("/v1/billing/confirm", json={"payment_id": "pay_missing"}, headers=ORIGIN).status_code == 502


def test_the_webhook_needs_the_shared_secret(client, moyasar):
    uid = verified_user(client, moyasar)
    moyasar.pay("pay_2", uid)
    assert client.post("/v1/billing/webhook/moyasar", json={"secret_token": "wrong", "type": "payment_paid", "data": {"id": "pay_2"}}).status_code == 403
    assert subscription(client, uid) is None
    assert client.post("/v1/billing/webhook/moyasar", json={"secret_token": "hook-secret", "type": "payment_paid", "data": {"id": "pay_2"}}).status_code == 200
    assert subscription(client, uid).status == "active"


# --- renewals ------------------------------------------------------------------------------------


def paid_up(client, moyasar):
    uid = verified_user(client, moyasar)
    moyasar.pay("pay_first", uid)
    client.post("/v1/billing/confirm", json={"payment_id": "pay_first"}, headers=ORIGIN)
    return uid


def test_renewal_charges_the_saved_card_and_continues_the_period(client, moyasar):
    uid = paid_up(client, moyasar)
    end = aware(subscription(client, uid).current_period_end)
    assert renew(client, end - timedelta(days=2))["reminded"] == 1
    assert renew(client, end - timedelta(days=1))["reminded"] == 0  # once per period
    assert moyasar.mail[-1]["Subject"].startswith("Your AlphaCouncil Pro renews on")
    counts = renew(client, end + timedelta(minutes=5))
    assert counts["renewed"] == 1 and moyasar.created[0]["source"]["token"] == "token_card1"
    new_end = aware(subscription(client, uid).current_period_end)
    assert new_end.day == end.day and new_end > end + timedelta(days=27)  # same day next month, no drift
    assert renew(client, end + timedelta(minutes=10))["renewed"] == 0


def test_failed_renewals_are_retried_then_pro_ends_and_the_card_is_deleted(client, moyasar):
    uid = paid_up(client, moyasar)
    end = aware(subscription(client, uid).current_period_end)
    moyasar.decline = True
    assert renew(client, end + timedelta(hours=1))["failed"] == 1
    sub = subscription(client, uid)
    assert sub.status == "past_due" and sub.renew_attempts == 1
    assert renew(client, end + timedelta(hours=2))["failed"] == 0  # next try is a day later
    assert renew(client, end + timedelta(days=1, hours=2))["failed"] == 1
    assert renew(client, end + timedelta(days=2, hours=3))["ended"] == 1
    sub = subscription(client, uid)
    assert sub.status == "expired" and sub.token_id is None and "token_card1" not in moyasar.tokens
    assert [m["Subject"] for m in moyasar.mail][-1] == "Your AlphaCouncil Pro has ended"
    assert len({b["given_id"] for b in moyasar.created}) == 3  # one Moyasar payment per attempt


def test_cancel_keeps_pro_to_the_period_end_then_stops(client, moyasar):
    uid = paid_up(client, moyasar)
    s = client.post("/v1/billing/cancel", headers=ORIGIN).json()
    assert s["plan"] == "pro" and s["renews"] is False and s["status"] == "canceled"
    assert client.post("/v1/billing/resume", headers=ORIGIN).json()["renews"] is True
    client.post("/v1/billing/cancel", headers=ORIGIN)
    end = aware(subscription(client, uid).current_period_end)
    assert renew(client, end + timedelta(minutes=1))["ended"] == 1 and moyasar.created == []
    assert client.get("/v1/billing").json()["plan"] == "free"


def test_a_refund_ends_pro_now(client, moyasar):
    uid = paid_up(client, moyasar)
    moyasar.payments["pay_first"]["status"] = "refunded"
    client.post("/v1/billing/webhook/moyasar", json={"secret_token": "hook-secret", "type": "payment_refunded", "data": {"id": "pay_first"}})
    assert subscription(client, uid).status == "expired" and "token_card1" not in moyasar.tokens
    assert client.get("/v1/billing").json()["plan"] == "free"


def test_deleting_the_account_deletes_the_saved_card(client, moyasar):
    paid_up(client, moyasar)
    assert client.post("/v1/me/delete", json={"password": "correct horse battery"}, headers=ORIGIN).status_code == 200
    assert "token_card1" not in moyasar.tokens


def test_add_month_keeps_the_day_or_takes_the_last():
    from app.billing import add_month

    assert add_month(datetime(2026, 1, 31, tzinfo=UTC)) == datetime(2026, 2, 28, tzinfo=UTC)
    assert add_month(datetime(2026, 12, 15, tzinfo=UTC)) == datetime(2027, 1, 15, tzinfo=UTC)


def test_complimentary_pro_never_charges_and_ends_by_itself(client, moyasar):
    from app.billing import grant

    uid = verified_user(client, moyasar)
    end = grant(client.app.state.settings, EMAIL.upper(), 30)
    assert client.get("/v1/billing").json()["plan"] == "pro"
    assert renew(client, end + timedelta(minutes=1))["ended"] == 1 and moyasar.created == []
    assert subscription(client, uid).status == "expired"


def test_outside_calls_send_a_user_agent(monkeypatch):
    """Moyasar's API is behind Cloudflare, which refuses Python's default user agent (1010)."""
    import urllib.request

    from app import http

    seen = {}

    class Answer:
        status = 200

        def read(self):
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout):
        seen.update({k.lower(): v for k, v in req.header_items()})
        return Answer()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert http.call("GET", "https://api.moyasar.com/v1/payments").ok
    assert seen["user-agent"].startswith("AlphaCouncil/")
