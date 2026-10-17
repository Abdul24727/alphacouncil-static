import hashlib
import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

ORIGIN = {"Origin": "http://testserver"}


def signup(client, email="tester@example.com", password="correct horse battery"):
    body = {"email": email, "password": password, "accept_terms": True}
    return client.post("/v1/auth/signup", json=body, headers=ORIGIN)


def test_signup_sets_session_and_me(client):
    r = signup(client)
    assert r.status_code == 200, r.text
    assert "acp_session" in r.cookies
    me = client.get("/v1/auth/me").json()
    assert me["user"]["email"] == "tester@example.com"


def test_duplicate_email_and_short_password(client):
    assert signup(client).status_code == 200
    client.cookies.clear()
    assert signup(client).status_code == 409
    r = client.post("/v1/auth/signup", json={"email": "b@example.com", "password": "short"}, headers=ORIGIN)
    assert r.status_code == 422


def test_login_logout(client):
    signup(client)
    client.cookies.clear()
    bad = client.post("/v1/auth/login", json={"email": "tester@example.com", "password": "wrong password!"}, headers=ORIGIN)
    assert bad.status_code == 403
    ok = client.post("/v1/auth/login", json={"email": "Tester@Example.com ", "password": "correct horse battery"}, headers=ORIGIN)
    assert ok.status_code == 200
    assert client.get("/v1/auth/me").json()["user"] is not None
    client.post("/v1/auth/logout", headers=ORIGIN)
    client.cookies.clear()
    assert client.get("/v1/auth/me").json()["user"] is None


def test_cookie_writes_need_our_origin(client):
    signup(client)
    r = client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 10}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 10})
    assert r.status_code == 403  # no Origin at all


def test_portfolio_requires_sign_in(client):
    assert client.get("/v1/portfolio").status_code == 403  # never 401: see auth.AUTH_FAILED


def test_holdings_value_exposure_and_council(client):
    signup(client)
    r = client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 10, "avg_cost": 20}, headers=ORIGIN)
    assert r.status_code == 200, r.text
    client.post("/v1/portfolio/holdings", json={"ticker": "FAB", "quantity": 100}, headers=ORIGIN)
    p = client.get("/v1/portfolio").json()
    h = {x["ticker"]["ticker_key"]: x for x in p["holdings"]}
    aramco = h["2222_TADAWUL"]
    assert aramco["market_value"] == 265.0  # 10 x 26.50 latest close in the price file
    assert aramco["pnl"] == 65.0 and aramco["pnl_pct"] == 32.5
    assert aramco["day_change_value"] == 5.0  # 10 x (26.50 - 26.00)
    # Two currencies, never converted.
    assert {g["currency"] for g in p["groups"]} == {"SAR", "AED"}
    sar = next(g for g in p["groups"] if g["currency"] == "SAR")
    assert sar["sectors"][0]["label"] == "Energy" and sar["sectors"][0]["weight_pct"] == 100.0
    income = next(s for s in p["council"] if s["seat"] == "income")
    assert income["bullish"] + income["neutral"] + income["bearish"] + income["abstain"] == 2
    # Update in place, then delete.
    client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 20}, headers=ORIGIN)
    p = client.get("/v1/portfolio").json()
    aramco = next(x for x in p["holdings"] if x["ticker"]["ticker_key"] == "2222_TADAWUL")
    assert aramco["quantity"] == 20 and len(p["holdings"]) == 2
    client.delete(f"/v1/portfolio/holdings/{aramco['id']}", headers=ORIGIN)
    assert len(client.get("/v1/portfolio").json()["holdings"]) == 1


def test_unknown_ticker_is_404(client):
    signup(client)
    assert client.post("/v1/portfolio/holdings", json={"ticker": "NOPE", "quantity": 1}, headers=ORIGIN).status_code == 404


def test_alerts_evaluate_against_latest_close(client):
    signup(client)
    client.post("/v1/portfolio/alerts", json={"ticker": "2222", "kind": "above", "price": 20}, headers=ORIGIN)
    a = client.post("/v1/portfolio/alerts", json={"ticker": "2222", "kind": "below", "price": 20}, headers=ORIGIN).json()
    assert [x["triggered"] for x in a] == [True, False]


def test_prefs_round_trip_and_unknown_keys_dropped(client):
    signup(client)
    r = client.put("/v1/me/prefs", json={"data": {"decimals": 3, "locale": "ar", "evil": 1}}, headers=ORIGIN)
    assert r.json()["data"] == {"decimals": 3, "locale": "ar"}
    assert client.get("/v1/auth/me").json()["user"]["locale"] == "ar"


