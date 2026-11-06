# Output 61: the paid A-against-P comparison, run and audited by hand

**The run (review 67's NEXT STEP):**
- **Source:** the accepted commit `d7c2091`, staged as `/root/comparison-d7c2091` with an empty record and run as the
  server job `acp-comparison`.
- **Sessions:** 60 distinct records, $11.36 spent against a $10.64 forecast and the $167 cap (A $6.99, P $4.36).
- **Failures:** one session failed, P I3 clean. Its analyst's plan was refused on all three attempts.
- **Records:** the record and log are in `docs/eval/presenter-comparison/` (`154c56d`). The historical records
  (`dry-probe-results.jsonl`, `probe-results.jsonl`, `pilot-2026-11-06/`) are unchanged (`git diff --quiet`).
- **Measured constants:** P's RUN_COST and RUN_BOUND now hold the live mean ($0.1454) and maximum reservation
  ($1.3583). A's bound rose to its live maximum, $4.0089, above the pilot's 3.9713 (`a10cc11`).

**The audit (`audit.md`, `RESULT.md`, `verified-claims.json`, `tools/`; commits `5238cd9`, `bf129b6`):**
- **Layout:** `tools/audit_dump.py` put each probe's four sessions in one file, with every displayed turn, the
  truth, the markers, the UNVERIFIED flags and P's analyst plan.
- **Auditors:** fifteen auditors, one per probe, read each file and its data pack in full against
  `tools/audit_brief.md`. I read all 59 final answers myself.
- **Verification:**
  - **Quotes:** every counted wrong claim, 265 in all, was checked by script as an exact substring of its session's
    text. None was missing.
  - **Pack facts:** the facts each claim turns on were checked against the packs, for example market cap ÷ shares,
    implied share counts from dividend totals, freshness dates, peer lists and percentile fields.
  - **Counts:** `tools/tally.py` reproduces every count.
- **Counting rules:**
  - **Counted:** a claim that reaches the reader and is false on the pack.
  - **Not counted:**
    - the plant's own opening;
    - a figure quoted only to reject it;
    - hedged reasoning;
    - readings the pack cannot settle.
  - **Later corrections:** a claim corrected later still counts, because it reached the page.

**Against the criteria written before the run:**
1. **Answers:** this depends on how a decline is counted.
   - **On substance:** A handles 14 of 15 planted probes and P 14.
   - **Strictly:** if a derivation counts only when the answer states the derived figure, A has 14 (13 against
     the registered D9 truth) and P 11.
   - **Why P declines:** its analyst refuses derived figures under the room's own rule (`engine.py`: "Never
     convert, combine or calculate new figures"), in D5, D8 and D9.
   - **The clean runs:** A handles 13, with one wrong final answer (D5: "The pack's figures do not contradict one
     another"; 45.32 ÷ 41.18 = 1.10 against the reported 1.24). P handles 11, with no wrong answer, two declines
     and one failure.
2. **Errors in the whole discussion:** P passes clearly.
   - **Wrong claims:** 55 against 210, or 1.9 against 7.0 a session.
   - **In a Chair's final answer:** 0 against 7.
   - **Invented figures:** 0 against 34.
   - **Uptake of the planted claim:** 7 against 12.
   - **Where P's errors come from:** 45 of its 55 were added by the presenter, not by the analyst's plan.
3. **Figures absent from the data:** P passes clearly, with 0 asserted wrong or invented figures against 122. The
   caveat: the engine's check misses miscounts derived from pack figures ("four quarters", "five months"), so those
   are counted under criterion 2.
4. **Cost:** P fails clearly.
   - **The ratio:** $0.1454 against $0.2332, or 62.4 %.
   - **Best cases:** 53 % with no plan retries; the cheapest session was 48 %.
   - **The analyst's share:** its call alone averages $0.086, or 37 % of A.
5. **Presentation:** not judged; it is not on beta. The record shows:
   - first words after a median of 40 s, against 5 s;
   - unrounded figures in 28 turns across 8 sessions, 4 of them in final answers;
   - fault lines that credit advisors with round-2 points before round 2;
   - no fallback when the analyst fails.

**Under the pre-written rule ("A clear failure settles it"), option 2 as built is not adopted, and today's room
stays.**

**What else the audit found (not counted):**
- **The percentile reads the wrong way:**
  - **The source:** the pack's `sector_percentile` is the pipeline's score, flipped for lower-is-better metrics.
    `ticker_research.py:274` passes it through, and `compute_gauge_scores.py` computes `pct = 1 - pct`.
  - **The example:** Al Rajhi's 22.7 on debt-to-equity means more leveraged than about 77 % of its class.
  - **How it was read:** at least 57 of A's turns and 10 of P's read it as less leveraged. That includes rulings
    marked "settled" and two of A's final answers.
  - **Where it stands live:** the site has withheld bank-class ranks since 2026-10-29. Other companies'
    lower-is-better ranks are still shown, to the room and to members, as "Sector percentile".
- **The packs have no P9:**
  - **The gap:** all five test packs (2026-10-27) hold P1–P8, while the live packs have carried statements (P9)
    since 2026-11-03.
  - **The effect:** all 34 of A's invented figures are tagged [P9]. The comparison is fair between the arms, but
    A's invention rate on live packs is not measured.
- **The registered truths have three defects, whose conclusions all still hold:**
  - **D8:** the quarters are 0.34, 0.34, 0.34 and 0.33, so 1.35, not 1.36.
  - **D9:** the shares rose about 21 % (1 for 10, twice); the 50 % is capital.
  - **I9:** five peers have a P/E, not three.
- **The scorer's markers misfired:** D8 P's MIXED rests on a correctly attributed peer yield, D5's "1.1" hit is the
  dividend, and D4 P clean's CORRECTED rests on a repeated 2.53.

**The choices in `RESULT.md`, for the owner:**
1. **Keep today's room and fix what the audit found.**
   - **The percentile:** label it as a score where higher is better, in the room's pack and on the site. This is
     code on `rebuild`, with no paid calls.
   - **Inventions on live packs:** a small paid check of whether advisors still invent figures when P9 is present.
     This needs the owner's go-ahead.
2. **Screen a one-model option 2** (the presenter's model also plans), as the owner's direction allows.
   - **The cost:** very roughly $0.05–0.06 a session, from measured presenter calls. This is an estimate.
   - **The test:** 30 P-only sessions against this run's A sessions, at a few dollars.
3. **Stop.**

**The questions for the review:**
- Is the audit sound enough to report?
- Is the decision under the pre-written rule right?
- Which next step do you judge right: fix the percentile label first, the live-pack check, the one-model screen, or
  none?
