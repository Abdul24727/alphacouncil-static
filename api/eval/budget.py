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
# quietly loosen the cap: the audit in `settle` compares every real charge against the bound this
# table produced and stops the run if the table is ever too low.
PRICES: dict[str, tuple[float, float]] = {           # model: (prompt, completion)
    "anthropic/claude-sonnet-5.5": (2.000e-6, 10.000e-6),
    "deepseek/deepseek-v4-pro": (0.955e-6, 1.911e-6),
    "openai/gpt-5.2": (1.750e-6, 14.000e-6),
}

# --- what `llm.ask` actually does, mirrored here ------------------------------------------------
#
# These four constants are the difference between a bound and an estimate, and the third review
# round was right that the first version missed three of them. They are MIRRORED rather than
# imported because eval.budget must stay importable with no application on the path - that is what
# makes these tests runnable from the verification package. test_eval_budget pins each one against
# app.debate.llm wherever the application IS importable, so raising the reasoning allowance in
# production cannot silently loosen the cap here.
REASONING_ROOM = 2_048          # llm.REASONING_ROOM: added to max_tokens unless reasoning is OFF
RETRY_ECHO_CHARS = 6_000        # llm.ask echoes the unusable reply back, text[:6_000]
RETRY_INSTRUCTION_CHARS = 400   # plus the correction sentence, generously rounded up
# llm.ask retries a 400 "reasoning is mandatory" WITHOUT incrementing its attempt counter, so one
# call can issue ATTEMPTS + 1 requests. That request carries the original prompt, not a grown one.
EXTRA_REQUESTS = 1
# Chat-template framing per message - role markers and separators. Generous: real templates spend
# 3-4 tokens a message.
MESSAGE_OVERHEAD_TOKENS = 8

RETRY_GROWTH_BYTES = RETRY_ECHO_CHARS + RETRY_INSTRUCTION_CHARS


def token_bound(prompt_bytes: int, messages: int = 2) -> int:
    """An upper bound on a prompt's token count, from its length in UTF-8 BYTES.

    Why bytes and not characters. The first version of this file assumed a floor of 2 characters per
    token. The third review round said that was not established, and they were right - it is an
    average dressed as a bound, and Arabic, which these prompts carry, is 2 bytes per character
    before the tokenizer sees it, so a 2-chars-per-token "floor" can be beaten by ordinary text.

    A byte-level BPE tokenizer cannot emit more tokens than the input has bytes: its base vocabulary
    is the 256 single bytes, and every merge replaces two adjacent tokens with one, so the token
    count starts at the byte count and only ever falls. That is a structural property of the
    algorithm, not a measurement, and it is the assumption this bound rests on - stated plainly
    because it is an assumption about the provider's tokenizer, which is not published for every
    model here.

    It is not left as an assumption at runtime. `metered` compares the prompt_tokens the provider
    reports against this bound on every single call and records an overrun if it is ever exceeded,
    which stops the run. So if the assumption is wrong, the first call says so and nothing further
    is spent.
    """
    return prompt_bytes + messages * MESSAGE_OVERHEAD_TOKENS


def price(model: str) -> tuple[float, float]:
    try:
        return PRICES[model]
    except KeyError:
        raise PriceUnknown(
            f"no price for {model!r}, so no upper bound can be computed and no call will be made. "
            f"Add it to eval.budget.PRICES from OpenRouter's /api/v1/models."
        ) from None


