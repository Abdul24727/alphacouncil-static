# Output 89: the push of `eeb9a9d..dcc4189`, on the owner's go-ahead

**The owner's go-ahead, in chat:** "Yes, scan and push". It answered the question "Run the credential scan and push
the 97 commits to the public repo?".

**What was done** (evidence in `docs/screenshots/push-2026-11-08/`; the record is in commits `766439a` and `64c59e3`,
which are not pushed):

1. **Step 2's outgoing-diff scan, before the push** (`scan-diff-hits.txt`):
   - **The hits:** 86, every one read. All are the word "Moyasar":
     - in prose (the standing rules, review notes, records);
     - in the public legal pages' text;
     - in file names inside a hash listing.
   - **Values:** none.
2. **Step 2's history scan** (`scan-history.txt`): only the standing false positives. The two tracked env templates
   are unchanged in the range.
3. **Wider checks** (`other-checks.md`):
   - **Emails:** the push added no new address; the author address is the one on the 408 commits already public.
   - **Passwords:** "password" appears only in route names, file names and legal text.
   - **Assignments:** the only value-shaped one is the locale cookie `NEXT_LOCALE=ar`.
   - **Argaam:** no line that mentions it names an account.
   - **A local path:** one scratch path exposes the Windows user name, which is already public as the GitHub handle.
   - **PNGs:** 82, all of signed-out pages. *(Corrected after review 95: 74 are the signed-out launch check's, and
     2 of the other 8 were opened. See `other-checks.md`.)*
4. **The push:** `git push origin rebuild` printed `eeb9a9d..dcc4189  rebuild -> rebuild`.
   - **Its kind:** a fast-forward, nothing forced.
   - **Scope:** `rebuild` is the only refspec, and the range holds no CI files.
5. **Verified** (`push-verify.txt`):
   - **The git checks:** local, remote-tracking and anonymous `ls-remote` all read `dcc4189`; left/right `0 0`.
   - **The other branches:** the remote's five other heads sit at the hashes recorded earlier.
   - **Publication:** six files fetched anonymously at the sha-pinned URL answer 200, and each is SHA-256-equal to
     `git cat-file -p dcc4189:<path>`.

**What was not done, and why:**
- **The check:** the Argaam account name, matched by its exact value. The 2026-11-07 pre-push audit left this check
  for push time.
- **Before the push:** I missed it.
- **After the push:** I tried a read-only SSH command showing only the shape of the nightly log's session-gate lines,
  with every value masked. The session's permission check refused it, and it was not tried another way.
- **What still covers it:**
  - no new email address in the range;
  - every added line that mentions Argaam was read.
- **What does not:** a non-email account name in a line that does not mention Argaam.
- **The owner can:**
  - run `git log -p eeb9a9d..dcc4189 | grep -cF '<name>'` themselves; or
  - allow the read.

**Plan files:** status lines only.
- **`PROJECT.md`:** the header's pushed hash, a Step 2 *Done (2026-11-08)* entry, the audit note's "Not run at push
  time either", and a changelog entry.
- **MASTER-PLAN:** one status sub-bullet.

**The question for the review:**
- Is this push done and recorded right?
- Is the missed Argaam check handled right: recorded, not worked around, and left to the owner?
- Should Step 2's *How* name that check explicitly as the owner's, before every push?
- What is next on the plan? The remaining items are the owner's (Step 7's lawyer handoff, Step 18 item 4).
