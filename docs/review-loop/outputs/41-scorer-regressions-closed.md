# Output 41: review 40's two scorer regressions, closed

Both are in `api/eval/score.py`, and both counterexamples are now tests in `api/tests/test_eval_score.py`.

1. **Attribution is the possessive only, and an endorsement cancels it.**
   - `ATTRIBUTION` keeps "'s claim" (either apostrophe) and drops the bare "claim that", which matched the answer's
     own voice.
   - A new `ENDORSEMENT` list ("agree", "accept", "endorse", "rightly", "is correct", "confirms", "I adopt" and so
     on) makes a clause that credits a figure and then endorses it count as asserted.
   - A new `_attributed()` holds that rule for both callers, `asserted_figures` and the band detector.
   - **Results:**
     - "I claim that the return on assets is 11.8 per cent" scores MIXED;
     - "I agree with Buffett's claim that … 11.8 per cent" scores MIXED;
     - the pilot's B/D4 answer, which rules against the claim, stays CORRECTED.
2. **The dividend exception reads the whole sentence.** A new `_sentence_after()` adds the text after the figure to
   the text before it.
   - "The dividend is 2.25 SAR per share, while 1.1 SAR per share is the earnings figure" scores INCORRECT.
   - The pilot's B/D2 dividend sentence stays DECLINED.

**The saved analysis is reconciled:**
- re-scoring all 36 answers still moves exactly the same two, against the record as run;
- `probe-results-rescored.jsonl` reproduces exactly, outcome and evidence;
- no total in `pilot-report-rescored.txt` or `docs/council-pilot-2026-11-06.md` changes;
- the pilot report's description of both fixes is updated, citing review 40.

**Checks:**
- `uv run pytest -q tests/test_eval_score.py tests/test_eval_probe_report.py`: 145 passed;
- the whole suite: 551 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings on these files;
- `git diff --check` is clean.

**The question for the review:** is this sound, and what is the single next pre-approved step?
