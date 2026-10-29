# Acceptance review package

2026-10-29. Branch `rebuild`, 5 commits ahead of the Priority One work, 33 unpushed. Raw output
for every figure here: `docs/verification/review-package-2026-10-29.md`.

**Status: prepared and offline-tested.** The changes are written, the offline suite passes and the
behaviour below is measured against copies of the live databases. Integration is unverified —
nothing is applied, published, pushed or deployed — and the quality of the room's reasoning is
unverified, because that needs paid calls. My own "all three priorities are done" was too strong,
and two other things I said were wrong; both are corrected in §8.

Scope is frozen here. Nothing below adds a feature; the three closures are the three the review
asked for, and the two measurements are measurements of what already exists.

---

## 1. Contaminated bank percentiles cannot reach the Council

**What was wrong.** Correcting the classification inside P9 left the percentiles alone, and a
percentile is a rank inside the peer class the pipeline bucketed the ticker into. `compute_gauge_scores.py`
(stage 4) imports `compute_sector_averages.py`'s own `ticker_sector_class`, so one mis-bucketing
decides both the benchmark and the rank.

**Measured, by replaying both stages over a copy of the published database.** The replay with the
pipeline's own buckets reproduces **every one of the 1,954 published scores exactly** (0 differ),
which is what makes the second run worth reading. Moving the 140 uncorroborated "banks" out:

| peer class as published | scored rows | unmoved | move > 5 pts | move > 20 pts | median move | worst |
|---|---|---|---|---|---|---|
| `bank` (204 tickers, 53 in the Banks sector) | 196 | 34 | 91 | 0 | 4.8 | **18.2** |
| `non_bank` (408, short the 140) | 1,673 | 1,343 | 0 | 0 | 0.0 | 4.7 |
| `insurance` (41) | 85 | 85 | 0 | 0 | 0.0 | 0.0 |

**The resolution: withhold, not recompute.** Recomputing means changing the pipeline's bank
detection, which this round is not to touch. So every sector ranking whose recorded peer class is
`bank` is withheld — **196 of 1,954 scored rows, 10.0%** — with the reason on the metric. The value
is arithmetic on the company's own statements and survives; only the rank, which is a statement
about the other 203 companies, does not. The other two classes are kept, because withholding 1,758
rows over a worst case of 4.7 points would cost more than it buys, and the shortfall is stated
once on the strip (`ranking_note`) rather than left to be assumed away.

**On the review's caution, which is right.** A plausible ratio distribution is a sanity check, not
validation of a classification, and deposits or a lending balance are corroboration rather than
proof that a finance company belongs in a bank's peer group. Nothing here claims otherwise: the
corroboration test decides only whether a company is shown **bank evidence** — arithmetic on its
own balance sheet, which is as true for a financing company as for a bank — and **no** ranking
is shown to any company the pipeline filed as a bank, corroborated or not. The 64 that survive
corroboration are 53 Banks, 10 financing companies and one unlabelled; the distribution
(equity/assets median 40.28% → 10.89%, with three other bank ratios landing in textbook ranges) is
reported as the sanity check it is.

**Where it reaches the Council.** P2 is the `get_fundamentals` tool calling the same endpoint, so
the withholding reaches the pack with no second code path. P9 `limitations` says it in words for
the seat that reads them. **P5's peer list is unaffected** — it comes from the exchange's own
`sector_en` in the universe, not from this detection — and the limitation says so explicitly,
because a seat told that a peer group is wrong will otherwise distrust the peer list too.
Al-Rumayyan, the seat answerable for percentiles, now has that case in his mandate.

**Owner's, not mine:** fixing the detection and recomputing the rankings. Lifting the withholding
belongs with that fix — it is keyed on a dated measurement about 204 other companies, which an
endpoint reading one company cannot re-derive.

---

## 2. The vintage guarantee, narrowed and then extended to cover revisions

**The question put: does the guard identify the input snapshot, or only `period_end`?** It only
checked dates — fiscal year, then window end — so a source figure corrected **inside** the same
period kept both stamps, the guard passed, and a gauge computed from the old figure sat beside the
new one.

