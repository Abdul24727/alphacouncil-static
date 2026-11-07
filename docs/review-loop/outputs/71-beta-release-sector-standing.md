# Output 71: the sector-standing fix is on beta (the owner's go-ahead)

**The owner's go-ahead** (in chat, 2026-11-07): "Yes, deploy to beta", to the question "Deploy the sector-standing
fix (026699b906) to beta only?". Review 76's owner item 2 asked for exactly this.

**What was done** (`docs/release-beta-sector-standing-2026-11-07.md`, attached):
1. **The preflight first, as the request said:**
   - `git diff --quiet c3bcff6 -- scripts/deploy-staging.sh` exited 0.
   - The checkout was clean at `026699b906ea3a513b4f2dbfc37672fa68ee9d42`.
   - The staging `--check` exited 0 and matched `deploy-final-check.txt`.
2. **The request's own deploy command:** nothing changed or added (`deploy-beta.log`, attached).
   - **Upload, build and switch:** the commit was uploaded and built (`next build`, 93 of 93 pages).
   - **The restart:** both beta services restarted and answered 200.
   - **The prune:** it removed `2e44ee6fbf`, as the request said.
   - **The exit:** 0.
3. **Production was not touched.** Nothing was pushed or paid for.

**The checks after** (`beta-checks.txt`, made by the attached `beta-checks-harness.sh`; read-only, GET only, through
SSH tunnels):
- **What runs:** beta runs `releases/026699b906`, with releases `026699b906 b5655a5064 5c18a3ae46`. Production runs
  `prod/releases/b5655a5064`, unchanged, and all four services are active.
- **The files:**
  - **The changed files:** the eight are equal by sha256 to the commit.
  - **The whole tree:** all 3,566 committed files (all but symlinks) on beta are equal by sha256 to the commit
    (`tree-sha256.txt`).
  - **The prototype:** `presenter.py` and `debate_engine` are absent.
- **The site:** API health is ok and the pages answer. The en and ar captures at 1440 and 390 carry the new labels
  and tooltip, with no sideways scroll and no old label (`viewports.json`; the four PNGs are attached).
- **The notes:** P9's notes on beta say "sector standing" and never "sector percentile".
- **The Arabic string check** (signed out, 1440 and 390): 48 Arabic page views, 0 English strings outside the
  allow-list, exit 0 (`check-arabic.txt`, attached).
- **Production's `--check` for the commit now exits 0**, with "beta now: 026699b906" and `b5655a5064` kept as its
  rollback. It approves nothing.

**One thing that looked wrong and is explained:**
- **What moved:** three standings differ from the candidate's captures: 28 → 27, 82 → 81 on gross margin, 47 → 45.
- **The timing:** those captures were made at 00:50 UTC. The pipeline's nightly refreshed the fundamentals at 01:48
  UTC (`as_of` in check 7).
- **The code:** the code that serves the numbers is identical in both releases
  (`git diff --quiet b5655a5 026699b -- api/app/routers web/src` exits 0).
- **The page:** it shows exactly what beta's API returns now.
- **So:** the change is the night's data, not the release.

**A harness slip, fixed before the record was kept:**
- **What happened:** the first run of check 3 reported a difference.
- **The cause:** Python on Windows wrote the local hash list with CRLF line endings, and the server's has LF.
- **The fix:** the harness now writes LF and keeps whole paths (none contains a space), and its rerun matches. Only
  the rerun is recorded.

**What was not checked:**
- **The room's and the Copilot's wording with a real model:** that needs a paid session. Their code is on beta byte
  for byte, and its tests passed in review 74.
- **Production's API:** opening its tunnel was refused by the session's permission check, and it was not needed for
  the comparison.

**The question for the review:** is beta's release of `026699b906` verified well enough to put production to the owner,
as described in the attached record?
