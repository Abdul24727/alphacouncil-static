# Output 104: the Step 7 owner handoff note (review 109's step)

**Review 109 ACCEPTED the push-record fixes.** Its step: one concise owner handoff note under `docs/`, covering:
- the exact documents to send;
- the three facts needing the owner's confirmation;
- the pending legal review.

The rules for it: don't reopen the accepted pack's wording, contact the lawyer, push, deploy, or make paid calls.

**What was done** (commit `2a2a0dd` on `rebuild`, local only; the note is `step7-lawyer-handoff-2026-11-08.md`):

1. **The three facts:** a table giving each fact, where it sits in the pack, and how the owner can confirm it. No
   answers are filled in.
   - **The 2026-11-06 counts (§2):** payments and refunds from the Moyasar dashboard. For accounts, the owner allows
     a read-only, counts-only query, which the permission check refused without the owner's say-so, or counts them
     another way.
   - **The hosting provider and the data centre's country (§5.2):** the Hostinger panel. Public records say
     Hostinger, with the address registered in France, which does not prove where the server sits.
   - **Where the AI services process the data (§5.2, (h)):** the OpenRouter account, if ascertainable. Otherwise it
     stays marked not verified.

   If any answer differs from the pack, the pack is corrected before sending.
2. **The two documents:** the pack, as updated 2026-11-07, and the legal questions (a) to (e).
   - **Links pinned to commit `7b32e2d`:** GitHub blob URLs.
   - **Checked:** each file is unchanged since its last edit (`ce99154` and `b0bc45a`), and each published raw copy
     at `7b32e2d` is SHA-256-equal to `git cat-file`.
3. **Access:**
   - the live site in English and Arabic, running production `ea51de796c`;
   - the beta copy, whose password the owner gives privately;
   - the pack's §3 walk-through. Claude signs up no test accounts on the live site.
4. **When the advice comes back:** it goes into `docs/legal-advisors-<date>.md`. Claude prepares the changes on
   `rebuild`, and each release needs the owner's go-ahead.
5. **Still open:**
   - Step 18 item 4, a real renewal, never simulated;
   - optionally, the Argaam username check, only without a sign-in.
6. **The plan files:** status lines only, in `PROJECT.md` and MASTER-PLAN.
7. **Checks:**
   - `git diff --check` is clean.
   - `git log -3`: `2a2a0dd`, `0816cbc`, `e797dd6`.
   - `git status -sb` reads `[ahead 3]`, with a clean tree before this output.
   - Anonymous `ls-remote` shows `7b32e2d`.
   - Nothing was sent, pushed, deployed or paid for.

**The question for the review:**
- Is the note right and complete for the owner to act on?
- What is next on the plan? Everything left is the owner's:
  - Step 7 itself;
  - Step 18 item 4;
  - the optional username check.
