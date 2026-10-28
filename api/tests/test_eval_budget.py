"""The benchmark spending cap, pinned at the level it actually binds.

An independent reviewer asked, on 2026-10-28, for a demonstration that the limit covers *concurrent
requests and retries* and not only completed calls, and that a failure to read the account balance
always stops further spending. The first two are what this file tests; the third is tested by the
refusals below never depending on any network call at all - `Budget` is arithmetic over what this
process has itself been billed, so an unreachable account endpoint cannot disable it.

Nothing here touches a model or the network.
"""

import asyncio

import pytest

from eval.budget import Budget, BudgetExhausted, PriceUnknown, bound_for, metered


def test_a_call_reserves_its_worst_case_not_its_average():
    """One ask can bill `attempts` times, so one ask reserves `attempts` times."""
    b = Budget(cap_usd=1.00, per_call_usd=0.03, attempts=3)
    assert b.reservation == pytest.approx(0.09)
    b.take()
    assert b.reserved == pytest.approx(0.09)
    assert b.committed == pytest.approx(0.09)


def test_retries_are_billed_and_counted_against_the_cap():
    """A failed attempt is still charged (F-7). Settling the accumulated cost of three attempts
    must move the cap, not just the cost of the one that eventually answered."""
    b = Budget(cap_usd=0.30, per_call_usd=0.03, attempts=3)
    b.take()
    b.settle(0.09)          # three attempts, all billed
    assert b.spent == pytest.approx(0.09)
    b.take()
    b.settle(0.09)
    assert b.spent == pytest.approx(0.18)
    b.take()
    b.settle(0.09)
    assert b.spent == pytest.approx(0.27)
    with pytest.raises(BudgetExhausted):
        b.take()               # 0.27 + 0.09 would pass 0.30
    assert b.refused == 1


def test_a_failed_call_is_still_charged():
    b = Budget(cap_usd=1.00, per_call_usd=0.03, attempts=3)
    b.take()
    b.settle(0.04)             # the call raised, and the provider billed the attempts anyway
    assert b.spent == pytest.approx(0.04)
    assert b.reserved == 0.0
    assert b.calls == 1


def test_a_call_that_returns_no_usage_still_releases_its_reservation():
    b = Budget(cap_usd=1.00)
    b.take()
    b.settle(None)
    assert b.reserved == 0.0 and b.spent == 0.0


