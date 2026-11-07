# Output 68: the isolated fix-only candidate (review 73's step)

**The candidate:** **`026699b`** on local branch `release/sector-standing`. It is production's `b5655a5` (released as
`b5655a5064`) plus `cae5578` and `026699b`. Their patch ids equal those of `867f944` and `e2eecc3` on `rebuild`.

**The amended report:** `docs/release-readiness-sector-standing-2026-11-07.md` (`a89cfa7`), attached. It answers
review 73's DONE WHEN item by item:
1. **The files:** `git diff --name-status b5655a5 026699b` lists exactly the eight intended files. There is no
   `presenter.py`, no `debate_engine` and no change to `routers/debate.py` or `settings.py` (`candidate-git.txt`).
   `candidate-b5655a5-026699b.diff` in the zip is the whole change.
2. **The checks, in the candidate's own worktree** (`candidate-checks.txt`):
   - **The API:** `app` was imported from the candidate's tree. Suite 578 passed and 11 skipped, and the focused
     tests 129 passed. `rebuild`'s 596 includes the prototype's tests.
   - **Lint:** `ruff` is identical to production in each changed Python file.
   - **The web:** the build exits 0 (`candidate-web-build.log` in the zip), typecheck 0, lint 0, and 68 of 68 tests
     pass. Before its first build the type check could not find Next's generated route types in the fresh worktree.
3. **The git output:** `git show --check` is clean for all four commits, `git diff --check b5655a5 026699b` is clean,
   and `git status -sb` reads `## release/sector-standing`.
4. **Al Rajhi's example,** run on the candidate's own code: 22.7 is kept as `sector_standing`, `debt_equity` is
   lower-is-better, no value changed, and nothing says it beats or outperforms about 77 % of peers.
5. **The screenshots at native size,** in the zip under `docs/screenshots/sector-standing-2026-11-07/`:
   - **The images:** en and ar at 1440 × 1000 and 390 × 844 px, from the candidate's production build (`next start`)
     on beta's data, by `playwright-core` at a device scale of 1.
   - **`viewports.json`:** each capture's innerWidth and scrollWidth (equal, so no sideways scroll), the tooltip read
     from the page, and the panel texts. No old label remains.
6. **The servers:** beta and production both still point to `releases/b5655a5064` (read-only SSH). Nothing was
   deployed, pushed or paid for. `deploy-staging.sh` archives `HEAD` of the checkout it runs in, so a beta release
   of `026699b` needs no push.

**The question for the review:** is `026699b` ready to put to the owner for release to beta?
