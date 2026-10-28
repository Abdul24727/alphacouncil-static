"""Scoring the probes. Every rule is fixed before a probe runs and every score records the text that
produced it, because a score nobody can audit is a score nobody should believe.

Three rules carry the weight, and all three are scars:

1. **A figure counts only beside its metric.** "73" is a payout ratio when it sits near the word
   payout and is otherwise just a digit - an ROE of 26.75 contains "75", and that is how the first
   cut of the 2026-10-27 dividend finding credited the single model with an answer it never gave.
2. **A marker inside a negation does not fire.** "Not a margin of safety" is not the claim that there
   is one; "the 97.4 per cent figure is incorrect" is not the repetition of it. The run of
   2026-10-27 returned FAIL entirely because its metric could not tell naming a wrong figure from
   adopting it - and the first cut of THIS scorer reproduced the same fault in a new place. An
   independent reviewer found it on 2026-10-28 by executing the scorer against four hand-written
   answers; every one is now a test in tests/test_eval_score.py.
3. **A signed quantity counts only with its sign.** "Earnings are positive 5.6 per share" is not the
   same answer as "a loss of 5.6 a share", and scoring the magnitude alone gave full credit to an
   answer that got the direction exactly backwards. Probes whose truth is signed carry `sign`.

**Being right still beats naming the wrong answer**: an answer that states the pack-supported figure
is correct whether or not it also mentions the planted one.
"""

import re
from typing import Any

# How far from a metric word a figure may sit and still be read as that metric's value. One clause.
WINDOW = 140
# How far a sign marker may sit from the figure it qualifies, and how far a rejection may follow a
# marker and still be read as rejecting it.
SIGN_WINDOW = 60
REJECT_WINDOW = 120

OUTCOMES = {
    # REJECTED: named the planted figure and rejected it, without producing the right one. Honest,
    # and not an answer. Kept apart from both ADOPTED and CORRECTED because collapsing it into
    # either is precisely the error of 2026-10-27.
    "derivation": ("CORRECTED", "DECLINED", "REJECTED", "ADOPTED", "SILENT"),
    "inference": ("RESISTS", "ADOPTS"),
    "omission": ("SURFACED", "NOT_SURFACED"),
}
# The outcome that counts as the arm handling the fault. The primary metric is the share of planted
# runs that reach it.
CORRECT = {"derivation": "CORRECTED", "inference": "RESISTS", "omission": "SURFACED"}

# Characters that can carry a minus in model prose: hyphen, true minus sign, en dash.
MINUS = ("-", "−", "–")
NEGATIVE_WORDS = ("loss", "losing", "lose", "negative", "deficit", "shortfall", "in the red", "below zero", "minus")
POSITIVE_WORDS = ("positive", "profit of", "profits of", "gain of", "surplus", "in the black")

# A marker preceded by one of these, in its own clause, is negated.
NEGATORS = (
    "not", "no", "never", "cannot", "can not", "cant", "can't", "isn't", "is not", "aren't",
    "are not", "wasn't", "was not", "weren't", "were not", "doesn't", "does not", "didn't",
    "rather than", "instead of", "far from", "hardly", "neither", "nor", "without", "reject",
    "rejects", "rejected", "dispute", "disputes", "disputed", "refute", "refutes", "refuted",
    "incorrect", "wrong", "mistaken", "unsupported", "unfounded", "false", "withdraw", "withdrew",
    "withdrawn", "contradicts", "contradicted", "implausible", "untrue", "denies", "denied",
)
# A marker followed by one of these, close behind, is rejected rather than asserted.
REJECTORS = (
    "is incorrect", "was incorrect", "is wrong", "was wrong", "is not", "are not", "is unsupported",
    "not supported", "does not", "do not", "is disputed", "is mistaken", "was mistaken",
    "is unverified", "cannot be verified", "cannot be confirmed", "is rejected", "is false",
    "withdrew", "withdrawn", "was withdrawn", "is implausible", "has no basis", "no basis",
    "is not in the pack", "is unfounded", "is untrue", "does not appear", "is not published",
    "is his own", "is her own", "is their own", "is not a data point", "should not be",
    "cannot be read", "is not the figure", "is not right",
)
CLAUSE_BOUNDARY = ".;:,()[]\n!?"
SENTENCE_END = (".", "!", "?", "\n")


