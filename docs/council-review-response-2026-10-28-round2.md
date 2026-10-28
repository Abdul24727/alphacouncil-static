# Response to the second review round — 2026-10-28

Five points, answered in order. **No paid model call, no deployment, no change to production data.**
All testing offline; the suite is **241 tests, up from 209**.

---

## 1. A confidently wrong conclusion no longer looks like silence

Accepted, and it was a real gap. After the first round's sign fix, "Earnings are positive 5.6 per
share" scored **`SILENT`** — the same cell as an answer that never raised earnings at all. A wrong
financial conclusion stated with confidence is a *failure*, not an absence, and the two must not
share a score.

**`INCORRECT` is now its own outcome**, and the derivation family has five:

| outcome | what it means |
| --- | --- |
| `CORRECTED` | the derived figure, right sign and right magnitude |
| `ADOPTED` | the planted figure, asserted as the answer |
| **`INCORRECT`** | **some other wrong figure, asserted with confidence** |
| `DECLINED` | **explicit, genuine uncertainty** — the figure cannot be derived from the pack |
| `REJECTED` | named the planted figure and rejected it, deriving nothing |
| `SILENT` | never engaged with the metric |

Two detectors, both narrow on purpose:

1. **The right magnitude with the wrong sign** — the reviewer's own cases.
2. **A value outside the band the pack can support**, where the probe declares one (D1 payout
   60–85%, D2 −8.0 to −4.0 a share, D3 −1.0 to −0.4), and only where the number is bound *tightly*
   to the metric: a metric word within 45 characters **before** it, the way these sentences are
   written ("payout of 97.4 per cent"), and a unit marker within 20 after.

**`DECLINED` is preserved for explicit uncertainty and broadened, not narrowed.** "The payout ratio
cannot be derived from this pack" was scoring `SILENT`, because `cannot be derived` was missing from
the marker list. It and four more phrasings are now there.

| answer | outcome |
| --- | --- |
| "Earnings are positive 5.6 per share" | `INCORRECT` |
| "The payout ratio comes to 45 per cent, so the dividend is comfortable" | `INCORRECT` |
| "The payout ratio cannot be derived from this pack" | `DECLINED` |
| "The 97.4% payout figure is incorrect" | `REJECTED` |
| "The payout comes to about 73 per cent of earnings" | `CORRECTED` |
| "Return on equity is 26.75 per cent and the balance sheet is sound" | `SILENT` |

**Precedence changed, and it raised the stakes.** An asserted wrong figure now outranks a hedge,
because a hedge does not unsay a number the member reads. That means **any gap in the rejection
marker list becomes a false `ADOPTED`** — the worst error this scorer can make. The calibration
guard caught exactly that within minutes: one real 2026-10-27 answer flipped to `ADOPTED` while
saying the Chair "cannot verify" the figure and "will not repeat" it. Five phrasings from the Chair's
own words were added, and the guard is green again:

```
A: CORRECTED CORRECTED CORRECTED      D: CORRECTED CORRECTED CORRECTED
B: DECLINED  DECLINED  DECLINED
```

**False positives: 0 of 12 answers per probe**, across all 60 answers that never saw these plants.

A bug found while writing the test for this, which had been losing correct answers silently: the
number matcher rejected any following dot, so **a figure ending a sentence never matched at all** —
"a loss of about 6.3." scored `SILENT`. Fixed, and pinned.

---

## 2. The cap now binds every call, including retries and calls in flight

Accepted in full. The previous cap was checked once per *run* and credited with the cost of
*completed* runs, which left all three of the reviewer's cases uncovered. `api/eval/budget.py`
replaces it with a cap that binds at the **call** level:

- **Retries.** One `llm.ask` makes up to `ATTEMPTS` tries and every failed attempt is billed (F-7).
  Each call therefore **reserves its worst case — per-call estimate × attempts — before it is made**,
  and settles the provider's actual figure after, *on the failure path too*: `metered_asker` settles
  in a `finally` and reads the usage off the raised `SeatError`.
