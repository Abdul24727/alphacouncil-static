# Output 54: reviews 59 and 60, both fixed

**Review 59, on output 52:**
1. **The credit, dated.** Both the lawyer's pack and `docs/launch-check-2026-11-06.md` now record that the owner topped
   up to $37.83, read at 15:30 UTC, and that the monitor's credit check is ok again.
   - **History kept:** the $7.83 reading stays as history in the 12:33/12:40 monitor capture.
   - **The pack's item:** struck through, with a dated "resolved" note.
2. **The private page.** Output 52's claim that creating the private page did not cross the publishing gate is
   withdrawn, with a correction note.
   - **The rule:** `PROJECT.md` §4 gates sending or publishing anything outside the project, whatever its visibility.
   - **What happened:** the page was created and republished twice without a per-action go-ahead. That is recorded as
     a departure and put to the owner.
   - **From now on:** it is not updated again without the owner's go-ahead, and the repository file is the pack of
     record. Today's credit update is therefore **not** on the page.

**Review 60, on output 53.** `docs/council-cost-options-2026-11-06.md` is rewritten from the record, with a
correction note. The figures were recomputed read-only from `docs/eval/probe-results.jsonl`:
- **Companies:** three (2222, 2010, 1120), across five question types.
- **Calls:**
  - A: 21 on clean runs (18 advisor + 3 Chair), 20 on planted runs, where the scripted plant opening is free (17 + 3);
  - D: 15 / 14;
  - B: 1.
- **Cost a run:** A $0.2511 ($0.2204–0.2841), D $0.1870, B $0.0318.
- **The advisor-against-Chair split** is now stated as **not measured**, and the 77 % figure is removed. The
  comparison will record per-turn costs.
- **Option costs:** options 1 and 2 are marked not measured.
- **The comparison:**
  - **Size and cost:** **60 sessions** (15 probes × A and option 2 × planted and clean). A ≈ $7.53; option 2 is a
    guess at $1.50–2.10; **about $9.0–9.6** in all.
  - **The cap:** left open until the prototype's dry run.
  - **What it records:** every displayed turn, per-turn costs, and the time to first words. This needs a harness
    change.
  - **The hand audit:** the final answer, any wrong figure or claim anywhere in the displayed discussion (including
    anything the presenter introduced), and any turn that contradicts the rulings.
  - **Acceptance criteria, written before the run:**
    - handled ≥ A − 1 of 15;
    - no more wrong answers or claims reaching the reader;
    - no more figures absent from the data;
    - measured cost ≤ 40 % of A's;
    - the owner judges the presentation unchanged on beta.
  - **What a pass means:** one repeat is a screening check. A narrow pass calls for a second repeat.
- **Option 2's accuracy** is stated as a hypothesis.
- **The lawyer:** "has not started" in the brief, `PROJECT.md`'s changelog entry and `MASTER-PLAN.md`. The site is
  ready for the review.
- **Output 53** carries a correction note.

`git diff --check` is clean. Documentation only.

**The question for the review:** is this sound, and what is the single next pre-approved step?
