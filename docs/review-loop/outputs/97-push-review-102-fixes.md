# Output 97: review 102's fix: both ends of the range are read

**Review 102 said FIX.** When the two ends of `A..B` have diverged, `A` is not a boundary commit, so its tree was
never read, although `git diff A..B` shows it. A value only in `A` returned three zeros and exit 0.

**What was done** (commit `1e8382f` on `rebuild`, local only; diff in `review-102-fixes.diff`):

1. **The start is resolved by name:** `basesha=$(git rev-parse --verify --quiet "$base^{commit}")`, checked to be
   non-empty.
2. **Both ends are always snapshots:** the list starts as `snaps=("$tipsha" "$basesha")`, before the range and
   boundary commits are added. `git rev-list --objects --no-walk` deduplicates, so a start that is also a boundary
   commit costs nothing.
3. **The header and Step 2** now say the snapshots include both ends of the range by name, even when they have
   diverged, and why: `git diff A..B` compares the two ends' trees.
4. **The tests:** 57 pass (`count-script-test.txt`).
   - **The new setup:** a side branch from `base` holds the value only there, diverging from `tip`.
   - **Two new cases:** `side..tip`, with the value only at the start, and `tip..side`, with it only at the end. Each
     must give exit 3 with `file-contents` ≥ 1 and only the three count lines.
   - **A slip, fixed before the commit:** the first run failed only on its own setup, because a tag and a branch were
     both named `side` and git warned that the name was ambiguous. The tag was dropped.
5. **Against the previous version (`ec45135`):** review 102's case gives exit 0 there and exit 3 here, with
   `file-contents 1`.
6. **Command output** (`git-state-97.txt`):
   - `git diff --check ec45135..1e8382f` exits 0.
   - `bash -n` passes for both scripts.
   - The branch is `[ahead 15]`.
   - The remote's `rebuild` is still `dcc4189`.

**What the snapshot set now covers:**
- **`git log -p A..B` and `git show` of any range commit:** each commit's tree and its parents' trees. A parent is
  either in the range or at the boundary.
- **`git diff A..B`:** the two ends' trees.
- **`git diff A...B`:** the merge base's tree, which is a boundary commit, and `B`.
- **What a push publishes:** every object reachable from the range's commits.

**The question for the review:**
- Is this right and complete?
- Does any path remain to exit 0 while a correctly supplied UTF-8 value is in what the range shows or publishes,
  without git or grep lying?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push after the checkpoint;
  - Step 18 item 4.
