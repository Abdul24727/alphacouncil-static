# Review 52: Review 51 fixes: monitor count 13 ok of 15; renewals line's evidential limit; Step 18 item 4 evidence

2026-11-06 12:39 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `49-production-monitor.md`.

VERDICT: FIX

ISSUES:

1. The correction remains contradictory. [PROJECT.md:1187](/C:/projects/alphacouncil-platform/PROJECT.md:1187) and [docs/launch-check-2026-10-27.md:165](/C:/projects/alphacouncil-platform/docs/launch-check-2026-10-27.md:165) still say the renewals line cannot turn green before a real renewal. [scripts/prod-monitor.py:300](/C:/projects/alphacouncil-platform/scripts/prod-monitor.py:300) accepts an empty run with `unreachable=0`. Correct or explicitly supersede those statements.
2. Review 51 requested complete original status output or a fresh timestamped capture. The correction supplies only the grouped table at [docs/launch-check-2026-10-27.md:262](/C:/projects/alphacouncil-platform/docs/launch-check-2026-10-27.md:262). Its corrected **13 ok + 1 failing + 1 pending** count is consistent, but the requested capture remains missing.

DRIFT: The output stayed within the master plan’s verification and documentation scope. The goal remains the existing site finished, published and polished in both languages at 1440 and 390 px, with the remaining launch requirements fulfilled.

NEXT STEP: Complete this monitor-record reconciliation on `rebuild` in `PROJECT.md` and `docs/launch-check-2026-10-27.md`: resolve the contradictory renewal explanations and attach complete status evidence. This is the most valuable immediate pre-approved step because it makes the remaining launch gate unambiguous and auditable.

DONE WHEN: Preserve the original stdout or capture a fresh, separately timestamped reading with `ssh root@alphacouncil.tech "python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status"`. Counts match every captured row; obsolete explanations are marked corrected; Step 18 item 4 remains open pending a real `renewal` payment row and an all-ok monitor. `git diff --check` passes.

OWNER ITEMS:

1. Top up shared OpenRouter credit; the recorded $7.83 is below the alert threshold.
2. Obtain Step 7’s written legal advice using the prepared lawyer pack.
3. Explicitly confirm or request reversal of the already-applied `owns` fix.
4. Resolve F-12’s duplicate Moyasar webhook.
5. Settle D5’s markers and separately approve any further paid run; the current proposal is capped at $426.

Response complete
