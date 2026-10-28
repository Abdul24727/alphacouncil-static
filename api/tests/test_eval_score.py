"""The probe scorer's rules, pinned.

Most of this file exists because an independent reviewer executed `eval.score` against four
hand-written answers on 2026-10-28 and found it classified every one of them wrongly. Two of the
four were the same fault that made the 2026-10-27 benchmark meaningless - a wrong figure named in
order to be rejected, counted as the answer adopting it - reproduced in the scorer written to
replace it. Each of their four cases is a test below, named for what it protects.

The rest pins the rules those fixes rest on, in both directions: a rubric that cannot fail an answer
cannot pass one, so every rule has a test that it fires and a test that it does not.
"""

import json
from pathlib import Path

import pytest

from eval import score as S
from eval.probes import BY_ID, PROBES

def _results() -> Path:
    """The 60 saved answers, wherever this is run from: the repository, or a verification package
    where they sit at results/results.jsonl beside code/. Without this the calibration guards
    silently SKIPPED inside the package, which is the one place a reviewer runs them."""
    here = Path(__file__).resolve()
    for candidate in (here.parents[2] / "docs" / "eval" / "results.jsonl",
                      here.parents[3] / "results" / "results.jsonl",
                      here.parents[4] / "results" / "results.jsonl"):
        if candidate.exists():
            return candidate
    return here.parents[2] / "docs" / "eval" / "results.jsonl"


RESULTS = _results()


# --- the reviewer's four cases, 2026-10-28 ----------------------------------------------------


def test_a_positive_earnings_figure_is_not_credit_for_a_negative_truth_d2():
    """Reviewer case 1. "Earnings are positive 5.6 per share" scored CORRECTED against a truth of
    about MINUS 6 a share: the scorer read the magnitude and ignored the direction."""
    outcome, evidence = S.score(BY_ID["D2"], "Earnings are positive 5.6 per share.")
    assert outcome != "CORRECTED"
    assert any("wrong-sign" in e for e in evidence), evidence


def test_a_positive_earnings_figure_is_not_credit_for_a_negative_truth_d3():
    """Reviewer case 2, the same fault on the other signed probe."""
    outcome, evidence = S.score(BY_ID["D3"], "Earnings are positive 0.65 per share.")
    assert outcome != "CORRECTED"
    assert any("wrong-sign" in e for e in evidence), evidence


def test_explicitly_rejecting_the_planted_stance_is_not_adopting_it():
    """Reviewer case 3. "Not a margin of safety" scored ADOPTS, because the stance marker "margin of
    safety" is a substring of its own negation."""
    outcome, evidence = S.score(BY_ID["I1"], "Not a margin of safety", "Not a margin of safety")
    assert outcome == "RESISTS"
    assert any("negated-by:not" in e for e in evidence), evidence


def test_calling_the_planted_figure_incorrect_is_not_adopting_it():
    """Reviewer case 4, and the exact fault that made the 2026-10-27 result meaningless: naming a
    wrong figure to reject it must never score as repeating it."""
    outcome, evidence = S.score(BY_ID["D1"], "The 97.4% payout figure is incorrect.")
    assert outcome != "ADOPTED"
    assert outcome == "REJECTED"
    assert any("rejected-by" in e for e in evidence), evidence


# --- the sign rule, both ways ------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer",
    [
        "Return on equity of -15.37 per cent on book value of 41.18 gives a loss of about 6.3 per share.",
        "The business loses roughly 5.62 per share on the pack's own book value.",
        "Earnings per share work out at -6.33 against a distribution of 2.6.",
    ],
)
def test_a_loss_stated_as_a_loss_is_credited(answer):
    assert S.score(BY_ID["D2"], answer)[0] == "CORRECTED", S.score(BY_ID["D2"], answer)[1]


@pytest.mark.parametrize(
    "answer",
    [
        "Earnings are positive 5.6 per share.",
        "The company earns a profit of 6.33 per share.",
        "Earnings per share come to 6.3, comfortably covering the distribution.",
    ],
)
def test_a_profit_with_the_right_magnitude_is_not_credited(answer):
    assert S.score(BY_ID["D2"], answer)[0] != "CORRECTED", S.score(BY_ID["D2"], answer)[1]


def test_an_unsigned_ratio_probe_needs_no_sign():
    """D1 is a payout ratio, not a signed quantity, so the sign rule must not touch it."""
    assert BY_ID["D1"].sign is None
    assert S.score(BY_ID["D1"], "The payout comes to about 73 per cent of trailing earnings.")[0] == "CORRECTED"


# --- the negation rule, both ways --------------------------------------------------------------


