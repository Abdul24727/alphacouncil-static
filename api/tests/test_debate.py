"""Advisors' debate room: seats, Pro gate and allowance, the stages, number and advice checks, sessions."""

import json
import re
from pathlib import Path

import pytest
from sqlalchemy import select

ORIGIN = {"Origin": "http://testserver"}
STAGES = ["brief", "openings", "faultlines", "debate", "final", "verdict"]


def signup(client, email="room@example.com"):
    body = {"email": email, "password": "correct horse battery", "accept_terms": True}
    assert client.post("/v1/auth/signup", json=body, headers=ORIGIN).status_code == 200


# An open question (the room answers it) and one that asks the room to choose between readings.
OPEN_Q = "Is the dividend covered by earnings?"
CHOICE_Q = "Is the dividend covered by earnings, or covered only if margins hold?"


def convene(client, question=OPEN_Q, ticker="2222", locale="en", status=200):
    events = []
    with client.stream(
        "POST", "/v1/debate/sessions", json={"ticker": ticker, "question": question, "locale": locale}, headers=ORIGIN
    ) as r:
        assert r.status_code == status, r.read()
        if status != 200:
            return json.loads(r.read())
        for line in r.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


@pytest.fixture
def room(client, monkeypatch):
    """No model key (the stand-in), and no wait between two sessions of one account."""
    from app.auth import RateLimit

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client.app.state.debate_start_limit = RateLimit(limit=100, window_s=1)
    # The four original seats keep these tests' arithmetic simple; test_six_seats... covers the default roster.
    monkeypatch.setattr(client.app.state.settings, "debate_advisors", "buffett,lynch,dalio,marks")
    return client


# --- seats -----------------------------------------------------------------------------------------


def test_every_seat_file_has_its_sections_and_says_it_is_simulated():
    from app.debate import roster

    advisors = roster.advisors("buffett,lynch,dalio,marks")
    assert [a.name for a in advisors] == ["Warren Buffett", "Peter Lynch", "Ray Dalio", "Howard Marks"]
    for a in advisors:
        assert set(roster.ADVISOR_SECTIONS) <= set(a.sections)
        who = a.sections["Who they are"]
        assert "simulated advisor" in who and "does not speak for" in who
        assert a.info.name_ar and a.info.lens_ar and len(a.info.initials) == 2
    chair = roster.chair()
    assert set(roster.CHAIR_SECTIONS) <= set(chair.sections) and chair.info.role == "chair"
    # Each named portrait is the seat's own file, and it is in web/public/advisors (served at /advisors/<file>).
    public = Path(__file__).resolve().parents[2] / "web" / "public"
    for seat in [*roster.advisors("buffett,lynch,dalio,marks,alwaleed,alrumayyan"), chair]:
        if seat.info.portrait:
            assert seat.info.portrait == f"/advisors/{seat.info.id}.webp"
            assert (public / seat.info.portrait.lstrip("/")).is_file(), seat.info.portrait


def test_six_seats_and_seats_tied_to_a_company_sit_out(room, monkeypatch):
    from app.debate import roster
    from app.settings import Settings

    default = Settings.model_fields["debate_advisors"].default
    assert default == "buffett,lynch,dalio,marks,alwaleed,alrumayyan"
    seats = roster.advisors(default)
    alwaleed, alrumayyan = roster.load("alwaleed").info, roster.load("alrumayyan").info
    assert (alwaleed.short_en, alwaleed.short_ar, alwaleed.recuse) == ("Alwaleed", "الوليد", ["4280_TADAWUL"])
    # The Al-Rumayyan seat carries no recuse list (owner, 2026-10-26), so it sits on every company
    # including the ones he chairs — unlike Alwaleed, who sits out Kingdom Holding. Deliberate, and one
    # of the things the lawyer is asked about at Step 7.
    assert alrumayyan.recuse == [] and alrumayyan.short_en == "Al-Rumayyan"
    assert roster.load("buffett").info.short_en == "Buffett"
    # Recusal still works where a seat has one: Alwaleed sits out Kingdom Holding.
    assert [a.id for a in roster.sitting(seats, "4280_TADAWUL")] == ["buffett", "lynch", "dalio", "marks", "alrumayyan"]
    # And it does not fire for Al-Rumayyan on the company he chairs, which is the owner's decision.
    assert [a.id for a in roster.sitting(seats, "2222_TADAWUL")] == [a.id for a in seats]

    monkeypatch.setattr(room.app.state.settings, "debate_advisors", default)
    assert [x["id"] for x in room.get("/v1/debate/status").json()["seats"]] == [*default.split(","), "chair"]
    signup(room)
    # Aramco: all seven seats sit, Al-Rumayyan included, though he chairs it.
    events = convene(room, ticker="2222")
    session = events[0]["session"]
    assert [x["id"] for x in session["seats"]] == [*default.split(","), "chair"]
    openings = [e["turn"]["seat"] for e in events if e["type"] == "turn" and e["turn"]["stage"] == "openings"]
    assert sorted(openings) == ["alrumayyan", "alwaleed", "buffett", "dalio", "lynch", "marks"]
    # Aramco: all six.
    events = convene(room, ticker="2222")
    assert len([e for e in events if e["type"] == "turn" and e["turn"]["stage"] == "final"]) == 6
    assert events[-1]["status"] == "done"


