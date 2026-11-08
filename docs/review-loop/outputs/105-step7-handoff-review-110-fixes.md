# Output 105: review 110's two fixes to the Step 7 handoff note

**Review 110 said FIX** on two points of `docs/step7-lawyer-handoff-2026-11-08.md`:
1. **The advice:** the note told the owner to save the lawyer's advice as received, or to give it to Claude to save.
   The accepted pack's §7 and the questions' "After the visit" require an owner-written summary instead: points of
   advice only, with no client names, personal data or fees. The repository is public.
2. **The links:** the links pinned to `7b32e2d` would still show the old text after a correction.

**What was done** (commit `0a24723` on `rebuild`, local only):

1. **§4 of the note** now reads: "**The owner writes a summary** into `docs/legal-advisors-<date>.md`, as the pack's §7
   and the questions' "After the visit" say. It holds the points of advice, each with the change it requires, and no
   client names, personal data or fees. The repository is public: never commit the lawyer's own letters, emails or
   documents, and do not hand them to Claude to save. Claude works from the summary."
2. **§2 of the note**, after the links, now reads: "**If section 1 led to a correction, these links still show the
   old text.** In that case, either send the corrected files as attachments, or, after a new push you approve (with
   its checks), use links pinned to that new commit. Never send the `7b32e2d` links as the corrected version."
3. **The evidence** (`review-110-fixes.txt`, captured before the commit):
   - `git diff --check` exits 0.
   - `git diff -- docs/step7-lawyer-handoff-2026-11-08.md` shows only these two hunks.
   - The only other change in the working tree was the review log's line for reply 110.
   - Blank diff context lines (a single space each) were stripped in the capture so that `git diff --check` passes.
     The capture says so.
4. **The plan file:** one status sub-bullet in `PROJECT.md`.
5. **After the commit** (`git-state-105.txt`):
   - `git show --check 0a24723` exits 0.
   - `git log -5`: `0a24723`, `2a2a0dd`, `0816cbc`, `e797dd6`, `7b32e2d`.
   - The branch is `[ahead 4]` with a clean tree.
   - Anonymous `ls-remote` shows `7b32e2d`, so nothing was pushed.
   - The accepted pack and the questions have 0 diff lines over `2a2a0dd..0a24723`.
   - `git show --stat 2a2a0dd` is included, which answers review 110's third point about evidence.

**The question for the review:**
- Are the two fixes right?
- Is the note now ready for the owner to act on?
- What is next on the plan? Everything left is the owner's:
  - confirm the three facts;
  - send the two documents;
  - write the advice summary when it comes;
  - Step 18 item 4.
