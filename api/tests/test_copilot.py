import json

from app.copilot.context import numbers_in, unverified_cells


def stream(client, question, panels=(), locale="en", ticker=None):
    body = {
        "messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": question}]}],
        "panels": list(panels),
        "locale": locale,
        "ticker": ticker,
    }
    parts = []
    with client.stream("POST", "/v1/copilot/chat", json=body) as r:
        assert r.status_code == 200
        assert r.headers["x-vercel-ai-ui-message-stream"] == "v1"
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                parts.append(json.loads(line[6:]))
    return parts


def text_of(parts):
    return "".join(p["delta"] for p in parts if p["type"] == "text-delta")


def data(parts, kind):
    return [p["data"] for p in parts if p["type"] == f"data-{kind}"]


def test_status_without_credentials_is_stand_in(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    assert client.get("/v1/copilot/status").json() == {"model": "stand-in", "stand_in": True, "sign_in_required": False}


def test_dividend_answer_cites_the_attached_metrics_panel(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    detail = client.get("/v1/tickers/2222").json()
    panel = {"id": "overview.metrics", "title": "Key metrics", "ticker": "2222", "data": detail}
    parts = stream(client, "Is the dividend safe?", [panel])
    text = text_of(parts)
    assert "Stand-in answer" in text
    assert "5.03% [P1]" in text  # yield read from the attached panel, cited by its tag
    assert "0.34" in text and "[DB]" in text  # latest dividend from the database
    assert data(parts, "sources")[0]["P1"]["id"] == "overview.metrics"
    assert data(parts, "table")[0]["rows"][0][3] == 0.34
    assert 2 <= len(data(parts, "followups")[0]["questions"]) <= 3
    assert parts[0]["type"] == "start" and parts[-1]["type"] == "finish"
    assert any(p["type"] == "tool-input-available" and p["toolName"] == "get_dividends" for p in parts)


def test_arabic_question_gets_arabic_answer(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text = text_of(stream(client, "ما عائد التوزيعات؟", locale="ar", ticker="2222"))
    assert "إجابة بديلة" in text and "[DB]" in text


def test_unknown_company_asks_for_one(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text = text_of(stream(client, "what is the dividend of zzqq"))
    assert "could not tell which company" in text


def test_empty_question_is_rejected(client):
    body = {"messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": "  "}]}]}
    assert client.post("/v1/copilot/chat", json=body).status_code == 422


def test_table_numbers_are_checked_against_what_was_read():
    seen = numbers_in({"note": "Q 2 _ 2026", "dps": 0.34, "ex_date": "2026-08-19", "yield": 5.03})
    rows = [["Q2 2026", "2026-08-19", 0.34], ["Q1 2026", "2026-06-01", 0.35]]
    # The second row was never read (period, date and amount): flagged; the first passes.
    assert unverified_cells(rows, seen) == [[1, 0], [1, 1], [1, 2]]


def test_copilot_is_rate_limited(client):
    from app.auth import RateLimit

    client.app.state.copilot_limit = RateLimit(limit=2, window_s=3600)
    body = {"messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": "hi"}]}], "panels": [], "locale": "en"}
    codes = [client.post("/v1/copilot/chat", json=body).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_a_real_model_answers_signed_in_users_only(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    s = client.get("/v1/copilot/status").json()
    assert s["stand_in"] is False and s["sign_in_required"] is True
    body = {"messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": "hi"}]}], "panels": [], "locale": "en"}
    assert client.post("/v1/copilot/chat", json=body).status_code == 401
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert client.get("/v1/copilot/status").json()["sign_in_required"] is False