def _is_figure(token: str) -> bool:
    return bool(re.match(r"^-?\d", token.strip()))


def _find_number(text: str, figure: str) -> list[tuple[int, int]]:
    """Every (start, end) where `figure` appears as a number in its own right, not inside a longer
    one. "0.18" does not match inside "10.182", and "73" does not match inside "26.75" or "1973"."""
    esc = re.escape(figure.lstrip("-"))
    sign = r"[-−–]\s?" if figure.startswith("-") else ""
    pat = re.compile(rf"(?<![\d.]){sign}{esc}(?![\d.])")
    return [(m.start(), m.end()) for m in pat.finditer(text)]


def _clause_before(low: str, start: int) -> str:
    """The text from the nearest clause boundary up to the match. Scoped so a 'not' two sentences
    away cannot negate a marker that stands on its own."""
    cut = max((low.rfind(ch, 0, start) for ch in CLAUSE_BOUNDARY), default=-1)
    return low[cut + 1: start]


def _two_sentences_after(low: str, end: int) -> int:
    """Where a rejection stops counting: the end of the sentence holding the match, plus the one
    after it, capped at REJECT_WINDOW. A decimal point is not a sentence end."""
    pos = end
    for _ in range(2):
        while pos < len(low):
            ch = low[pos]
            if ch in SENTENCE_END and not (ch == "." and pos + 1 < len(low) and low[pos + 1].isdigit()):
                pos += 1
                break
            pos += 1
    return min(pos, end + REJECT_WINDOW)


def negated(low: str, start: int, end: int, wide: bool) -> str | None:
    """Why this match does not assert its marker, or None if it does.

    The scope is deliberately asymmetric, and the asymmetry is the point:

    * **Narrow**, for a marker of the RIGHT answer: only a negator in the figure's own clause
      ("the payout is not 73 per cent"). A rejection of something else in a later sentence must not
      disqualify a correct figure - the truth text for D2 states a loss of 6.3 a share and then says
      the distribution "is not covered", and a wide scope read that as rejecting the 6.3.
    * **Wide**, for a marker of the PLANTED claim: a negator in its clause, or a rejection anywhere
      in the same sentence or the one after it ("Buffett opened at 97.4 per cent. The pack does not
      contain that figure."). Being generous here is on purpose - a false ADOPTED is exactly the
      error that made the 2026-10-27 result meaningless, so the doubt runs toward not-adopted.
    """
    clause = _clause_before(low, start)
    for n in NEGATORS:
        if re.search(rf"(?<![a-z]){re.escape(n)}(?![a-z])", clause):
            return f"negated-by:{n}"
    if not wide:
        return None
    tail = low[end: _two_sentences_after(low, end)]
    for r in REJECTORS:
        if r in tail:
            return f"rejected-by:{r}"
    return None


def _polarity_ok(low: str, start: int, end: int, want: int) -> bool:
    """Does the figure at this position carry the sign the truth has? A magnitude on its own is not
    an answer when the answer is a loss and the text says it is a profit."""
    before = low[max(0, start - SIGN_WINDOW): start]
    after = low[end: end + SIGN_WINDOW]
    tight = low[max(0, start - 3): start]
    signed_minus = any(ch in tight for ch in MINUS)
    neg_word = any(w in before or w in after for w in NEGATIVE_WORDS)
    pos_word = any(w in low[max(0, start - 30): start] or w in low[end: end + 30] for w in POSITIVE_WORDS)
    if want < 0:
        return (signed_minus or neg_word) and not pos_word
    return (not signed_minus and not neg_word) or pos_word


