"""The benchmark spending cap, pinned at the level it actually binds.

Three review rounds shaped this file and each one found something the previous one had taken on
trust. Keeping their cases named here is the point: a cap is a claim about money, and a claim about
money that nobody re-executes is a comment.

* **Round two** asked for a demonstration that the limit covers *concurrent requests and retries*
  and not only completed calls, and that a failure to read the account balance always stops further
  spending.
* **Round three** asked for "a hard upper bound derived from model pricing, input size, maximum
  output tokens, and retry limits" to be distinguished from "a forecast that is monitored and
  settled after execution", because those are different guarantees.
* **Round four** found that the bound existed and three code paths went around it: arms B and E
  reserved a flat forecast, `should_stop()` was advisory, and the bound itself left out the
  reasoning allowance, the growth of a retried prompt and the fourth request `llm.ask` can issue.

Nothing here touches a model or the network.
"""

import asyncio

import pytest

from eval.budget import (
    EXTRA_REQUESTS,
    MESSAGE_OVERHEAD_TOKENS,
    REASONING_ROOM,
    RETRY_ECHO_BYTES,
    RETRY_GROWTH_BYTES,
    RETRY_INSTRUCTION_BYTES,
    Budget,
    BudgetExhausted,
    PriceUnknown,
    bound_for,
    metered,
    prompt_token_ceiling,
    token_bound,
)

SONNET = "anthropic/claude-sonnet-5.5"


def test_a_call_reserves_its_worst_case_not_its_average():
    """One ask can bill `attempts` times, so one ask reserves `attempts` times. This is the FLAT
    forecast path, which has to be asked for by name - see the test below it."""
    b = Budget(cap_usd=1.00, per_call_usd=0.03, attempts=3)
    assert b.reservation == pytest.approx(0.09)
    b.take(allow_forecast=True)
    assert b.reserved == pytest.approx(0.09)
    assert b.committed == pytest.approx(0.09)


def test_omitting_the_bound_raises_rather_than_reserving_a_forecast():
    """Round four's first finding, and the one that mattered most: `probe_run` called
    `budget.take()` with no bound for arms B and E, so the two single-model arms reserved a flat
    $0.09 where their real upper bound is several times that. The cap was enforced - against the
    wrong number. A fallback that is silently reachable is not a fallback, it is a hole, so it is
    now opt-in by name and the default is a refusal."""
    b = Budget(cap_usd=1.00)
    with pytest.raises(PriceUnknown) as exc:
        b.take("an inference call")
    assert "no upper bound" in str(exc.value)
    assert b.reserved == 0.0 and b.calls == 0
    # and the opt-in still works, for the tests and callers that have no prompt in hand
    assert b.take("an inference call", allow_forecast=True) == pytest.approx(0.09)


def test_retries_are_billed_and_counted_against_the_cap():
    """A failed attempt is still charged (F-7). Settling the accumulated cost of three attempts
    must move the cap, not just the cost of the one that eventually answered."""
    b = Budget(cap_usd=0.30, per_call_usd=0.03, attempts=3)
    for expected in (0.09, 0.18, 0.27):
        b.take(allow_forecast=True)
        b.settle(0.09)          # three attempts, all billed
        assert b.spent == pytest.approx(expected)
    with pytest.raises(BudgetExhausted):
        b.take(allow_forecast=True)   # 0.27 + 0.09 would pass 0.30
    assert b.refused == 1


def test_a_failed_call_is_still_charged():
    b = Budget(cap_usd=1.00, per_call_usd=0.03, attempts=3)
    b.take(allow_forecast=True)
    b.settle(0.04)             # the call raised, and the provider billed the attempts anyway
    assert b.spent == pytest.approx(0.04)
    assert b.reserved == 0.0
    assert b.calls == 1


def test_a_call_that_returns_no_usage_still_releases_its_reservation():
    b = Budget(cap_usd=1.00)
    b.take(allow_forecast=True)
    b.settle(None)
    assert b.reserved == 0.0 and b.spent == 0.0


