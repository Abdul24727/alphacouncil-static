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


class BudgetExhausted(RuntimeError):
    """Raised in place of making a call that could carry the total past the cap."""


class Budget:
    def __init__(self, cap_usd: float, per_call_usd: float = 0.03, attempts: int = 3) -> None:
        self.cap = float(cap_usd)
        self.per_call = float(per_call_usd)
        self.attempts = int(attempts)
        self.spent = 0.0        # actually billed, summed from the provider's own per-call figures
        self.reserved = 0.0     # the worst case of what is in flight right now
        self.calls = 0
        self.refused = 0
        self._lock = threading.Lock()

    @property
    def reservation(self) -> float:
        """What one call might cost at worst: every attempt billed."""
        return self.per_call * self.attempts

    @property
    def committed(self) -> float:
        return self.spent + self.reserved

    def take(self, what: str = "a call") -> None:
        """Reserve the worst case for one call, or refuse it. Called BEFORE the call."""
        with self._lock:
            if self.committed + self.reservation > self.cap:
                self.refused += 1
                raise BudgetExhausted(
                    f"refusing {what}: ${self.spent:.4f} billed and ${self.reserved:.4f} in flight, "
                    f"and one more call could add ${self.reservation:.4f}, which would pass the "
                    f"${self.cap:.2f} cap"
                )
            self.reserved += self.reservation

    def settle(self, actual_usd: float | None) -> None:
        """Release the reservation and record what was really billed. Called after the call whether
        it succeeded or raised: a failed attempt is still charged."""
        with self._lock:
            self.reserved = max(0.0, self.reserved - self.reservation)
            self.spent += float(actual_usd or 0.0)
            self.calls += 1

    def __str__(self) -> str:
        return (f"${self.spent:.4f} billed over {self.calls} calls, ${self.reserved:.4f} in flight, "
                f"cap ${self.cap:.2f}" + (f", {self.refused} calls refused" if self.refused else ""))