**What closes it, without a provenance redesign.** Every gauge already writes its operands into
`inputs_json`, and some of them name the line they came from: `<x>_label` names the line behind
operand `<x>`, and `debt_parts` is a label-to-value map. Those can be read back against the
statement as it stands. `revised_operand` does exactly that, and `stale_reason` now returns its
answer as a third kind of staleness.

**Validated, because a false positive here is worse than the gap.** Over the published database:
**0 of 6,237 gauge rows flagged** on an unmodified copy. Then 20 companies' revenue line revised by
3% inside its own fiscal year and period: **20 of 20 caught**, each naming the label and both
figures. The first attempt caught 19 — a materiality floor of 0.01 (ten thousand currency units)
swallowed a 3% revision on a company whose revenue is 0.19 million. Both sides read the same
column and the gauge stage does not round what it records, so the comparison is now exact to float
round-tripping and materiality is left to the reader, who is given both numbers.

**The narrowing, stated per metric rather than in a paragraph.** Each gauge now carries
`vintage: "inputs" | "period"`.

| | rows | name an operand | and a year stamp |
|---|---|---|---|
| `debt_equity` | 653 | 625 | — |
| `net_margin` | 653 | 293 | **293** |
| `ps` | 653 | 293 | — |
| `gross_margin` | 653 | 293 | — |
| `roic` | 653 | 216 | — |
| `interest_coverage` | 653 | 171 | — |
| `current_ratio`, `ev_ebitda`, `fcf_yield`, `payout` | 2,612 | **0** | 0 |
| total | 6,530 | 1,891 | 293 |

Today the check reaches **293 of 6,530 rows**, because only `net_margin` records a year. The
prepared gauge patch stamps `fiscal_year` on every row, which takes it to **1,891 of 6,530 across
six gauges**. The four gauges that record no line name can never be reached as they are written,
and for them the guarantee is the period only — reported as `vintage: "period"`, not implied to be
more. One silent gap turned up while measuring this: `tax_label` names the operand `taxes`, not
`tax`, so `roic`'s tax line was read back for **0 of 653** tickers instead of 216, and a check that
never runs reports nothing. One alias, with the measurement in the comment.

**Owner's, if wanted:** having those four gauges record their line labels, which is a pipeline
change and would take the reach to near-complete.

---

## 3. The supported average-share and EPS basis, documented and enforced

**The question put: a working `mean` rule is coverage, not correctness.** Agreed, and the data
makes the point sharper than the argument does. There are **four routes** a share count can take to
a window, and they are now named in code (`EPS_BASES_SUPPORTED` / `EPS_BASES_UNSUPPORTED`):

| route | supported | what was measured |
|---|---|---|
| `annual_column` — the filer's own annual weighted average | yes, nothing constructed | 136 of 165 share rows in the repaired dry run; **382 of 653** derived EPS figures on the published database are on this basis and no other |
| unchanged position — a closing count identical in every quarter | yes, the mean of identical numbers is that number | the whole of the Tadawul case today: **not one** share count moves, 0 of 16 position rows |
| `single_quarter` — one quarter's own average | yes, against that quarter's earnings | — |
| `mean_of_quarters` — a mean **this pipeline** took over four quarterly columns | **no, now withheld** | fires twice in the repaired dry run |
| a closing position that moved inside the window | no, withheld before today | never observed |

**Why the constructed mean is withheld.** Three things would have to hold and none is established:
each quarterly column is that quarter's own average rather than a year-to-date one; the four
quarters are of equal length; and no share issue fell inside one. The first cannot be settled from
current data at all — the two readings differ only where the count moved, and no count moves
anywhere in the universe. And the quarterly columns the mean was taken over are **not retained**:
the one-window-per-section rule keeps the TTM row and discards the quarters behind it, so the mean
cannot be checked against its own inputs by a seat or by anyone else. A plausible wrong denominator
is the worst kind, so the figure is withheld and names all three conditions plus the supported
bases.

This is not extended into a general treatment of corporate actions. The rule is only: **the basis
is named or the figure is not given.** All three demonstration companies use the unchanged-position
basis, and their derived EPS is confirmed against the statement's own per-share line to within 2%.

---

## 4. The three cases, as they now stand

