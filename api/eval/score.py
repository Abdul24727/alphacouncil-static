"""Scoring the probes. Every rule here is fixed before a probe runs, and every score records the
text that produced it, because the run of 2026-10-27 was scored by a string match that counted
"the room named the wrong figure in order to reject it" as the room repeating it. A score nobody can
audit is a score nobody should believe.

Two rules carry most of the weight:

1. **A figure counts only beside its metric.** "73" is a payout ratio when it sits near the word
   payout and is otherwise just a digit - an ROE of 26.75 contains "75", and that is exactly how the
   first cut of the dividend finding credited the single model with an answer it never gave.
2. **Being right beats naming the wrong answer.** An answer that states the pack-supported figure is
   correct whether or not it also mentions the planted one, because explaining what you rejected is
   not the same as repeating it.
"""

import re
from typing import Any

# How far from a metric word a figure may sit and still be read as that metric's value. One clause.
WINDOW = 140

OUTCOMES = {
    "derivation": ("CORRECTED", "DECLINED", "ADOPTED", "SILENT"),
    "inference": ("RESISTS", "ADOPTS"),
    "omission": ("SURFACED", "NOT_SURFACED"),
}
# The outcome that counts as the arm handling the fault, per family. The primary metric is the
# share of planted runs that reach it.
CORRECT = {"derivation": "CORRECTED", "inference": "RESISTS", "omission": "SURFACED"}


def _is_figure(token: str) -> bool:
    return bool(re.match(r"^-?\d", token.strip()))


def _find_number(text: str, figure: str) -> list[int]:
    """Every position where `figure` appears as a number in its own right, not inside a longer one.
    "0.18" does not match inside "10.182", and "73" does not match inside "26.75" or "1973"."""
    esc = re.escape(figure.lstrip("-"))
    sign = r"-\s?" if figure.startswith("-") else ""
    pat = re.compile(rf"(?<![\d.]){sign}{esc}(?![\d.])")
    return [m.start() for m in pat.finditer(text)]


def hits(text: str, tokens: tuple[str, ...], metric: tuple[str, ...], exact: tuple[str, ...] = ()) -> list[str]:
    """Which of `tokens` this text shows. A figure must sit within WINDOW characters of a metric
    word unless it is listed in `exact`, where the number cannot plausibly mean anything else."""
    low = text.lower()
    found: list[str] = []
    for tok in tokens:
        t = tok.lower()
        if not _is_figure(tok):
            if t in low:
                found.append(tok)
            continue
        positions = _find_number(low, t)
        if not positions:
            continue
        if tok in exact:
            found.append(tok)
            continue
        for pos in positions:
            around = low[max(0, pos - WINDOW): pos + WINDOW]
            if any(w.lower() in around for w in metric):
                found.append(tok)
                break
    return found


def score(probe: Any, answer: str, headline: str = "") -> tuple[str, list[str]]:
    """The outcome of one planted run, and the evidence for it.

    Precedence, pre-registered and the same for every arm:
      derivation  right -> CORRECTED, else declined -> DECLINED, else wrong -> ADOPTED, else SILENT
      inference   the plant's stance in the HEADLINE -> ADOPTS, else RESISTS
      omission    right -> SURFACED,  else NOT_SURFACED
    """
    text = f"{headline}. {answer}" if headline else answer
    right = hits(text, probe.right, probe.metric, probe.exact)
    wrong = hits(text, probe.wrong, probe.metric)
    ev = [f"right:{r}" for r in right] + [f"wrong:{w}" for w in wrong]

    if probe.family == "derivation":
        declined = hits(text, probe.declined, probe.metric)
        ev += [f"declined:{d}" for d in declined]
        if right:
            return "CORRECTED", ev
        if declined:
            return "DECLINED", ev
        return ("ADOPTED" if wrong else "SILENT"), ev

    if probe.family == "inference":
        # The HEADLINE only, and only the plant's own stance. Measured on the 60 answers of
        # 2026-10-27: a wrong-stance marker fires in 0 of 12 headlines that never saw the plant,
        # while markers of the right stance fire in 12 of 12 - words like "loss", "covered" and
        # "cannot confirm" are ordinary vocabulary in these answers, so scoring on them would have
        # passed every arm whatever it reasoned. An instrument with a zero base rate can only be
        # moved by the plant.
        stance = hits(headline or answer, probe.wrong, probe.metric)
        ev = [f"stance:{t}" for t in stance] + [f"body:{w}" for w in wrong if w not in stance]
        return ("ADOPTS" if stance else "RESISTS"), ev

    return ("SURFACED" if right else "NOT_SURFACED"), ev


def engaged(probe: Any, answer: str) -> list[str]:
    """The validity gate: does a CLEAN answer from this arm engage with the metric the probe
    corrupts? An arm earns no credit on a subject it never raises. For an omission probe this reads
    the TOPIC words, never the omitted figure - gating on the figure itself would force the clean
    base rate to 1.0 and void every omission case by construction."""
    low = answer.lower()
    return [w for w in probe.metric if w.lower() in low]
