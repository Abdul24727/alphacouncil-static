# Review 02: Review 01 fixes and the Gulf English-page labels

2026-11-05 23:14 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `02-gulf-english-labels.md`.

VERDICT: FIX

ISSUES:

1. [check-data-fixes.mjs:202](C:/projects/alphacouncil-platform/web/scripts/check-data-fixes.mjs:202) silently skips failed statement requests. Running the new sweep block with mocked HTTP 500 or 429 responses produced **PASS with 0 lines checked**. A later 403 also suppresses Arabic-label failures already found because lines 214–222 report only the gate. This can falsely certify incomplete coverage.
2. The report’s counts are incorrect: [the label record:327](C:/projects/alphacouncil-platform/docs/arabic-statement-labels-2026-11-03.md:327) says 27 new English keys; the committed dictionary adds **29** after normalization. Line 350 and Output 02 say five new tests; the diff adds **four**, taking the suite from 43 to 47. I confirmed **47/47 pass**, lint passes, and all existing dictionary mappings remain unchanged.

DRIFT: The work stays within finishing existing bilingual pages and checks; no scope drift found. The destination remains the completed, published and polished launch plan, with recorded owner decisions left settled.

NEXT STEP: On `rebuild`, finish the English-label verification in `web/scripts/check-data-fixes.mjs` and correct its accompanying report. Make unexpected HTTP failures fail the check, preserve failures found before a gate, and distinguish unavailable coverage from completed coverage; this makes the existing launch evidence trustworthy before release.

DONE WHEN: Regression checks prove that HTTP 500/429 fail, an untranslated row remains a failure after a later 403, an entirely gated run explicitly reports unavailable coverage, and successfully translated responses pass. `cd web; npm.cmd test` and lint pass; the report records accurate counts. F-16’s post-publish verification remains pending—the 05:00 UTC publish is still ahead.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using the prepared questions.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Authorize releases and the public-repository push separately once fixes and verification are complete.
4. Fund and authorize the $66 pilot; decide on the $393 run after its results.

Response complete