def test_calls_in_flight_count_against_the_cap_so_concurrency_cannot_slip_past():
    """The room asks its seats in parallel. Twenty concurrent calls must not all pass a check that
    looks only at what has already settled: a cap with room for three must admit three."""
    b = Budget(cap_usd=0.30, per_call_usd=0.03, attempts=3)   # reservation 0.09 -> room for 3
    admitted, refused = 0, 0
    for _ in range(20):
        try:
            b.take(allow_forecast=True)   # nothing settles: every one of these is in flight
            admitted += 1
        except BudgetExhausted:
            refused += 1
    assert admitted == 3, f"admitted {admitted}"
    assert refused == 17
    assert b.committed <= b.cap


@pytest.mark.parametrize("workers", [2, 8, 32])
def test_the_cap_holds_under_concurrent_takes_and_settles(workers):
    """Many coroutines reserving and settling at once, with the real cost coming in ABOVE the
    reservation. This exercises the FALLBACK path - the flat per-call estimate, which is a forecast
    and not a bound - so the invariant it can assert is weaker: spend stays within one call's
    overshoot of the cap. The hard-cap guarantee is tested separately, with the computed bound as
    the reservation and no slack term. Keeping the two apart is the distinction round three asked
    for, and the reason this test has to say which one it is."""
    b = Budget(cap_usd=0.50, per_call_usd=0.03, attempts=3)
    over_estimate = 0.12      # every call costs more than its reservation

    async def one():
        try:
            b.take(allow_forecast=True)
        except BudgetExhausted:
            return False
        await asyncio.sleep(0)
        b.settle(over_estimate)
        return True

    async def main():
        return await asyncio.gather(*[one() for _ in range(workers * 5)])

    done = asyncio.run(main())
    assert b.spent <= b.cap + over_estimate, f"spent {b.spent} over cap {b.cap}"
    assert any(done), "nothing ran at all"
    assert b.calls == sum(1 for d in done if d)


def test_the_cap_needs_no_account_endpoint():
    """Round two's third point. Every refusal here came from arithmetic on this process's own
    billed cost - no balance read, no network. So a failed balance lookup cannot disable the cap;
    the run-level guard stops on it, and this cap keeps binding regardless."""
    b = Budget(cap_usd=0.05, per_call_usd=0.03, attempts=3)
    with pytest.raises(BudgetExhausted) as exc:
        b.take("a first call", allow_forecast=True)
    assert "cap" in str(exc.value)
    assert b.spent == 0.0 and b.calls == 0


# --- the hard bound, and how it differs from a forecast ----------------------------------------


def test_the_bound_is_built_from_pricing_tokens_and_retries():
    """Every input round three named, and the arithmetic is checkable by hand.

    sonnet-5.5 is $2/M prompt and $10/M completion. 2,000 prompt bytes in two messages bound at
    2,000 + 2x8 = 2,016 tokens = $0.004032. The output ceiling is 1,000 + 2,048 of reasoning room =
    3,048 tokens = $0.030480. One attempt is now exactly one request, so $0.034512.

    It was $0.069024 until the fifth review round: `llm.ask` could issue a request that its attempt
    counter did not count, and round four priced that fourth request rather than removing it, which
    doubled a one-attempt bound. The counter now covers every request it issues, so the extra
    request is gone from the arithmetic because it is gone from the code. This is the one direction
    in which a bound may fall - the request it was paying for cannot happen any more.
    """
    one = bound_for(SONNET, 2000, 1000, attempts=1)
    assert one == pytest.approx(0.034512)
    # more attempts, a bigger prompt and a bigger output ceiling each raise it
    assert bound_for(SONNET, 2000, 1000, 3) > bound_for(SONNET, 2000, 1000, 2) > one
    assert bound_for(SONNET, 4000, 1000, 1) > one
    assert bound_for(SONNET, 2000, 2000, 1) > one
    # and the cheaper advisor model bounds lower than the chair's
    assert bound_for("deepseek/deepseek-v4-pro", 2000, 1000, 1) < one


def test_the_bound_includes_the_reasoning_allowance():
    """Round four, finding three. `llm.ask` sends `max_tokens + REASONING_ROOM` unless reasoning is
    explicitly off, and Sonnet 5.5 on OpenRouter refuses the request with reasoning off - so the
    chair's own model always takes the larger ceiling. The first bound priced `max_tokens` alone and
    was therefore too low by 2,048 completion tokens on every single call."""
    with_room = bound_for(SONNET, 2000, 1000, 1)
    without = bound_for(SONNET, 2000, 1000, 1, reasoning=False)
    assert with_room > without
    # the gap is exactly the reasoning allowance, priced at completion rates, once per request
    requests = 1 + EXTRA_REQUESTS
    assert with_room - without == pytest.approx(REASONING_ROOM * 10.000e-6 * requests)