def bound_for(model: str, prompt_bytes: int, max_output_tokens: int, attempts: int = 3, *,
              messages: int = 2, reasoning: bool = True, retries_grow: bool = True) -> float:
    """The most one `llm.ask` can be charged, from the four inputs the review named - model pricing,
    input size, the maximum output tokens and the retry limit - plus the three things the first
    version of this function missed:

    * **The reasoning allowance.** `llm.ask` sends `max_tokens + REASONING_ROOM` unless reasoning is
      explicitly disabled, and Sonnet 5.5 on OpenRouter *refuses* the request with reasoning off, so
      the chair's own model takes the larger ceiling. The bound assumes the larger one.
    * **Retry prompt growth.** A retry is not the same request again: `llm.ask` appends the unusable
      reply (up to 6,000 characters) and a correction instruction, so request 2 carries a bigger
      prompt than request 1 and request 3 bigger still. Multiplying one prompt by three undercounts.
    * **The fourth request.** The 400-on-reasoning retry does not increment the attempt counter.

    `prompt_bytes` is the prompt's length in UTF-8 bytes - see `token_bound` for why bytes.

    This is the number the hard cap is enforced against, and it is nothing like a forecast: for a
    real arm-B call of 2026-10-27 it is about **fourteen times** what the call was billed. That gap
    is what a guarantee costs, and the two numbers are reported separately everywhere precisely so
    the one cannot be mistaken for the other.
    """
    in_price, out_price = price(model)
    out_tokens = max_output_tokens + (REASONING_ROOM if reasoning else 0)
    return sum(token_bound(b, m) * in_price + out_tokens * out_price
               for b, m in _requests(prompt_bytes, attempts, messages, retries_grow))


def _requests(prompt_bytes: int, attempts: int, messages: int,
              retries_grow: bool = True) -> list[tuple[int, int]]:
    """The (bytes, message count) every request one `llm.ask` may issue carries: EXTRA_REQUESTS at
    the original size, then one per attempt, each grown by the echoed reply and its two extra
    messages. Exact rather than loose - over-counting here would inflate the cap the owner has to
    authorise, and a bound padded with slack is a bound nobody will set."""
    grow, msgs = (RETRY_GROWTH_BYTES, 2) if retries_grow else (0, 0)
    return ([(prompt_bytes, messages)] * EXTRA_REQUESTS
            + [(prompt_bytes + i * grow, messages + msgs * i) for i in range(attempts)])


def prompt_token_ceiling(prompt_bytes: int, attempts: int = 3, messages: int = 2) -> int:
    """The most prompt tokens one `llm.ask` can report in total, summed over every request it may
    issue. `Usage.prompt_tokens` accumulates across attempts, so this is the figure the runtime
    audit compares it against - the whole call's ceiling, not one request's."""
    return sum(token_bound(b, m) for b, m in _requests(prompt_bytes, attempts, messages))


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

    def take(self, what: str = "a call", bound: float | None = None, *,
             allow_forecast: bool = False) -> float:
        """Reserve one call's UPPER BOUND, or refuse it. Called BEFORE the call. Returns the amount
        reserved, which must be handed back to `settle` so the same figure is released.

        `bound` is a real upper bound from `bound_for` - pricing, prompt size, the output ceiling and
        the retry limit.

        **Omitting it raises.** It used to fall back to the flat per-call forecast, and the third
        review round found what that was worth: arms B and E called `take()` with no bound at all,
        so the two single-model arms reserved a flat $0.09 each and bypassed the guarantee the rest
        of the harness was built around. A silent fallback inside a guarantee is the F-10 fault
        again - a safety check that is trusted and does nothing. So the fallback is now opt-in by
        name, `allow_forecast=True`, which no production path passes and which says in the caller
        what it is giving up.
        """
        if bound is None and not allow_forecast:
            raise PriceUnknown(
                f"refusing {what}: no upper bound was computed for it. Pass a bound from "
                f"bound_for(), or allow_forecast=True to reserve the flat per-call estimate and "
                f"give up the hard-cap guarantee."
            )
        amount = self.reservation if bound is None else float(bound)
        with self._lock:
            # A stop reason already recorded means the cap is no longer a guarantee (an overrun) or
            # spending has passed what history predicts. Either way nothing further is admitted:
            # should_stop() used to be advisory, and a runner that only checked `refused` would
            # carry on calling right through an overrun.
            stop = self.overruns[0] if self.overruns else self.over_forecast
            if stop:
                self.refused += 1
                raise BudgetExhausted(f"refusing {what}: {stop}")
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

    def audit_tokens(self, prompt_tokens: int | None, ceiling: int) -> None:
        """Check the provider's own reported prompt token count against the bound `token_bound`
        assumed, and record an overrun if the assumption was wrong.

        This is what keeps the one-token-per-byte assumption from being merely asserted. The third
        review round said it was "not established", which was fair - it rests on a structural
        property of byte-level BPE that is not published for every model here. So it is checked on
        every call against what the provider actually billed tokens for, and the first violation
        stops the run through `should_stop`. An assumption that fails loudly on its first counter-
        example is a different thing from an assumption nobody ever tests.
        """
        if not prompt_tokens or prompt_tokens <= ceiling:
            return
        with self._lock:
            self.overruns.append(
                f"a call reported {prompt_tokens} prompt tokens against a ceiling of {ceiling}: "
                f"the tokenizer is denser than one token per UTF-8 byte, so every bound computed "
                f"by eval.budget is too low"
            )

    def __str__(self) -> str:
        return (f"${self.spent:.4f} billed over {self.calls} calls, ${self.reserved:.4f} in flight, "
                f"cap ${self.cap:.2f}" + (f", {self.refused} calls refused" if self.refused else "")
                + (f", {len(self.overruns)} OVERRUNS" if self.overruns else ""))


