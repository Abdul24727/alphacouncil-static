# Output 99: review 104's fixes: the checked hash is the pushed hash

**Review 104 said FIX.**
- **HIGH:** the checks scanned `origin/rebuild..rebuild` and the push named `rebuild`, so a commit made in between
  went up unscanned. Review 104 reproduced it.
- **LOW:** the tag test did not assert that its push succeeded.

**What was done** (commit `18bc71c` on `rebuild`, local only; diff in `review-104-fixes.diff`):

1. **Step 2's *How* now starts by pinning the range:**
   - `git fetch origin`;
   - `BASE=$(git rev-parse origin/rebuild)` and `TIP=$(git rev-parse rebuild)`, with both hashes recorded.

   Every check then runs over `$BASE..$TIP`: the diff scan (`git diff "$BASE..$TIP" | grep …`) and the exact-value
   check (`count-exact-value.sh "$BASE..$TIP" <file>`). The history scan stays `git log --all -p`, all history.
2. **Immediately before the push:** `git -c credential.helper= ls-remote origin refs/heads/rebuild` must still show
   `$BASE`. If not, stop and redo every check on a new pin.
3. **The push sends the checked hash, not the branch name:**
   `git push --no-follow-tags --recurse-submodules=no origin "$TIP:refs/heads/rebuild"`.
   - **Fast-forward only:** it fast-forwards or fails, and it is never forced.
   - **The first push:** the 2026-10-22 command (`git remote add origin <URL>` and `git push -u origin rebuild`) is
     kept as history.
4. **The tag test** now asserts that the push exited 0 and that the bare remote's branch equals the pushed hash,
   before the no-tag assertions.
5. **A new pinned-push regression,** run against a local bare remote:
   1. The remote starts at the pin's base.
   2. A safe commit makes `$TIP`.
   3. The check of `$B..$T` is clean (exit 0).
   4. A commit holding the dummy value is made after the check.
   5. The remote is confirmed unmoved.
   6. The pinned push exits 0, and the remote is at `$T`.
   7. The value is in none of the remote's objects.

   The contrast: a push naming the branch, to a second bare remote, does send the value.
6. **The tests:** 69 pass (`count-script-test.txt`). That is the 63 before, plus the tag-push assertion, plus 5
   pinned-push checks.
7. **Command output** (`git-state-99.txt`):
   - `git diff --check 68c1d57..18bc71c` exits 0.
   - `bash -n` passes for both scripts.
   - The branch is `[ahead 18]`.
   - The remote's `rebuild` is still `dcc4189`.

**The question for the review:**
- Is this right and complete?
- Does any path remain by which Step 2's documented, pinned push could publish a correctly supplied UTF-8 value that
  the check reports as absent, without git or grep lying?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a pinned push after the checkpoint;
  - Step 18 item 4.
