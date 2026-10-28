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

RESULTS = Path(__file__).resolve().parents[2] / "docs" / "eval" / "results.jsonl"


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
