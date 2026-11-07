# Output 69: the deploy preflight for candidate 026699b, and the owner-facing release request (review 74's step)

**Commit:** `d13a8af` on `rebuild`. Nothing was deployed, pushed or paid for.

**The preflight found a blocker:**
- **What the scripts did:** `scripts/deploy-staging.sh` refused any branch but `rebuild`
  (`[[ "$branch" == "rebuild" ]] || refusing`), and so did `scripts/deploy-production.sh`.
- **Why that blocks:** run from the candidate's checkout, they would have deployed nothing. `rebuild` itself carries
  the rejected prototype. So the candidate could not be released with the scripts as they stood.

**The change** (`69-scripts.diff`, both scripts attached):
- **The opt-in:** `expected="${DEPLOY_BRANCH:-rebuild}"`. Another reviewed branch is accepted only when named
  explicitly, and the default is exactly as before.
- **`--check`, read-only:** it prints the checkout, branch, full HEAD, release path and archive size, plus beta's
  current release and beta's releases (or, for production, whether beta matches HEAD). It exits before any upload,
  build or switch.
- **Unchanged:** every other line. Production still refuses unless beta runs the same HEAD, and still refuses
  uncommitted changes.

**The DONE WHEN of review 74:**
1. **The deployment checkout:** `git rev-parse HEAD` in `C:/AlphaCouncil-Staging/deploy-026699b`, a clean checkout of
   `release/sector-standing`, prints `026699b906ea3a513b4f2dbfc37672fa68ee9d42` (`deploy-preflight.txt`).
2. **How the archive source is chosen:**
   - **The lines:** `ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"`, then `git archive --format=tar HEAD | ssh …
     tar -x -C $rel`.
   - **So:** HEAD of the checkout the script runs in is what ships, and only its committed files.
   - **Read-only proof, in four runs:** `rebuild`, no opt-in, behaves as before (exit 0). The candidate checkout
     without the opt-in **refuses** (exit 1). With `DEPLOY_BRANCH=release/sector-standing` it reports HEAD
     `026699b906…`, release `releases/026699b906` and 3,837 paths (exit 0). Production's `--check` from the
     candidate reports that a deploy would refuse, because beta runs `b5655a5064`.
3. **The raw git checks with exit codes** (`candidate-git-raw.txt`): `git show --check --format=` prints nothing and
   exits 0 for `867f944`, `e2eecc3`, `cae5578` and `026699b`. `git diff --check b5655a5 026699b` exits 0,
   `git status -sb` reads `## release/sector-standing`, and the name-status lists the eight files.
4. **The earlier results,** cited and not re-run, in `docs/release-readiness-sector-standing-2026-11-07.md`: the tests,
   the build and the four native screenshots.
5. **The rollback target and the state:**
   - **The rollback:** `b5655a5064`, kept on beta. A beta deploy prunes beta to its 3 newest releases, so
     `2e44ee6fbf` would go.
   - **The state:** beta and production both run `b5655a5064` (the preflight's "beta now" and "prod now"). Beta has
     not been deployed.

**The owner-facing request:** `docs/release-request-sector-standing-2026-11-07.md`, attached.

**The question for the review:** are the script change and the preflight sound, and may the beta release of
`026699b` be put to the owner?
