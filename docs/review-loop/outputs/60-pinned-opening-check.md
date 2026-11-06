# Output 60: review 66's fix. A plan may leave the planted seat's opening out

**The defect (review 66):** the analyst's prompt says "write no opening for their seats", but `check_plan` required an
`opening` object for every seat. So a plan that obeyed was refused, which means a paid retry or a failed session.
The stand-in always wrote an opening, so neither the tests nor the dry runs could see it.

**The fix (commit `d7c2091`, `api/app/debate/presenter.py`):**
- **`check_plan`:** a pinned seat needs only its `challenge` and `final` objects. Its opening is never served from
  the plan, because the room serves it through `with_plant` and the engine's check. So it may be missing, empty or
  anything else, even a non-object. Every other seat is checked as before: an `opening` object with a non-empty
  `position`, plus `challenge` (with a valid `responds_to`) and `final`.
- **`_seat_plan`** returns `{}` for a part that is not an object, rather than calling `dict()` on it. In today's
  flow it is never asked for a pinned seat's opening, because `_present` skips pinned seats in openings and
  `with_plant` answers that turn first. The change is a guard.

**The regression tests (`api/tests/test_eval_probe_run.py`):**
- **`test_a_plan_that_writes_no_opening_for_the_planted_seat_is_accepted[drop|empty]`:** a full planted arm-P session
  on the stand-in. The analyst's plan has the pinned seat's opening removed, or set to `{}`, before `check_plan` reads
  it. The session completes on 4 calls with `{"calls": 4, "fallbacks": 0, "round_failures": 0}`, and costs reconcile.
- **`test_the_plan_check_waives_the_opening_for_a_pinned_seat_only`:**
  - for the pinned seat, a dropped, empty or string opening is accepted;
  - the same plans are refused when nothing is pinned;
  - a missing opening on an **unpinned** seat is refused, and so is a missing `final` on the pinned seat.
- **Against the old `presenter.py`:** the dropped case and the check test fail. The empty case passed before too,
  as review 66 found.

**Checks:**
- **The probe-run tests:** `python -m pytest tests/test_eval_probe_run.py -q` gives 51 passed. They include the
  equivalence test on all 15 active probes (room == single == analyst).
- **The full suite:** 594 passed, 10 skipped.
- **Lint:** `ruff check .` gives the same 116 findings as before, none new.
- **Whitespace:** `git diff --check` is clean.

**The 60-session dry comparison, repeated** from a clean `git archive` copy of `d7c2091`, locally, with its own empty
dry record:
- **All 60 ran:** 30 A at 20–21 calls; 30 P at 4 calls, with 0 fallbacks, 0 round failures and 30 analyst plans.
  Every turn is `simulated`.
- **Reserved:** $127.3381, identical to the run after review 65. The fix changes no prompt.
  - **P:** maximum $1.262354, mean $1.239651.
  - **A:** maximum $3.154860, mean $3.004952.
- **So the provisional figures and the quote are unchanged:** about $10.64 expected, a $167 cap.
- **Records:** `docs/eval/presenter-comparison/` holds this run. `docs/eval/dry-probe-results.jsonl`,
  `docs/eval/probe-results.jsonl` and `docs/eval/pilot-2026-11-06/` are unchanged (`git diff --quiet`).

**Also since output 59** (commit `64c0c14`, report only; `eval probe` is unchanged): `probe_report.py` prints the
"contested in the round of challenges" line for arm P too, since `run_room` records it for every room. It also adds
one comparison, "option 2: A vs P", read as a difference like six seats against four. The decision on option 2
stays with the hand audit, against the criteria written before the run. One test covers both lines.

**How the approved run will be staged:** from one named commit, the one this review accepts, not from whatever
`HEAD` is. The command is unchanged: `git archive <sha> api docs/eval`, with an empty `probe-results.jsonl`, run as
`systemd-run --unit=acp-comparison`, then `eval probe --arm A --arm P --repeats 1 --clean-arms A --clean-arms P
--cap-usd 167 --pause 5`. The model account holds $37.83 (monitor, 2026-11-07 00:20 local).

**The questions for the review:** is the fix sound, and may the approved comparison now run from this commit?
