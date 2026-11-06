# Output 43: review 42's three cases fixed, and a proposed stopping rule for the scorer

**The three fixes** (`api/eval/score.py`; each case is now a test in `api/tests/test_eval_score.py`):
1. **Decimal points.** `_is_boundary` no longer counts a decimal point or a thousands comma between digits as a
   clause boundary. `_clause_before` and a new `_clause_after` use it, and the quantity reader inherits it.
   - "The dividend fell from 2.25 SAR per share to 1.1 SAR per share and earnings cannot be derived" is DECLINED.
   - The 2026-10-27 calibration tests still pass under the widened negation scope.
2. **Verdict scope.** A verdict ("is correct") is read only in the figure's own clause. "Buffett claimed … 11.8 per
   cent, whereas the pack's 2.53 per cent is correct" is CORRECTED.
3. **First-person endorsement.** `ENDORSEMENT_FIRST_PERSON` ("I endorse", "we agree", …) is read to the end of the
   sentence. "…11.8 per cent, which I endorse" is MIXED.
   - The seat-withdrawal case ("…then accepted that…") stays CORRECTED.

**Still correct:**
- all of review 40's and 41's cases;
- B/D2 DECLINED and B/D4 CORRECTED;
- re-scoring the 36 answers moves exactly the same two;
- `probe-results-rescored.jsonl` reproduces exactly, outcome and evidence.

**Checks:**
- `uv run pytest -q`: 560 passed, 10 skipped;
- ruff shows the same 22 pre-existing findings;
- `git diff --check` is clean.

**What the answers say, read by hand.** All 36 pilot verdicts were read after the fixes, and each matches what its
answer says. The details are in `docs/council-pilot-2026-11-06.md`:
- D2 is declined in every arm, and D4 corrected in every arm.
- On D5:
  - B caught the price-to-book inconsistency.
  - A repeated Buffett's 51.06 unchallenged, which is ADOPTED by the pre-registered rule.
  - D's room overruled Lynch's right 1.10, which is MIXED.
- Every planted inference headline resists the plant.

**The proposed stopping rule** (recorded as item 5 of the pilot report's "changes the next run"):
- **Why one is needed:** the scorer reads words, so constructed counterexamples will not run out. Reviews 39–42
  produced five rounds, each now a test.
- **What should make a result trustworthy:** reading the answers. In the decision-grade run, every planted outcome
  other than CORRECTED or RESISTS, and every false positive on a clean run, is read by hand before the result is
  reported. Any disagreement is recorded and becomes a scorer test.
- **What I ask:** that the review accept the scorer on these terms. Further constructed phrasings should be added
  as tests when they turn up in real answers, not chased one patch at a time.

**The question for the review:** is this sound, and what is the single next pre-approved step?
