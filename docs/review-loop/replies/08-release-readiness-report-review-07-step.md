# Review 08: Release-readiness report (review 07 step)

2026-11-06 00:10 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `08-release-readiness.md`.

VERDICT: FIX

ISSUES:

1. `docs/review-loop/outputs/08-release-readiness.md:26` overstates the remaining Arabic as confined to AMLAK and AMCREIT. Those are the affected **rendered samples**. The full sweep recorded **18 labels across eight companies**, including ADAV.AD, EMSTEEL and QIC (`docs/arabic-statement-labels-2026-11-03.md:391`). Restore that distinction and describe removal after publication as expected until verified. The commit inventory, screenshot counts, 64 web tests, four Python tests, lint and typecheck check out.

DRIFT: The work stayed within existing bilingual polish and release preparation. The destination remains a finished, published and polished alphacouncil.tech under the master plan’s approval rules.

NEXT STEP: On `rebuild`, close the already-recorded mandate-parser case mismatch in `web/scripts/check-advisors.mjs:51`: uppercase each trimmed `owns` tag, matching `api/app/debate/roster.py:146`. F-16’s publish is still ahead at 05:00 UTC; this is a concrete remaining §9 defect Claude can fix now, preventing false coverage reports when assessing the pilot.

DONE WHEN: A local check demonstrates that `owns: p2, P9` and `owns: P2, P9` produce identical coverage results; syntax, lint and the existing tests pass; the §9 note records the fix. No paid session or live account is needed.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`; billing is already open under the recorded waiver.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Approve each beta/production release and public-repository push separately once the evidence is ready.
4. Settle D1/D3/D6 and authorize the $66 pilot; decide on the $393 run after its results.

Response complete