def test_the_bound_grows_with_each_retry_because_the_prompt_does():
    """Round four, finding on retry prompt growth. A retry is not the same request again: `llm.ask`
    appends the unusable reply (up to 6,000 BYTES since the fifth review round) and a bounded
    correction instruction, so request 2
    carries a bigger prompt than request 1. Multiplying one prompt by three undercounts - which is
    what the first bound did."""
    flat = bound_for(SONNET, 2000, 1000, 3, retries_grow=False)
    grown = bound_for(SONNET, 2000, 1000, 3)
    assert grown > flat
    # request 1 at P, request 2 at P + G, request 3 at P + 2G: three extra G of prompt in all,
    # plus the two extra messages each retry adds
    extra_bytes = (0 + 1 + 2) * RETRY_GROWTH_BYTES
    extra_messages = (0 + 2 + 4) * MESSAGE_OVERHEAD_TOKENS
    assert grown - flat == pytest.approx((extra_bytes + extra_messages) * 2.000e-6)
    assert RETRY_GROWTH_BYTES >= RETRY_ECHO_BYTES


def test_the_fourth_request_is_prevented_rather_than_priced():
    """`llm.ask` retried a 400 "reasoning is mandatory" with `continue` placed BEFORE
    `attempts += 1`, so one call could issue ATTEMPTS + 1 requests, and round four priced that
    fourth request instead of removing it. The fifth review round asked for the configured attempt
    count to be enforced directly. It now is - every issued request is counted as it is issued - so
    the bound counts exactly `attempts` requests and nothing extra.

    The behavioural half of this is `test_a_reasoning_refusal_cannot_buy_a_fourth_request`, which
    drives the real call path and counts the requests that actually leave."""
    assert EXTRA_REQUESTS == 0
    per_request = bound_for(SONNET, 2000, 1000, 1, retries_grow=False)
    # three attempts with no growth is three requests, not four
    assert bound_for(SONNET, 2000, 1000, 3, retries_grow=False) == pytest.approx(per_request * 3)


def test_the_token_bound_is_bytes_not_characters():
    """Round three said the 2-characters-per-token floor was "not established". It was not: it was
    an average wearing a bound's name, and Arabic beats it before the tokenizer is even reached.
    These prompts carry Arabic.

    Bytes are a bound for a byte-level BPE tokenizer - the base vocabulary is the 256 single bytes
    and every merge replaces two tokens with one, so the count starts at the byte count and only
    falls. The assumption is enforced at runtime as well, by `audit_tokens`.
    """
    arabic = "ما الذي تقوله البيانات عن هذا السؤال؟"
    chars, byts = len(arabic), len(arabic.encode("utf-8"))
    assert byts > chars * 1.5, "Arabic is ~2 bytes a character, which is the whole point"
    # the old floor would have claimed HALF the characters as the token count; the bound is bytes
    assert token_bound(byts, 0) == byts
    assert token_bound(byts, 0) > chars / 2.0
    assert token_bound(100, 2) == 100 + 2 * MESSAGE_OVERHEAD_TOKENS


def test_an_unpriced_model_refuses_rather_than_guesses():
    """A bound cannot be computed for a model that is not in the table, so no call is made. Guessing
    here would turn the hard cap back into a forecast without saying so."""
    with pytest.raises(PriceUnknown):
        bound_for("some/new-model", 2000, 1000, 3)


def test_the_bound_is_far_above_the_forecast_and_that_is_the_point():
    """Measured on a real arm-B call: 21,971 bytes of prompt, a 2,200-token output ceiling and three
    attempts bound at about $0.30, where the run actually cost $0.0292. A cap set to the forecast is
    not a guarantee; a cap set to the bound is, and it is **ten times** larger. The first version of
    this bound said 4.5x, and the difference is the reasoning allowance and the retried prompt.

    It read $0.3843 and thirteen times until the fifth review round removed the fourth request
    `llm.ask` could issue. The guarantee is unchanged; one request that used to be possible is
    not."""
    bound = bound_for(SONNET, 21971, 2200, 3)
    assert bound == pytest.approx(0.297858, abs=0.0005)
    assert bound / 0.0292 > 10


