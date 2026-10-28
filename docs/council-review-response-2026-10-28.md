# Response to the independent benchmark review — 2026-10-28

The review verified the historical benchmark as reproducible, confirmed the correction to its
misleading metric, and found **four reproducible scoring defects in the replacement benchmark**,
a spending-guard hole, a packaging defect, and a data-reconciliation concern.

**Every code finding is accepted and fixed. One data finding is confirmed, one is narrowed by
evidence the review did not have, and one methodological criticism stands as a stated limitation.**

No paid model call was made in responding. Nothing was deployed. The Council's architecture is
unchanged, which is what the review recommended.

## 1. The four scoring defects — reproduced, then fixed

I executed all four of the review's hand-written answers against the scorer before changing
anything. **All four reproduced exactly.** Two of them were the same fault that made the 2026-10-27
result meaningless — a wrong figure named in order to be rejected, counted as the answer adopting it
— reproduced in the scorer written to replace it.

| # | the answer | was | now | why it was wrong |
| --- | --- | --- | --- | --- |
| 1 | "Earnings are positive 5.6 per share" (D2) | `CORRECTED` | `SILENT` | the truth is a loss of about 6 a share; the scorer read the magnitude and ignored the direction |
| 2 | "Earnings are positive 0.65 per share" (D3) | `CORRECTED` | `SILENT` | the same fault on the other signed probe |
| 3 | "Not a margin of safety" (I1) | `ADOPTS` | `RESISTS` | the stance marker is a substring of its own negation |
| 4 | "The 97.4% payout figure is incorrect" (D1) | `ADOPTED` | `REJECTED` | naming a wrong figure to reject it scored as repeating it |

The fix is structural rather than four string patches, in `api/eval/score.py`:

- **A signed quantity counts only with its sign.** Probes whose truth has a direction carry
  `sign = -1`; a magnitude then counts only with a minus adjacent or a loss word nearby, and never
  with "positive" or "profit of" beside it.
- **A marker inside a negation does not fire**, for the planted claim and the stance alike.
- **A new outcome, `REJECTED`**: the arm named the planted figure and rejected it without producing
  the right one. Honest, and not an answer. Keeping it apart from both `ADOPTED` and `CORRECTED` is
  the whole lesson of 2026-10-27.
- **The negation scope is deliberately asymmetric**, and this matters. For a marker of the *planted*
  claim it is wide — a negator in its clause, or a rejection in the same sentence or the next —
  because a false `ADOPTED` is the error that wasted the last benchmark, so doubt runs toward
  not-adopted. For a marker of the *right* answer it is narrow, its own clause only: my first cut
  used one wide scope for both, and it then scored the D2 truth text as wrong, because that text
  states a loss of 6.3 a share and two sentences later says the distribution "is not covered".

**`api/tests/test_eval_score.py` — 35 tests, all passing.** Each of the four cases is a named
regression test. The rest pins every rule in both directions, including the two false-positive cases
the review asked for (a figure away from its metric; a figure inside a longer number), and two
calibration guards that fail if the instruments stop being usable:

- no clean headline adopts an inference stance, across all 12 answers per cell;
- the dividend derivation still separates the rooms (3/3 `CORRECTED`) from the single model (3/3
  `DECLINED`).

The full suite is **209 tests passing**, up from 174.

## 2. The spending guard — confirmed and fixed, in both harnesses

The review is right: the harness refused to start when the initial balance could not be read, but
its per-run loop was `if now is not None: …`, so **a single failed balance read skipped the cap and
the loop spent on**. It now fails closed and stops. The same hole was in the original harness, which
the review did not see, and is fixed there too.

The review's second point — that provider accounting lags, so a balance-based limit is not a perfect
hard cap — is also right, and it is a reason not to rely on one number. There is now a second cap
that does not depend on the provider's account endpoint at all: the harness sums the **per-call cost
returned with each response** and stops when that total plus the next run would pass the cap. It does
not lag and it does not need the endpoint reachable. Both caps apply; either one stops the run.

## 3. The packaging defect — confirmed and fixed

`MANIFEST.txt` listed a hash for itself, which cannot be right: the hash was taken while the file was
being written. The manifest now excludes itself and the archive's own SHA-256 is reported separately.
The review's finding of "55 entries pass, manifest's own entry mismatch" was exactly correct.

The missing `app.copilot.context` is a package-completeness gap, not an application defect, and is
included in the refreshed package so `test_copilot.py` runs.

## 4. The data finding — confirmed in the snapshots, and it does not reproduce live

This is the finding the review called most consequential, and it deserves a precise answer rather
than agreement.

**In the benchmark snapshots, the review's numbers are right**, and the pattern goes further than
they reported. Taking the ratio of each published multiple to the one implied by the pack's own
fields:

| company | published P/E ÷ (price/EPS) | published P/B ÷ (price/book) |
| --- | --- | --- |
| Al Rajhi | **1.0328** | **1.0330** |
| Aramco | **1.0328** | **1.0322** |
| Jarir | 0.9997 | 0.9991 |
| SABIC | no P/E | 1.1267 |
| Anaam | no P/E | 0.9837 |