def test_sessions_are_per_user(client):
    from fastapi.testclient import TestClient

    from app import main

    signup(client, "a@example.com")
    client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 1}, headers=ORIGIN)
    other = TestClient(main.create_app())
    signup(other, "b@example.com")
    assert other.get("/v1/portfolio").json()["holdings"] == []


def test_rate_limit_ignores_a_forged_forwarded_for(client):
    # Each attempt claims a new address in X-Forwarded-For; the limit still counts them as one visitor.
    codes = [
        client.post(
            "/v1/auth/login",
            json={"email": f"x{i}@example.com", "password": "wrong password!"},
            headers={**ORIGIN, "X-Forwarded-For": f"10.0.0.{i}"},
        ).status_code
        for i in range(12)
    ]
    assert codes[:10] == [403] * 10 and codes[10:] == [429, 429]
    # nginx's X-Real-IP is the address that counts.
    r = client.post("/v1/auth/login", json={"email": "y@example.com", "password": "wrong password!"}, headers={**ORIGIN, "X-Real-IP": "203.0.113.9"})
    assert r.status_code == 403


def test_signup_needs_and_records_acceptance(client):
    from sqlalchemy import select

    from app.appdb import consents, engine_for

    r = client.post("/v1/auth/signup", json={"email": "c@example.com", "password": "correct horse battery"}, headers=ORIGIN)
    assert r.status_code == 422 and "Terms of Service" in r.json()["detail"]
    assert signup(client, email="c@example.com").status_code == 200
    with engine_for(client.app.state.settings.database_url).connect() as conn:
        row = conn.execute(select(consents)).one()
    assert row.kind == "registration" and row.text_version == "1.0" and row.documents == {"terms": "1.2", "privacy": "1.2"}


def test_registration_versions_match_the_documents_on_the_site():
    import json
    from pathlib import Path

    from app.legal import REGISTRATION

    content = Path(__file__).resolve().parents[2] / "web" / "src" / "content" / "legal"
    for doc, version in REGISTRATION["documents"].items():
        assert json.loads((content / f"{doc}.en.json").read_text(encoding="utf-8"))["version"] == version


def test_delete_account_removes_everything(client):
    signup(client)
    client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 10}, headers=ORIGIN)
    assert client.post("/v1/me/delete", json={"password": "wrong password!"}, headers=ORIGIN).status_code == 403
    r = client.post("/v1/me/delete", json={"password": "correct horse battery"}, headers=ORIGIN)
    assert r.status_code == 200 and r.json() == {"user": None}
    assert client.get("/v1/auth/me").json()["user"] is None
    client.cookies.clear()
    login = client.post("/v1/auth/login", json={"email": "tester@example.com", "password": "correct horse battery"}, headers=ORIGIN)
    assert login.status_code == 403


def test_rate_limits_are_shared_between_workers(data_files):
    from app.auth import DbRateLimit

    # Two limiters on one database stand for two uvicorn workers.
    a = DbRateLimit(data_files.database_url, "copilot", limit=3, window_s=3600)
    b = DbRateLimit(data_files.database_url, "copilot", limit=3, window_s=3600)
    assert [a.hit("user:1"), b.hit("user:1"), a.hit("user:1"), b.hit("user:1")] == [True, True, True, False]
    assert b.hit("user:2") is True  # per key


def test_pinned_items_are_saved_to_the_account(client):
    signup(client)
    pin = {"kind": "table", "id": "t1", "title": "2222 dividends", "columns": ["Period", "DPS"], "rows": [["Q2 2026", 0.34]],
           "unverified": [], "source": "DB", "pinnedAt": "2026-10-16T12:00:00Z"}
    r = client.put("/v1/me/prefs", json={"data": {"dashboards": [pin], "unknown": 1}}, headers=ORIGIN)
    assert r.status_code == 200 and r.json()["data"] == {"dashboards": [pin]}
    assert client.get("/v1/me/prefs").json()["data"]["dashboards"][0]["rows"] == [["Q2 2026", 0.34]]
    huge = {"dashboards": [{**pin, "id": f"t{i}", "rows": [["x" * 1000]] * 30} for i in range(20)]}
    assert client.put("/v1/me/prefs", json={"data": huge}, headers=ORIGIN).status_code == 413