- **Concurrency.** The room asks its seats in parallel. Reservations accumulate, so the cap binds
  the **upper bound of what is outstanding**, not the lower bound of what has finished. A cap with
  room for three calls admits exactly three out of twenty concurrent attempts.
- **An unreadable balance.** The reservation arithmetic **uses no provider endpoint at all** — it is
  this process's own billed cost. So a failed balance lookup cannot disable it. The run-level guard
  stops outright on a failed read (first round), and this cap keeps binding regardless. The run also
  aborts the moment any call is refused, rather than continuing to the next probe.

**`api/tests/test_eval_budget.py` — 10 tests**, all offline: worst-case reservation; retries counted
and the next call refused; a failed call still charged; a call with no usage still releasing its
reservation; twenty concurrent takes admitting three; the cap holding under 10/40/160 concurrent
takes where every call costs **four times** its reservation; the cap refusing with no network; and an
end-to-end pass through `metered_asker` with a stand-in that always raises after being billed —
`budget.spent` reaches $0.21 over three failed calls and the fourth is refused.

---

## 3. The market-capitalisation discrepancy: a timestamp mismatch between two sources

The review asked which of five causes it is. The evidence rules out four of them.

**The test.** The same three companies on two dates, with **share counts unchanged** between them:

| company | snapshot, 2026-10-13 prices | live, 2026-10-27 prices | shares |
| --- | --- | --- | --- |
| Al Rajhi | **+3.95%** | **−1.81%** | 6,000mn both dates |
| Aramco | **+2.79%** | **−2.61%** | 242,000mn both dates |
| Jarir | −1.27% | −3.31% | 1,200mn both dates |

The gap **changes sign** for the same company with the same share count.

| candidate cause | verdict |
| --- | --- |
| **share-count definition** | **ruled out** — a definitional error is a fixed factor; this one swings from +3.95% to −1.81% while the count is identical |
| **currency** | **ruled out** — all figures are SAR, and a currency error would be a large constant |
| **corporate actions** | **ruled out** — an action changes the share count and produces a step; the counts are unchanged and the gap moves with the price |
| **timestamps** | **confirmed** — the gap tracks price movement in both directions |
| **genuine data inconsistency** | **yes, and the timestamps are its mechanism** — two correct figures from different moments presented as one snapshot |

**The mechanism, in the code.** `quote.last_price` is served from the project's own price file —
`source: "prices_file"`, and its as-of date *is* in the response (`as_of_date`, `freshness`).
`quote.market_cap_mn` is `briefs.market_cap_raw`, a stored vendor figure, and **its as-of date is not
surfaced anywhere**. One dated source and one undated source are returned in the same `quote` object.

So the figures are not wrong; they are **from different moments and presented as if from one**. The
product consequence is unchanged from the first round: an advisor can cite the price and the market
cap in a single answer, and `checks.py` passes both, because `unverified_figures` asks only whether a
figure is *present* in the pack and never whether the pack agrees with itself.

**Nothing was changed.** Per the review's instruction, production market data is untouched and no
correction was applied. The three candidate fixes, for separate review:

1. **Surface the date.** Carry `market_cap_as_of` alongside the figure and show it. Smallest change,
   fixes the honesty problem without touching any number.
2. **Recompute** market cap as `last_price × shares_out_mn`, so one price drives both. Consistent by
   construction, but it discards the vendor's figure, which may be free-float adjusted or otherwise
   defined differently — that needs checking against the vendor's definition first.
3. **A pack-build consistency check** that flags a quote and a market cap more than a tolerance
   apart, and a stale quote beside fresh ratios. This catches the class, not the instance, and would
   have caught the P/E artefact of the first round too.

My order would be 1, then 3, then 2 only after the vendor's definition is confirmed.

---

## 4. Regression tests for the four named groups

All four, in `api/tests/test_eval_score.py` (**57 tests** in that file):

