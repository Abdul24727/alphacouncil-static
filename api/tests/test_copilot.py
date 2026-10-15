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


# --- OpenAI-compatible provider (OpenRouter) ------------------------------------------------------


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _chunk(content=None, tool=None, finish=None):
    calls = None
    if tool:
        i, cid, name, args = tool
        calls = [_Obj(index=i, id=cid, function=_Obj(name=name, arguments=args))]
    delta = _Obj(content=content, tool_calls=calls)
    return _Obj(choices=[_Obj(delta=delta, finish_reason=finish)])


class _FakeOpenAI:
    """Scripted turns: a split-up tool call, then a cited answer with follow-ups."""

    turns: list = []
    seen: list = []

    def __init__(self, **kw):
        self.chat = _Obj(completions=_Obj(create=self._create))

    async def _create(self, **body):
        _FakeOpenAI.seen.append(body)
        chunks = _FakeOpenAI.turns.pop(0)

        async def gen():
            for c in chunks:
                yield c

        return gen()


def test_openrouter_provider_runs_tools_and_streams_the_answer(client, monkeypatch):
    from app.copilot import openai_compat

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(openai_compat.openai, "AsyncOpenAI", _FakeOpenAI)
    _FakeOpenAI.seen = []
    _FakeOpenAI.turns = [
        [  # the dividend tool, its arguments split across chunks as models stream them
            _chunk(tool=(0, "call_1", "get_dividends", '{"tick')),
            _chunk(tool=(0, None, "", 'er": "2222"}')),
            _chunk(finish="tool_calls"),
        ],
        [
            _chunk(content="Saudi Aramco paid 0.34 per share in Q2 2026 [DB]."),
            _chunk(tool=(0, "call_2", "suggest_follow_ups", '{"questions": ["Payout ratio?", "Yield vs peers?"]}')),
            _chunk(finish="tool_calls"),
        ],
    ]
    s = client.get("/v1/copilot/status").json()
    assert s["stand_in"] is False and s["sign_in_required"] is True

    signup = {"email": "or@example.com", "password": "correct horse battery", "accept_terms": True}
    assert client.post("/v1/auth/signup", json=signup, headers={"Origin": "http://testserver"}).status_code == 200
    parts = []
    body = {"messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": "Aramco dividends?"}]}], "panels": [], "locale": "en"}
    with client.stream("POST", "/v1/copilot/chat", json=body, headers={"Origin": "http://testserver"}) as r:
        assert r.status_code == 200
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                parts.append(json.loads(line[6:]))

    types = [p["type"] for p in parts]
    assert "error" not in types
    calls = [p for p in parts if p["type"] == "tool-input-available"]
    assert calls[0]["toolName"] == "get_dividends" and calls[0]["input"] == {"ticker": "2222"}
    text = "".join(p.get("delta", "") for p in parts if p["type"] == "text-delta")
    assert "0.34" in text and "[DB]" in text
    assert any(p["type"] == "data-followups" for p in parts)
    # The second request carried the database result back to the model as a tool message.
    tool_msgs = [m for m in _FakeOpenAI.seen[1]["messages"] if m["role"] == "tool"]
    assert tool_msgs and tool_msgs[0]["tool_call_id"] == "call_1" and "2026-08-19" in tool_msgs[0]["content"]
    assert _FakeOpenAI.seen[0]["model"] == client.app.state.settings.copilot_model
    assert _FakeOpenAI.seen[0]["tools"][0]["type"] == "function"
    assert len(_FakeOpenAI.seen) == 2  # the follow-ups close the answer: no third model turn


def test_provider_follows_the_environment(client, monkeypatch):
    from app.routers.copilot import provider

    req = type("R", (), {"app": client.app})()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert provider(req) == "standin"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert provider(req) == "anthropic"
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")
    assert provider(req) == "openrouter"
    monkeypatch.setattr(client.app.state.settings, "copilot_provider", "anthropic")
    assert provider(req) == "anthropic"
    monkeypatch.setattr(client.app.state.settings, "copilot_provider", "standin")
    assert provider(req) == "standin"


def test_openrouter_asks_for_follow_ups_when_the_model_skips_them(client, monkeypatch):
    from app.copilot import openai_compat

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")
    monkeypatch.setattr(openai_compat.openai, "AsyncOpenAI", _FakeOpenAI)
    _FakeOpenAI.seen = []
    _FakeOpenAI.turns = [
        [_chunk(content="The yield is 5.03% [P1]."), _chunk(finish="stop")],
        [  # the nudge turn: a stray sentence (never shown) and the follow-ups
            _chunk(content="Sure."),
            _chunk(tool=(0, "call_9", "suggest_follow_ups", '{"questions": ["Payout ratio?", "Next ex-date?"]}')),
            _chunk(finish="tool_calls"),
        ],
    ]
    signup = {"email": "nudge@example.com", "password": "correct horse battery", "accept_terms": True}
    client.post("/v1/auth/signup", json=signup, headers={"Origin": "http://testserver"})
    body = {"messages": [{"id": "u1", "role": "user", "parts": [{"type": "text", "text": "Is the dividend safe?"}]}], "panels": [], "locale": "en"}
    parts = []
    with client.stream("POST", "/v1/copilot/chat", json=body, headers={"Origin": "http://testserver"}) as r:
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                parts.append(json.loads(line[6:]))
    text = "".join(p.get("delta", "") for p in parts if p["type"] == "text-delta")
    assert text == "The yield is 5.03% [P1]."
    follow = [p["data"]["questions"] for p in parts if p["type"] == "data-followups"]
    assert follow == [["Payout ratio?", "Next ex-date?"]]
    assert _FakeOpenAI.seen[1]["tool_choice"] == {"type": "function", "function": {"name": "suggest_follow_ups"}}
    assert len(_FakeOpenAI.seen) == 2  # one nudge, then done
    assert _FakeOpenAI.seen[0]["extra_body"] == {}  # reasoning off by default (COPILOT_REASONING)


def test_keepalive_fills_silences_without_touching_parts():
    import asyncio

    from app.copilot.stream import KEEPALIVE, with_keepalive

    a, b = "data: a\n\n", "data: b\n\n"

    async def slow():
        yield a
        await asyncio.sleep(0.25)
        yield b

    async def collect():
        return [c async for c in with_keepalive(slow(), every_s=0.1)]

    out = asyncio.run(collect())
    assert out[0] == a and out[-1] == b
    assert KEEPALIVE in out and set(out) <= {a, b, KEEPALIVE}