def test_the_roster_setting_is_checked():
    from app.debate import roster

    with pytest.raises(roster.RosterError):
        roster.advisors("buffett")  # too few
    with pytest.raises(roster.RosterError):
        roster.advisors("buffett,../../settings")
    with pytest.raises(roster.RosterError):
        roster.advisors("buffett,nobody")


def test_the_final_leans_are_counted_by_the_engine():
    from app.debate.engine import count_answers, count_leans

    finals = {
        "a": {"lean": "A", "text": "x"},
        "b": {"lean": "B", "text": "x"},
        "c": {"lean": "A", "text": "x"},
        "d": {"absent": True, "error": "busy"},
    }
    r = count_leans(["A", "B"], finals)
    assert r["mode"] == "choice" and r["tally"] == {"A": 2, "B": 1} and r["best"] == ["A"] and r["voters"] == 3
    assert r["leans"] == {"a": "A", "b": "B", "c": "A"}
    tie = count_leans(["A", "B"], {"a": {"lean": "A"}, "b": {"lean": "B"}})
    assert tie["best"] == ["A", "B"] and tie["voters"] == 2
    # Nobody gave a lean: no option is favoured, rather than all of them.
    assert count_leans(["A", "B"], {"a": {"absent": True}})["best"] == []
    # An open session has nothing to count, only who answered.
    assert count_answers(finals) == {"mode": "open", "voters": 3}


def test_the_stand_in_reads_which_questions_ask_the_room_to_choose():
    from app.debate.standin import mode_for

    for q in (CHOICE_Q, "Should I read the payout as safe?", "هل يجب قراءة التوزيعات كمغطاة؟", "Covered, or at risk?"):
        assert mode_for(q) == "choice", q
    for q in (OPEN_Q, "How safe is the dividend?", "ما الذي تُظهره الميزانية؟"):
        assert mode_for(q) == "open", q


def test_checks_cite_flag_and_remove_advice():
    from app.debate.checks import Checked, advice_in

    c = Checked({"P1": {"26.75", "5.03"}}, {"26.75", "5.03"})
    text = c.text("ROE is 26.75%. I would buy at this price. The P/E is ٩٩٫٩ on my reading.")
    assert text == "ROE is 26.75% [P1]. The P/E is 99.9 on my reading."
    assert c.flags() == {"unverified": ["99.9"], "cited": 1, "removed": 1}
    for ok in ("If margins hold, the dividend is covered", "Selling expenses rose", "The buyback continued", "I hold the view that ROE matters"):
        assert not advice_in(ok), ok
    for bad in ("You should hold the shares.", "It is a buy.", "A price target of 30", "أنصح بشراء السهم"):
        assert advice_in(bad), bad
    assert advice_in("Buy on weakness", short=True) and not advice_in("Covered only if margins hold", short=True)


# --- status, gate, allowance ---------------------------------------------------------------------------


def test_status_describes_the_room(room):
    s = room.get("/v1/debate/status").json()
    assert s["plan"] == "pro" and s["signed_in"] is False and s["stand_in"] is True
    assert s["limit"] == 20 and s["used"] == 0 and s["rounds"] == 3
    assert [x["id"] for x in s["seats"]] == ["buffett", "lynch", "dalio", "marks", "chair"]
    assert s["models"] == {"advisors": "stand-in", "chair": "stand-in"}