def metered(ask_fn: Any, budget: Budget) -> tuple[Any, dict[str, float]]:
    """Wrap an asker so the cap applies to every call, whatever the asker is.

    A transparent pass-through: every keyword reaches `ask_fn` untouched, so this wraps the real
    `llm.ask`, the single-model arms, and the stand-in used by `--dry` without any of them knowing.
    That matters more than it looks. The third review round found that arms B and E reserved a flat
    forecast instead of a bound, and the reason they could is that they had a metering path of their
    own, written inline. There is now ONE path: a call that is not metered is a call that was not
    made. `--dry` goes through it too, which is why the plan's published maximum is exactly the sum
    of the reservations a paid run would take rather than a figure computed beside it.

    `ask_fn(**kw)` returns `(checked, usage)` and may raise; a raised error carrying `.usage` is
    still settled, because a failed attempt is billed (F-7). The asker is INJECTED rather than
    imported so this module - and its tests - need nothing from the application.
    """
    calls = {"n": 0.0, "cost": 0.0, "bound": 0.0}

    async def ask(**kw: Any):
        messages, model = kw.get("messages"), kw["model"]
        max_tokens, seat = kw["max_tokens"], kw.get("seat")
        # The bound is computed from THIS call's own prompt, not from an average: the prompt is in
        # hand before the request is made, so its size is known rather than assumed. Bytes, not
        # characters - see token_bound.
        msgs = [m for m in (messages or []) if isinstance(m, dict)]
        prompt_bytes = sum(len(str(m.get("content", "")).encode("utf-8")) for m in msgs)
        n_messages = max(len(msgs), 1)
        bound = bound_for(model, prompt_bytes, max_tokens, budget.attempts, messages=n_messages)
        ceiling = prompt_token_ceiling(prompt_bytes, budget.attempts, n_messages)
        reserved = budget.take(f"a call for seat {getattr(seat, 'id', 'chair')!r}", bound)
        calls["bound"] += reserved
        usage = None
        try:
            checked, usage = await ask_fn(**kw)
            return checked, usage
        except Exception as exc:
            usage = getattr(exc, "usage", None)
            raise
        finally:
            cost = getattr(usage, "cost_usd", None)
            # Before settling: was the token assumption the bound rests on actually true for this
            # call? A denser tokenizer than the floor makes every bound too low, so it is recorded
            # as an overrun and the run stops rather than continuing inside a broken guarantee.
            budget.audit_tokens(getattr(usage, "prompt_tokens", None), ceiling)
            budget.settle(cost, reserved)
            calls["n"] += 1
            calls["cost"] += float(cost or 0.0)

    return ask, calls
