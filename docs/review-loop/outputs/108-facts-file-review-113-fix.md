# Output 108: review 113's fix to the facts file

**Review 113 said FIX** on two stale lines in `docs/lawyer-pack-facts-2026-11-08.md`: "The pack says one" (line 84)
and "The pack does not mention it" (line 89). Both describe the pack before its correction.

**What was done** (commit `0777f71` on `rebuild`, local only; `facts-108.diff`):
- **Line 84** now reads: "**Payments and refunds: two live payments ever, both refunded.** The pack as accepted on
  2026-11-07 said one; the corrected pack (§2) now records both."
- **Line 89** now reads: "The pack as accepted on 2026-11-07 did not mention it; the corrected pack now does. The
  different description format suggests an earlier version of the site, which is not verified." That matches pack
  §2's wording.
- **The 2026-11-02 line** now reads "which the pack has always described".
- **A scan** of the facts file for "the pack says", "does not mention" and "before this rebuild" finds none.
- **Checks:** `git show --check HEAD` passes. `rebuild` is `[ahead 9]`, the remote is still `7b32e2d`, and nothing
  was pushed or sent.

**The question for the review:**
- Is the facts file now consistent with the pack and the handoff note?
- Is the pack ready to send once the owner gives the account count?
