# Output 70: the deploy scripts ship only the exact approved commit (review 75's step)

**Commits on `rebuild`:** `724e742` (the guard), `8e53826` and `c3bcff6` (two output wordings), `6959e1f` (the request
and the record). Nothing was uploaded, deployed, pushed or paid for.

**What changed in both scripts** (`70-scripts-since-review-75.diff`, both scripts attached):
- **The commit is pinned (issue 1):**
  - **When it is required:** with `DEPLOY_BRANCH` set to anything but `rebuild`, `DEPLOY_SHA` is required.
  - **What it must be:** a full 40-character lowercase commit (`^[0-9a-f]{40}$`), equal to
    `git rev-parse --verify "HEAD^{commit}"`.
  - **What ships:** the script stores that commit in `commit` and archives it (`git archive --format=tar "$commit"`),
    so HEAD is not resolved again.
  - **The release name:** `${commit:0:10}`, the same 10 characters as the old `--short=10`.
- **The default is kept:** with no `DEPLOY_*` set, `rebuild` deploys as before. `DEPLOY_SHA` may also pin a `rebuild`
  deploy.
- **`--check` fails when prerequisites are unmet (issue 2):**
  - **Production:** it exits 1 with "NOT READY: beta runs …" while beta runs another commit.
  - **Both scripts:** they now also report which releases a deploy would prune and the rollback release, and exit 1 if
    the rollback release would be pruned.
  - **A passing check** prints "preconditions met (this check approves nothing; deploying needs the owner's
    go-ahead)". It no longer says "ready", because `rebuild` passes it too and must not ship.
  - **Still read-only:** `--check` reads the server and exits before any upload.
- **The placeholder is gone (issue 3):** `docs/release-request-sector-standing-2026-11-07.md` now gives the tested
  command in full:
  `cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh`.
  It also adds a step before the deploy: confirm the script is unchanged since `c3bcff6`, then rerun with `--check`.
- **Issue 4 (evidence cited, not attached):** noted. Per review 75, review 74's suite is not repeated, since the
  application code did not change. Only the two deploy scripts and documents changed.

**The DONE WHEN of review 75, item by item** (`deploy-preflight.txt`, made by the attached
`deploy-preflight-harness.sh`; each case shows its command, output and exit code):
1. **`bash -n`:** exit 0 for both scripts.
2. **Staging `--check` accepts `release/sector-standing` only with the exact SHA:**
   - **S9, the exact SHA:** exit 0, "commit: 026699b906ea3a513b4f2dbfc37672fa68ee9d42 (equals DEPLOY_SHA)", 3,837
     paths, release `releases/026699b906`.
   - **S3 (no SHA), S4 (short `026699b`) and S5 (`b5655a5…` full):** each refused, exit 1.
3. **Each failure refuses before any upload, build, switch or deletion:**
   - **The cases:** missing SHA (S3), wrong SHA (S5), a different branch (S6: `rebuild`'s checkout with the candidate's
     settings), and an advanced release-branch HEAD (S7). Each is refused with exit 1.
   - **The advanced HEAD:** S7 ran in a throwaway local clone whose `release/sector-standing` is one empty commit past
     `026699b`. The real branch was not touched, and the clone was deleted afterwards.
   - **On the deploy path itself:** S2', S3', S5', S6' and S7' rerun these cases without `--check`, with
     `STAGING_HOST=nobody@deploy-guard.invalid`, so even a broken guard could not have uploaded. Each is refused,
     exit 1, and none prints `== upload`.
4. **The default `rebuild` invocation:** S1 exits 0 with the same fields as before (checkout, branch, the full commit,
   now labelled `commit:` rather than `HEAD:`, archive count, release, beta now, releases), plus the prune and rollback
   lines. S8 shows that `DEPLOY_SHA` also pins
   `rebuild`: a wrong SHA is refused.
5. **Production's preflight fails while beta runs `b5655a5064`:**
   - **P1, the candidate with the exact SHA:** exit 1, "NOT READY: beta runs b5655a5064, not 026699b906".
   - **P2 (no SHA), P3 (advanced HEAD) and P4 (`rebuild`):** exit 1 each.
   - Nothing was deployed.
6. **The final read-only preflight** (S9 and P1, and the server read at the end):
   - **The checkout:** `C:/AlphaCouncil-Staging/deploy-026699b`, branch `release/sector-standing`, clean.
   - **The commit and archive source:** commit `026699b906ea3a513b4f2dbfc37672fa68ee9d42`, which is also the archive
     source.
   - **Beta and production:** both `/…/releases/b5655a5064`, all four services active.
   - **Release lists:** `b5655a5064 5c18a3ae46 2e44ee6fbf` on both tiers.
   - **The prune:** `2e44ee6fbf`.
   - **The rollback:** `releases/b5655a5064 (kept)`.
7. **The updated request** (attached) states:
   - **The candidate:** the exact commit.
   - **The commands:** the check, the deploy and a rollback.
   - **The scope:** beta only.
   - **The prune:** it removes `2e44ee6fbf`, and `b5655a5064` stays as the rollback.
   - **Production:** a separate go-ahead, whose `--check` passes only once beta runs `026699b906`.

**Whitespace:** `git diff --check` is clean for every commit. The record has no trailing spaces, which is why
`c3bcff6` joins the release lists with `paste -sd` rather than `tr`.

**The question for the review:** is the exact-commit guard sound, and may the beta release of
`026699b906ea3a513b4f2dbfc37672fa68ee9d42` now be put to the owner?