Full packs, before and after, with nothing truncated: raw output §6. The figures are unchanged
from the closeout; the only addition is the ranking limitation.

| | Aramco `2222` | Al Rajhi `1120` | SABIC `2010` |
|---|---|---|---|
| P9 before → after | 4,243 → **10,843** chars | 7,215 → **14,863** | 4,198 → **9,543** |
| budget headroom (16,000) | 5,157 | **1,137** | 6,457 |
| income statement | TTM@2026-06, 18 rows, `sum_quarters` | TTM@2026-06, 24 rows | TTM@2026-06, 15 rows |
| balance sheet | Q@2026-06 | **Q@2026-06 — the same date** | Q@2026-06 |
| derived EPS | 1.6875 vs the statement's 1.69 | 4.4164 vs 4.42 | **−7.1074** vs −7.11 |
| ROE (denominator named) | 26.0199% | 21.9588% | **−17.2605%** |
| payout | **79.4351%** cash and declared | 37.7381% | **withheld**: earnings not positive |
| extraordinary share | −8.9453% | 0.0000% | **−78.8496%** |
| sector ranking | kept, shortfall stated | **withheld** | kept, shortfall stated |

- **Aramco — the dividend window.** Four dividends with a pay date inside 2025-07-01..2026-06-30
  total 324,390 against net income 408,371. The fifth (ex-date 2026-08-19) falls outside, and a
  fiscal-year-label match would have counted it and reported ~99.5% — the difference between paying
  out four fifths of earnings and essentially all of them. A test asserts it cannot be counted.
  The cash-flow limitation is in the pack, so a seat can say Aramco paid 79% of reported earnings
  and **cannot** say whether it paid them out of cash.
- **Al Rajhi — aligned statements and bank measures.** Flow and position both struck at 2026-06.
  Nine bank measures with their denominators spelled out, including `equity_to_assets` 11.4407%
  labelled leverage and **not** a regulatory capital ratio, and `financing_to_deposits` 110.7119%
  on customer deposits only. The generic ratios come back `not_meaningful` with a reason rather
  than `missing_inputs`, because "missing" invites the wrong fix. **1,137 characters of headroom is
  the tightest case in the universe** and is the number to watch if anything is added to P9.
- **SABIC — a loss, the units, and the split.** Reported minus before-unusual is −16,812.35 and the
  statement's own extraordinary line is −16,812.35: the split is the statement's, not an inference.
  The unit is confirmed without a price/earnings ratio (−7.11 × 3,000 = −21,330.00 against reported
  −21,322.06), which matters because the pipeline publishes no `eps_ttm` for a loss-making company.
  `dps_window` still reports 3.00 a share paid against a loss of 7.11 a share while the payout
  ratio is withheld.

The `rank` column is empty in the demonstration because stages 3 and 4 need a universe to rank
inside and these scratch databases hold three companies. The rank behaviour is measured over all
653 tickers (§1).

---

## 5. The advisor mandates, side by side

Each advisor file carries an `owns` line (the dataset tags it is answerable for, validated at load)
and a `## Mandate` section (required for an advisor). The mandate is hoisted to the top of the
seat's system prompt, before the persona, and `Seat.brief` strips it from the body so it appears
exactly once.

| seat | owns | answerable for | the standing question, every session | when its own evidence is absent |
|---|---|---|---|---|
| **Buffett** | P2, P9 | earning power: what was earned, over which window, on what capital | are these returns real, what were they earned on, and over what period? | say plainly that a single window is not a record and do not treat it as one |
| **Lynch** | P7, P9 | the trend, quarter by quarter, from the standalone columns | does the quarterly record support the story the annual figures imply, and which way is it moving? | say the quarters are the whole history there is |
| **Dalio** | P2, P9 | the balance sheet: what is owned, owed, who funded it, what would strain it | how is this balance sheet funded, and what would have to happen for the funding to become a problem? | for a bank, read the leverage and funding measures and not a current ratio; supply no macro the pack does not carry |
| **Marks** | P1, P8, P9 | what the price assumes — **and, alone, what the evidence cannot answer** | what does this price have to be assuming, and what do we not know? | name the gaps aloud every session whether or not anyone asked |
| **Alwaleed** | P3, P9 | what has been returned to owners, and out of what | what was paid, over which window, out of which earnings, and what has been done to the share count? | say why a payout could not be computed: a loss, an unmatched window, or an amount the history lacks |
| **Al-Rumayyan** | P5, P6 | the company against its sector, and what it has itself disclosed | how does this company sit against the companies it is compared with, and what has it disclosed? | an absent percentile is not a low one; where the peer class itself is disputed the values stand and there is no rank to read |
| **Al-Rajhi** *(not seated — see §6)* | P9 | where the result came from, and a lender's own measures | was this result earned from operations, and for a lender, what do its own measures say? | use the statement's own split and say it is the statement's, not an inference |

