# Output 44: review 43's step. All 36 pilot answers audited by hand, and the stopping rule now covers every answer.

**The audit** (`docs/eval/pilot-2026-11-06/audit.md`, built from the saved record; the original record and the
re-scored copy are unchanged). Every answer, successes included, was read against its probe's registered truth. Each
row has:
- the scorer's outcome as run, and as re-scored where it moved;
- the human verdict;
- handled or not, and whether a wrong answer reached the member;
- a supporting excerpt in the answer's own words;
- a note.

**Agreement:** 32 of 36. **Disagreements:** 4, all on D5.
- **What D5's markers cannot see:** they recognise the inconsistency only as "inconsistent", "do not agree", "does
  not agree", "cannot both" or "contradict", and the plant only as 51.06. So they cannot see an answer stating that
  the pack's inconsistent figures **agree**.
- **What the answers did:** every clean D5 answer did exactly that.
  - **A** said so in words.
  - **B** said so in its body, though its headline says "disagree". It was first read as a catch and corrected on
    reading the whole answer.
  - **D** derived "price-to-book is 1.24" from 45.32 and 41.18; it is 1.10.
  - **A's planted answer** said the same while rejecting the plant, which the scorer read as ADOPTED.
- **What happens to them:** the human verdicts stand. The scorer is left as registered, and the marker gap goes to
  the owner (item 6 below): extending D5's markers now would be choosing them after reading answers.

**The audited result:**

| Arm | Handled, planted | Handled, clean | Wrong answer, planted | False positive, clean |
|---|---|---|---|---|
| A | 4/6 | 4/6 | 1/6 | 1/6 |
| B | 5/6 | 4/6 | 0/6 | 1/6 |
| D | 4/6 | 4/6 | 1/6 | 1/6 |

- **D5 is the probe that separates answers.** Unprompted, no arm saw the inconsistency. With the plant, only the
  single model said the three figures do not agree; both rooms missed it.
- **Cost per handled answer:** 9.4× B's for six seats and 6.9× for four.
- **Weight:** nothing here decides six against four. It is n = 6, one repeat, with inference at a ceiling.

**The stopping rule** (`docs/council-pilot-2026-11-06.md`, item 5), revised as review 43 asked:
- **What gets audited:** the decision-grade run is reported only after the same audit of **every** answer, planted
  and clean, successes included. Each answer gets a human verdict, an excerpt and the scorer's outcome beside it.
- **How disagreements are settled:** before reporting. A scorer defect becomes a test; a gap in a probe's registered
  markers is recorded, and the human verdict stands.
- **What it costs:** about 180 answers for a 15-probe run.

**Also fixed:** a misplaced line in the report's list of scorer fixes. `PROJECT.md`'s pilot entry now carries the
audited figures.

`git diff --check` is clean. No code changed in this output.

**The question for the review:** is this sound, and what is the single next pre-approved step?
