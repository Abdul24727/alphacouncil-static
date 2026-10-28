"""A spending cap that binds every model CALL, including retries and calls in flight.

Why this exists. Until 2026-10-28 the cap was checked once before each *run* and credited with the
cost of *completed* runs. An independent reviewer pointed out what that leaves uncovered, and they
were right about all three:

* **Retries.** `llm.ask` makes up to `ATTEMPTS` tries, and a failed attempt is still billed (F-7).
  A run that retried its way past the cap was not noticed until it finished.
* **Calls in flight.** The room asks its seats in parallel. Twenty concurrent calls could all pass a
  check that looked only at what had already settled.
* **A balance that cannot be read.** The old loop skipped the check entirely, so the reservation
  below deliberately depends on no provider endpoint at all: it is arithmetic over what this process
  has itself been charged.

So every call reserves its worst case before it is made and settles its actual cost after, whether it
succeeded or failed. The reservation is the per-call estimate times the retry count, because one
`ask` can bill that many times. The cap therefore binds the *upper bound* of what is outstanding,
not the lower bound of what is finished.
"""

from __future__ import annotations

import threading
from typing import Any


class BudgetExhausted(RuntimeError):
    """Raised in place of making a call that could carry the total past the cap."""


class PriceUnknown(RuntimeError):
    """Raised rather than guessing a price for a model that is not in the table below."""


# $ per token, read from OpenRouter's own /api/v1/models catalogue on 2026-10-28. A table rather
# than a live lookup so a bound can be computed with no network, and so a silent repricing cannot
# quietly loosen the cap: `audit` below compares every real charge against the bound this table
# produced and stops the run if the table is ever too low.
PRICES: dict[str, tuple[float, float]] = {           # model: (prompt, completion)
    "anthropic/claude-sonnet-5.5": (2.000e-6, 10.000e-6),
    "deepseek/deepseek-v4-pro": (0.955e-6, 1.911e-6),
    "openai/gpt-5.2": (1.750e-6, 14.000e-6),
}
# Characters per token for the UPPER BOUND on prompt size. English runs about 4; 2 is deliberately
# pessimistic and covers Arabic, which these prompts also carry. A bound that is sometimes loose is
# a bound; an average is not.
CHARS_PER_TOKEN_FLOOR = 2.0


def bound_for(model: str, prompt_chars: int, max_output_tokens: int, attempts: int = 3) -> float:
    """The most one call can be charged: the prompt at its pessimistic token count, plus the output
    ceiling the request itself sets, times the retry limit.

    This is the number the cap is enforced against. It is NOT a forecast and it is not close to one:
    measured against a real arm-B call on 2026-10-28 - 21,971 characters of prompt and a 2,200-token
    output ceiling - this returns $0.1379 where the run actually cost $0.0292. **4.7 times the
    measured cost.** That gap is what a hard guarantee costs, and it is the whole reason the two
    numbers are reported separately: a cap set to a forecast admits about five times as many runs as
    a cap set to the worst case, and only one of the two is a guarantee.
    """
    try:
        in_price, out_price = PRICES[model]
    except KeyError:
        raise PriceUnknown(
            f"no price for {model!r}, so no upper bound can be computed and no call will be made. "
            f"Add it to eval.budget.PRICES from OpenRouter's /api/v1/models."
        ) from None
    prompt_tokens = prompt_chars / CHARS_PER_TOKEN_FLOOR
    return (prompt_tokens * in_price + max_output_tokens * out_price) * attempts


