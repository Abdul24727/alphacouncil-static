# Review 23: F-16 verified live; candidate 2f50598 (review 22 step)

2026-11-06 05:26 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `23-f16-verified-live.md`.

VERDICT: FIX

ISSUES:

1. The three mappings in `web/src/content/data-labels.json:505` pass tests and the sweep, but candidate checks 1–8 contain no DIC/KFH rendered checks or screenshots. `CLAUDE.md:50` requires page evidence at 1440 and 390 px before declaring completion. I independently confirmed 68/68 web tests and eight F-16 regression tests pass.
2. The updated records contradict the verified result: `PROJECT.md:274` and `:1276` still say F-16’s after-publish check remains pending; `docs/release-readiness-2026-11-06.md:104` says the rendered data predates publication, immediately before claiming post-publication verification.

DRIFT: The work stayed within correcting source data and polishing existing Financials. The goal remains the finished, published bilingual site at 1440 and 390 px, with the master plan’s owner gates preserved.

NEXT STEP: Complete candidate `2f50598`’s release evidence on `rebuild`: inspect the affected DIC and KFH statements in both languages at both widths, save screenshots under `docs/screenshots/release-candidate-2f50598/`, and reconcile the contradictory status sentences in `PROJECT.md` and the readiness report. This closes the evidence gap for the latest changes before the owner decides on release.

DONE WHEN: Screenshots visibly show all three changed labels without clipping, Arabic remains correct, and displayed figures match the API. Both records consistently distinguish F-16’s live data fix from the unreleased app candidate. `git diff --stat 2f50598..HEAD -- web/src api deploy web/messages web/public` remains empty for this evidence-only step.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Address disk pressure at 83% and F-14’s rejected pipeline key.
3. Authorize beta release, production release and public push separately after the evidence closes.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot; decide on the $393 run afterward.
5. Decide whether to approve the explicitly gated `owns` patch.

Response complete