def test_the_hard_cap_holds_even_when_every_call_bills_its_full_bound():
    """Round three's exact worry: if calls are admitted and each costs far more than reserved, the
    bill can pass the cap. With the bound as the reservation that cannot happen - a call billed at
    its full bound still leaves the total inside the cap, with no slack term in the assertion."""
    bound = bound_for(SONNET, 2000, 1000, 3)                   # 0.142032
    b = Budget(cap_usd=0.50, attempts=3)
    admitted = []
    for _ in range(10):
        try:
            admitted.append(b.take("a call", bound))
        except BudgetExhausted:
            break
    assert len(admitted) == 3, f"admitted {len(admitted)}"      # a fourth would pass 0.50
    for amount in admitted:
        b.settle(amount, amount)                               # billed at the FULL bound
    assert b.spent <= b.cap                                    # no slack: a true hard cap
    assert not b.overruns


def test_a_charge_above_its_bound_is_recorded_and_stops_the_run():
    """If a real charge ever passes the bound, the price table is wrong and the cap has stopped
    being a guarantee. That is recorded, and should_stop() tells the runner to stop rather than
    carry on inside a guarantee that no longer holds."""
    b = Budget(cap_usd=1.00)
    amount = b.take("a call", 0.01)
    b.settle(0.05, amount)
    assert b.overruns and "price table" in b.overruns[0]
    assert b.should_stop()


def test_a_prompt_denser_than_the_token_ceiling_is_recorded_and_stops_the_run():
    """What keeps the byte assumption honest. If a provider ever reports more prompt tokens than the
    input had bytes, every bound in this module is too low - so the first such call is recorded as
    an overrun and the run stops. The assumption is not merely documented; it is checked against the
    provider's own accounting on every call."""
    b = Budget(cap_usd=10.00)
    ceiling = prompt_token_ceiling(2000, 3, 2)
    b.audit_tokens(ceiling, ceiling)             # exactly at the ceiling is fine
    assert not b.overruns
    b.audit_tokens(None, ceiling)                # a provider that reports nothing cannot be audited
    assert not b.overruns
    b.audit_tokens(ceiling + 1, ceiling)
    assert b.overruns and "denser than one token per UTF-8 byte" in b.overruns[0]
    assert b.should_stop()


def test_take_refuses_once_a_stop_reason_is_recorded():
    """Round four's second finding: `should_stop()` could report an overrun while `take()` carried
    on admitting calls, and the runner only checked `refused`. So the guarantee could be known to be
    broken and the spending continue. The condition is now enforced at the point of admission, which
    is the only place that can actually prevent a charge."""
    b = Budget(cap_usd=100.00)
    amount = b.take("a call", 0.01)
    b.settle(0.05, amount)                       # a charge above its bound: an overrun
    assert b.should_stop()
    with pytest.raises(BudgetExhausted) as exc:
        b.take("the next call", 0.01)            # cap has room; the overrun is what stops it
    assert "price table" in str(exc.value)
    assert b.refused == 1


def test_the_forecast_ceiling_also_stops_admission():
    """The same enforcement for the other ceiling. Spending above what the measured history predicts
    stops the next call rather than being noticed after the run."""
    b = Budget(cap_usd=100.00, expect_usd=0.10)
    for _ in range(3):
        amount = b.take("a call", 0.05)
        b.settle(0.05, amount)
    assert b.spent == pytest.approx(0.15)
    assert b.should_stop() and "forecast ceiling" in b.should_stop()
    assert not b.overruns          # nothing exceeded its bound; the plan was simply dearer
    with pytest.raises(BudgetExhausted):
        b.take("one more", 0.05)


def test_the_two_ceilings_are_independent():
    b = Budget(cap_usd=0.20, expect_usd=10.00)
    amount = b.take("a call", 0.15)
    b.settle(0.15, amount)
    assert b.should_stop() is None           # inside both
    with pytest.raises(BudgetExhausted):     # the hard cap binds first
        b.take("a call", 0.15)