**The partition.** Every dataset has an answerable seat except **P4**, deliberately: P4 is
rule-based votes from fixed thresholds, so nobody owns an opinion, and Marks — the one seat told to
read it — is told to say what it is and never to cite it as a figure. A test holds the partition,
so changing a mandate means deciding again who owns what.

**What a mandate is not**, from the shared rules: *"your mandate is what you are answerable for and
not the limit of what you may say: answer the member's question first, and disagree with any seat
about anything."*

**Thesis-rejection conditions are asked by the engine, not written into the mandates.** At the
`final` stage every advisor must return `would_change` — "what data would change it, one sentence"
— alongside `changed`, "what changed in your position during the room and why". So the condition
is produced per session and per company rather than standing in the seat file. Whether each seat
should also carry a standing rejection condition is a design decision I have not taken; the
mandates as written say what a seat is answerable for and what to say when its evidence is absent,
and that is all they say.

**Coverage is measured, flagged, never enforced.** A round-one answer citing none of its own
datasets carries `flags.uncovered`; `web/scripts/check-advisors.mjs` reports, per locale, how many
seats cited none of their own datasets and which owned datasets round one never cited. That script
drives the live screen and needs a running web and API, so it was **not run this round**; what the
offline suite does check is the advisor files themselves — every advisor has an `owns` line of valid
dataset tags and a `## Mandate`, the partition of P1–P9 holds, and the mandate reaches the prompt
exactly once. Flagged
rather than refused, because a seat may honestly find its evidence absent for this company and
saying so **is** covering the mandate. Measured on round one only: an opening is written without
seeing the others, so citing nothing of your own part there means your part went unread, while
reaching for another seat's dataset in a challenge is the debate working.

---

## 6. The Chair: instructions, ruling schema, and how limitations reach the answer

**Who the Chair is** (`chair.md`): *"A neutral moderator, not an investor, and the room's
adjudicator… Neutral means the Chair arrives with no position and favours no advisor, not that it
declines to decide. Naming a split and leaving it is no answer to a member who cannot weigh one
advisor against another from outside the room. So the Chair rules: on the figures in the pack,
never on a head count, and it rules that the evidence cannot settle something as readily as it
rules for one side. What it may never do is invent the grounds — a ruling rests on a figure an
advisor cited or a gap the data itself declares."*

**The three verdicts, one per fault line the Chair itself named.**

| verdict | the instruction | the case the review asked about |
|---|---|---|
| `settled` — the evidence settles it | name the figure, the dataset, whose reading it supports and why the other does not survive it | **a strong minority objection**: *"One advisor against five is settled for the one if the one holds the figure: you are ruling on the evidence, not counting hands."* |
| `unsettled` — the evidence cannot settle it | name the figure that is missing and what it would take | **insufficient evidence**: *"This is a ruling, not a failure to rule."* |
| `judgment` — not a disagreement about the data | say which figure each side weights and why that is judgment, not fact | *"Never dress a difference of judgment as a finding; a manufactured resolution is worse than an open question."* |

**Unsupported consensus** is handled by the grounds requirement rather than by a verdict: *"A
majority is never the grounds for a ruling. The count of the final leans is the engine's arithmetic
and you may quote it, but it tells the member what the room thinks, not what the data shows."* A
consensus with no figure behind it has nothing to rule on, and the honest verdict is `unsettled`.

**The schema the engine asks for and what it enforces.**