def test_signed_out_and_free_members_cannot_convene(room, monkeypatch):
    body = {"ticker": "2222", "question": "Is the dividend covered?", "locale": "en"}
    assert room.post("/v1/debate/sessions", json=body, headers=ORIGIN).status_code == 401  # not signed in
    signup(room)
    monkeypatch.setattr(room.app.state.settings, "billing_open", True)
    s = room.get("/v1/debate/status").json()
    assert s["plan"] == "free" and s["limit"] == 0
    r = room.post("/v1/debate/sessions", json=body, headers=ORIGIN)
    assert r.status_code == 403 and r.json()["detail"] == "pro_required"


def test_an_open_session_runs_every_stage_and_is_saved(room):
    """A question that is not a choice: no options, no leans, the room answers the question itself."""
    signup(room)
    events = convene(room)
    assert events[0]["type"] == "session" and events[0]["session"]["status"] == "running"
    sid = events[0]["session"]["id"]
    assert [e["stage"] for e in events if e["type"] == "stage"] == STAGES
    rounds = [(e["stage"], e["round"], e["rounds"]) for e in events if e["type"] == "stage" and e["round"]]
    assert rounds == [("openings", 1, 3), ("debate", 2, 3), ("final", 3, 3)]
    turns = [e["turn"] for e in events if e["type"] == "turn"]
    assert [t["seat"] for t in turns if t["stage"] == "openings"] != []
    assert len(turns) == 1 + 4 + 1 + 4 + 4 + 1
    brief = turns[0]["data"]
    assert brief["mode"] == "open" and brief["options"] == []
    # Buffett's stand-in quotes ROE from the overview, cited to it; the answer's length is counted, not cut.
    opening = next(t for t in turns if t["stage"] == "openings" and t["seat"] == "buffett")
    assert "26.75%" in opening["data"]["text"] and "[P1]" in opening["data"]["text"]
    assert opening["data"]["lean"] is None and opening["flags"]["unverified"] == []
    assert opening["flags"]["words"] == len(opening["data"]["text"].replace("[P1]", "").split())
    final = next(t for t in turns if t["stage"] == "final" and t["seat"] == "buffett")
    assert final["data"]["lean"] is None and final["data"]["lean_changed"] is False and final["data"]["would_change"]
    verdict = next(t for t in turns if t["stage"] == "verdict")["data"]
    assert verdict["answer"] and verdict["favours"] == "" and verdict["gaps"]
    writing = [e["seats"] for e in events if e["type"] == "writing"]
    assert ["chair"] in writing and ["buffett", "lynch", "dalio", "marks"] in writing
    result = next(e["result"] for e in events if e["type"] == "result")
    assert result == {"mode": "open", "voters": 4}
    assert events[-1]["type"] == "done" and events[-1]["status"] == "done"

    listed = room.get("/v1/debate/sessions").json()
    assert [x["id"] for x in listed] == [sid] and listed[0]["ticker"]["symbol"] == "2222"
    assert listed[0]["result"]["labels"] == {} and listed[0]["result"]["headline"]
    full = room.get(f"/v1/debate/sessions/{sid}").json()
    assert full["status"] == "done" and len(full["turns"]) == 15 and full["sources"]["P1"]["ok"] is True
    assert full["seats"][0]["name_en"] == "Warren Buffett" and full["rounds"] == 3
    assert room.get("/v1/debate/status").json()["used"] == 1

    from app.debate import store

    stats = store.stats(room.app.state.settings.database_url)
    assert stats["done"] == 1 and stats["failed"] == 0 and stats["seconds_median"] is not None
    assert stats["models"] == ["stand-in / stand-in"]


def test_a_choice_session_frames_options_and_counts_the_final_leans(room):
    signup(room)
    events = convene(room, question=CHOICE_Q)
    turns = [e["turn"] for e in events if e["type"] == "turn"]
    brief = turns[0]["data"]
    assert brief["mode"] == "choice" and [o["id"] for o in brief["options"]] == ["A", "B", "C"]
    leans = {t["seat"]: t["data"]["lean"] for t in turns if t["stage"] == "final"}
    assert set(leans) == {"buffett", "lynch", "dalio", "marks"} and all(x in ("A", "B", "C") for x in leans.values())
    result = next(e["result"] for e in events if e["type"] == "result")
    assert result["mode"] == "choice" and result["voters"] == 4
    assert sum(result["tally"].values()) == 4 and result["leans"] == leans
    # The most-favoured option is the one most advisors ended on, and nothing is scored.
    assert all(result["tally"][o] == max(result["tally"].values()) for o in result["best"])
    assert "average" not in result and not any(t["stage"] == "vote" for t in turns)
    verdict = next(t for t in turns if t["stage"] == "verdict")["data"]
    assert verdict["favours"] and verdict["answer"]
    assert room.get("/v1/debate/sessions").json()[0]["result"]["labels"]["A"]


