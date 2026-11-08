# Output 98: review 103's fixes: real objects only, and no tags or submodules in the push

**Review 103 said FIX.** It found two ways a value could be published without being scanned:
1. **A replacement ref:** it made `git cat-file` read substitute content while a push sent the original.
2. **An annotated tag pointing into the branch:** with `push.followTags` on, a plain branch push publishes it, and
   the scan reads no tag objects.

**What was done** (commits `11736b5` and `68c1d57` on `rebuild`, local only; diff in `review-103-fixes.diff`):

1. **Real objects only.** The script now exports `GIT_NO_REPLACE_OBJECTS=1` before any git call. It also refuses a
   repository with a grafts file: `git rev-parse --git-path info/grafts` exists means exit 2. The header says git is
   made to read the objects a push sends.
2. **Tags and submodules are kept out of the push.** Step 2's push command is now
   `git push --no-follow-tags --recurse-submodules=no -u origin rebuild`.
   - **Why:** the scan reads the branch's commits and trees, not tag objects or submodules.
   - **The rule:** name only the branch, and never push tags from here.
   - **`--recurse-submodules=no`:** added without being asked, because `push.recurseSubmodules` would make a branch
     push send submodule commits the same way.
   - **In the script:** the header says tags are not covered and why Step 2's command makes that safe.
3. **The tests:** 63 pass (`count-script-test.txt`). The 6 new cases:
   - **Replacement ref:** a branch whose blob holds the value gets a replacement ref to harmless content. A setup
     check confirms plain git now reads the replacement; the script still finds the real content, with exit 3.
   - **Grafts file:** refused, exit 2.
   - **Tags:** an annotated tag whose message holds the value, with `push.followTags=true`, pushed to a local bare
     remote.
     - `git push --no-follow-tags` publishes no tag.
     - The value is in none of the remote's objects (`cat-file --batch-all-objects`).
     - The contrast: a plain push to a second bare remote does publish the tag, so the flag is what matters.
4. **Against the previous version (`1e8382f`):** the replacement case gives exit 0 there and exit 3 here.
5. **This repository** (`git-state-98.txt`): neither path was active.
   - **Refs and grafts:** 0 replace refs, and no grafts file.
   - **Settings:** `push.followTags`, `push.recurseSubmodules`, `remote.origin.push` and `remote.origin.mirror` are all
     unset.
   - **Submodules:** none on `rebuild`.
   - **The one local annotated tag:** `option-a-approved-v7`, on `1be3c0b` (the old static site). The remote already
     has it.
6. **Command output:**
   - `git diff --check 1e8382f..68c1d57` exits 0.
   - `bash -n` passes for both scripts.
   - The branch is `[ahead 17]`.
   - The remote's `rebuild` is still `dcc4189`.

**The question for the review:**
- Is this right and complete?
- Does any path remain by which Step 2's documented push could publish a correctly supplied UTF-8 value that the
  check reports as absent, without git or grep lying?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push after the checkpoint;
  - Step 18 item 4.
