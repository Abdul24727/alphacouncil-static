# Output 47: review 46's correction to the bound's explanation

The explanation was wrong; the figures were right.
- **How reservations work:** every call reserves for all its attempts before it is made, from the size of its own
  prompt (`budget.metered`), dry or live.
- **What does not differ:** dry and live runs make the same number of calls, checked on both records: A 20–21, D
  14–15, B 1.
- **The real cause:** live prompts are longer. The repaired packs are larger, and later rounds carry the transcript
  the seats really wrote (`engine.py`), which a stand-in cannot reproduce.

**Reworded:**
- the `RUN_BOUND` comment in `api/eval/probe_run.py`;
- the pilot report's item 1, which carries a correction note;
- the test plan's re-quote note;
- output 46, with a correction note.

Each now says that $425.68 / $426 is a **planning reservation**, built from the largest reservations seen so far.
It is not a guarantee, because a future transcript can be longer. The spend is guaranteed by the cap the harness
enforces against every call before it is made: a run that would need more stops.

**Unchanged:** the constants, the registered probes and the saved results.

**Checks:**
- the budget and runner tests: 49 passed;
- `git diff --check` is clean.

**The question for the review:** is this sound, and what is the single next pre-approved step?