# --- the wrapper every arm goes through --------------------------------------------------------


def test_the_metered_wrapper_reserves_a_bound_and_not_a_forecast():
    """End to end through the wrapper the runner uses, with a stand-in call. The reservation must be
    the computed bound for the prompt actually passed - this is the assertion that would have failed
    while arms B and E metered themselves inline."""
    class FakeUsage:
        cost_usd = 0.01
        prompt_tokens = 40

    async def succeeds(**kw):
        return {"ok": True}, FakeUsage()

    budget = Budget(cap_usd=5.00, attempts=3)
    ask, calls = metered(succeeds, budget)
    messages = [{"role": "system", "content": "x" * 1000}, {"role": "user", "content": "y" * 1000}]

    asyncio.run(ask(messages=messages, model=SONNET, max_tokens=1000, temperature=0.0, check=lambda x: x))

    expected = bound_for(SONNET, 2000, 1000, 3, messages=2)
    assert calls["bound"] == pytest.approx(expected)
    assert calls["bound"] > budget.reservation * 1.5, "a bound, not the flat forecast"
    assert budget.spent == pytest.approx(0.01)
    assert budget.reserved == 0.0
    assert not budget.overruns


def test_the_metered_wrapper_measures_the_prompt_in_bytes():
    """An Arabic prompt bounds higher than an English one of the same character count, because the
    bound is taken from bytes. Under the old characters-per-token floor the two were identical."""
    class FakeUsage:
        cost_usd = 0.0
        prompt_tokens = 10

    async def succeeds(**kw):
        return {"ok": True}, FakeUsage()

    def bound_of(content):
        budget = Budget(cap_usd=50.00, attempts=3)
        ask, calls = metered(succeeds, budget)
        asyncio.run(ask(messages=[{"role": "user", "content": content}], model=SONNET,
                        max_tokens=100, temperature=0.0, check=lambda x: x))
        return calls["bound"]

    assert bound_of("س" * 500) > bound_of("s" * 500)


def test_the_metered_wrapper_settles_on_the_failure_path():
    """A stand-in model call that always raises after being billed. The budget must still advance,
    or a retry storm would be free.

    The call function is injected, so this needs nothing from the application - which is the point:
    the first version imported the harness, that imported `app.main`, and the test could not run
    from a verification package carrying only part of `app`."""
    class FakeUsage:
        cost_usd = 0.07
        prompt_tokens = 20

    class FakeError(Exception):
        usage = FakeUsage()

    async def always_raises(**kw):
        raise FakeError("the provider refused")

    budget = Budget(cap_usd=1.00, attempts=3)
    ask, calls = metered(always_raises, budget)

    async def main():
        for _ in range(3):
            with pytest.raises(FakeError):
                await ask(seat=type("S", (), {"id": "buffett"})(), messages=[], model=SONNET,
                          max_tokens=10, temperature=0.0, check=lambda x: x)

    asyncio.run(main())

    assert budget.calls == 3
    assert budget.spent == pytest.approx(0.21)
    assert calls["cost"] == pytest.approx(0.21)
    assert calls["bound"] == pytest.approx(3 * bound_for(SONNET, 0, 10, 3, messages=1))


def test_the_metered_wrapper_passes_every_keyword_through():
    """The wrapper has to be transparent, because the stand-in asker used by --dry takes `seat`,
    `stage` and `state` and the real one does not. That transparency is what allows ONE metering
    path for every arm and both modes - and one path is why a bound can no longer be skipped."""
    seen = {}

    class FakeUsage:
        cost_usd = 0.0
        prompt_tokens = 1

    async def record(**kw):
        seen.update(kw)
        return {"ok": True}, FakeUsage()

    ask, _calls = metered(record, Budget(cap_usd=1.00))
    asyncio.run(ask(seat="s", stage="openings", round=1, state="st", messages=[],
                    model=SONNET, max_tokens=10, temperature=0.3, check=lambda x: x))
    assert seen["stage"] == "openings" and seen["state"] == "st" and seen["round"] == 1
    assert seen["seat"] == "s" and seen["temperature"] == 0.3


