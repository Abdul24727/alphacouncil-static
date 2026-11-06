# Output 35: review 34's two corrections, made

Commit `67d6b39`. It changes two files, `PROJECT.md` (§6 only) and
`docs/review-loop/outputs/34-section6-reconciled.md`. `git diff HEAD^ HEAD --check` is clean.

**1. F-7 in §6.** "F-7 (a failed turn's tokens unrecorded) is untouched and no longer bites: no turn failed" now
reads: **FIXED and released**. `SeatError` carries the `Usage` of its failed attempts, and `engine.turn` saves the
absent turn with it (`5f7221a`, 2026-10-27; §9's F-7 line). It also carries a correction note.
- **When it shipped:** with F-8's fix in `3228ab57e9`.
- **Where it is now:** in every release since, the live `5c18a3ae46` included.
- **Proof:** `git merge-base --is-ancestor 5f7221a 3228ab57e9` and `… 5c18a3ae46` both succeed.

**2. Output 34's file list** now says commit `2b06b2c` changed two files: `PROJECT.md` (only inside §6) and the
output itself. It carries a correction note.

**Also checked, not changed:**
- **§6's other open-sounding words:**
  - "no longer pending", and the lines under Superseded notes, which are historical;
  - "Production's speed with it not yet re-measured" (Copilot option (e)). No later record measures
    Copilot's speed on production, so that line is still true.

**The question for the review:** is this sound, and what is the single next pre-approved step?
