# Result: option 2 (analyst + presenter) against today's room

**Run:** the paid comparison of 2026-11-07, from commit `d7c2091`: 60 live sessions, **$11.36** spent. Every
session was audited by hand (`audit.md`), and every counted claim is quoted and checked in
`verified-claims.json`.

## The decision the pre-written rule gives

**Option 2 as built fails criterion 4, cost, by a wide margin:** it costs 62 % of today's room against a limit of
40 %. The rule was written before the run: "A clear failure settles it." So today's room stays as the room.

**The other criteria do not change that, but the audit does change what is worth trying next:**
- On errors, option 2's discussion was far more accurate than today's room's.
- Its cost sits almost entirely in the analyst's one long call on the stronger model.

## Against the five criteria

| # | Criterion (written before the run) | Result |
|---|---|---|
| 1 | Handles at least A's count − 1 of the 15 planted probes | **Depends on how a decline is counted.** On substance: A 14, P 14. Strictly, if a derivation counts only when the answer states the derived figure: A 14 (13 against the registered D9 truth), P 11. P's analyst declines derived figures by the room's own rule ("Never convert, combine or calculate new figures"). |
| 2 | No more wrong answers or wrong claims reach the reader, across the whole discussion | **P passes clearly.** Wrong claims: 55 against 210 (1.9 against 7.0 a session). In a final answer: 0 against 7. Inventions: 2 against 48. Today's room has 23 with invented figures and 25 invented statements about what the pack holds; option 2 has no invented figure and 2 invented statements, both added by its presenter. 45 of P's 55 were added by its presenter, not by the analyst's plan. |
| 3 | No more figures absent from the data per session | **P passes clearly:** 0 asserted wrong or invented figures against 121 (about 4.0 a session). Caveat: the engine's check misses miscounts the presenter derives ("four quarters", "five months"); those are counted under criterion 2. |
| 4 | Measured cost at most 40 % of today's room | **P fails clearly:** $0.1454 against $0.2332, **62.4 %**. With no plan retries it is 53 %, and its cheapest session was 48 %. The analyst's call alone, every attempt and the failed session included, averages **$0.1094, or 46.9 % of A**; when the plan passed first time, $0.086 (37 %). *(Corrected after review 68: this gave only the single-attempt figure.)* |
| 5 | The owner judges the presentation unchanged (beta, both languages, 1440 and 390) | **Not judged;** it is not on beta. The record shows changes the owner would see: see below. |

**What would show on the page:**
- **The wait:** the first words appear after a median of **40 seconds** (worst 108), against 5 seconds today, and a
  whole session takes 85 seconds against 39. The analyst has to finish before anything is shown.
- **Unrounded numbers:** 28 turns in 8 sessions show figures such as "0.26061782975782133", 4 of them in a final
  answer. Today's room shows 3 such turns.
- **Fault lines ahead of the debate:** the Chair's fault lines sometimes credit advisors with points they make only
  in the next round, because the analyst writes the whole room in advance.
- **A failure with no recovery:** 1 session in 30 failed with nothing shown, after the analyst's plan was refused
  three times. An analyst failure has no fallback to the room. In 6 of 30 sessions the plan was refused at least
  once and retried at full price.

## What the run says about today's room (the live product)

1. **Wrong claims:** about **7 a session** reach the reader. Most are in the openings and many are corrected later on
   the page, but **7 reached a Chair's final answer** in 6 of 30 sessions. Three examples:
   - D5 clean says the pack's figures agree. They do not: 45.32 ÷ 41.18 = 1.10, against the reported 1.24.
   - D5 planted endorses a false market-cap check.
   - D9 clean leaves a dividend cut as an open question.
2. **Inventions:** advisors invent **income-statement, quarterly and balance-sheet figures**: 23 claims with
   invented figures, and 25 more that say the pack holds data or a comparison it does not, such as peer returns on
   equity.
   - **What they rest on:** all but one rest on statement data the advisors' briefs place in P9, though the turns
     cite them to [P1], [P2], [P3], [P7], [P9] or nothing.
   - **Why the packs matter:** the test packs date from 2026-10-27 and have no P9, while the live packs have
     carried statements since 2026-11-03. How often this happens on live packs is not measured.
   - *(Corrected after reviews 68 and 69. Review 68: this said 34 invented figures, all tagged [P9]. Review 69: one
     definition is now applied to both arms.)*
3. **The percentile is misread:** the **"sector percentile" field reads the wrong way** for lower-is-better metrics.
   The API passes through the pipeline's flipped score, so Al Rajhi's 22.7 on debt-to-equity means more
   leveraged than about 77 % of its class. Both arms mostly read it as the opposite, today's room in at least 57
   turns. That includes rulings marked "settled" and two final answers. The site shows the same number to members
   labelled "Sector percentile".

## What the run says about option 2

- **Accuracy:** one coherent plan from the stronger model produced far fewer errors than six independent seats.
  Most of option 2's errors come from the cheaper presenter, which adds figures, including three carryings-forward
  of the planted claim and the misread percentile.
- **Derived figures:** the analyst refuses them (the D8 annual dividend, the D5 ratio, the D9 share count, the I3
  payout). That follows the room's own rule, and it is why option 2 is "weaker" on the derivation probes. Today's
  room computes those figures, breaking the rule, and mostly gets them right.
- **Cost:** three-quarters of the cost is the analyst's call. A two-model version with this analyst cannot reach 40 %
  without a cheaper analyst.

## The choices for the owner

1. **Keep today's room (recommended for launch) and fix what the audit found in it:**
   - **The percentile:** say in the room's data pack, and on the site, that the sector percentile is a score where
     higher is better for every metric, or show the plain rank. This is a code change on `rebuild` and needs no
     paid calls.
   - **Inventions on live packs:** check whether advisors still invent figures when the pack has P9. A small paid
     check of a few sessions on today's live packs needs the owner's go-ahead.
2. **Screen a one-model option 2,** as the owner's direction of 2026-11-06 allows ("run it on one model, two at most"):
   - **The design:** the presenter's model also writes the plan.
   - **The cost:** from this run's measured presenter calls, a session would cost very roughly $0.05–0.06, about a
     quarter of today's room. That is an estimate, not a measurement.
   - **The test:** 30 P-only sessions on the same packs, compared with this run's 30 A sessions. That would cost a
     few dollars, needs a small code change, the reviewer's acceptance and the owner's go-ahead.
   - **The risk:** the accuracy came from the stronger analyst, and the wait before the first words remains.
3. **Stop here:** keep today's room as it is, with no change to the room's cost.

## What this run cannot show

- **Repeats:** one repeat per probe is a screening check, not proof of equal performance. A second repeat was not
  needed, because criterion 4 failed clearly.
- **The live packs:** all packs are the five frozen 2026-10-27 packs without statements, so the live room's error
  rate on today's packs is not measured.
- **The probes:** three registered truths are slightly wrong against their packs (D8, D9, I9). Their conclusions
  hold, and the audit judged against the pack.