def test_the_mirrored_llm_constants_still_match_the_application():
    """The bound is computed from constants copied out of `app.debate.llm`, because `eval.budget`
    must import with no application on the path. A copy can drift, and a drifted copy loosens the
    cap silently - so where the application IS importable, the copies are pinned to it. Raising the
    reasoning allowance in production now fails this test instead of quietly making every bound too
    low."""
    try:
        from app.debate import llm
    except Exception as exc:                 # pragma: no cover - the verification package's path
        # Named precisely rather than "the application is not available": inside the verification
        # package this is `app.routers`, which `copilot.openai_compat` imports at module scope, and
        # saying so is what stops a reader looking for a missing file that is not missing.
        pytest.skip(f"app.debate.llm does not import here - {type(exc).__name__}: {exc}")
    assert REASONING_ROOM == llm.REASONING_ROOM
    assert Budget(0).attempts == llm.ATTEMPTS
    # The echo limit is now a named constant on both sides and the same unit on both sides - it was
    # a literal 6,000 CHARACTER slice in llm.ask against 6,000 bytes spent here.
    assert RETRY_ECHO_BYTES == llm.RETRY_ECHO_BYTES
    # The correction sentence quotes the parser's message. Its longest fixed wording is 172 bytes,
    # and llm clips the quoted message, so the whole instruction fits what is accounted for here.
    assert RETRY_INSTRUCTION_BYTES >= 172 + llm.RETRY_PROBLEM_BYTES


# --- the retry limits, against the real model-call path ----------------------------------------
#
# The fifth review round asked for these two limits to be tested "against the real model-call
# path", not against the mirrored constants - which is the right ask, because every defect in this
# family was a disagreement between what `llm.ask` does and what this file priced. These two drive
# `llm.ask` itself with a stand-in transport and count what actually leaves.


class _Stub:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _llm_or_skip(clear: bool = True):
    """`app.debate.llm`, or a skip naming why it does not import here.

    `clear` empties REASONING_REQUIRED, which most of these tests want so the runtime
    reasoning-refusal path is reachable. The seeding test passes False, because the seeded state is
    exactly what it is testing.
    """
    try:
        from app.debate import llm
    except Exception as exc:                 # pragma: no cover - the verification package's path
        pytest.skip(f"app.debate.llm does not import here - {type(exc).__name__}: {exc}")
    if clear:
        llm.REASONING_REQUIRED.clear()
    return llm


def _usage():
    return _Stub(prompt_tokens=10, completion_tokens=1, cost=0.0)


