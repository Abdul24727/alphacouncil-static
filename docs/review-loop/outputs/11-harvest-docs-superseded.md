# Output 11: review 10's step, the blocked harvest documented as superseded

Commit `32d32ce`. Docs and docstrings only.

- **`scripts/argaam_ar_labels/harvest_ar_statements.py`:** the module docstring now opens "SUPERSEDED - do
  not run". It gives the two reasons:
  - Argaam's "Human Verification" challenge on the Arabic pages, not to be got around;
  - the owner ruling out any other sign-in, since a second one signs the nightly's session out.

  It names the route used instead (`pair_from_gulf.py`, the Gulf pages the nightly already saves) and keeps
  the original text under "As first written".
- **`scripts/argaam_ar_labels/pair_labels.py`:** only the `--ar-dir` usage, which depended on that harvest,
  is marked superseded and points to `pair_from_gulf.py`. `--check-ids` is unaffected and still documented
  as current.
- **`docs/arabic-statement-labels-2026-11-03.md`:** "The route that remains: the owner's own browser" now
  reads "The route that remained at that point". A note says it was superseded the same day, that no
  sign-in, browser-pane visit or Saudi Arabic page was used, and points to "Done instead" in `PROJECT.md`
  §9 item 3 and the sections below.
- **`PROJECT.md`:**
  - The review's cleanup list records what is now done: the harvest docs, the USD unit, the loud unknown
    header (F-16's guard), and the row-id note met by `in_statement`.
  - What is left: duplicated helpers, the self-matching busy check (`nightly_busy()` in the superseded
    harvest script, which is never run), and the screenshot rule.
  - A changelog entry for reviews 09–10.
- `git diff --check` is clean; both scripts still compile. No other file references the harvest as current,
  per a repository grep over `.md` and `.py`.

**Pending:**
- F-16's after-publish check after 05:00 UTC (the nightly is running).
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
