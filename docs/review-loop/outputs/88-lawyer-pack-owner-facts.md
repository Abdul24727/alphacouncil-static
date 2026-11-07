# Output 88: the owner's facts, read-only (review 93's step)

**Review 93 ACCEPTED the pack.** Its step: settle the owner's open facts from read-only, non-secret evidence where
possible, keep historical counts dated, and leave unknown AI processing locations marked unverified.

**What was done** (commit `ce99154`; evidence in `docs/screenshots/lawyer-pack-check-2026-11-07/`):
1. **The hosting provider, from public records only** (`hosting-public-records.txt` from
   `hosting-public-records.sh`; public DNS and RIPE's RDAP through rdap.org; no server access):
   - **The address:** `alphacouncil.tech` resolves to 72.60.91.24, whose reverse DNS is `srv1556505.hstgr.cloud`.
   - **RIPE's record:** the network 72.60.88.0–72.60.95.255 is `HOSTINGER-HOSTING`, country `FR`. Its contacts are
     Hostinger NOC, in Vilnius, Lithuania.
   - **In the pack:** §5.2 gives these as public records and says they do not prove where the server sits. The owner
     confirms the provider and the data centre's country.
2. **The account and payment counts: not read.**
   - **What was tried:** a read-only, aggregate-only query on production's accounts database, with counts and no
     personal fields.
   - **The result:** the session's permission check refused it ("Production Reads"), and it was not tried another
     way.
   - **In the pack:** the 2026-11-06 counts stay as they are, dated, for the owner to confirm.
3. **Where the AI data is processed:** still not verified, and marked so.
4. **The plan files:** status lines only.
   - **`PROJECT.md`:** review 93 and this step.
   - **MASTER-PLAN:** one status sub-bullet saying review 93 accepted the pack.

`git diff --check` is clean, and only `docs/` and `PROJECT.md` changed.

**The owner's three facts, now:**
1. **The counts:** as of 2026-11-06.
2. **Hosting:** Hostinger by public records, with the data centre's country to confirm.
3. **Where the AI data is processed:** if ascertainable.

**Attachments:**
- this prompt;
- the pack and the check record;
- `hosting-public-records.txt`.

**The question for the review:**
- Is this step done and right?
- What is next on the plan, given that the remaining items are the owner's?
