# The advisors' room: its cost, and how to keep the presentation on one or two models

**What this is:** the owner's direction of 2026-11-06, written out with what is measured and what is not. The
room's presentation is a major selling point and stays as it is: the portraits, the rounds and the Chair. If its
answers are no better than a single model's, it should run on one model, or two at most, one to present and one
to do the real work. The direction is quoted in full in `docs/review-loop/MASTER-PLAN.md`.

Option 2 is built as a prototype (`api/app/debate/presenter.py`, harness arm P), off by default; nothing is released. **Any paid run needs the owner's go-ahead per run.** *(Updated 2026-11-06 after review 64: this said nothing was built.)*

**RESULT (2026-11-07):** the paid comparison ran: 60 sessions from `d7c2091`, $11.36, every session audited by hand.
- **Cost:** option 2 fails criterion 4 clearly, at 62 % of today's room against the 40 % limit, so today's room
  stays.
- **Accuracy:** option 2's discussion was far more accurate (55 wrong claims against 210).
- **Details:** `docs/eval/presenter-comparison/RESULT.md` gives the decision and the choices, and `audit.md` the
  audit.

*(Corrected after review 60. The first version split the room's cost into advisors (77 %) and Chair by comparing
six seats with four. That comparison cannot isolate either: fewer seats also make every remaining prompt's
transcript shorter. It also counted 18 advisor calls where the pilot paid for 17.5 on average, said five
companies where the record has three, underpriced the comparison, and said the lawyer was already evaluating the
site.)*

## What is measured

The record is `docs/eval/probe-results.jsonl`: the $66 pilot's 36 live runs, on **three companies** (2222, 2010,
1120) and five question types.

