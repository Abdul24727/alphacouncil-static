# Output 102: the pinned push of `7b32e2d`, on the owner's go-ahead

**Review 107 ACCEPTED the pinned verification.** Its step was for the owner to run the two exact-value checks, and
only then to give an explicit push go-ahead.

**The owner's checks** (run in the owner's own Git Bash, pasted in chat as counts only):
- **The value:** the Argaam login email.
- **The results:**
  - `count-exact-value.sh dcc4189…..7b32e2d… <file>` gave `commits 0`, `file-contents 0`, `file-names 0`, exit 0.
  - `count-exact-value.sh eeb9a9d..dcc4189 <file>` gave the same: three zeros, exit 0.
- **The username:** not checked. The owner said that seeing it needs an Argaam sign-in, which signs the nightly
  scraper out; the standing rule is never to sign in to Argaam.
- **Recorded:** only the counts and the kind of value used, never the value.

**The owner's go-ahead, in chat:** "Yes, push 7b32e2d".

**The push** (`docs/screenshots/push-pin-2026-11-08/push-verify.txt`):
1. **Immediately before:** anonymous `ls-remote` showed `rebuild` = BASE `dcc4189…`, local `rebuild` = TIP, and TIP is
   a descendant of BASE.
2. **The command:** `git push --no-follow-tags --recurse-submodules=no origin "7b32e2d9b80186814a44294ce57eed3288192739:refs/heads/rebuild"`.
   It printed `dcc4189..7b32e2d  7b32e2d… -> rebuild` and exited 0: a fast-forward, nothing forced.
3. **Afterwards:**
   - **The git checks:** anonymous `ls-remote`, `origin/rebuild` after fetch, and local `rebuild` all read `7b32e2d`;
     left/right `0 0`.
   - **The refs:** every remote head and tag, before and after, differs only in `refs/heads/rebuild`. No tag was
     added.
   - **Published:** six files fetched anonymously at the sha-pinned URL answer 200, and each is SHA-256-equal to
     `git cat-file -p 7b32e2d:<path>`: both check scripts, `PROJECT.md`, the script test record, reply 105 and
     MASTER-PLAN.
4. **The record:** commit `e797dd6`, local, and unpushed by construction.
   - **What it holds:** the push record, plus what was held back while the pin stood (the pinned-verification
     evidence, outputs 100 and 101, replies 106 and 107, and the Argaam results).
   - **A fix in it:** one captured context line in `verify.txt` had a trailing space, stripped so that
     `git diff --check` passes.

**The question for the review:**
- Is this push done and recorded right?
- What is next on the plan? The items still open are the owner's:
  - Step 7, the lawyer handoff;
  - Step 18 item 4, a real renewal;
  - optional: the username form of the Argaam check, only if it can be had without a sign-in.
