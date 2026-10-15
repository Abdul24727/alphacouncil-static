ORIGIN = {"Origin": "http://testserver"}


def signup(client, email="tester@example.com", password="correct horse battery"):
    return client.post("/v1/auth/signup", json={"email": email, "password": password}, headers=ORIGIN)


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
    assert bad.status_code == 401
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
    assert client.get("/v1/portfolio").status_code == 401


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