def test_one_account_cannot_change_anothers_holdings_or_alerts(client):
    signup(client, email="qa1@example.com")
    h = client.post("/v1/portfolio/holdings", json={"ticker": "2222", "quantity": 7, "avg_cost": 23.4567}, headers=ORIGIN)
    holding_id = h.json()["holdings"][0]["id"]
    a = client.post("/v1/portfolio/alerts", json={"ticker": "1120", "kind": "above", "price": 99.8765}, headers=ORIGIN)
    alert_id = a.json()[0]["id"]
    qa1_cookie = client.cookies.get("acp_session")

    client.cookies.clear()
    signup(client, email="qa2@example.com")
    # qa2 deletes qa1's ids: nothing of qa2's matches, and qa1 keeps both.
    assert client.delete(f"/v1/portfolio/holdings/{holding_id}", headers=ORIGIN).status_code == 200
    assert client.delete(f"/v1/portfolio/alerts/{alert_id}", headers=ORIGIN).status_code == 200
    assert client.get("/v1/portfolio").json()["holdings"] == []

    client.cookies.clear()
    client.cookies.set("acp_session", qa1_cookie)
    assert [x["id"] for x in client.get("/v1/portfolio").json()["holdings"]] == [holding_id]
    assert [x["id"] for x in client.get("/v1/portfolio/alerts").json()] == [alert_id]


def test_signed_out_calls_never_answer_401(client):
    # A 401 would drop the staging gate's Basic credentials in the browser (auth.AUTH_FAILED).
    calls = [
        ("get", "/v1/portfolio", None), ("get", "/v1/portfolio/alerts", None), ("get", "/v1/me/prefs", None),
        ("put", "/v1/me/prefs", {"data": {}}), ("post", "/v1/portfolio/holdings", {"ticker": "2222", "quantity": 1}),
        ("post", "/v1/portfolio/alerts", {"ticker": "2222", "kind": "above", "price": 1}),
        ("delete", "/v1/portfolio/holdings/1", None), ("delete", "/v1/portfolio/alerts/1", None),
        ("post", "/v1/me/delete", {"password": "x"}),
        ("post", "/v1/auth/reset-password", {"token": "not-a-real-token", "password": "a long new password"}),
    ]
    for method, path, body in calls:
        r = client.request(method.upper(), path, json=body, headers=ORIGIN)
        assert r.status_code == 403, (method, path, r.status_code)


def test_ids_are_random_and_lists_keep_creation_order(client):
    signup(client, email="ids@example.com")
    me = client.get("/v1/auth/me").json()["user"]["id"]
    for t in ("2222", "1120", "2010"):
        client.post("/v1/portfolio/holdings", json={"ticker": t, "quantity": 1}, headers=ORIGIN)
        client.post("/v1/portfolio/alerts", json={"ticker": t, "kind": "above", "price": 1}, headers=ORIGIN)
    holdings = client.get("/v1/portfolio").json()["holdings"]
    alerts = client.get("/v1/portfolio/alerts").json()
    # Listed in the order they were added, whatever their ids.
    assert [h["ticker"]["symbol"] for h in holdings] == ["2222", "1120", "2010"]
    assert [a["ticker"]["symbol"] for a in alerts] == ["2222", "1120", "2010"]
    ids = [me] + [h["id"] for h in holdings] + [a["id"] for a in alerts]
    # No running count: no two ids are neighbours (a chance of about 1 in 10^8 if random).
    assert all(abs(a - b) > 1 for i, a in enumerate(ids) for b in ids[i + 1 :])
    assert all(0 < i < 2**31 for i in ids)


# --- forgot password ---------------------------------------------------------------------------

NEW_PASSWORD = "a brand new passphrase"


