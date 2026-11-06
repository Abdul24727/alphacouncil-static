# Output 59: review 65's fix. The analyst is shown the planted claim exactly as the room's Chair is

**The defect (review 65):**
- **Where:** `probe_run.py` pinned the plant raw, as `{"headline", "text"}`, and `presenter.py` printed it as
  `- <seat id>: <json>`.
- **What the room's Chair sees instead:** the line the engine's transcript shows. That line has been through
  `check_opening`, so it has the `[Pn]` tags the engine adds, and it names the advisor by surname (`engine._line`).

**The fix (commit `2e948d9`):**
- **One source for the line:** `probe_run._plant_line(probe, pack)` builds `- <surname>: <headline> <text>` through
  the same `Checked.text` the engine's opening check runs: 200 characters for the headline, 4,000 for the text.
  - `_note`, the single model's framing, is now `"THE ADVISORS' ANSWERS:\n" + _plant_line(...)`, so arm B is
    unchanged.
  - Arm P pins `{PLANT_SEAT: _plant_line(probe, pack)}`.
- **What the analyst is shown:** `presenter.py` takes `pinned` as `dict[seat id, line]`. The analyst gets:
  - the same `THE ADVISORS' ANSWERS:` header and line as the single model;
  - a note mapping surname to seat id, which its plan needs as keys;
  - "write no opening for their seats";
  - "in choice mode each of them leans to the first option your brief lists".
- **Why the lean is a rule and not a value:** in choice mode the room shows the plant's lean as
  `[leans <first option>]` (`with_plant` uses `state.options()[0]`). The analyst writes those options in the same
  call, so it can't be shown the value ahead of time; it is told the rule instead. This is the one difference that
  remains, and it applies only in choice mode.
- **Unchanged:** the plant's displayed turn still goes through `with_plant` and the engine's check, as before.

**The test:**
- **What it checks:** `test_every_arm_is_shown_the_identical_planted_claim` now runs on **every active probe (15)**
  and covers arm P. For each probe it captures:
  - the prompts of the room's verdict call (A);
  - the single model's call (B);
  - the analyst's call (P).
  It then asserts `room == single == analyst`, character for character.
- **It catches the defect:** against the previous code it **fails on all 15.** On all 15 the old line was the raw
  JSON under the seat id, not the surname line. On 14 the engine's tags were also missing; D7's text gains no tags,
  so it differs only in that framing and attribution (checked by comparing `_plant_line` with the raw text).
- **Arm P's plant test** now asserts the analyst's prompt contains `_note(probe, pack)`, the checked and cited
  framing, rather than the raw text.

**Checks:**
- **Tests:** 590 passed, 10 skipped (full suite); `-k "identical_planted or presenter"` gives 21 passed.
- **Lint:** `ruff check .` reports the same 116 findings before and after the change; none are new.
- **Whitespace:** `git diff --check` is clean.

**The 60-session dry comparison, repeated:**
- **Where it ran:** locally, from a clean `git archive` copy of `2e948d9` in the scratchpad, with its own empty
  dry record. Locally and on the server, no `DEBATE_*` setting is overridden, so both use the code defaults. Prices
  are in `eval.budget.PRICES`, and the packs are tracked in git. So it is the same plan the server ran.
- **All 60 ran:** 30 A at 20–21 calls; 30 P at 4 calls, with 0 fallbacks, 0 round failures and 30 analyst plans
  saved. Every turn is `simulated`.
- **Reserved:** $127.3381 in all, against $127.3202 before. The analyst's prompt is a little longer.
  - **P:** maximum $1.262354, unchanged; mean $1.239651, against $1.2391.
  - **A:** unchanged, maximum $3.1549, mean $3.0050.
- **The provisional figures do not move:** `RUN_COST["P"]` is 1.239651 × 0.2511 / 3.0050 = 0.103586, which rounds
  up to **0.1036**, still 41.3 % of A. `RUN_BOUND["P"]` is 1.262354 × 1.2588, which rounds up to **1.5891**.
- **So the quote stands:** about **$10.64** expected and a **$167** cap. The comments in `probe_run.py` record the
  re-measured mean.
- **Records:**
  - `docs/eval/presenter-comparison/` is replaced by this run;
  - `docs/eval/dry-probe-results.jsonl`, `docs/eval/probe-results.jsonl` and `docs/eval/pilot-2026-11-06/` are
    unchanged (verified with `git diff --quiet`).

**Plans updated:**
- `PROJECT.md` changelog: the prototype, the quote and the owner's go-ahead were missing, and are now recorded.
- `docs/review-loop/MASTER-PLAN.md`: a "Since then" block.
- `docs/council-cost-options-2026-11-06.md`: the re-run and the plant equivalence.

**The owner's go-ahead is already given:** "Yes, run it", in answer to "Once ChatGPT accepts the fixes, run the paid
comparison (about $11, ceiling $167)?". The cap and the expected cost are unchanged by this fix.

**The questions for the review:** is the fix sound, and may the approved comparison now run, unchanged:
`eval probe --arm A --arm P --repeats 1 --clean-arms A --clean-arms P --cap-usd 167`, staged from `rebuild` HEAD
on the server with an empty probe record?