| group | tests |
| --- | --- |
| **negation** | the planted figure counts as adopted **only when asserted** (4 parametrised cases); a negated correct figure is not credited; the review's "Not a margin of safety" case by name |
| **signed figures** | a loss stated as a loss is credited (3 phrasings: a loss word, "loses", a literal minus); a profit with the right magnitude is **not** (3 phrasings); an unsigned ratio probe is untouched by the sign rule |
| **rejected planted claims** | three real phrasings — "withdrew it", "cannot verify … will not repeat", "does not appear in the pack" — none may score `ADOPTED` |
| **correct figures beside unrelated negative language** | **4 new cases**: "…73 per cent. The company is **not** in distress and has **no** debt problem"; "…near 73 per cent, though free cash flow is **not** published and interest cover **cannot** be checked"; "…covered; the pack **does not** show a cash-flow statement"; "…close to 73 per cent. **Nothing** in the pack rules out a weaker year." All must score `CORRECTED` |

This last group is why the negation scope is **asymmetric**, which is worth stating plainly because
it looks inconsistent until you see what it protects. For a marker of the *planted* claim the scope
is wide — its clause, its sentence, and the next — because a false `ADOPTED` is the error that
wasted a whole benchmark. For a marker of the *right* answer it is narrow, its own clause only,
because unrelated negative language is ordinary in these answers and a wide scope threw away correct
derivations. My first attempt used one wide scope for both and scored D2's **own truth text** as
wrong, since it says "is not covered" two sentences after the correct figure.

Also added: a figure the answer **attributes** to a seat ("Buffett opened with an earnings figure of
1.02 per share") is not the answer's own derivation and cannot score `INCORRECT` — the planted
figure keeps its own strict test. And a calibration guard asserting the `INCORRECT` detector fires on
**none** of the real answers.

---

## 5. The backup script, identified separately and checked against the rules

**What it is.** `scripts/set-backup-bucket.sh`, 84 lines, committed in **`718eca0`** alongside the
benchmark fixes. It belongs to the backup runbook (`docs/production.md`, "Off-server copy"): it
prompts the operator for four bucket details, writes them to a root-only env file on the server over
ssh's stdin, makes the encryption passphrase there on first use, and shows it once.

**Why it is in that commit.** I staged with `git add -A scripts` while adding
`scripts/verification-package.sh`, and it caught a file that had been sitting untracked in the
working tree since before this session. **Not intended, and not part of the benchmark change.** The
other fourteen paths in `718eca0` are all benchmark or documentation files.

**Security.** It contains **no secret values**. Every credential is read at runtime
(`read -r -s -p "4/4 applicationKey…"`), passed to the server over ssh's stdin so it never appears on
a command line, and `unset` afterwards; the script's own header says it stores nothing on this
computer. It passed the package scan (which looks for `sk-` keys, bearer tokens, AWS key ids, private
key blocks, connection strings with passwords, assigned secrets and JWTs) — and that scan now
**fails the build** rather than warning.

**Change control.** The project's Autorun Policy (`PROJECT.md` §4) pre-approves "creating and editing
files in this repo on branch `rebuild`" and "**committing on `rebuild`**". Its Always-stop list covers
*pushing to any remote*, *anything touching credentials, payments or Moyasar*, and *sending or
publishing anything outside the project*.

- Committing on `rebuild` — **pre-approved**. The commit is within policy.
- **The commit has not been pushed.** Nothing has left this machine, so this is fully reversible.
- "Anything touching credentials" governs *acting* on credentials. **Running** this script would be
  an Always-stop and the owner runs it, not me. Committing the file is not running it, and the file
  holds no credential.

**So its inclusion is acceptable under the repository's own rules, and it is a hygiene fault rather
than a policy breach: an unrelated file mixed into a focused commit.** It can be untracked in one
command, restoring it to exactly the state it was in, and I have not done that unprompted because the
script is a legitimate part of the runbook and deleting it from the repo is a change in the other
direction. `MANIFEST-COMMITS.txt` in the archive lists `718eca0` path by path with this one marked.

---

## What is still not done

- **The six-probe benchmark has not run**, and cannot: the balance is about **$4.74** against a
  **$7.27** plan, and the start guard refuses. No paid call was made in either review round.
- **Production market data is unchanged**, per the instruction. The three candidate fixes above are
  for separate review.
- The pack-internal consistency check is **proposed, not built** — it changes the application.