def test_calls_in_flight_count_against_the_cap_so_concurrency_cannot_slip_past():
    """The room asks its seats in parallel. Twenty concurrent calls must not all pass a check that
    looks only at what has already settled: a cap with room for three must admit three."""
    b = Budget(cap_usd=0.30, per_call_usd=0.03, attempts=3)   # reservation 0.09 -> room for 3
    admitted, refused = 0, 0
    for _ in range(20):
        try:
            b.take()           # nothing settles: every one of these is in flight
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
    the reservation and no slack term. Keeping the two apart is the distinction the second review
    round asked for."""
    b = Budget(cap_usd=0.50, per_call_usd=0.03, attempts=3)
    over_estimate = 0.12      # every call costs more than its reservation

    async def one():
        try:
            b.take()
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
    """The reviewer's third point. Every refusal above came from arithmetic on this process's own
    billed cost - no balance read, no network. So a failed balance lookup cannot disable the cap;
    the run-level guard stops on it, and this cap keeps binding regardless."""
    b = Budget(cap_usd=0.05, per_call_usd=0.03, attempts=3)
    with pytest.raises(BudgetExhausted) as exc:
        b.take("a first call")
    assert "cap" in str(exc.value)
    assert b.spent == 0.0 and b.calls == 0


def test_the_metered_wrapper_settles_on_the_failure_path():
    """End to end through the harness's own wrapper, with a stand-in model call that always raises
    after being billed. The budget must still advance, or a retry storm would be free.

    The call function is injected, so this needs nothing from the application - which is the point:
    the first version imported the harness, that imported `app.main`, and the test could not run
    from a verification package carrying only part of `app`."""
    class FakeUsage:
        cost_usd = 0.07

    class FakeError(Exception):
        usage = FakeUsage()

    async def always_raises(_model, _messages, _max_tokens, _temperature, _check):
        raise FakeError("the provider refused")

    budget = Budget(cap_usd=0.30, per_call_usd=0.03, attempts=3)
    ask, calls = metered(always_raises, budget)

    async def main():
        for _ in range(3):
            with pytest.raises(FakeError):
                await ask(seat=type("S", (), {"id": "buffett"})(), messages=[], model="anthropic/claude-sonnet-5.5",
                          max_tokens=10, temperature=0.0, check=lambda x: x)

    asyncio.run(main())

    assert budget.calls == 3
    assert budget.spent == pytest.approx(0.21)
    assert calls["cost"] == pytest.approx(0.21)
    with pytest.raises(BudgetExhausted):
        budget.take()


def test_the_metered_wrapper_settles_the_real_cost_on_success():
    class FakeUsage:
        cost_usd = 0.05

    async def succeeds(_model, _messages, _max_tokens, _temperature, _check):
        return {"ok": True}, FakeUsage()

    budget = Budget(cap_usd=1.00, per_call_usd=0.03, attempts=3)
    ask, calls = metered(succeeds, budget)

    async def main():
        return await ask(messages=[], model="anthropic/claude-sonnet-5.5", max_tokens=10, temperature=0.0, check=lambda x: x)

    checked, usage = asyncio.run(main())
    assert checked == {"ok": True}
    assert budget.spent == pytest.approx(0.05)
    assert budget.reserved == 0.0
    assert calls["n"] == 1


# --- the hard bound, and how it differs from a forecast ----------------------------------------
#
# The second review round asked for the implementation to distinguish "a hard upper bound derived
# from model pricing, input size, maximum output tokens and retry limits" from "a forecast that is
# monitored and settled after execution". They are different guarantees and these tests pin both.


def test_the_bound_is_built_from_pricing_tokens_and_retries():
    """Every input the reviewer named, and the arithmetic is checkable by hand."""
    # sonnet-5.5: $2/M prompt, $10/M completion. 2,000 chars at the 2-chars-per-token floor is
    # 1,000 prompt tokens = $0.002; a 1,000-token output ceiling = $0.010; one attempt = $0.012.
    one = bound_for("anthropic/claude-sonnet-5.5", 2000, 1000, attempts=1)
    assert one == pytest.approx(0.012)
    assert bound_for("anthropic/claude-sonnet-5.5", 2000, 1000, attempts=3) == pytest.approx(0.036)
    # a bigger prompt and a bigger output ceiling both raise it
    assert bound_for("anthropic/claude-sonnet-5.5", 4000, 1000, 1) > one
    assert bound_for("anthropic/claude-sonnet-5.5", 2000, 2000, 1) > one
    # and the cheaper advisor model bounds lower than the chair's
    assert bound_for("deepseek/deepseek-v4-pro", 2000, 1000, 1) < one


def test_an_unpriced_model_refuses_rather_than_guesses():
    """A bound cannot be computed for a model that is not in the table, so no call is made. Guessing
    here would turn the hard cap back into a forecast without saying so."""
    with pytest.raises(PriceUnknown):
        bound_for("some/new-model", 2000, 1000, 3)


def test_the_bound_is_far_above_the_forecast_and_that_is_the_point():
    """Measured on a real arm-B call: 21,971 characters of prompt, a 2,200-token output ceiling and
    three attempts bound at about $0.13, where the run actually cost $0.0292. A cap set to the
    forecast is not a guarantee; a cap set to the bound is, and it is roughly 4-6x larger."""
    bound = bound_for("anthropic/claude-sonnet-5.5", 21971, 2200, 3)
    assert bound == pytest.approx(0.1319, abs=0.0005)
    assert bound / 0.0292 > 4


def test_the_hard_cap_holds_even_when_every_call_bills_its_full_bound():
    """The reviewer's exact worry: if calls are admitted and each costs far more than reserved, the
    bill can pass the cap. With the bound as the reservation that cannot happen - a call billed at
    its full bound still leaves the total inside the cap, with no slack term in the assertion."""
    bound = bound_for("anthropic/claude-sonnet-5.5", 2000, 1000, 3)   # 0.036
    b = Budget(cap_usd=0.10, attempts=3)
    admitted = []
    for _ in range(10):
        try:
            admitted.append(b.take("a call", bound))
        except BudgetExhausted:
            break
    assert len(admitted) == 2, f"admitted {len(admitted)}"     # 0.036 * 2 = 0.072; a third would pass 0.10
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


def test_the_forecast_ceiling_stops_a_run_that_costs_more_than_history_predicts():
    """The second ceiling, with the other job: the hard cap makes catastrophe impossible, this one
    notices that spending is running above what the measured history says it should."""
    b = Budget(cap_usd=10.00, expect_usd=0.10)
    for _ in range(3):
        amount = b.take("a call", 0.05)
        b.settle(0.05, amount)
    assert b.spent == pytest.approx(0.15)
    assert b.should_stop() and "forecast ceiling" in b.should_stop()
    assert not b.overruns          # nothing exceeded its bound; the plan was simply dearer


def test_the_two_ceilings_are_independent():
    b = Budget(cap_usd=0.20, expect_usd=10.00)
    amount = b.take("a call", 0.15)
    b.settle(0.15, amount)
    assert b.should_stop() is None           # inside both
    with pytest.raises(BudgetExhausted):     # the hard cap binds first
        b.take("a call", 0.15)
