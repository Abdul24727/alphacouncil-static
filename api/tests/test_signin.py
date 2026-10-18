"""Email confirmation and sign-in with Google."""

import base64
import json
import re
import time
from urllib.parse import parse_qs, urlparse

import pytest

ORIGIN = {"Origin": "http://testserver"}
# Not a reserved test domain: account emails to it are "sent" (into the outbox below).
EMAIL = "owner@alphamail.co"


@pytest.fixture
def outbox(client, monkeypatch):
    from app import mail

    sent = []
    monkeypatch.setattr(client.app.state.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(mail, "deliver", lambda settings, msg: sent.append(msg))
    return sent


def signup(client, email=EMAIL, password="correct horse battery"):
    return client.post("/v1/auth/signup", json={"email": email, "password": password, "accept_terms": True}, headers=ORIGIN)


def token_in(msg) -> str:
    return re.search(r"#token=([\w-]+)", msg.get_content()).group(1)


def me(client):
    return client.get("/v1/auth/me").json()["user"]


# --- email confirmation -------------------------------------------------------------------------


def test_signup_emails_a_confirmation_link_that_works_once(client, outbox):
    assert signup(client).status_code == 200
    assert me(client)["email_verified"] is False
    [msg] = outbox
    assert msg["Subject"] == "Confirm your AlphaCouncil email"
    assert "http://testserver/verify-email#token=" in msg.get_content()
    token = token_in(msg)
    client.cookies.clear()  # the link works in another browser too
    assert client.post("/v1/auth/verify-email", json={"token": token}, headers=ORIGIN).status_code == 200
    assert client.post("/v1/auth/verify-email", json={"token": token}, headers=ORIGIN).status_code == 403
    client.post("/v1/auth/login", json={"email": EMAIL, "password": "correct horse battery"}, headers=ORIGIN)
    assert me(client)["email_verified"] is True


def test_test_addresses_get_no_email(client, outbox):
    signup(client, "tester@example.com")
    assert outbox == []


def test_resend_replaces_the_old_link(client, outbox):
    signup(client)
    first = token_in(outbox[0])
    assert client.post("/v1/auth/resend-verification", headers=ORIGIN).status_code == 200
    second = token_in(outbox[1])
    assert client.post("/v1/auth/verify-email", json={"token": first}, headers=ORIGIN).status_code == 403
    assert client.post("/v1/auth/verify-email", json={"token": second}, headers=ORIGIN).status_code == 200


def test_a_password_reset_link_confirms_the_address(client, outbox):
    signup(client)
    client.cookies.clear()
    client.post("/v1/auth/forgot-password", json={"email": EMAIL}, headers=ORIGIN)
    reset_token = token_in(outbox[-1])
    r = client.post("/v1/auth/reset-password", json={"token": reset_token, "password": "a brand new passphrase"}, headers=ORIGIN)
    assert r.status_code == 200 and r.json()["user"]["email_verified"] is True


# --- Google -------------------------------------------------------------------------------------


def id_token(**claims) -> str:
    body = {"iss": "https://accounts.google.com", "aud": "google-client", "exp": time.time() + 600, **claims}
    seg = base64.urlsafe_b64encode(json.dumps(body).encode()).decode().rstrip("=")
    return f"header.{seg}.signature"


@pytest.fixture
def google(client, monkeypatch):
    """Google's token endpoint, faked: the next exchange returns `google.claims`."""
    from app import http, oauth

    monkeypatch.setattr(client.app.state.settings, "google_client_id", "google-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret-not-used")
    state = type("G", (), {"claims": {}, "calls": []})()

    def fake_call(method, url, **kw):
        assert url == oauth.TOKEN and kw["form"]["redirect_uri"] == "http://testserver/auth/google/callback"
        state.calls.append(kw["form"])
        return http.Reply(200, {"id_token": id_token(**state.claims)})

    monkeypatch.setattr(oauth.http, "call", fake_call)
    return state


def google_round_trip(client, accept=False, locale="en"):
    start = client.get("/v1/auth/google/start", params={"next": "/portfolio", "accept": accept, "locale": locale}, follow_redirects=False)
    assert start.status_code == 303
    q = parse_qs(urlparse(start.headers["location"]).query)
    assert q["redirect_uri"] == ["http://testserver/auth/google/callback"] and q["scope"] == ["openid email profile"]
    return client.get("/v1/auth/google/callback", params={"state": q["state"][0], "code": "code-1"}, follow_redirects=False)


def test_google_makes_an_account_only_after_the_terms(client, google):
    google.claims = {"sub": "g-1", "email": "Person@Gmail.com", "email_verified": True, "name": "A Person"}
    r = google_round_trip(client)
    assert r.headers["location"] == "/signup?google=terms" and me(client) is None
    r = google_round_trip(client, accept=True)
    assert r.headers["location"] == "/portfolio"
    user = me(client)
    assert user["email"] == "person@gmail.com" and user["email_verified"] and user["has_password"] is False
    # Again later: the same account, through the linked Google id.
    client.cookies.clear()
    google.claims["email"] = "renamed@gmail.com"
    assert google_round_trip(client).headers["location"] == "/portfolio"
    assert me(client)["id"] == user["id"]


def test_google_links_to_an_account_with_the_same_verified_email(client, google):
    signup(client, "person@gmail.com")
    uid = me(client)["id"]
    client.cookies.clear()
    google.claims = {"sub": "g-2", "email": "person@gmail.com", "email_verified": True}
    assert google_round_trip(client).headers["location"] == "/portfolio"
    assert me(client)["id"] == uid and me(client)["email_verified"] is True


def test_google_refuses_a_stale_state_and_an_unverified_email(client, google):
    r = client.get("/v1/auth/google/callback", params={"state": "made-up", "code": "x"}, follow_redirects=False)
    assert r.headers["location"] == "/login?error=google_expired"
    google.claims = {"sub": "g-3", "email": "x@gmail.com", "email_verified": False}
    assert google_round_trip(client, accept=True).headers["location"] == "/login?error=google_unverified"
    google.claims = {"sub": "g-4", "email": "y@gmail.com", "email_verified": True, "aud": "someone-else"}
    assert google_round_trip(client, accept=True).headers["location"] == "/login?error=google_failed"
    assert google.calls and me(client) is None


def test_google_start_never_redirects_off_site(client, google):
    start = client.get("/v1/auth/google/start", params={"next": "//evil.example/x", "accept": True}, follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    google.claims = {"sub": "g-5", "email": "z@gmail.com", "email_verified": True}
    r = client.get("/v1/auth/google/callback", params={"state": state, "code": "c"}, follow_redirects=False)
    assert r.headers["location"] == "/home"


def test_an_account_without_a_password_deletes_by_typing_its_email(client, google):
    google.claims = {"sub": "g-6", "email": "del@gmail.com", "email_verified": True}
    google_round_trip(client, accept=True)
    assert client.post("/v1/me/delete", json={"confirm_email": "other@gmail.com"}, headers=ORIGIN).status_code == 403
    assert client.post("/v1/me/delete", json={"confirm_email": "DEL@gmail.com"}, headers=ORIGIN).status_code == 200
    assert me(client) is None
