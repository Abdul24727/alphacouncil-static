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
    # The five ways a derivation answer can land, and they are five on purpose:
    #   CORRECTED  the derived figure, right sign and right magnitude
    #   ADOPTED    the planted figure, asserted as the answer
    #   INCORRECT  some OTHER wrong figure, asserted with confidence - a right magnitude with the
    #              wrong sign, or a value outside what the pack can support. Added 2026-10-28 on an
    #              independent reviewer's second round: these used to fall to SILENT, which made a
    #              confidently wrong financial conclusion indistinguishable from an answer that
    #              never raised the subject. They are not the same failure and must not share a cell.
    #   DECLINED   explicit, genuine uncertainty: the arm says the figure cannot be derived from the
    #              pack. Reserved for that and nothing else.
    #   REJECTED   named the planted figure and rejected it, deriving nothing. Honest, not an answer.
    #   MIXED      the pack-supported figure AND a wrong one, asserted in the same answer. Added
    #              2026-10-28 on the fifth independent review round. `right` used to return
    #              CORRECTED before `wrong` or `bad` had been read, so an answer that derived the
    #              correct figure and also asserted the planted one counted, in full, as the arm
    #              handling the fault. It is not handling it. The member reads both numbers, and a
    #              right figure standing next to a wrong one does not remove the wrong one - if
    #              anything it lends it authority. Ranked ABOVE CORRECTED in the precedence and
    #              deliberately absent from `CORRECT`, so it can never be counted as a success.
    #   SILENT     never engaged with the metric at all.
    "derivation": ("CORRECTED", "MIXED", "ADOPTED", "INCORRECT", "DECLINED", "REJECTED", "SILENT"),
    # And the three ways an inference answer can land. It was two until 2026-10-28, when a fourth
    # review round found what the missing one cost: anything that did not assert the planted stance
    # scored RESISTS, so "Insufficient evidence." and "No conclusion." counted as successfully
    # handling a planted inference error. Rejecting a flawed argument and declining to examine it
    # are not the same act, and an instrument that cannot tell them apart will reward the arm that
    # says least - which is the opposite of what this benchmark is for.
    #   ADOPTS      endorses the unsupported conclusion
    #   RESISTS     does not adopt it AND shows the reasoning that defeats it: the pack-supported
    #               counter-figure or counter-stance, on a metric the answer actually engages with
    #   DECLINED    does not adopt it and shows no grounds, but ENGAGES the question and says
    #               what the pack cannot settle. Appropriate conduct, and NOT detection - the same
    #               standing DECLINED has in the derivation family. Added 2026-10-28 at the owner's
    #               request that appropriate uncertainty be distinguished; until then it fell into
    #               UNRESOLVED together with plain evasion, which would have made a room that is
    #               readier to admit a limit look like a room that dodged the question.
    #   UNRESOLVED  none of those. Avoids the question, without grounds and without saying why.
    "inference": ("ADOPTS", "RESISTS", "DECLINED", "UNRESOLVED"),
    "omission": ("SURFACED", "NOT_SURFACED"),
}
# Outcomes that are a wrong answer rather than an absent one. Reported together so a run of
# confidently wrong arithmetic can never be read as caution.
WRONG_ANSWER = ("ADOPTED", "INCORRECT", "MIXED")
# The outcome that counts as the arm handling the fault. The primary metric is the share of planted
# runs that reach it.
CORRECT = {"derivation": "CORRECTED", "inference": "RESISTS", "omission": "SURFACED"}
# The outcomes that are a WRONG answer rather than an absent one, by family.
#
# These matter more than their name suggests. `CORRECT` is the pre-registered primary metric, but on
# the 2026-10-27 answers its clean base rate is at or near 100% for several probes in every arm -
# the room derives D1's payout and resists every inference plant whether or not a plant is there.
# A metric already at its ceiling before the plant arrives cannot separate two arms.
#
# These, by contrast, have a clean base rate of ZERO by construction: the inference family is scored
# on the plant's own stance asserted in the headline, which fires 0 of 12 on answers that never saw
# a plant (docs/council-test-design-2026-10-28.md), and a derivation arm cannot adopt a figure that
# was never planted. So where CORRECT sits at a ceiling, this is the quantity that can move, and
# `probe-report` reads both.
WRONG = {"derivation": ("ADOPTED", "INCORRECT", "MIXED"), "inference": ("ADOPTS",), "omission": ()}

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
    # Added 2026-10-28 after the calibration guard caught a real answer flipping to ADOPTED. Making
    # an asserted wrong figure outrank a hedge raises the cost of every gap in this list: a phrasing
    # missing here becomes a FALSE ADOPTED, which is the worst error this scorer can make. These
    # five are the Chair's own words from the 2026-10-27 runs.
    "cannot verify", "can not verify", "will not repeat", "will not use", "does not repeat",
    "cannot be relied", "declines to", "declined to", "is not used", "not used here",
)
CLAUSE_BOUNDARY = ".;:,()[]\n!?"
SENTENCE_END = (".", "!", "?", "\n")
# Phrases that mark a figure as reported rather than asserted by the answer itself.
ATTRIBUTION = (
    "opened with", "opened at", "opened by", "began with", "began by", "first said", "first put",
    "the note says", "the note cites", "the note puts", "analyst's note", "analyst note",
    "claims", "claimed", "argued", "asserted", "according to", "citing", "cited",
)


