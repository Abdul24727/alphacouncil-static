# The advisors' room: where its cost goes, and how to keep the presentation on one or two models

**What this is:** the owner's direction of 2026-11-06, written out with the measured costs. The room's
presentation is a major selling point and stays as it is: the portraits, the rounds and the Chair. If its
answers are no better than a single model's, it should run on one model, or two at most, one to present and
one to do the real work. The direction is quoted in full in `docs/review-loop/MASTER-PLAN.md`.

Nothing here is built or released. Any paid test needs the reviewer to judge it necessary and the owner's
go-ahead per run.

## What a session costs today, measured

The pilot's live runs (`docs/eval/probe-results.jsonl`, 12 runs an arm, one question on one company each) give
the cost per run. They don't record each turn. So the advisor-against-Chair split below is **derived**, not
read: six seats against four differ by exactly six advisor calls.

| | calls a session | cost a session |
|---|---|---|
| A: six advisors and the Chair (today's room) | 20.5 | $0.2511 |
| D: four advisors and the Chair | 14.5 | $0.1870 |
| B: the Chair's model alone, one pass | 1 | $0.0318 |

- **One advisor call:** (0.2511 − 0.1870) ÷ 6 = **$0.0107**. Advisors run on `deepseek/deepseek-v4-pro`.
- **In today's room**, 18 advisor calls cost about **$0.19 (77 %)**. About 2.5 Chair calls on
  `anthropic/claude-sonnet-5.5` cost about **$0.06 (23 %)**.
- **Most of the money is the number of advisor calls,** each carrying the company's data and the transcript so
  far. It is not the Chair's stronger model.
- **At the Pro allowance:** a member who uses all 20 sessions a month costs about **$5 a month** today, against
  SAR 79, about $21, in revenue.

*Caveat:* these are the pilot's three-round rooms on five companies. A real session's cost depends on the company
and the question. Real sessions' per-turn costs are stored (`debate_turns`), but none is stored now: the finished
sessions belonged to test accounts, deleted on 2026-11-06.

## What the pilot says about quality, as far as it goes

On 6 probes with one repeat:
- **Handled:** the single model handled 5 of 6, and both rooms 4 of 6.
- **Cost per handled answer:** 9.4× B's for six seats, and 6.9× for four.
- **What that proves:** n = 6 cannot prove the room is no better. It shows no sign that it is better
  (`docs/council-pilot-2026-11-06.md`, with every answer audited by hand).

## The options, in the owner's terms

The page stays the same in every option: the stages (Brief, Answers, Fault lines, Challenges, Final word, The
answer), the seats with their portraits and lenses, and the Chair's answer. What changes is how many model calls
produce it.

| | how it is built | calls | estimated cost | what changes for the visitor |
|---|---|---|---|---|
| **0. As today** | one call per advisor per round, and three Chair calls | ~21 | $0.25 | nothing |
| **1. One call per round** | the advisors' model writes all six seats' turns for a round in one call; the Chair unchanged | ~6 | about $0.08–0.10 | the page looks the same. The advisors no longer write "at the same time, without seeing the others": one call writes them together |
| **2. Analyst and presenter** (the owner's "two maximum") | the **analyst**, today's Chair model, studies the data and decides the answer, the fault lines and the rulings, as B does now. The **presenter**, a cheaper model, writes the six advisors' rounds and the Chair's words from that analysis, in each advisor's lens | 2–4 | about $0.05–0.07 | the page looks the same. The advisors' discussion becomes a presentation of one analysis, not six independent answers |

The estimated costs are arithmetic from the figures above, not measurements. Option 2's accuracy should be about
B's, because the analysis is B's kind of call.

## What option 1 or 2 would need before release

1. **Built behind a setting, off by default,** on `rebuild`. Today's room stays the default until the owner
   chooses.
2. **Measured against today's room on the same probes,** with every answer audited by hand, as in the pilot:
   - accuracy, paired by probe;
   - cost per session, read from real runs;
   - time to the first words on screen.

   That is a paid run, so it needs the reviewer to judge it necessary and the owner's go-ahead.
3. **Shown to the owner on beta,** in both languages at 1440 and 390, so the owner can judge that the
   presentation is kept.
4. **The site's words kept true.**
   - **What must change:** the How-it-works line "Each advisor writes their own full answer at the same time,
     from their own principles and from our data alone" (`web/messages/en.json`, `debate.how.steps.openings`,
     and its Arabic) would no longer be accurate. The "simulated advisors debate" wording on `/pricing` and the
     room's intro would need checking too.
   - **Who sees it first:** the lawyer, who is evaluating the live site now, so the change is shown to the lawyer
     before it is released.
5. **Released only on the owner's go-ahead,** beta first and then production.