def test_a_session_saved_in_the_scored_format_still_loads(room):
    """Sessions held before 2026-10-24 scored options in a vote stage: they are served as they were."""
    from sqlalchemy import insert, update

    from app.appdb import debate_sessions, debate_turns, engine_for, users
    from app.debate import roster, store

    signup(room)
    url = room.app.state.settings.database_url
    with engine_for(url).connect() as conn:
        user_id = conn.execute(select(users.c.id)).scalar_one()
    seats = [roster.load(i).info.model_dump() for i in ("buffett", "marks")] + [roster.chair().info.model_dump()]
    sid = store.create(
        url, user_id=user_id, ticker_key="2222_TADAWUL", question="Is it covered?", locale="en",
        seats=seats, models={"advisors": "m", "chair": "c"}, rounds=3,
    )
    with engine_for(url).begin() as conn:
        for stage, rnd, seat, data in [
            ("brief", None, "chair", {"question": "Is it covered?", "options": [{"id": "A", "label": "Covered", "detail": ""}], "focus": [], "weighing": {}, "note": ""}),
            ("vote", 3, "buffett", {"scores": {"A": 7, "B": 4}, "top": "A", "reason": "Because."}),
            ("verdict", None, "chair", {"headline": "Covered", "summary": "s", "why": [], "watch_out": None, "disagreements": [], "gaps": []}),
        ]:
            conn.execute(insert(debate_turns).values(session_id=sid, stage=stage, round=rnd, seat=seat, data=data, flags=None))
        conn.execute(update(debate_sessions).where(debate_sessions.c.id == sid).values(
            status="done", result={"average": {"A": 7.0, "B": 4.0}, "best": ["A"], "agreement": 2, "voters": 2, "scores": {}},
        ))

    full = room.get(f"/v1/debate/sessions/{sid}").json()
    assert [t["stage"] for t in full["turns"]] == ["brief", "vote", "verdict"]
    assert full["turns"][1]["data"]["scores"] == {"A": 7, "B": 4}
    assert full["result"]["average"]["A"] == 7.0 and full["turns"][2]["data"]["summary"] == "s"
    assert "mode" not in full["turns"][0]["data"] and "mode" not in full["result"]


def test_arabic_sessions_answer_in_arabic(room):
    signup(room)
    events = convene(room, question="هل يجب قراءة التوزيعات كمغطاة أم كمعرضة للخطر؟", locale="ar")
    turns = [e["turn"] for e in events if e["type"] == "turn"]
    brief = turns[0]["data"]
    assert brief["mode"] == "choice"
    assert re.search(r"[؀-ۿ]", brief["question"]) and re.search(r"[؀-ۿ]", brief["options"][0]["label"])
    for stage in ("openings", "debate", "final", "verdict"):
        text = next(t for t in turns if t["stage"] == stage)["data"]
        assert re.search(r"[؀-ۿ]", text.get("text") or text["answer"]), stage


def test_the_monthly_allowance_and_one_session_at_a_time(room, monkeypatch):
    from app import plans

    signup(room)
    monkeypatch.setitem(plans.LIMITS["pro"], "debates_per_month", 1)
    convene(room)
    assert convene(room, status=429)["detail"] == "debate_limit"
    assert room.get("/v1/debate/status").json()["used"] == 1


def test_sessions_are_private_and_go_with_the_account(room):
    from app.appdb import debate_sessions, debate_turns, engine_for

    signup(room)
    sid = convene(room)[0]["session"]["id"]
    room.cookies.clear()
    signup(room, "other@example.com")
    assert room.get(f"/v1/debate/sessions/{sid}").status_code == 404
    assert room.get("/v1/debate/sessions").json() == []
    room.cookies.clear()
    room.post("/v1/auth/login", json={"email": "room@example.com", "password": "correct horse battery"}, headers=ORIGIN)
    assert room.post("/v1/me/delete", json={"password": "correct horse battery"}, headers=ORIGIN).status_code == 200
    with engine_for(room.app.state.settings.database_url).connect() as conn:
        assert conn.execute(select(debate_sessions.c.id)).fetchall() == []
        assert conn.execute(select(debate_turns.c.id)).fetchall() == []


