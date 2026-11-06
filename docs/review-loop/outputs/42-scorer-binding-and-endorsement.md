# Output 42: review 41's three counterexamples, handled by rules instead of word patches

All changes are in `api/eval/score.py`, and all counterexamples are tests in `api/tests/test_eval_score.py`.

1. **Whole words.** `_word_at` matches terms as whole words, so "disagree" is not "agree" and "incorrectly" is not
   "correctly".
2. **Endorsement, both sides, never when negated.**
   - `_attributed(low, start, end)` requires the credit in the figure's own clause. It treats the figure as the
     answer's own if:
     - the clause before holds an un-negated agreeing word (`ENDORSEMENT`); or
     - the rest of the sentence holds a verdict on the claim (`ENDORSEMENT_AFTER`: "is correct", "is right",
       "pack confirms", …).
   - Agreeing verbs are not read after the figure. A calibration test on the 2026-10-27 answers caught that
     version: in "Buffett began with a payout of 97.4 per cent, then accepted that…" the seat is withdrawing.
     The case is now a test as well.
3. **Which quantity a per-share figure is.** `_quantity_kind` reads the nearest naming word in the figure's own
   clause, before and then after it, and else the clauses before it in the same sentence. It never reads a later
   clause.

**Results:**

| Text | Outcome |
|---|---|
| "I disagree with Buffett's claim … 11.8" | CORRECTED |
| "Buffett incorrectly argued … 11.8" | CORRECTED |
| "Buffett's claim … 11.8 per cent is correct" | MIXED |
| "I do not agree with Buffett's claim … 11.8" | CORRECTED |
| "The dividend fell from 2.25 … to 1.1 SAR per share, while earnings cannot be derived" | DECLINED |

Review 40's cases still score MIXED, MIXED and INCORRECT. B/D2 is still DECLINED and B/D4 still CORRECTED.

**The saved analysis:**
- re-scoring the 36 answers moves exactly the same two outcomes against the record as run;
- `probe-results-rescored.jsonl` reproduces exactly;
- no total in the pilot report changes, and its description of both rules is updated.

**Checks:**
- `uv run pytest -q`: 557 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings on these files;
- `git diff --check` is clean.

**The question for the review:** is this sound, and what is the single next pre-approved step?