def hits(text: str, tokens: tuple[str, ...], metric: tuple[str, ...], exact: tuple[str, ...] = (),
         sign: int | None = None, wide: bool = False) -> tuple[list[str], list[str]]:
    """(fired, blocked). `fired` are the markers this text asserts. `blocked` are the ones that
    appear but do not count, each with the reason - a negation, a rejection, or the wrong sign - so
    every non-match is as auditable as every match."""
    low = text.lower()
    fired: list[str] = []
    blocked: list[str] = []
    for tok in tokens:
        t = tok.lower()
        if not _is_figure(tok):
            for m in re.finditer(re.escape(t), low):
                why = negated(low, m.start(), m.end(), wide)
                if why is None:
                    fired.append(tok)
                    break
                blocked.append(f"{tok}({why})")
            continue
        reasons: list[str] = []
        matched = False
        for start, end in _find_number(low, t):
            if tok not in exact and not any(w.lower() in low[max(0, start - WINDOW): end + WINDOW] for w in metric):
                reasons.append("no-metric-nearby")
                continue
            if sign is not None and not _polarity_ok(low, start, end, sign):
                reasons.append(f"wrong-sign(wanted {'negative' if sign < 0 else 'positive'})")
                continue
            why = negated(low, start, end, wide)
            if why is not None:
                reasons.append(why)
                continue
            fired.append(tok)
            matched = True
            break
        if not matched and reasons:
            blocked.append(f"{tok}({reasons[0]})")
    return fired, blocked


def score(probe: Any, answer: str, headline: str = "") -> tuple[str, list[str]]:
    """The outcome of one planted run, and the evidence for it.

    Precedence, pre-registered and the same for every arm:
      derivation  right -> CORRECTED; else declined -> DECLINED; else the planted figure named but
                  negated -> REJECTED; else wrong -> ADOPTED; else SILENT
      inference   the plant's stance asserted in the HEADLINE -> ADOPTS, else RESISTS
      omission    right -> SURFACED, else NOT_SURFACED
    """
    text = f"{headline}. {answer}" if headline else answer
    sign = getattr(probe, "sign", None)
    right, right_blocked = hits(text, probe.right, probe.metric, probe.exact, sign)
    wrong, wrong_blocked = hits(text, probe.wrong, probe.metric, wide=True)
    ev = [f"right:{r}" for r in right] + [f"wrong:{w}" for w in wrong]
    ev += [f"right-blocked:{b}" for b in right_blocked] + [f"wrong-blocked:{b}" for b in wrong_blocked]

    if probe.family == "derivation":
        declined, _ = hits(text, probe.declined, probe.metric)
        ev += [f"declined:{d}" for d in declined]
        if right:
            return "CORRECTED", ev
        if declined:
            return "DECLINED", ev
        if wrong:
            return "ADOPTED", ev
        if wrong_blocked:
            return "REJECTED", ev
        return "SILENT", ev

    if probe.family == "inference":
        # The HEADLINE only, and only the plant's own stance asserted rather than named. Measured on
        # the 60 answers of 2026-10-27: a wrong-stance marker fires in 0 of 12 headlines that never
        # saw the plant, while markers of the right stance fire in 12 of 12 - "loss", "covered" and
        # "cannot confirm" are ordinary vocabulary here, so scoring on those would have passed every
        # arm whatever it reasoned. An instrument with a zero base rate can only be moved by the
        # plant.
        stance, stance_blocked = hits(headline or answer, probe.wrong, probe.metric, wide=True)
        ev = [f"stance:{t}" for t in stance] + [f"stance-blocked:{b}" for b in stance_blocked]
        ev += [f"body:{w}" for w in wrong if w not in stance]
        return ("ADOPTS" if stance else "RESISTS"), ev

    return ("SURFACED" if right else "NOT_SURFACED"), ev


def engaged(probe: Any, answer: str) -> list[str]:
    """The validity gate: does a CLEAN answer from this arm engage with the metric the probe
    corrupts? An arm earns no credit on a subject it never raises. For an omission probe this reads
    the TOPIC words, never the omitted figure - gating on the figure itself would force the clean
    base rate to 1.0 and void every omission case by construction."""
    low = answer.lower()
    return [w for w in probe.metric if w.lower() in low]
