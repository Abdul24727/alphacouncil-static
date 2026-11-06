# Review 11: Blocked harvest documented as superseded (review 10 step)

2026-11-06 00:20 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `11-harvest-docs-superseded.md`.

VERDICT: ACCEPT

ISSUES: none. Commit `32d32ce` changes only documentation and docstrings. Both scripts compile, their executable ASTs are unchanged, and `git diff --check` passes.

DRIFT: The output stays on the master plan and respects the Argaam restrictions. The goal remains alphacouncil.tech finished, published and polished in both languages at 1440 and 390 px.

NEXT STEP: On `rebuild`, close the duplicated-helper cleanup recorded at `PROJECT.md:1297`: share the equivalent normalization and row-extraction logic in `scripts/argaam_ar_labels/pair_labels.py:36` and `pair_from_gulf.py:51`, preserving their different page-selection rules. This addresses remaining maintenance work in the active label workflow while F-16’s verification awaits the 05:00 UTC publish.

DONE WHEN: Both scripts produce identical before/after output over the same saved HTML corpus, including `pair_labels.py --check-ids`; `python -B -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py` passes; `git diff --check` passes; and `PROJECT.md` records completion. Verification uses saved pages without contacting Argaam or changing server files.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice using `docs/legal-questions-2026-10-27.md`; this remains the principal launch blocker.
2. Approve the prepared polish’s beta release, production release and public push separately.
3. Address disk pressure and F-14’s rejected pipeline key.
4. Decide on the prepared `owns` patch; its explicit approval gate stands.
5. Resolve D1/D3/D6 and authorize the $66 pilot, then decide on the $393 run from its results.

Response complete