class Budget:
    def __init__(self, cap_usd: float, per_call_usd: float = 0.03, attempts: int = 3,
                 expect_usd: float | None = None) -> None:
        # TWO ceilings, because they answer different questions and conflating them is what the
        # second review round caught:
        #   cap_usd     a HARD cap, enforced against each call's computed upper bound. Its job is to
        #               make a catastrophe impossible, not to predict cost, so it is set to the
        #               plan's worst case - about 6x the forecast for a room arm - and in a normal
        #               run it never binds.
        #   expect_usd  a FORECAST ceiling, checked against what has really been billed. Its job is
        #               to stop early when spending runs above expectation, which is how a repriced
        #               model or a retry storm shows up. Optional.
        self.cap = float(cap_usd)
        self.expect = None if expect_usd is None else float(expect_usd)
        self.per_call = float(per_call_usd)
        self.attempts = int(attempts)
        self.spent = 0.0        # actually billed, summed from the provider's own per-call figures
        self.reserved = 0.0     # the worst case of what is in flight right now
        self.calls = 0
        self.refused = 0
        self.overruns: list[str] = []
        self.over_forecast: str | None = None
        self._lock = threading.Lock()

    @property
    def reservation(self) -> float:
        """What one call might cost at worst: every attempt billed."""
        return self.per_call * self.attempts

    @property
    def committed(self) -> float:
        return self.spent + self.reserved

    def should_stop(self) -> str | None:
        """Why the run must not continue, or None. An overrun means the bound was wrong, so the hard
        cap has stopped being a guarantee; over-forecast means costs are above history. Either is a
        reason to stop rather than to carry on and find out."""
        if self.overruns:
            return self.overruns[0]
        return self.over_forecast

    def take(self, what: str = "a call", bound: float | None = None) -> float:
        """Reserve one call's UPPER BOUND, or refuse it. Called BEFORE the call. Returns the amount
        reserved, which must be handed back to `settle` so the same figure is released.

        `bound` is a real upper bound from `bound_for` - pricing, prompt size, the output ceiling and
        the retry limit. With no bound it falls back to the flat per-call estimate, which is a
        FORECAST and not a guarantee; `probe_run` always passes a bound, and the fallback exists for
        tests and for callers that have no prompt yet.
        """
        amount = self.reservation if bound is None else float(bound)
        with self._lock:
            if self.spent + self.reserved + amount > self.cap:
                self.refused += 1
                raise BudgetExhausted(
                    f"refusing {what}: ${self.spent:.4f} billed and ${self.reserved:.4f} in flight, "
                    f"and this call could add up to ${amount:.4f}, which would pass the "
                    f"${self.cap:.2f} cap"
                )
            self.reserved += amount
        return amount

    def settle(self, actual_usd: float | None, reserved: float | None = None) -> None:
        """Release the reservation and record what was really billed. Called after the call whether
        it succeeded or raised: a failed attempt is still charged.

        If the real charge comes in ABOVE the bound that was reserved for it, the bound was wrong -
        a repriced model, a tokenizer denser than the floor, a charge the table does not model. That
        is recorded as an overrun, and `probe_run` stops the run on it, because from that moment the
        cap is no longer a guarantee and pretending otherwise is worse than stopping.
        """
        amount = self.reservation if reserved is None else float(reserved)
        actual = float(actual_usd or 0.0)
        with self._lock:
            self.reserved = max(0.0, self.reserved - amount)
            self.spent += actual
            self.calls += 1
            if self.expect is not None and self.spent > self.expect:
                self.over_forecast = (
                    f"${self.spent:.4f} billed against a forecast ceiling of ${self.expect:.2f}: "
                    f"spending is running above what the measured history predicts"
                )
            if actual > amount + 1e-12:
                self.overruns.append(
                    f"a call was charged ${actual:.4f} against an upper bound of ${amount:.4f}: "
                    f"the price table or the token floor in eval.budget is wrong"
                )

    def __str__(self) -> str:
        return (f"${self.spent:.4f} billed over {self.calls} calls, ${self.reserved:.4f} in flight, "
                f"cap ${self.cap:.2f}" + (f", {self.refused} calls refused" if self.refused else "")
                + (f", {len(self.overruns)} OVERRUNS" if self.overruns else ""))


def metered(ask_fn: Any, budget: Budget) -> tuple[Any, dict[str, float]]:
    """Wrap a model-call function so the cap applies to every call.

    `ask_fn(model, messages, max_tokens, temperature, check)` returns `(checked, usage)` and may
    raise; a raised error carrying `.usage` is still settled, because a failed attempt is billed
    (F-7). The call function is INJECTED rather than imported so this module - and its tests - need
    nothing from the application: importing the harness used to pull in `app.main` and through it
    `app.routers`, which made the test unrunnable from a partial verification package.
    """
    calls = {"n": 0.0, "cost": 0.0, "bound": 0.0}

    async def ask(*, seat: Any = None, messages: Any, model: str, max_tokens: int,
                  temperature: float, check: Any, **_: Any):
        # The bound is computed from THIS call's own prompt, not from an average: the prompt is in
        # hand before the request is made, so its size is known rather than assumed.
        chars = sum(len(str(m.get("content", ""))) for m in (messages or []) if isinstance(m, dict))
        bound = bound_for(model, chars, max_tokens, budget.attempts)
        reserved = budget.take(f"a call for seat {getattr(seat, 'id', 'chair')!r}", bound)
        calls["bound"] += reserved
        usage = None
        try:
            checked, usage = await ask_fn(model, messages, max_tokens, temperature, check)
            return checked, usage
        except Exception as exc:
            usage = getattr(exc, "usage", None)
            raise
        finally:
            cost = getattr(usage, "cost_usd", None)
            budget.settle(cost, reserved)
            calls["n"] += 1
            calls["cost"] += float(cost or 0.0)

    return ask, calls