# --- the models (OpenRouter) ------------------------------------------------------------------------


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeRouter:
    """Answers by seat and step, read from the prompt the engine sends."""

    calls: list = []  # requests answered
    refused = 0  # requests refused for switching reasoning off
    fail_chair = False

    def __init__(self, **kw):
        self.chat = _Obj(completions=_Obj(create=self._create))

    async def _create(self, **body):
        import openai

        system, user = body["messages"][0]["content"], body["messages"][1]["content"]
        seat = "chair" if "YOUR SEAT: the Chair" in system else re.search(r"YOUR SEAT: .*?\(id (\w+)\)", system).group(1)
        step = re.search(r"THIS STEP \(([^)]+)\)", user).group(1)
        retry = len(body["messages"]) > 2
        if seat == "chair" and FakeRouter.fail_chair:
            raise openai.APIConnectionError(request=None)
        if seat == "chair" and body["extra_body"].get("reasoning") == {"enabled": False}:
            # Like Claude Sonnet 5.5 on OpenRouter: reasoning cannot be switched off.
            msg = "Reasoning is mandatory for this endpoint and cannot be disabled."
            response = _Obj(status_code=400, headers={}, request=None)
            FakeRouter.refused += 1
            raise openai.BadRequestError(msg, response=response, body={"message": msg, "code": 400})
        FakeRouter.calls.append(body)
        reply = self.reply(seat, step, retry)
        usage = _Obj(prompt_tokens=1000, completion_tokens=100, cost=0.001)
        return _Obj(choices=[_Obj(message=_Obj(content=reply), finish_reason="stop")], usage=usage)

    @staticmethod
    def reply(seat, step, retry):
        if step == "Brief":
            first = "Buy the shares" if not retry else "Earnings cover the dividend"
            return json.dumps(
                {
                    "mode": "choice",
                    "question": "Is the dividend covered by earnings?",
                    "options": [{"id": "A", "label": first, "detail": "Payout ratio 41.9 [P2]."}, {"id": "B", "label": "Covered only if margins hold", "detail": "x"}],
                    "focus": ["payout", "debt"],
                    "weighing": {"buffett": "the payout ratio", "lynch": "P/E", "dalio": "the cycle", "marks": "the downside"},
                    "note": "",
                }
            )
        if step == "Answers":
            text = {
                "buffett": "ROE is 26.75%. I would buy at this price.",
                "lynch": "The P/E is 99.9 [P1].",
            }.get(seat, "The yield is 5.01% [P1].")
            return "```json\n" + json.dumps({"lean": "A", "headline": "Covered.", "text": text}) + "\n```"
        if step == "Fault lines":
            return json.dumps({"lines": [{"title": "Payout", "between": ["buffett", "marks", "nobody"], "text": "They differ."}], "summary": ""})
        if step == "Challenges":
            return json.dumps({
                "responds_to": "buffett" if seat != "buffett" else "lynch",
                "lean": "B" if seat == "marks" else "A",
                "headline": "No.",
                "text": "I disagree.",
                "concedes": "The payout ratio matters." if seat == "lynch" else "",
            })
        if step == "Final word":
            # Lynch moves to B here (it challenged on A); Marks was already on B.
            return json.dumps({
                "lean": "B" if seat in ("marks", "lynch") else "A",
                "text": "That is where I land.",
                "changed": "The payout ratio." if seat == "lynch" else "",
                "would_change": "A longer earnings record.",
            })
        return json.dumps(
            {
                "headline": "The data supports a covered dividend",
                "answer": "The room reads the payout as covered, with Marks and Lynch on the conditional reading.",
                "favours": "The room splits evenly between the two readings.",
                "disagreements": ["Marks reads the cycle differently."],
                "gaps": ["No earnings forecasts."],
            }
        )


@pytest.fixture
def router(room, monkeypatch):
    from app.copilot import openai_compat

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-used")
    monkeypatch.setattr(openai_compat.openai, "AsyncOpenAI", FakeRouter)
    FakeRouter.calls, FakeRouter.fail_chair, FakeRouter.refused = [], False, 0
    from app.debate import llm

    llm.REASONING_REQUIRED.clear()
    return room


