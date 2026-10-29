# Priority Two: differentiated advisor mandates

2026-10-29. Branch `rebuild`. Models, roster and debate rounds unchanged. Nothing pushed, nothing
deployed, no paid model call made.

## The gap

Every seat already had a distinct persona — principles, what it looks at first, how it argues,
blind spots, voice. What no seat had was a **job**.

Reading the prompt assembly: each seat receives the shared rules, the roster, the whole data pack,
and its own persona file; the task for the step comes from `chair.md`'s stage section and is
**identical for every seat**. So seven differently-voiced seats were asked the same question of the
same data. Differentiation was in the manner of the answer, not in what any seat was responsible
for finding.

That had no visible cost while the pack held only headline ratios — there was little to divide.
It has one now. P9 carries the statements, the quarterly series, the derived calculations with
their denominators, and a `limitations` list saying what the data cannot answer. If no seat is
answerable for a part of that, the likely outcome is seven seats reaching for the P/E, the ROE and
the yield, and the rest going unread.

## The change

Each advisor file gains a `## Mandate` section and an `owns` line in its front matter naming the
pack's dataset tags that mandate covers. A mandate says four things: what this seat is answerable
for, which datasets it must read and what to read in each, the standing question it answers in
every session, and what to say when its own evidence is absent.

| seat | owns | answerable for | the question it answers every session |
|---|---|---|---|
| Buffett | P2, P9 | earning power, and what it was earned on | are these returns real, what were they earned on, and over what period? |
| Lynch | P7, P9 | the trend, quarter by quarter | does the quarterly record support the story the annual figures imply, and which way is it moving? |
| Dalio | P2, P9 | the balance sheet and how it is funded | how is this balance sheet funded, and what would have to happen for the funding to become a problem? |
| Marks | P1, P8, P9 | what the price assumes, **and what the evidence cannot answer** | what does this price have to be assuming, and what do we not know? |
| Alwaleed | P3, P9 | what has been returned to owners, and out of what | what was paid, over which window, out of which earnings, and what has been done to the share count? |
| Al-Rumayyan | P5, P6 | the company against its sector, and its own disclosures | how does this company sit against the companies it is compared with, and what has it itself disclosed? |
| Al-Rajhi *(seventh seat, not in the default six)* | P9 | where the result came from, and a lender's own measures | was this result earned from operations, and for a lender, what do its own measures say? |

**The mandates partition the pack.** Every dataset has an answerable seat except **P4**, and that
is deliberate: P4 is the rule-based council votes, which are thresholds rather than measurements.
Nobody is answerable for an opinion, and the one seat told to read it — Marks — is told to say what
it is and never to cite it as a figure. A test holds this shape, so changing a mandate means
deciding again who owns what rather than quietly leaving a gap.

**One mandate is worth naming on its own.** Marks is answerable for *what the evidence cannot
answer*: the `limitations`, and every calculation that came back with `missing` instead of a value.
Before today nothing in the room was anyone's job to say out loud, so a gap in the data could pass
unmentioned by seven seats in turn. Now the room's confidence has a seat answerable for checking it
against the room's evidence.

### Where the mandate sits in the prompt

First and on its own, before the persona it is part of:

```
YOUR SEAT: Howard Marks (id marks).

YOUR MANDATE IN THIS ROOM (datasets P1, P8, P9):
You are answerable for two things, and the second is yours alone: ...

# Howard Marks (simulated advisor)
## Who they are ...
```

It is the one thing in a seat's prompt that differs by seat rather than by step, and burying it in
the brief would make it read as another line of character notes. `Seat.brief` is the body with the
Mandate section removed, so the prompt carries it exactly once — a test asserts that, because a
second copy back among the character notes would quietly undo the hoisting.

The shared rules gained one paragraph saying what a mandate is, and in particular what it is not:

> Your mandate is what you are answerable for and not the limit of what you may say: answer the
> member's question first, and disagree with any seat about anything.

`chair.md`'s Answers stage — the step instruction every seat shares — says that covering the
mandate is part of answering the question rather than a second task after it, and that a seat whose
own evidence is absent covers its mandate by saying so and naming what is absent.

### Coverage is measured, and flagged rather than enforced

A round-one answer that cites none of the datasets its seat is answerable for carries
`flags.uncovered` listing them, beside the existing `unverified`, `cited`, `removed` and `words`.
`web/scripts/check-advisors.mjs` — the existing offline checker, reusing the screen it already
reads — reports two lines per locale: how many seats cited none of their own datasets, naming them,
and which datasets some seat is answerable for that round one never cited at all.

Flagged, never refused, for a reason: a seat may honestly find that its own evidence is absent for
this company, and saying so *is* covering the mandate. The flag is a question for whoever reads the
session, not a verdict on the answer.

**Measured on round one only.** An opening is the seat's own complete answer, written without
seeing the others', so citing nothing of your own part there means your part went unread. A
challenge or a final word is a reply, and reaching for another seat's dataset there is the debate
working.

## What is not known yet

**Whether the room's answers actually differentiate is unmeasured.** The mandates are in the
prompts, the partition is tested and the coverage flag is wired, but whether seven seats with
mandates produce seven differently-grounded answers can only be seen in a real session, which
needs paid model calls. Those are not authorised, so this delivery ends at the prompt and the
check. The first paid run should read the two coverage lines before anything else.

Three things to watch in that run, each a plausible way this could go wrong:

- **Mandate recited rather than used.** A seat may name its datasets and say little with them. The
  coverage flag would read clean while the answer got worse; only reading the answers catches it.
- **Narrower answers, not better ones.** The rules say the mandate is not a ceiling, but a seat may
  treat it as one and stop answering the member's question. Round-one word counts and the Chair's
  answer are where that would show.
- **P9's size against the mandates' reach.** Five of six seats are answerable for part of P9, which
  is the dataset that grew the prompt by half. If answers crowd out each other, the trim order in
  `evidence.fit` is the lever, not the mandates.

## Files

| file | what |
|---|---|
| `api/app/advisors/*.md` (7) | a `## Mandate` section and an `owns` line each |
| `api/app/advisors/chair.md` | the Answers stage says covering a mandate is part of answering |
| `api/app/advisors/README.md` | what a mandate is, the partition, P4's deliberate exception, and how to write one when swapping a seat |
| `api/app/debate/roster.py` | `Mandate` a required section, `owns` validated, `Seat.brief` |
| `api/app/debate/engine.py` | the Mandate paragraph in the rules, the mandate hoisted in `system()`, `check_opening` flags coverage |
| `api/app/debate/checks.py` | `tags_in` and `uncovered` |
| `api/tests/test_debate.py` | 7 new tests |
| `web/scripts/check-advisors.mjs` | two coverage lines per locale |

Suite: **522 passed, 11 skipped** (515 after Priority One).

Raw output — the partition, one seat's prompt as it is received, and the mandate-appears-once
check — is in `docs/verification/priority-one-closeout-2026-10-29.md`, section 8.
