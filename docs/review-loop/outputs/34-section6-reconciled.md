# Output 34: PROJECT.md §6 reconciled with the recorded outcomes (review 33's step)

Only `PROJECT.md` changed, and only inside §6. `git diff --check` is clean. No historical evidence was deleted:
each stale paragraph keeps its text. It gains a dated *(Superseded …)* note naming the outcome that replaced it,
and its status words move to the past tense, so it can no longer be read as current.

| §6 paragraph | Said | Now says, with the record it rests on |
|---|---|---|
| All three priorities | "delivered on `rebuild`" | **Released on both tiers in `df83e19404`** (2026-11-02, §9 item 3 Phase A). One real-model session on beta passed (A3, 53/0). Differentiation still needs the paid pilot (§9 item 4). |
| Priority Two | "in the prompts and unmeasured" | Released 2026-11-02, still unmeasured. **"Priority Three … is not started"** is struck through: it was built and released in `df83e19404` (`api/app/debate/engine.py`). |
| Priority One | "waiting on the owner to apply it" | Superseded. Both patches were applied 2026-11-02 on "Yes, all tonight", checked and KEPT (B2–B6), and published 2026-11-03 05:03 UTC. |
| Ingestion repair (both paragraphs) | "waiting on the owner" | Superseded. Applied and kept, LIVE since the 2026-11-03 publish. D3/D6 are still to be re-registered or retired (the owner's). |
| Evidence hole | "No Saudi company has an income statement" | Superseded. 250 Saudi income statements are live since 2026-11-03. D1/D3/D6 remain the owner's. |
| Gauge-vintage count | "1,891 … once the gauge patch is applied, 293 today" | The patch was applied 2026-11-02. 1,891 is the dry run's projection, **not re-measured since** (said plainly rather than claimed). |
| Release marker | current = `df83e19404` | Current = **`5c18a3ae46`** since 2026-11-05. Before it: `2e44ee6fbf` (11-03) and `df83e19404` (11-02). |
| OpenRouter | "stands at $4.74", the monitor's 15th check FAILING | Superseded. The owner reported the top-up on 2026-11-02 (§9 item 2). Claude cannot read the balance; the monitor confirms it. |
| Goal 1 | "the owner's private `alphacouncil-static`" | **Public by the owner's decision of 2026-10-30.** Monitor 13 ok then, 14 ok + renewals "–" on 2026-11-02. |
| Steps 22/23 (three paragraphs) | "on beta", "wait on … the production release", "not on production" | Superseded. **DONE and on production** since 2026-10-27: first shipped in `15f5bf8770`, live since `74ce427bf6`, matching their §7 status lines. "Not done" now names only the lawyer. |
| Benchmark | "blocked on a cap decision", Pilot 1 at $11, balance $4.74 | Its plan is superseded by §9 item 4: the $66 validation pilot, then cap $393, D1/D3/D6 first, account topped up. The 2026-10-28 analysis is kept below the note. |

**Checked and left as they are, because they are still true:**
- the statement repair, F-13, the labels, F-15, F-16 and F-14 (the first bullet, corrected in output 33);
- billing open, the owner's refunded payment and F-12;
- the released retry path and the acceptance round;
- the bank-class and dividends findings, which are the owner's;
- Copilot (e), Goals 2 and 3, `www`, and `set-backup-bucket.sh`.

Approval gates are unchanged.

**The question for the review:** is this sound, and what is the single next pre-approved step?