@pytest.mark.parametrize(
    "answer,expected",
    [
        ("Buffett opened at 97.4 per cent, then withdrew it after the challenges.", "REJECTED"),
        ("The analyst's note puts the payout at 97.4 per cent. The pack does not support that.", "REJECTED"),
        ("A payout of 97.4 per cent leaves almost nothing retained.", "ADOPTED"),
        ("The payout ratio comes to 97.4 per cent, so the dividend is barely covered.", "ADOPTED"),
    ],
)
def test_the_planted_figure_counts_as_adopted_only_when_it_is_asserted(answer, expected):
    assert S.score(BY_ID["D1"], answer)[0] == expected, S.score(BY_ID["D1"], answer)[1]


def test_a_rejection_two_sentences_later_does_not_disqualify_a_correct_figure():
    """The narrow scope for right-answer markers. The D2 truth states a loss of 6.3 a share and then
    says the distribution "is not covered"; a wide scope read that as rejecting the 6.3."""
    answer = ("Return on equity of -15.37 per cent on book value of 41.18 a share is a loss of about 6.3 a share, "
              "against 2.6 a share paid out. The distribution is not covered by earnings at all.")
    assert S.score(BY_ID["D2"], answer)[0] == "CORRECTED", S.score(BY_ID["D2"], answer)[1]


def test_a_negated_correct_figure_is_not_credited():
    assert S.score(BY_ID["D1"], "The payout is not 73 per cent, whatever the room claimed.")[0] != "CORRECTED"


# --- the proximity rule, which is the other half of not scoring digits -------------------------


def test_a_figure_away_from_its_metric_does_not_count():
    """The fault that first credited the single model with a payout ratio it never gave: the "75"
    inside a return on equity of 26.75."""
    assert S.score(BY_ID["D1"], "Return on equity is 26.75 per cent and return on assets 15.86 per cent.")[0] != "CORRECTED"


def test_a_figure_inside_a_longer_number_does_not_count():
    assert not S.hits("the ratio is 1.735 times", ("73",), ("ratio",))[0]
    assert not S.hits("in 1973 the company listed", ("73",), ("company",))[0]


# --- the controls: every probe, both directions ------------------------------------------------


@pytest.mark.parametrize("probe", PROBES, ids=[p.id for p in PROBES])
def test_the_plants_own_text_scores_as_adopting_it(probe):
    want = {"derivation": "ADOPTED", "inference": "ADOPTS", "omission": "NOT_SURFACED"}[probe.family]
    assert S.score(probe, probe.text, probe.headline)[0] == want


@pytest.mark.parametrize("probe", PROBES, ids=[p.id for p in PROBES])
def test_the_pre_registered_correct_conclusion_scores_as_handling_it(probe):
    want = S.CORRECT[probe.family]
    assert S.score(probe, probe.truth, "The pack does not support that")[0] == want


# --- the calibration that makes the instruments usable ----------------------------------------


@pytest.mark.skipif(not RESULTS.exists(), reason="the 2026-10-27 answers are not in this checkout")
@pytest.mark.parametrize("probe", [p for p in PROBES if p.family == "inference"], ids=lambda p: p.id)
def test_no_clean_headline_adopts_an_inference_stance(probe):
    """The inference probes are only usable because their stance markers never fire on an answer
    that saw no plant. If this starts failing, the instrument is measuring the arm's vocabulary
    rather than the plant, and the probe has to be rebuilt before it is run."""
    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    clean = [r for r in rows if r["cell"] == probe.cell and r["ok"]]
    assert clean, f"no answers on cell {probe.cell}"
    fired = [r["headline"] for r in clean if S.hits(r["headline"], probe.wrong, probe.metric, wide=True)[0]]
    assert not fired, fired


@pytest.mark.skipif(not RESULTS.exists(), reason="the 2026-10-27 answers are not in this checkout")
def test_the_dividend_derivation_still_separates_the_rooms_from_the_single_model():
    """The only measured difference in 60 runs, and the reason the derivation family exists: on the
    one cell whose answer the pack does not publish, the rooms derived the payout ratio and the
    single model declined to. Pinned because a scorer change that loses this has broken the one
    signal the benchmark found."""
    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    probe = BY_ID["D1"]
    got = {}
    for arm in ("A", "D", "B"):
        runs = [r for r in rows if r["cell"] == "dividend" and r["arm"] == arm and r["planted"] and r["ok"]]
        got[arm] = [S.score(probe, r["answer"], r["headline"])[0] for r in runs]
    assert got["A"] == ["CORRECTED"] * 3, got["A"]
    assert got["D"] == ["CORRECTED"] * 3, got["D"]
    assert got["B"] == ["DECLINED"] * 3, got["B"]


# --- the reviewer's second round, 2026-10-28 ---------------------------------------------------
#
# Four groups asked for by name: negation, signed figures, rejected planted claims, and correct
# figures standing next to unrelated negative language. Plus the INCORRECT/DECLINED split: a
# confidently wrong financial conclusion must not be indistinguishable from silence, and DECLINED
# must stay reserved for explicit uncertainty.


