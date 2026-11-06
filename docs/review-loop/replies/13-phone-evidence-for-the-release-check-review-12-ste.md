# Review 13: Phone evidence for the release check (review 12 step)

2026-11-06 00:47 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `13-phone-gap.md`.

VERDICT: FIX

ISSUES:

1. `web/src/components/stock/research-panels.tsx:193–209`: horizontal scrolling hides the row labels. The saved `301-balance-en-390-scrolled.png` and `8010-balance-ar-390-scrolled.png` confirm this. Older figures are reachable, but their meaning becomes difficult to read—a remaining phone-polish defect.
2. `PROJECT.md:1299` marks the screenshot work complete, while output 13 records visual inspection of only two panels. Review 12 required all eleven. The recorded numerical checks pass; they do not establish visual correctness.
3. `docs/release-readiness-2026-11-06.md:76` still says 130 screenshots; the directory contains 150.

DRIFT: The output stayed within the master plan’s existing-site verification scope. The goal remains a finished, published, polished site in both languages at 1440 and 390 px, respecting the recorded owner decisions and approval gates.

NEXT STEP: On `rebuild`, repair horizontal scrolling in `StatementPanel` so row labels remain visible beside older values in English and Arabic. This directly improves the existing financial tables and is more valuable now than repairing the superseded harvest script, while F-16 awaits its 05:00 UTC publish.

DONE WHEN: Visually inspect all eleven phone panels after the fix, including scrolled states, and verify both languages at 1440 px. Labels and visible values must remain readable, every period reachable, and all cells equal to the API. Save updated screenshots and candidate evidence, correct the readiness report and completion record, and pass the existing web tests and `git diff --check`—both pass currently, with 64 tests.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`.
2. Approve each beta release, production release and public push separately.
3. Address disk pressure and F-14’s rejected pipeline key.
4. Decide on the explicitly gated `owns` patch.
5. Resolve the pilot’s recorded prerequisites and authorize the $66 pilot; decide on the $393 run afterward.

Response complete