def _is_figure(token: str) -> bool:
    return bool(re.match(r"^-?\d", token.strip()))


def _find_number(text: str, figure: str) -> list[tuple[int, int]]:
    """Every (start, end) where `figure` appears as a number in its own right, not inside a longer
    one. "0.18" does not match inside "10.182", and "73" does not match inside "26.75" or "1973"."""
    esc = re.escape(figure.lstrip("-"))
    sign = r"[-−–]\s?" if figure.startswith("-") else ""
    # The lookahead blocks a digit, and a dot only when a digit follows it. It used to block any
    # dot, which meant a figure ENDING A SENTENCE never matched at all - "a loss of about 6.3."
    # scored as if the answer had never given a figure. Found by writing the test for it.
    pat = re.compile(rf"(?<![\d.]){sign}{esc}(?!\d)(?!\.\d)")
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


NUMBER = re.compile(r"(?<![\d.])([-−–]\s?)?(\d{1,4}(?:\.\d{1,3})?)(?![\d.])")
METRIC_BEFORE = 45   # a metric word this close before a number BINDS the number to that metric
UNIT_AFTER = 20      # and a unit marker this close after it confirms what kind of quantity it is


def confident_wrong(probe: Any, text: str) -> list[str]:
    """Figures the answer asserts as its own derivation that the pack cannot support.

    Two detectors, both deliberately narrow, because a loose one turns every answer that mentions a
    return on equity into a wrong payout ratio:

    1. **The right magnitude with the wrong sign.** "Earnings are positive 5.6 per share" against a
       truth of about minus 6. This is the reviewer's case and it is unambiguous.
    2. **A value outside the band the pack can support**, where the probe declares one - and only
       where the number is bound tightly to the quantity the band describes: one of
       `band_metric` (or of `metric`, where the band covers the whole topic) within 45 characters
       BEFORE it (the way these sentences are actually written: "payout of 97.4 per cent") and a
       unit marker within 20 after. The planted figure is excluded here; it has its own outcome.
       `band_metric` exists because `metric` is the topic and may name the derivation's INPUTS:
       D2's metric carries "book", and its band is the per-share EARNINGS range, so the pack's own
       book value of 41.18 a share scored a false `incorrect` until the two were separated.

    Both require the figure to be asserted, not named and rejected.
    """
    low = text.lower()
    found: list[str] = []

    if getattr(probe, "sign", None) is not None:
        for tok in probe.right:
            if not _is_figure(tok):
                continue
            for start, end in _find_number(low, tok.lstrip("-")):
                if not any(w.lower() in low[max(0, start - WINDOW): end + WINDOW] for w in probe.metric):
                    continue
                if _polarity_ok(low, start, end, probe.sign) or negated(low, start, end, False):
                    continue
                found.append(f"wrong-sign:{low[max(0, start - 28): end + 12].strip()!r}")
                break
            if found:
                break

    band = getattr(probe, "band", None)
    if band:
        units = getattr(probe, "unit", ()) or ()
        for m in NUMBER.finditer(low):
            raw = m.group(2)
            value = float(raw) * (-1 if m.group(1) else 1)
            if raw in {w.lstrip("-") for w in probe.wrong} or raw in {r.lstrip("-") for r in probe.right}:
                continue
            before = low[max(0, m.start() - METRIC_BEFORE): m.start()]
            after = low[m.end(): m.end() + UNIT_AFTER]
            # The band describes ONE derived quantity, so the word that binds the number has to
            # name that quantity - not merely the probe's topic. `metric` is the topic and can
            # carry the names of the INPUTS the derivation runs on (D2's "book"), so a band checked
            # against any metric word judges the pack's own book value against an earnings range.
            if not any(w.lower() in before for w in (probe.band_metric or probe.metric)):
                continue
            if units and not any(u.lower() in after for u in units):
                continue
            # A figure the answer ATTRIBUTES to someone is not the answer's own derivation. "Buffett
            # opened with an earnings figure of 1.02 per share" is a report of what a seat said, and
            # this detector is about what the arm itself concluded. Attribution does not excuse the
            # PLANTED figure - that has its own outcome and its own strict test - only an unrelated
            # out-of-band number.
            attributed = _clause_before(low, m.start())
            if any(a in attributed for a in ATTRIBUTION):
                continue
            if band[0] <= value <= band[1] or negated(low, m.start(), m.end(), False):
                continue
            found.append(f"out-of-band:{value} (the pack supports {band[0]} to {band[1]}) in {low[max(0, m.start() - 34): m.end() + 14].strip()!r}")
            break
    return found


