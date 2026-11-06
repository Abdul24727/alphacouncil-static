# Review 26: Capital panel caption verified (review 25 fixes)

2026-11-06 06:04 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `26-capital-caption.md`.

VERDICT: FIX

ISSUES:

1. The caption verification and corrected release summary are sound, but `CapitalPanel` still has adjoining column text. [research-panels.tsx:657](/C:/projects/alphacouncil-platform/web/src/components/stock/research-panels.tsx:657) lacks horizontal cell spacing. The checked `capital-captions/` screenshots show Arabic date/type text touching at **both 1440 and 390**, plus English capital/change figures touching at **390**. This predates the commit but remains a polish defect.

DRIFT: No scope drift: the output verifies existing panels without inventing data. The destination remains finished, published and polished alphacouncil.tech under PROJECT.md, preserving the owner’s decisions and approval gates.

NEXT STEP: On `rebuild`, fix column spacing in the existing `CapitalPanel`, following the nearby table’s RTL-aware pattern at line 464. This is the most valuable immediate pre-approved work because it resolves a demonstrated readability defect in financial data.

DONE WHEN: New-candidate screenshots under `docs/screenshots/` show clearly separated columns and complete captions in both languages at 1440 and 390. All nine 1010 rows still match the API, KFH retains its empty state, and `npm --prefix web run lint` plus `npm --prefix web run build` pass. Update the readiness report to identify the changed candidate.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Address disk pressure and F-14’s rejected pipeline key.
3. After verification, separately authorize beta release, production release and public push.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot before deciding on the $393 run.
5. Decide on the explicitly gated `owns` patch.

Response complete