| Arm | Calls, clean run | Calls, planted run | Cost a run, mean (range) |
|---|---|---|---|
| A: six advisors and the Chair (today's room) | 21 (18 advisor + 3 Chair) | 20 (17 + 3) | $0.2511 ($0.2204–0.2841) |
| D: four advisors and the Chair | 15 (12 + 3) | 14 (11 + 3) | $0.1870 ($0.1609–0.2372) |
| B: the Chair's model alone | 1 | 1 | $0.0318 ($0.0300–0.0386) |

- **The planted runs' scripted opening:** in each planted run one advisor's opening is the harness's scripted
  plant, which costs nothing (`eval/probe_run.py`, `with_plant`). That is why A averages 17.5 paid advisor calls.
- **What is not measured: how a session's cost divides between the advisors and the Chair.**
  - **Why:** the harness saved each run's total, not each turn's.
  - **Where it would be read:** a real session records each turn's model and cost (`debate_turns`), but none is
    stored now. They belonged to the test accounts deleted on 2026-11-06.
  - **When it gets measured:** the comparison below records per-turn costs.
- **At the Pro allowance:** a member who uses all 20 sessions a month costs about 20 × $0.25 = **$5 a month** at
  today's measured mean, against SAR 79, about $21, in revenue.

## What the pilot says about quality, as far as it goes

On 6 probes with one repeat, every answer audited by hand:
- **Handled:** the single model handled 5 of 6, and both rooms 4 of 6.
- **What that proves:** n = 6 cannot prove the room is no better. It shows no sign that it is better
  (`docs/council-pilot-2026-11-06.md`).

## The options, in the owner's terms

The page stays the same in every option: the stages (Brief, Answers, Fault lines, Challenges, Final word, The
answer), the seats with their portraits and lenses, and the Chair's answer. What changes is how many model calls
produce it.

| | how it is built | calls | cost a session |
|---|---|---|---|
| **0. As today** | one call per advisor per round, and three Chair calls | 21 | **$0.25 measured** |
| **1. One call per round** | the advisors' model writes all the seats' turns for a round in one call; the Chair unchanged | about 6 | **not measured** |
| **2. Analyst and presenter** (the owner's "two maximum"; built as a prototype, off by default) | the **analyst**, today's Chair model, studies the data and decides the answer, the fault lines and the rulings. The **presenter**, a cheaper model, writes the advisors' rounds from that analysis, in each advisor's lens; the Chair's turns are the analyst's own words | 4 | **not measured live**: about $0.10 provisional, from the dry run |

**Option 2's accuracy is a hypothesis to test, not an expectation.** The analysis is B's kind of call, but what a
visitor reads is the presenter's rewriting of it. The presenter can introduce figures or claims of its own, or
blur the Chair's answer. So the test has to read everything the page would show, not only the final answer.

## The comparison that would decide it

Review 60 judged a paid comparison of today's room against option 2 **necessary before adoption**, and an
A-against-D run **unnecessary** for this decision.

**The runs:**
- **Plan:** the 15 active probes, today's room (A) and option 2 (harness arm **P**), one planted and one clean run
  each: **60 sessions**, 30 an arm.
- **The prototype exists** (`app/debate/presenter.py`, off by default), and the plan was dry-run in full on the
  server on 2026-11-06. After reviews 65 and 66 it was run again on 2026-11-07, locally, from clean copies of
  commits 2e948d9 and then d7c2091, with the same settings and packs (`docs/eval/presenter-comparison/` holds the
  second). Both gave the same figures. All 60 sessions ran:
  - **P:** 4 calls each, 21 turns, no fallbacks;
  - **A:** 20–21 calls each.
- **The planted claim is shown alike** *(review 65)*: P's analyst plans before any turn exists, so it is shown the
  plant up front. It now sees the same line, character for character, as today's room's Chair and the single
  model: the engine's citation tags included, and the advisor named by surname. This is tested on all 15 active
  probes.
- **Reservations measured dry:** P's per-run maximum is **$1.2624**, mean $1.2397; A's is $3.1549 dry and $3.9713 live.
  The dry plan reserved $127.34 in all.
- **P's live figures are provisional,** because P has never run live:
  - **Bound:** its dry maximum scaled by the room's measured live-to-dry ratio (1.2588), $1.5891 a run.
  - **Forecast:** its dry mean times the room's cost-to-reservation ratio, about **$0.10 a session**. The guess of
    $0.05–0.07 above was too low: the analyst writes one long answer on the stronger model.
  - **Against criterion 4:** $0.1036 is **41.3 %** of today's room's $0.2511, so on this provisional estimate it is
    **above** the 40 % limit. Only the live comparison can settle it. *(Corrected after review 64: this said "right
    at" the limit.)*
- **Expected cost:** A ≈ 30 × $0.2511 = **$7.53**, P ≈ 30 × $0.1036 = $3.11: about **$10.64 in all**.
- **The cap:** 30 × $3.9714 + 30 × $1.5891 = **$166.82, so $167**. That is a ceiling enforced per call, not an expected
  spend, and the owner approves it.

**What is recorded for every session:**
- every turn the page would show, saved whole: every advisor turn, the fault lines, the rulings and the Chair's
  answer. The harness has kept these since 2026-11-06 (`ProbeResult.turns`);
- for option 2, the analyst's whole plan (`analyst_plan`), so the audit can tell what the presenter wrote beyond the
  analysis, and the calls a fallback superseded (`extra_calls`);
- each turn's model, tokens and cost;
- the time to the first words on screen.

**The audit, by hand, of every session, planted and clean, successes included:**
- **The answer:** was the final answer right, against the probe's registered truth?
- **The whole discussion:** anywhere in the displayed text, did a wrong figure or claim reach the reader? For
  option 2 that includes anything the presenter introduced that the analysis did not say. The engine's own check
  for figures that are not in the data is recorded beside it.
- **Agreement:** do the seats' turns contradict the Chair's rulings without the page saying so?

**Proposed acceptance criteria for option 2.** They are written down before the run; the decision is the owner's:
1. **Answers:** it handles no fewer planted probes than today's room, less one: at least A's count − 1 of 15.
2. **Errors:** no more wrong answers or wrong claims reach the reader than in today's room, counting the whole
   displayed discussion.
3. **Unchecked figures:** no more figures absent from the data per session than in today's room.
4. **Cost:** its measured cost is at most 40 % of today's room's.
5. **Presentation:** the owner judges it unchanged, on beta, in both languages at 1440 and 390.

**What one repeat can show:**
- **It is a screening check,** not proof of equal performance.
- **A clear failure** settles it.
- **A narrow pass** calls for a second repeat before adoption.

## Before any release, whichever option

1. **Built behind a setting, off by default,** on `rebuild`. Today's room stays the default until the owner
   chooses. *(Done for option 2. Before the app itself may use it, its session total must also count the calls a
   fallback superseded. Today the app sums only displayed turns' costs, and the harness records those calls
   separately as `extra_calls`.)*
2. **The comparison above,** on the owner's go-ahead, with its cap set from the prototype.
3. **Shown to the owner on beta.**
4. **The site's words kept true.**
   - **What must change:** "Each advisor writes their own full answer at the same time, from their own principles
     and from our data alone" (`web/messages/en.json`, `debate.how.steps.openings`, and its Arabic) would no
     longer hold.
   - **What to check too:** the "simulated advisors debate" wording on `/pricing` and in the room's intro.
   - **The lawyer:** the site is ready for the lawyer's review now, but that review has **not started** (Step 7
     is the owner's to send). The changed mechanism and wording go to the lawyer before release.
5. **Released only on the owner's go-ahead,** beta first and then production.