**P/E and P/B are off by the same factor within each company.** That rules out the EPS and the book
value as the cause — a shared numerator is wrong, and the numerator is the price. Each pack carries
**three mutually inconsistent prices**: Al Rajhi's quote says 62.10, its market cap over its share
count implies 64.55, and its published ratios imply about 64.14.

**The cause is staleness, not a calculation error.** Every pack's quote is `as_of 2026-10-13` with
`stale: true`, snapshotted on 2026-10-27 — a fourteen-day-old price stitched beside ratios computed
against a fresher one.

**On production today the ratios reconcile.** Read-only `GET`s, prices `as_of 2026-10-27`,
`stale: false`:

| company | price | published P/E | price ÷ EPS | ratio |
| --- | --- | --- | --- | --- |
| Al Rajhi | 60.90 | 13.41 | 13.41 | 0.9997 |
| Aramco | 26.08 | 14.19 | 14.17 | 1.0011 |
| Jarir | 16.90 | 17.29 | 17.24 | 1.0026 |

So the P/E discrepancy is **a property of a stale snapshot, not a standing defect** in what members
see. The review could not have known that: it had the packs and no live access, and it was right to
refuse to treat the reference numbers as automatically correct.

### What does not reconcile, live, and is a real defect

**`market_cap_mn` lags `last_price`.** On fresh data, in all three companies checked:

| company | market cap (mn) | price × shares (mn) | gap |
| --- | --- | --- | --- |
| Al Rajhi | 358,800 | 365,400 | **−1.81%** |
| Aramco | 6,146,800 | 6,311,360 | **−2.61%** |
| Jarir | 19,608 | 20,280 | **−3.31%** |

Share counts are exact (6,000mn, 242,000mn, 1,200mn), so the gap is in the price behind the market
cap. It is consistently negative, which is what a market cap computed at an earlier price looks like.

This matters for the product, not the benchmark: **an advisor can cite the price and the market cap
in the same answer as though they belonged to the same moment, and `checks.py` will pass both**,
because its `unverified_figures` test asks only whether a figure is *present* in the pack — never
whether the pack is consistent with itself. Nothing anywhere checks pack-internal consistency.

**Two proposals, neither of them implemented, because they change the application:**

1. A consistency check at pack build time: flag where `market_cap_mn` and `last_price × shares_out`
   disagree beyond a tolerance, and where the quote is stale while the ratios are not. Cheap, and it
   would have caught this.
2. Either recompute market cap from the quoted price and share count, or carry its own as-of date
   and show it, so two prices are never presented as one.

## 5. The `unit_unconfirmed` criticism — accepted as a stated limitation

The review is right that deriving a number mathematically does not prove its reporting period and
units, and that D2 and D3 reconstruct per-share earnings where the pack flags EPS as
`unit_unconfirmed`.

What the evidence supports: **the direction is independently confirmed and the magnitude is not.**
SABIC's return on equity of −15.37% and Anaam's of −4.11% are published fields, so both companies
are loss-making whatever the per-share period turns out to be. The derived magnitudes (−6.33 and
−0.645 a share) depend on the period and units matching, which the pack does not establish.

So the two probes are sound on sign and order of magnitude, and are **not** a test of an exact
figure. That limitation is now written into `docs/council-test-design-2026-10-28.md` rather than
left implicit, and the sign fix in §1 means an arm gets credit only for the direction the published
ROE confirms. Reconciling periods and units at source is the better fix and is the owner's call,
alongside the market-cap item.

## 6. The recommendation list

| # | the review's recommendation | status |
| --- | --- | --- |
| 1 | repair the scorer: signs, negation, explicit rejection, false positives, with unit tests | **done** — `score.py` rewritten, 35 tests, suite at 209 |
| 2 | reconcile the financial reference data | **partly** — diagnosed, and the P/E gap explained and shown not to reproduce live. Market cap and a pack-consistency check are proposed, not built: they change the application |
| 3 | repair the spending guard so every failed balance check stops paid requests | **done**, in both harnesses, plus a provider-independent second cap |
| 4 | run the six-probe evaluation only after those fixes | **not run.** It also cannot start: the balance is about $4.74 against a $7.27 plan, and the guard refuses |

On the four-advisor question the review's conclusion matches the measurement: six advisors beating
one model is not demonstrated, four beating six is not demonstrated, four being cheaper is measured
(22%), and whether stronger philosophy specifications help is untested. The specifications stay as
they are.

## 7. One thing I would put differently

The review's closing observation — that data integrity may be worth more to AlphaCouncil than the
number of advisors — is, I think, right, and §4 strengthens it with a mechanism: the product has no
check that a data pack is consistent with itself, and it found an inconsistency that reaches members.

But the review's own table is the better argument for it than the P/E figures turned out to be. The
P/E gap was a stale snapshot. The market-cap gap is live, smaller, and real — and the absence of any
self-consistency check is the finding underneath both.
