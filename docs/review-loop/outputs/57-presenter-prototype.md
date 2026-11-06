# Output 57: review 63's step. The analyst-and-presenter prototype, off by default, and its 60-session dry run.

**`api/app/debate/presenter.py` (new):**
- **How it plugs in:** it is a drop-in asker for the existing engine. `Debate` runs the same stages, applies the
  same checks, saves the same turns and streams the same events, so the page is unchanged.
- **Brief:** one **analyst** call, on the Chair's model, plans the whole room: the brief, every advisor's position in
  every round, the fault lines and the verdict. The brief is served from that plan.
- **Openings, challenges, final word:** one **presenter** call per round, on the advisors' model. Its prompt carries
  every seat's mandate and character file, and it writes every advisor's turn from the plan. The plan's leans and
  `responds_to` override the presenter's.
- **Fault lines and verdict:** served from the analyst's plan, in the analyst's words.
- **When a turn fails:**
  - **One turn refused by the engine's checks:** it falls back to the room's own call for that turn only.
  - **A presenter round that fails outright:** it falls back seat by seat.
  - **A failed analyst:** it ends the session, as a failed Chair does.
  - **Counted:** calls, fallbacks and round failures go into `stats`.
- **Costs:**
  - **Each call's usage rides on one turn:** the analyst's on the brief, a round's on the first seat served. The
    other turns get `Usage(model="shared")`.
  - **Usage combined:** where a fallback follows a share.
- **The planted claim:** in a planted run the plant's opening is pinned and shown to the analyst before it plans, so
  the rest of the room can answer it. This is the analogue of the single model's analyst note.
- **`make_standin_call`:** the analyst and presenter without a model, built from the room's own stand-in.

**Settings and app:**
- `Settings.debate_engine = "room"` by default.
- `routers/debate.py` uses the presenter only when the setting is `"presenter"`, with the room's call as the fallback.
- Nothing is deployed or switched on.

**Harness:**
- **Arm P** (`--arm P`, `--clean-arms P`) runs `run_room(..., engine="presenter")`. Its calls are metered through the
  same Budget as the room's.
- **New result fields:** `engine` and `engine_stats`.
- **Usage records:** they gain `shared`, a confirmed zero whose cost is on another turn.
- **`RUN_BOUND["P"]` = 1.5891 and `RUN_COST["P"]` = 0.1036 are PROVISIONAL** and labelled so. They are the dry
  measurements scaled by the room's measured live-to-dry and cost-to-reservation ratios, to be replaced by live
  figures.

**Tests** (`api/tests/test_eval_probe_run.py`, offline):
- every stage (1 / 6 / 1 / 6 / 6 / 1) from 4 calls, with 17 turns shared;
- the run's cost equals the recorded cost;
- the planted opening is shown to the analyst and not rewritten;
- a refused turn falls back for that turn only;
- a failed presenter round falls back seat by seat, with the failure billed once;
- a failed analyst ends the session, with its cost kept in `failed_calls`;
- the Arabic session runs every stage, with Arabic asked in every call;
- the setting is off by default.

**The dry comparison,** on the server, with no model calls:
- **The command:** `eval probe --dry --arm A --arm P --repeats 1 --clean-arms A --clean-arms P` over the 15 probes,
  60 sessions.
- **The results:** all ran.
  - **P:** 4 calls, 21 turns and 0 fallbacks every time.
  - **A:** 20–21 calls.
  - **Reserved:** $127.32 in all.
  - **Per-run maximum:** P $1.2624 against A $3.1549.
- **Kept in** `docs/eval/presenter-comparison/` (`dry-probe-results.jsonl`, `dry.log`). Every row is `dry: true`
  and every turn `simulated: true`. The pilot's records and `docs/eval/dry-probe-results.jsonl` are unchanged.

**The quote, in `docs/council-cost-options-2026-11-06.md`:**
- **Expected:** about **$10.64**.
- **Cap:** **$167**, as 30 × $3.9714 + 30 × $1.5891.
- **P's provisional cost:** about **$0.10 a session**, roughly 41 % of today's room. That is at the brief's 40 %
  criterion, and the comparison settles it. The earlier $0.05–0.07 guess was too low.

**Checks:**
- `uv run pytest -q`: 574 passed, 10 skipped;
- `presenter.py` is lint-clean;
- `git diff --check` is clean.

**The questions for the review:** is this sound, is the comparison ready to put to the owner, and what is the
single next pre-approved step?
