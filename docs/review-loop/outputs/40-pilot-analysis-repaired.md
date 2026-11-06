# Output 40: review 39's fixes. The pilot analysis was repaired offline, with no paid calls.

**1. The scorer** (`api/eval/score.py`). Both rules are general, not written to these two answers.
- **A unit is not a metric.** A per-share band no longer judges a figure that is bound only by the unit
  ("per share"), in a sentence that names another per-share quantity (dividend, distribution, DPS, book value,
  payout) and none of the band's own words. A new helper, `_sentence_before`, finds that sentence.
- **Attribution in the noun form.** `ATTRIBUTION` gains "claim that" and "'s claim", with either apostrophe.
- **Tests** (`tests/test_eval_score.py`):
  - both saved answers, quoted: B/D2 → DECLINED and B/D4 → CORRECTED;
  - the other direction: out-of-band earnings per share are still INCORRECT, even beside a dividend, and the
    arm's own 11.8 is still MIXED;
  - a test pinning that re-scoring the 36 saved answers moves exactly these two.

**2. Coverage** (`api/eval/probe_report.py`). The section now prints **missing one or more** and **citing none**
side by side, reading each seat's `owns` from the roster.
- **Scripted openings:** the planted seat's scripted opening in a planted run is left out of both counts and the
  denominator.
- **Tests:** the existing one is updated (2/8 → 1/7, with the reason), and a new one covers partial against no
  coverage.
- **Re-measured from the record:**
  - A: 36 of 66 miss one or more, and 1 of 66 cites none;
  - D: 20 of 42 and 1 of 42.

  These match review 39's 7/72 and 7/48 once its six scripted openings per room are removed.

**3. Reservations:** the per-run **maxima** are now the figures quoted (A $3.971305, D $2.792840, B $0.330336), with
the medians, the dry run and `RUN_BOUND` beside them.

**4. Outcome classes:** the report now says which were seen live and which were not. REJECTED, and the inference
classes ADOPTS, DECLINED and UNRESOLVED, are not validated.

**The record:**
- `docs/eval/probe-results.jsonl` is unaltered, as run.
- `docs/eval/pilot-2026-11-06/probe-results-rescored.jsonl` holds the re-scored answers. Every row is labelled, and
  the changed rows keep `outcome_as_run` and `evidence_as_run`.
- `pilot-report-rescored.txt` reproduces the corrected tables.

**After re-scoring:**
- B handled 5 of 6 with 0 incorrect, and the rooms 4 of 6 each;
- cost per handled answer is 9.4× B's for six seats and 6.9× for four;
- the paired six-against-four reading is unchanged.

`docs/council-pilot-2026-11-06.md`, `PROJECT.md` and output 39 are corrected, each with a dated note.

**Checks:**
- `uv run pytest -q`: 549 passed, 10 skipped;
- `tests/test_eval_score.py` and `tests/test_eval_probe_report.py` pass;
- ruff shows the same 22 pre-existing findings on these files;
- `git diff --check` is clean.

**The question for the review:** is this sound, and what is the single next pre-approved step?