@pytest.fixture
def outbox(client, monkeypatch):
    """Email configured, with the SMTP delivery replaced by a list of sent messages."""
    from app import mail

    sent = []
    monkeypatch.setattr(client.app.state.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(mail, "deliver", lambda settings, msg: sent.append(msg))
    return sent


def forgot(client, email="tester@example.com", **extra):
    return client.post("/v1/auth/forgot-password", json={"email": email, **extra}, headers=ORIGIN)


def token_of(msg) -> str:
    return re.search(r"#token=([\w-]+)", msg.get_content()).group(1)


def reset(client, token, password=NEW_PASSWORD):
    return client.post("/v1/auth/reset-password", json={"token": token, "password": password}, headers=ORIGIN)


def login(client, password, email="tester@example.com"):
    return client.post("/v1/auth/login", json={"email": email, "password": password}, headers=ORIGIN)


def test_forgot_password_emails_a_link_that_sets_a_new_password(client, outbox):
    signup(client)
    client.cookies.clear()
    r = forgot(client, "Tester@Example.com ")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    [msg] = outbox
    assert msg["To"] == "tester@example.com" and msg["Subject"] == "Reset your AlphaCouncil password"
    # The site's own address, the token in the fragment (never sent to a server).
    assert re.search(r"http://testserver/reset-password#token=[\w-]{40,}\n", msg.get_content())
    done = reset(client, token_of(msg))
    assert done.status_code == 200 and done.json()["user"]["email"] == "tester@example.com"
    assert client.get("/v1/auth/me").json()["user"]["email"] == "tester@example.com"  # signed in
    client.cookies.clear()
    assert login(client, "correct horse battery").status_code == 403
    assert login(client, NEW_PASSWORD).status_code == 200


def test_arabic_page_gets_an_arabic_email_and_link(client, outbox):
    signup(client)
    forgot(client, locale="ar")
    [msg] = outbox
    assert msg["Subject"] == "إعادة تعيين كلمة مرور AlphaCouncil"
    assert "http://testserver/ar/reset-password#token=" in msg.get_content()


def test_reset_link_works_once(client, outbox):
    signup(client)
    forgot(client)
    token = token_of(outbox[0])
    assert reset(client, token).status_code == 200
    again = reset(client, token, "another long passphrase")
    assert again.status_code == 403  # never 401: see auth.AUTH_FAILED
    assert "expired or was already used" in again.json()["detail"]
    client.cookies.clear()
    assert login(client, NEW_PASSWORD).status_code == 200


def test_reset_link_expires_after_an_hour(client, outbox, monkeypatch):
    from app import auth

    signup(client)
    forgot(client)
    forgot(client)
    late, in_time = token_of(outbox[0]), token_of(outbox[1])
    real = auth.utcnow
    monkeypatch.setattr(auth, "utcnow", lambda: real() + timedelta(minutes=61))
    assert reset(client, late).status_code == 403
    monkeypatch.setattr(auth, "utcnow", lambda: real() + timedelta(minutes=59))
    assert reset(client, in_time).status_code == 200


def test_forgot_password_does_not_say_whether_an_account_exists(client, outbox):
    signup(client)
    client.cookies.clear()
    known, unknown = forgot(client), forgot(client, "nobody@example.com")
    assert known.status_code == unknown.status_code == 200
    assert known.content == unknown.content
    assert "set-cookie" not in known.headers and "set-cookie" not in unknown.headers
    assert [m["To"] for m in outbox] == ["tester@example.com"]  # nothing sent for an unknown address


def test_token_is_stored_only_as_its_hash(client, outbox):
    from sqlalchemy import select

    from app.appdb import engine_for, password_resets

    signup(client)
    forgot(client)
    token = token_of(outbox[0])
    with engine_for(client.app.state.settings.database_url).connect() as conn:
        rows = conn.execute(select(password_resets)).all()
    assert [r.token_hash for r in rows] == [hashlib.sha256(token.encode()).hexdigest()]
    assert all(token not in str(v) for r in rows for v in r)


def test_reset_ends_every_session_and_every_other_link(client, outbox):
    signup(client)  # session 1, in this browser
    phone = TestClient(client.app)
    assert login(phone, "correct horse battery").status_code == 200  # session 2, another device
    forgot(client)
    forgot(client)
    first, second = token_of(outbox[0]), token_of(outbox[1])

    elsewhere = TestClient(client.app)
    assert reset(elsewhere, second).status_code == 200
    assert client.get("/v1/auth/me").json()["user"] is None
    assert phone.get("/v1/auth/me").json()["user"] is None
    assert elsewhere.get("/v1/auth/me").json()["user"]["email"] == "tester@example.com"
    assert reset(TestClient(client.app), first).status_code == 403  # the earlier link went too


def test_a_short_new_password_keeps_the_link(client, outbox):
    signup(client)
    forgot(client)
    token = token_of(outbox[0])
    assert reset(client, token, "short").status_code == 422
    assert reset(client, token).status_code == 200


def test_without_email_configured_the_answer_is_the_same_and_the_log_says_so(client, caplog):
    signup(client)
    client.cookies.clear()
    with caplog.at_level("WARNING"):
        known, unknown = forgot(client), forgot(client, "nobody@example.com")
    assert known.status_code == unknown.status_code == 200 and known.content == unknown.content
    assert "email is not configured" in caplog.text
    assert "token" not in caplog.text and "tester@example.com" not in caplog.text


def test_forgot_password_is_rate_limited_per_email_and_per_address(client, outbox):
    signup(client)
    codes = [
        client.post(
            "/v1/auth/forgot-password", json={"email": "tester@example.com"}, headers={**ORIGIN, "X-Real-IP": f"203.0.113.{i}"}
        ).status_code
        for i in range(6)
    ]
    assert codes == [200] * 5 + [429]
    assert len(outbox) == 5
    codes = [forgot(client, f"other{i}@example.com").status_code for i in range(6)]
    assert codes == [200] * 5 + [429]
