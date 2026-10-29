# Priority Three: the Chair adjudicates

2026-10-29. Branch `rebuild`. Models, roster and debate rounds unchanged. Nothing pushed, nothing
deployed, no paid model call made.

## The gap

The Chair ran the room and reported it. Read in its own words, before today:

> name where they disagree, and write the room's complete answer: where it agrees, **where it
> splits and why**, and what the data cannot tell

and, in the fault-lines stage, *"Do not resolve them and do not take a side."* The verdict carried
`disagreements`: a list of sentences saying where the room still split. Nothing in the room ever
decided one of those splits.

That leaves the member holding the thing they are least able to do. A member who could weigh
Buffett's reading against Marks's from outside the room would not need the room. Reporting a split
is a faithful account of the proceedings and not an answer.

## The change

The Chair now rules on each fault line it named, after the final words, and the ruling is
structured rather than buried in prose. Three verdicts, and only three (`engine.RULINGS`):

| verdict | means | what the grounds must say |
|---|---|---|
| `settled` | the evidence settles it | which figure, which dataset, whose reading it supports, and why the other does not survive it |
| `unsettled` | the evidence cannot settle it | which figure is missing, withheld, or on a period that cannot be compared, and what would settle it |
| `judgment` | not a disagreement about the data | which figure each side is weighting, and why that is a matter of judgment rather than of fact |

**The third verdict is why there are three.** A room can disagree about what figures are *worth*
rather than about what they *are*. A Chair with only "settled" and "unsettled" would have to dress
that as a finding, and a manufactured resolution is worse than an open question. The chair's brief
says so in those words.

**`unsettled` is a ruling, not a failure to rule.** Saying which figure would have decided it tells
the member more than "they disagreed" does — and after Priority One the Chair has the material for
it: P9's `limitations` and every calculation that came back `missing` instead of a value.

**A head count is never grounds.** The engine's tally of final leans stays what it was — the
engine's own arithmetic, which the Chair may quote — but the brief is explicit:

> One advisor against five is settled for the one if the one holds the figure: you are ruling on
> the evidence, not counting hands.

### Neutrality, reconciled rather than left to contradict

"Who the Chair is" said the Chair *"never takes a side in the room"*. Left alone, that would have
contradicted the new duty in the same prompt, and the model reads both. It now says what neutral
actually has to mean here:

> Neutral means the Chair arrives with no position and favours no advisor, not that it declines to
> decide. ... So the Chair rules: on the figures in the pack, never on a head count, and it rules
> that the evidence cannot settle something as readily as it rules for one side. What it may never
> do is invent the grounds — a ruling rests on a figure an advisor cited or a gap the data itself
> declares.

The fault-lines stage is unchanged and still says "do not resolve them": it runs *before* the
challenges round, so resolving there would pre-empt the debate the room exists to have.

### What the engine enforces

- A ruling whose verdict is not one of the three is **refused**, and the Chair is asked again with
  the three named. "The room split", offered as a ruling, is exactly what this stage exists to
  stop.
- A Chair that named fault lines and returned no rulings is **refused**.
- A ruling with no grounds is **flagged** (`flags.unruled` names it) rather than refused — a
  verdict with nothing behind it is the failure mode of asking for one at all, and it should be
  visible rather than fatal.
- `disagreements` is no longer asked for. It is assembled from the rulings that are **not**
  settled, in the Chair's own words, so what the room settled is not also listed as an open split.
  The engine joins the Chair's text; it writes none of its own.
- Grounds go through the same checks as any other text the room writes: figures cited to their
  dataset, unverified figures flagged, advice removed.

### On screen, and for sessions held before today

The verdict shows a rulings block, each ruling marked with its verdict (`data-ruling`), with
labels in English and Arabic. Sessions held before today carry `disagreements` and no rulings, and
render exactly as they did — the same pattern the room already uses for the scored sessions held
before 2026-10-24.

`web/scripts/check-advisors.mjs`, the existing offline checker, reports one line per locale: how
many of the fault lines the Chair ruled on, and the mix of verdicts. Reported rather than failed —
which way a ruling goes is the Chair's to decide on the evidence, and a room where every ruling
came back `judgment` is worth looking at rather than worth failing. The count against the fault
lines is the part that would show a fault line going unruled.

## What is not known yet

**Whether the rulings are any good is unmeasured**, for the same reason as Priority Two: it needs
a real session, and paid calls are not authorised. The shape is enforced and the three verdicts are
offered; whether a model chooses among them honestly is the open question.

Two failure modes to look for in the first paid run, in this order:

- **Everything comes back `judgment`.** The easiest verdict to write is the one that decides
  nothing, and it is available by name. If the mix is all `judgment`, the Chair is declining to
  decide with extra steps. The checker's verdict mix is there to show it.
- **`settled` on grounds that do not settle anything.** The more expensive failure: a confident
  ruling resting on a figure that does not bear on the dispute. Nothing automatic catches this —
  the grounds have to be read against the fault line. `flags.unruled` catches only the empty case.

A third, smaller: the Chair quoting the lean count *as* the grounds. The brief forbids it in two
places, and it is the first thing to grep the grounds for.

## Files

| file | what |
|---|---|
| `api/app/advisors/chair.md` | the Chair is the room's adjudicator; the answer stage rules on each fault line, with the three verdicts and a majority ruled out as grounds |
| `api/app/debate/engine.py` | `RULINGS`, the verdict shape asks for rulings, `check_verdict` validates them, derives `disagreements` and flags `unruled` |
| `api/app/debate/standin.py` | a session without a model still rules, honestly `judgment` |
| `api/tests/test_debate.py` | 7 new tests |
| `web/src/lib/debate.ts`, `web/src/components/debate/Transcript.tsx` | the `Ruling` type, the rulings block, `data-fault-line` and `data-ruling` |
| `web/messages/en.json`, `web/messages/ar.json` | the heading and the three verdict labels |
| `web/scripts/check-advisors.mjs` | rulings against fault lines, and the verdict mix |

Suite: **529 passed, 11 skipped** (522 after Priority Two).

Raw output — the three verdicts, a checked verdict with its rulings, what is refused, and the
Chair's own words — is in `docs/verification/priority-one-closeout-2026-10-29.md`, section 9.