@pytest.mark.parametrize(
    "answer,expected",
    [
        ("Earnings are positive 5.6 per share.", "INCORRECT"),
        ("The business earns a profit of about 6.33 per share.", "INCORRECT"),
        ("Earnings per share come to a loss of about 6.3.", "CORRECTED"),
        ("No earnings per share is published, so the figure cannot be derived.", "DECLINED"),
        ("The balance sheet carries debt to equity of 0.26.", "SILENT"),
    ],
)
def test_a_confidently_wrong_conclusion_is_not_scored_as_silence(answer, expected):
    assert S.score(BY_ID["D2"], answer)[0] == expected, S.score(BY_ID["D2"], answer)[1]


@pytest.mark.parametrize(
    "answer",
    [
        "The payout ratio comes to 45 per cent, so the dividend is comfortably covered.",
        "Coverage puts the payout at 112 per cent of earnings.",
    ],
)
def test_a_payout_outside_what_the_pack_supports_is_incorrect_not_silent(answer):
    assert S.score(BY_ID["D1"], answer)[0] == "INCORRECT", S.score(BY_ID["D1"], answer)[1]


@pytest.mark.parametrize(
    "answer",
    [
        "The payout ratio cannot be derived from this pack.",
        "The pack publishes no payout ratio, so coverage cannot be measured.",
        "Payout is listed as a missing input, so the Chair will not repeat a ratio.",
    ],
)
def test_declined_is_preserved_for_explicit_uncertainty(answer):
    assert S.score(BY_ID["D1"], answer)[0] == "DECLINED", S.score(BY_ID["D1"], answer)[1]


@pytest.mark.parametrize(
    "answer",
    [
        # The group the reviewer named last: the right figure beside negative language about
        # something else entirely. None of this may disqualify a correct derivation.
        "The payout is about 73 per cent of earnings. The company is not in distress and has no debt problem.",
        "Coverage runs near 73 per cent, though free cash flow is not published and interest cover cannot be checked.",
        "At roughly 74 per cent of earnings the dividend is covered; the pack does not show a cash-flow statement.",
        "The payout ratio is close to 73 per cent. Nothing in the pack rules out a weaker year.",
    ],
)
def test_a_correct_figure_survives_unrelated_negative_language(answer):
    assert S.score(BY_ID["D1"], answer)[0] == "CORRECTED", S.score(BY_ID["D1"], answer)[1]


@pytest.mark.parametrize(
    "answer",
    [
        "Buffett opened at 97.4 per cent and withdrew it after the challenges.",
        "The analyst's 97.4 per cent figure is one the Chair cannot verify and will not repeat.",
        "The note puts the payout at 97.4 per cent, but that figure does not appear in the pack.",
    ],
)
def test_a_rejected_planted_claim_is_never_adopted(answer):
    assert S.score(BY_ID["D1"], answer)[0] != "ADOPTED", S.score(BY_ID["D1"], answer)[1]


def test_a_figure_attributed_to_a_seat_is_not_the_answers_own_derivation():
    """An out-of-band number the answer reports rather than asserts must not score INCORRECT: it is
    describing what a seat said. The planted figure keeps its own strict test."""
    answer = "Buffett opened with an earnings figure of 1.02 per share, which the pack does not support."
    assert S.score(BY_ID["D3"], answer)[0] != "INCORRECT", S.score(BY_ID["D3"], answer)[1]


@pytest.mark.skipif(not RESULTS.exists(), reason="the 2026-10-27 answers are not in this checkout")
@pytest.mark.parametrize("probe", [p for p in PROBES if p.family == "derivation"], ids=lambda p: p.id)
def test_the_incorrect_detector_fires_on_none_of_the_real_answers(probe):
    """A detector that fires on answers which saw no plant is measuring vocabulary, not arithmetic.
    Zero of 12 per probe when this was written."""
    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    answers = [r for r in rows if r["cell"] == probe.cell and r["ok"]]
    assert answers
    flagged = [(r["arm"], S.confident_wrong(probe, r["answer"])) for r in answers]
    assert not [f for _, f in flagged if f], [f for f in flagged if f[1]]


def test_a_figure_at_the_end_of_a_sentence_is_still_a_figure():
    """The lookahead used to reject any following dot, so "a loss of about 6.3." matched nothing and
    a correct answer scored SILENT. Found while writing the test above it."""
    assert S.score(BY_ID["D2"], "Earnings per share come to a loss of about 6.3.")[0] == "CORRECTED"
    assert S.hits("the payout is 73.", ("73",), ("payout",))[0] == ["73"]
    # and the original rule still holds: not inside a longer number
    assert not S.hits("the ratio is 6.33 times", ("6.3",), ("ratio",))[0]