def test_the_retry_limits_hold_on_the_real_call_path(monkeypatch):
    """Arabic prose and an unbounded parser message, through `llm.ask`.

    The echo was `text[:6_000]` - six thousand CHARACTERS, spent here as six thousand BYTES - and
    Arabic is about two bytes a character, so the retry could carry roughly twice the accounted
    growth in the product's own second language. The correction sentence quoted the parser's
    message, which had no limit at all. Both are clipped in bytes now, and this test reads the
    messages the client was actually handed."""
    llm = _llm_or_skip()
    # 24,000 characters, 48,000 bytes: eight times the echo limit either way round.
    arabic = "ولا" * 8_000
    sent: list = []

    async def create(**body):
        sent.append(body["messages"])
        return _Stub(choices=[_Stub(message=_Stub(content=arabic), finish_reason="stop")],
                     usage=_usage())

    monkeypatch.setattr(llm, "make_client",
                        lambda s: _Stub(chat=_Stub(completions=_Stub(create=create))))
    monkeypatch.setattr(llm, "host_routing", lambda s: {})

    def check(_obj):
        raise ValueError("the parser's own message, which used to go into the next prompt whole: "
                         + "x" * 5_000)

    with pytest.raises(llm.SeatError):
        asyncio.run(llm.ask(_Stub(debate_reasoning=True), SONNET,
                            [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                            max_tokens=100, temperature=0.0, check=check))

    assert len(sent) == llm.ATTEMPTS, f"{len(sent)} requests for {llm.ATTEMPTS} attempts"
    echo, instruction = sent[-1][-2]["content"], sent[-1][-1]["content"]
    assert len(echo.encode("utf-8")) <= RETRY_ECHO_BYTES
    assert len(instruction.encode("utf-8")) <= RETRY_INSTRUCTION_BYTES
    # The old character slice would have broken the byte limit on this very reply, so the test
    # discriminates rather than passing on text that happens to be ASCII.
    assert len(arabic[:RETRY_ECHO_BYTES].encode("utf-8")) > RETRY_ECHO_BYTES
    # And the whole prompt grew by no more than the bound accounts for per retry.
    grown = sum(len(m["content"].encode("utf-8")) for m in sent[-1])
    first = sum(len(m["content"].encode("utf-8")) for m in sent[0])
    assert grown - first <= (llm.ATTEMPTS - 1) * RETRY_GROWTH_BYTES


def test_a_reasoning_refusal_cannot_buy_a_fourth_request(monkeypatch):
    """The behavioural half of `test_the_fourth_request_is_prevented_rather_than_priced`.

    A 400 "reasoning is mandatory" is retried with `continue`, and while that sat before the
    attempt counter one `ask` could issue ATTEMPTS + 1 requests. On the old code this test counts
    four."""
    import openai

    llm = _llm_or_skip()
    calls: list = []

    async def create(**body):
        calls.append(body)
        if len(calls) == 1:
            # Claude Sonnet 5.5 on OpenRouter, verbatim in effect: reasoning cannot be switched off.
            msg = "Reasoning is mandatory for this endpoint and cannot be disabled."
            raise openai.BadRequestError(
                msg, response=_Stub(status_code=400, headers={}, request=None),
                body={"message": msg, "code": 400})
        return _Stub(choices=[_Stub(message=_Stub(content="not json"), finish_reason="stop")],
                     usage=_usage())

    monkeypatch.setattr(llm, "make_client",
                        lambda s: _Stub(chat=_Stub(completions=_Stub(create=create))))
    monkeypatch.setattr(llm, "host_routing", lambda s: {})

    with pytest.raises(llm.SeatError):
        asyncio.run(llm.ask(_Stub(debate_reasoning=False), SONNET,
                            [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                            max_tokens=100, temperature=0.0, check=lambda o: o))

    assert SONNET in llm.REASONING_REQUIRED, "the reasoning-refusal path was never exercised"
    assert len(calls) == llm.ATTEMPTS, (
        f"{len(calls)} requests left for {llm.ATTEMPTS} attempts: a refusal is buying a request")


def test_the_chairs_model_spends_no_request_learning_it_needs_reasoning(monkeypatch):
    """The regression the attempt-count fix would otherwise have introduced, closed at the cause.

    `debate_reasoning` is False by default, so `_reasoning` asks for reasoning OFF, and the chair's
    model refuses that with a 400 - once per process, until `REASONING_REQUIRED` learns it. Now that
    every issued request counts against ATTEMPTS, that one refused request would have left the
    chair's first call of each process with two attempts at usable JSON instead of three, on the
    longest answers in the room (F-1). Seeding the set removes the refusal instead of paying for it:
    no 400, and the full attempt budget available for the answer."""
    import openai

    llm = _llm_or_skip(clear=False)

    from app.settings import get_settings

    # NOT cleared: the seeded state is what production starts from.
    assert get_settings().debate_chair_model in llm.REASONING_REQUIRED

    calls: list = []

    async def create(**body):
        calls.append(body)
        if body["extra_body"].get("reasoning") == {"enabled": False}:
            msg = "Reasoning is mandatory for this endpoint and cannot be disabled."
            raise openai.BadRequestError(
                msg, response=_Stub(status_code=400, headers={}, request=None),
                body={"message": msg, "code": 400})
        return _Stub(choices=[_Stub(message=_Stub(content="not json"), finish_reason="stop")],
                     usage=_usage())

    monkeypatch.setattr(llm, "make_client",
                        lambda s: _Stub(chat=_Stub(completions=_Stub(create=create))))
    monkeypatch.setattr(llm, "host_routing", lambda s: {})

    with pytest.raises(llm.SeatError):
        asyncio.run(llm.ask(_Stub(debate_reasoning=False), SONNET,
                            [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
                            max_tokens=100, temperature=0.0, check=lambda o: o))

    assert all(b["extra_body"].get("reasoning") != {"enabled": False} for b in calls), (
        "a request was spent being refused for reasoning")
    assert len(calls) == llm.ATTEMPTS, f"only {len(calls)} of {llm.ATTEMPTS} attempts reached the model"