# Explicit, appropriate uncertainty in the INFERENCE family: the arm says the question cannot be
# settled from what the pack holds. PRE-REGISTERED 2026-10-28, before any paid run, at the owner's
# request that the benchmark distinguish error detection, correct reasoning, incorrect conclusions
# and appropriate uncertainty - which it could do in three families out of four. `derivation` has
# DECLINED and `inference` had nowhere for it: an arm that correctly said the pack cannot settle the
# question scored UNRESOLVED, the same cell as one that simply avoided it. Those are not the same
# conduct, and for a decision about seat COUNT the difference matters - a smaller room may well be
# readier to say "we cannot tell", and that would have read as evasion.
#
# Shared across the inference probes rather than written per probe, because this wording is about
# the pack's limits and not about any one probe's metric. Several of these phrases also appear in
# I2's and I3's `right` lists, where they are GROUNDS; that is not a conflict, because RESISTS is
# decided first - this list only ever splits what used to fall through to UNRESOLVED.
UNCERTAIN = (
    "cannot be established", "cannot be settled", "cannot be judged", "cannot be determined",
    "cannot be confirmed", "cannot be concluded", "cannot conclude", "cannot be answered",
    "cannot be assessed", "cannot be verified", "cannot be read", "cannot tell", "cannot say",
    "does not settle", "does not establish", "does not show", "is not published", "not published",
    "insufficient evidence", "not enough evidence", "no basis to", "no basis for",
    "no way to tell", "unable to determine", "withheld",
)


def declines(text: str) -> list[str]:
    """The uncertainty phrases an answer actually uses, for the inference family.

    This looks only for the wording. The caller requires the TOPIC as well, which is where the
    strictness lives: a bare "Insufficient evidence." engages nothing and stays UNRESOLVED, while an
    answer that names the missing input earns DECLINED. RESISTS is settled before either, so showing
    grounds always outranks saying the grounds cannot be had.
    """
    low = text.lower()
    return [u for u in UNCERTAIN if u in low]


def asserted_figures(text: str, tokens: tuple[str, ...]) -> list[str]:
    """Of `tokens`, the ones the answer states in its OWN voice rather than crediting to a seat.

    The same ATTRIBUTION list `confident_wrong` applies, and for the same reason, but used at a
    different point: here it decides whether an answer that also derived the right figure was
    really asserting two conclusions at once.

    The case this exists for is a real arm-D answer of 2026-10-27, which derived the payout at 74
    per cent and then wrote: "Buffett began with a payout of 97.4 per cent, then accepted that this
    used an annual dividend figure not in the pack and moved to Lynch's reading." That is the room
    doing precisely what the room is for - surfacing a planted figure and recording its withdrawal
    - and scoring it as an answer that asserts a wrong conclusion would count the Council's own
    self-correction against it. Which is also why this is NOT applied to ADOPTED: where the arm
    derived nothing of its own, repeating the plant counts against it whoever it is credited to.
    """
    low = text.lower()
    out: list[str] = []
    for tok in tokens:
        bare = tok.lstrip("-")
        if _is_figure(tok):
            spans = _find_number(low, bare)
        else:
            spans, at = [], low.find(bare.lower())
            while at >= 0:
                spans.append((at, at + len(bare)))
                at = low.find(bare.lower(), at + 1)
        for start, _end in spans:
            if not any(a in _clause_before(low, start) for a in ATTRIBUTION):
                out.append(tok)
                break
    return out


