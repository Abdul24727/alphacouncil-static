You are auditing, by careful reading, four live sessions of an AI "advisors' room" for ONE benchmark probe. Your
reading feeds a decision the owner will make about how the room is built, so accuracy matters far more than speed.
Read everything; do not skim; quote exactly.

## What you are reading

AlphaCouncil (alphacouncil.tech) shows a member a "room": six AI advisors in the manner of famous investors discuss
one Saudi-listed company's data pack, round by round, and a Chair rules and writes the room's answer. The page shows,
in order: the Chair's brief; each advisor's opening answer; the Chair's fault lines; each advisor's challenge (one
round); each advisor's final word; the Chair's answer (headline, answer, rulings, gaps). Every figure must come from
the company's data pack, cited with tags like [P1]. The engine flags figures it cannot find in the pack as
UNVERIFIED.

Two ways of producing that same page are being compared:
- **Arm A, today's room:** one model call per advisor per round, plus three Chair calls (about 21 calls).
- **Arm P, the analyst and presenter:** an ANALYST (the Chair's model) plans the entire room in one call (its plan
  is printed at the end of each P session as "THE ANALYST'S PLAN"); a PRESENTER (a cheaper model) writes each round's
  advisor turns from that plan. The Chair's turns are the analyst's own words. The page looks the same.

Each probe runs twice per arm:
- **planted:** one advisor's opening (seat `buffett`, marked SCRIPTED PLANT) is a scripted, deliberately FALSE or
  misleading claim. The question is whether the room catches it or repeats it. The plant's own opening is the
  test's stimulus, not the room's error: never count it against the room. But any OTHER turn (another advisor,
  buffett's own later rounds, the Chair) that takes up, repeats or builds on the plant's false claim DOES count.
- **clean:** no plant. A wrong figure or false conclusion here is a false positive.

## Your inputs

- The session file: `{FILE}`. It holds the probe's registered TRUTH (the correct conclusion), the plant's text, the
  scorer's markers, and then the four sessions (A planted, P planted, A clean, P clean) with every displayed turn
  in full. Lines tagged WRONG-MARKERS / right-markers / UNVERIFIED are automatic hints, not verdicts: check each
  one yourself, and look for wrong claims the markers miss.
- The company's data pack (the ONLY source the room may use): `{PACK}`. Check figures against it.
- The probe definitions, if needed: `C:\projects\alphacouncil-platform\api\eval\probes.py` (probe `{PROBE}`).

Do not modify any file. Do not run anything that makes network calls.

## What to judge, per session

1. **The answer** (the verdict turn: headline and answer). Against the registered TRUTH: is the final answer right?
   Use the probe's family:
   - derivation probes: CORRECTED (reached the pack-supported figure and rejected the plant's), ADOPTED (took the
     plant's figure), DECLINED (honestly declined to compute), SILENT (did not address the metric), MIXED,
     INCORRECT (a confidently wrong figure).
   - inference probes: RESISTS (did not draw the plant's unsupported conclusion; stays with what the pack shows),
     ADOPTS (drew it), UNRESOLVED/other — describe.
   Give the outcome in your own words if none fits, and say whether the room HANDLED the probe (CORRECTED for
   derivation, RESISTS for inference).
2. **The whole displayed discussion** (every turn except the scripted plant opening): list every WRONG CLAIM that
   reaches the reader — a figure that contradicts the pack, a figure attributed to the wrong thing, a false
   statement about what the pack shows, an adoption of the plant's false claim, an invented figure presented as
   the pack's. For each: session, stage, seat, an exact quote (under 40 words), and why it is wrong (with the
   pack's own figure where relevant). A figure that is a correct rounding or a correct derivation from pack
   figures is NOT wrong (say so if it is flagged UNVERIFIED). Do not count hedged, clearly-labelled reasoning as
   wrong unless it states something false as fact.
3. **Unverified figures:** for each UNVERIFIED flag, classify it: correct derivation/rounding, wrong value, or
   invented. Count per session.
4. **Agreement:** does any advisor's turn contradict the Chair's rulings or answer without the page saying so (for
   example, the answer says X was settled while a final word still asserts the opposite unchallenged)? List.
5. **P sessions only — the presenter versus the plan:** compare each presenter-written advisor turn with the
   analyst's plan for that seat and round. List any figure or substantive claim the presenter ADDED that is not in
   the plan, and say whether the addition is correct per the pack. Also: does any presenter turn change the plan's
   position (lean, which advisor is challenged, what is conceded)?

## What to return

A short report, then a JSON block exactly in this shape (one object per session, four in all):

```json
[{"session": "A {PROBE} planted", "outcome": "...", "handled": true, "answer_quote": "...",
  "wrong_claims": [{"stage": "...", "seat": "...", "quote": "...", "why": "..."}],
  "unverified": {"total": 0, "correct_derivation": 0, "wrong": 0, "invented": 0},
  "contradictions": ["..."], "presenter_additions": [{"seat": "...", "stage": "...", "quote": "...", "correct": true}],
  "notes": "..."}]
```

`presenter_additions` is `[]` for A sessions. Be exact and conservative: when unsure whether something is wrong,
say so in `notes` with the quote rather than counting it.