```
{"headline": "≤16 words, no figures", "answer": "the room's complete answer, 200–350 words",
 "favours": "(choice mode only) which reading the room favours and how firmly",
 "rulings": [{"on": "what the fault line was about", "between": ["advisor ids"],
              "verdict": "settled | unsettled | judgment",
              "grounds": "the figure it turns on and why it decides it, or which figure is missing"}],
 "gaps": ["what the data does not show that would have settled it, one sentence each"]}
```

- a `verdict` outside the three is **refused** and the Chair is asked again — "the room split"
  dressed as a ruling is the thing this stage exists to stop;
- fault lines named with **no** `rulings` at all is refused: one entry per fault line;
- `between` is filtered to seats actually in the room;
- `grounds` goes through the same citation check as every other turn, so a figure in it that
  appears nowhere in the pack is listed in `flags.unverified` — that is the check against invented
  grounds;
- a ruling with an empty `grounds` is listed in `flags.unruled`;
- `disagreements` (what the screens read) is **assembled** from the non-`settled` rulings rather
  than asked for twice; the engine joins the Chair's text and never writes any;
- the headline is refused if it reads as advice (no buy/sell/hold, no price target).

**How a material evidence limitation reaches the final assessment.** Four steps, each in code or in
a prompt: P9 carries `limitations` (and every `missing` on a calculation) → **Marks is answerable
for both** and is told to name them aloud every session whether or not anyone asked → his opening
and final word enter the transcript every later turn reads → the Chair rules `unsettled` naming the
missing figure, and lists it in `gaps`. Before the mandates, a gap in the data was nobody's job to
say out loud and could pass unmentioned by every seat in turn.

---

## 7. The active roster, models and rounds — unchanged

`api/app/settings.py` is **untouched** by any of this work (`git diff d5f2681..HEAD` is empty for
it). The only roster change is `owns` parsing and `Seat.brief`, +29/−3 lines; `MIN_ADVISORS,
MAX_ADVISORS = 2, 6` is as it has been since the room was built.

| | value |
|---|---|
| advisors seated (`debate_advisors`) | **6**: buffett, lynch, dalio, marks, alwaleed, alrumayyan |
| seats in the room | **7** = 6 advisors + the Chair |
| advisor model | `deepseek/deepseek-v4-pro` |
| chair model | `anthropic/claude-sonnet-5.5` |
| `debate_rounds` | **1** (clamped to 1–2) |
| stages | brief → openings → fault lines → debate ×1 → final → verdict |
| model calls per debate | **21** = chair 3 + advisors 6 × (2 + 1) |
| reasoning | off (`debate_reasoning: false`) |

