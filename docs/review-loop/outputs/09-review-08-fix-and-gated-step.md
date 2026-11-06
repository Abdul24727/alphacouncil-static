# Output 09: review 08's fix, and its next step held for the owner

Commits `f2fc5b0` and `4f787b3`.

**Review 08's issue, fixed** (`docs/release-readiness-2026-11-06.md`): the paragraph now separates the
rendered samples from the full sweep.
- The rendered samples are AMLAK and AMCREIT, 15–16 cash-flow lines per panel.
- The full sweep found **18 labels across eight companies**: ADAV.AD, AMCREIT, AMLAK, DSI, DUBAIRES, EMSTEEL,
  QIC and UPP. I re-derived that list from the live database labels against the current dictionary, rather
  than reading it off the sweep log, which prints only examples.
- Their removal by the 05:00 UTC publish is stated as **expected and unverified** until the after-publish
  checks run.

**Review 08's next step needs the owner's go-ahead, so it was prepared, not applied.** The step was the
`check-advisors.mjs:51` `owns` case fix.
- The owner's standing word is to ask before applying it, as a behaviour change to a check script.
  `PROJECT.md` §9's note on it says "Not applied - it is a change to a check script and nobody asked for it".
  A review cannot grant that go-ahead (master plan, "Rules no review can change").
- What exists:
  - `docs/check-advisors-owns-case-2026-11-06.patch`: `.trim()` becomes `.trim().toUpperCase()`, plus one
    comment line. `git apply --check` is clean, and the working tree is unchanged.
  - A demonstration on the parser alone: `owns: p2, P9` reported `["p2"]` missing before and `[]` after,
    the same as `owns: P2, P9`.
  - The owner is being asked. The §9 list of the owner's go-aheads names it.
- Unchanged: syntax, lint and tests (nothing applied).

**Server:** the nightly started at 00:00 UTC and is running. F-16's after-publish check is due after
05:00 UTC.

**The question for the review:** is the fix sound, and what is the single next step Claude may take now
**without** an owner go-ahead (pre-approved work only), while the owner decides on the patch and the
publish is still ahead?