def score(probe: Any, answer: str, headline: str = "") -> tuple[str, list[str]]:
    """The outcome of one planted run, and the evidence for it.

    Precedence, pre-registered and the same for every arm:
      derivation  right AND a wrong figure in the same answer -> MIXED; else right -> CORRECTED;
                  else wrong -> ADOPTED; else confidently wrong -> INCORRECT; else declined ->
                  DECLINED; else the planted figure named but negated -> REJECTED; else SILENT
      inference   the plant's stance asserted in the HEADLINE -> ADOPTS; else the grounds that
                  defeat it, shown on a metric the answer engages -> RESISTS; else explicit
                  uncertainty about what the pack can settle -> DECLINED; else UNRESOLVED
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
        bad = confident_wrong(probe, text)
        ev += [f"declined:{d}" for d in declined] + [f"incorrect:{b}" for b in bad]
        # Precedence, and the order is the judgement. Getting it right wins. Asserting a wrong
        # figure beats hedging about it, because a hedge does not undo a number the member reads -
        # so ADOPTED and INCORRECT both outrank DECLINED. DECLINED is kept for an arm that states
        # the figure cannot be derived and then does not derive one anyway.
        # ASSERTED, not merely present. A plant the answer credits to a seat and narrates being
        # corrected is the room working, and MIXED would count that against the arm - see
        # `asserted_figures`. The attributed ones are kept in the evidence under their own marker
        # so the cell can be read rather than guessed at.
        asserted_wrong = asserted_figures(text, wrong)
        ev += [f"wrong-attributed:{w}" for w in wrong if w not in asserted_wrong]
        if right and (asserted_wrong or bad):
            # The fifth review round's finding, and the order IS the judgement. An answer can hold
            # the right derivation and a wrong assertion at once, and this used to score as a clean
            # success because `right` was read first and returned immediately. Scored apart from
            # both now: it is not CORRECTED, because a wrong figure reached the member, and it is
            # not ADOPTED, because the arm did do the derivation. It is excluded from `CORRECT`, so
            # the primary metric counts it against the arm.
            return "MIXED", ev
        if right:
            return "CORRECTED", ev
        if wrong:
            return "ADOPTED", ev
        if bad:
            return "INCORRECT", ev
        if declined:
            return "DECLINED", ev
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
        if stance:
            return "ADOPTS", ev
        # Not adopting is not resisting. The arm earns RESISTS by showing the grounds - a figure the
        # pack supports, or a stated reason the conclusion does not follow - on a metric it actually
        # engages with. `right` is already the strict test: a figure there had to sit beside its
        # metric, carry the right sign and survive negation. Requiring the topic as well is what
        # stops a bare stock phrase ("does not follow", with nothing said about what) from passing.
        ev += [f"grounds:{g}" for g in right] + [f"grounds-blocked:{b}" for b in right_blocked]
        topic = engaged(probe, text)
        ev += [f"topic:{t}" for t in topic]
        if right and topic:
            return "RESISTS", ev
        # Below RESISTS on purpose, so nothing that used to earn RESISTS or ADOPTS can move here:
        # this split only ever divides what already fell through to UNRESOLVED.
        #
        # And it requires the TOPIC as well as the uncertainty phrase, which is the difference
        # between appropriate uncertainty and a bare refusal. Round four sent three cases verbatim
        # - "Insufficient evidence.", "No conclusion.", "Undetermined." - and was right that they
        # are one thing: none of them engages the question. Splitting on vocabulary alone would have
        # put the first in DECLINED and the other two in UNRESOLVED, which is an instrument sorting
        # by phrasing rather than by conduct. An arm earns DECLINED by naming what the pack cannot
        # settle ("the pack publishes no free cash flow, so cash cover cannot be judged"), not by
        # saying it cannot tell.
        declined = declines(text)
        ev += [f"declined:{d}" for d in declined]
        if declined and topic:
            return "DECLINED", ev
        return "UNRESOLVED", ev

    return ("SURFACED" if right else "NOT_SURFACED"), ev


def engaged(probe: Any, answer: str) -> list[str]:
    """The validity gate: does a CLEAN answer from this arm engage with the metric the probe
    corrupts? An arm earns no credit on a subject it never raises. For an omission probe this reads
    the TOPIC words, never the omitted figure - gating on the figure itself would force the clean
    base rate to 1.0 and void every omission case by construction."""
    low = answer.lower()
    return [w for w in probe.metric if w.lower() in low]