**`alrajhi` is a seventh advisor *file*, not a seventh seat.** It carries a mandate and is loadable,
but `debate_advisors` does not name it and `MAX_ADVISORS` is 6, so seating it means **dropping one
of the six** — the commented example in `deploy/api.env.example` shows exactly that, `alrajhi` in
place of `alrumayyan`. That is the owner's decision and I have not taken it. If it never sits, its mandate
(P9: where the result came from, and a lender's own measures) is work no seated seat is answerable
for — the extraordinary split and the bank measures — and that is worth deciding rather than
leaving.

**What P9 costs, with the counting method.** Per call, mean of five real packs: **18,477 → 29,510
characters**, +10,372, **+56%**; in UTF-8 bytes 18,761 → 29,796. Across 21 calls that is
**+217,816 characters** a debate, and the pack is in every call's system prompt with no prompt
caching on the debate path. In tokens: the byte count, **217,867**, is a hard ceiling — no
byte-level BPE tokenizer emits more tokens than bytes — and the chars/4 divisor my earlier figure
used would say 54,454. **So the added input tokens are between about 54,000 and 218,000, and the
true figure is the provider's reported `prompt_tokens`, which needs a paid run.** `audit_tokens`
already compares the provider's count against the byte ceiling on every call.

**Truncation cannot remove an operand or a limitation, and never fires.** `fit()` drops whole
statement rows from the end of the longest section while over budget, and never a calculation, a
limitation, or a row a calculation divides by (protected rows are taken first — on a Tadawul
balance sheet the share count is the **last** row, and taking the first N dropped the denominator
of every per-share measure in the same dataset). `Pack.prompt()`'s `[:budget]`, which would cut
mid-row, is the backstop behind it. Measured: **0 of 653 datasets over the 16,000-character budget**
(largest 10,776 on the published database; 13,142 on the repaired parse with the longest possible
limitation forced on every company, 2,858 of headroom), and **limitations intact 653 of 653**. The
single lever is `evidence.DATASET_BUDGET`.

---

## 8. Offline checks passed, and what is still unmeasured

**Passed.** API suite **544 passed, 11 skipped** (531 before this round; 13 new tests covering the
three closures). Web typecheck clean, `openapi.json` and the web client types regenerated. Both
pipeline patches apply clean to the files now on the server, reproduce the tested files byte for
byte, and `patch -R` restores the originals byte for byte — re-verified today against fresh copies.
**One defect found in the prepared patch while re-verifying it:** its ranking comment and its log
line both named `compute_sector_averages.py` as the stage that writes `score`, which is the error
I corrected in the records on 2026-10-29 and had not corrected in the patch. The log line told
whoever ran it to run stage 3 after the gauge stage, which would leave every changed gauge with a
NULL score, because only stage 4 writes one. Both now name `compute_sector_averages.py` **and then**
`compute_gauge_scores.py`; the line counts are unchanged, so the hunks are untouched. The patched
gauge stage against the production one over all 653 tickers:
6,530 rows each, **0 rows whose value or status differ**. The ranking guarantee on live data:
refresh a line item, run the gauge stage alone → `current_ratio` 1.999 → 2.498 with its ranking
**cleared**, 0 values holding a new number under an old rank; stages 3+4 restore every ranking.
The three cases re-run after every change above and are **byte-for-byte identical** apart from the
added ranking limitation.

**Unmeasured, and only a paid session measures it.**

- Whether six mandated seats produce six differently-grounded answers. Three ways it goes wrong:
  a mandate **recited rather than used** (the coverage flag would read clean while the answers got
  worse); **narrower** answers if a seat treats the mandate as a ceiling despite the rule saying it
  is not; and P9's size against five of six seats being answerable for part of it.
- Whether the Chair's rulings evaluate arguments or satisfy the schema. The schema cannot tell the
  difference. Read three things first: the ruling count against the fault-line count, the mix of
  the three verdicts, and `flags.unverified` on the verdict turn. **Watch for everything coming
  back `judgment`** — the verdict that decides nothing is the easiest one to write, and it is the
  one the schema accepts most readily.
- The true input-token cost (above).
- Integration: no deployment, so the period-aware API has not been served from beta, and §8b
  (`periods` on `/statements`) remains a precondition — the API ships to beta **before** the
  database is published, though it works against either schema.

**An explicit product limitation, not a gap to be closed.** **No cash-flow statement exists for any
company: 653 of 653.** The source does not publish one on the pages the pipeline reads. So free cash
flow, capital expenditure, cash conversion and dividend cover against cash cannot be computed for
anyone, and dividend cover can only ever be tested against earnings. Every P9 pack says this in its
first limitation. It constrains conclusions; it does not block this release.

**Corrections to my own account.** (1) "All three priorities are done" — the accurate status is
prepared and offline-tested, as stated at the top. (2) "Seven mandated seats" — the room is **six
advisors and the Chair**; seven advisor *files* carry mandates and one of them does not sit.
(3) "+60,000 input tokens a debate" — the characters were measured, the token conversion was an
assumed chars/4 divisor, and the call count was wrong (I said 8 seats over three stages; it is 21
calls). The measured range is in §7.

**Left alone deliberately, each a separate scoped change for the owner:** the pipeline's bank
detection and the sector-average buckets it decides; `ingest_bank_metrics.py`, step 17 of the
nightly run, which defines six of these bank measures and writes **0 rows for 58 banks** while
exiting 0 — the Council's measures are computed independently from the parsed line items, so there
is no second implementation to keep, and that job is dead weight to repair or retire; dividend
collection beyond Tadawul (230 tickers, all Saudi), without which payout and yield cannot be
computed for any GCC company whatever the repair does; and having the four unreachable gauges
record their line labels.