def test_models_debate_with_checked_numbers_and_no_advice(router):
    signup(router)
    s = router.get("/v1/debate/status").json()
    assert s["stand_in"] is False and s["models"] == {"advisors": "deepseek/deepseek-v4-pro", "chair": "anthropic/claude-sonnet-5.5"}
    events = convene(router)
    assert events[-1]["status"] == "done"
    turns = {(t["stage"], t["seat"]): t for t in (e["turn"] for e in events if e["type"] == "turn")}

    # The Chair's first options offered an action: asked again, it framed a reading of the data.
    brief = turns[("brief", "chair")]["data"]
    assert [o["label"] for o in brief["options"]] == ["Earnings cover the dividend", "Covered only if margins hold"]
    # Untagged figure cited, advice removed; an invented figure flagged.
    buffett = turns[("openings", "buffett")]
    assert buffett["data"]["text"] == "ROE is 26.75% [P1]." and buffett["flags"]["removed"] == 1 and buffett["flags"]["cited"] == 1
    assert turns[("openings", "lynch")]["flags"]["unverified"] == ["99.9"]
    # The fault line keeps only real advisors; challenges record a changed lean and a conceded point.
    assert turns[("faultlines", "chair")]["data"]["lines"][0]["between"] == ["buffett", "marks"]
    assert turns[("debate", "marks")]["data"]["changed"] is True and turns[("debate", "lynch")]["data"]["changed"] is False
    assert turns[("debate", "lynch")]["data"]["concedes"] == "The payout ratio matters."
    # The final word: Lynch moved from A to B and says what changed; Marks was already on B.
    lynch = turns[("final", "lynch")]["data"]
    assert lynch["lean"] == "B" and lynch["lean_changed"] is True and lynch["changed"] == "The payout ratio."
    assert turns[("final", "marks")]["data"]["lean_changed"] is False
    # The leans are counted here, not scored by a model: two on each reading is a tie.
    result = next(e["result"] for e in events if e["type"] == "result")
    assert result["mode"] == "choice" and result["tally"] == {"A": 2, "B": 2} and result["best"] == ["A", "B"]
    assert result["leans"] == {"buffett": "A", "lynch": "B", "dalio": "A", "marks": "B"}
    verdict = turns[("verdict", "chair")]["data"]
    assert verdict["answer"].startswith("The room reads the payout") and verdict["favours"]

    # One model for the advisors, another for the Chair; the data pack precedes every seat's brief.
    models = {c["model"] for c in FakeRouter.calls}
    assert models == {"deepseek/deepseek-v4-pro", "anthropic/claude-sonnet-5.5"}
    chair_calls = [c for c in FakeRouter.calls if "YOUR SEAT: the Chair" in c["messages"][0]["content"]]
    assert all(c["model"] == "anthropic/claude-sonnet-5.5" for c in chair_calls) and len(chair_calls) == 4  # brief asked twice
    system = FakeRouter.calls[0]["messages"][0]["content"]
    assert system.index("DATA PACK") < system.index("YOUR SEAT") and "[P1] Quote, valuation" in system
    assert "return_12m_pct" in system and "Never tell the member or anyone else to buy, sell or hold" in system
    assert FakeRouter.calls[0]["extra_body"]["usage"] == {"include": True}
    # The Chair's model refused "reasoning off" once; it then runs at the lowest effort, the advisors with it off.
    assert FakeRouter.refused == 1 and {str(c["extra_body"].get("reasoning")) for c in chair_calls} == {"{'effort': 'low'}"}
    assert all(c["extra_body"]["reasoning"] == {"enabled": False} for c in FakeRouter.calls if c not in chair_calls)
    assert {c["max_tokens"] for c in chair_calls} == {1_200 + 2_048, 900 + 2_048, 2_200 + 2_048}

    from app.appdb import debate_sessions, engine_for

    with engine_for(router.app.state.settings.database_url).connect() as conn:
        row = conn.execute(select(debate_sessions)).one()
    calls = len(FakeRouter.calls)
    assert row.status == "done" and row.seconds is not None
    assert row.cost_usd == pytest.approx(0.001 * calls) and row.prompt_tokens == 1000 * calls


def test_a_session_the_chair_cannot_run_fails_and_does_not_count(router):
    signup(router)
    FakeRouter.fail_chair = True
    events = convene(router)
    assert [e["code"] for e in events if e["type"] == "error"] == ["unreachable"]
    assert events[-1]["status"] == "failed"
    assert router.get("/v1/debate/status").json()["used"] == 0
    assert router.get("/v1/debate/sessions").json()[0]["status"] == "failed"
