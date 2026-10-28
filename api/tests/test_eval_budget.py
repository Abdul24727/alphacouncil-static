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

from eval.budget import Budget, BudgetExhausted, metered


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
    """Many coroutines reserving and settling at once, with the real cost coming in above the
    estimate. The invariant is that billed spend never passes the cap."""
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
                await ask(seat=type("S", (), {"id": "buffett"})(), messages=[], model="m",
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
        return await ask(messages=[], model="m", max_tokens=10, temperature=0.0, check=lambda x: x)

    checked, usage = asyncio.run(main())
    assert checked == {"ok": True}
    assert budget.spent == pytest.approx(0.05)
    assert budget.reserved == 0.0
    assert calls["n"] == 1
