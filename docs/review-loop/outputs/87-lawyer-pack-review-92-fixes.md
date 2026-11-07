# Output 87: review 92's two passages, fixed

**Review 92 said FIX:** two passages, and nothing else to change.

**What was done:**
- **The fix:** commit `787c896`, which touches only `docs/lawyer-review-pack-2026-11-06.md` and
  `docs/lawyer-pack-check-2026-11-07.md`.
- **The record:** `docs/screenshots/lawyer-pack-check-2026-11-07/review-92-check.txt`, committed with a `PROJECT.md`
  status line in `579cfcf`. It holds `git diff --check` (exit 0), `--name-status` and the full diff of the fix
  commit.

1. **Question (h)** now reads: "When an AI feature calls an externally hosted model, the member's question and the
   company's data are sent to the configured AI service. Three things were not verified (§5.2): that requests are
   delivered, which companies serve them, and where those companies process them." The PDPL question is kept as it
   was.
2. **Discrepancy 5** in the check record now separates three things:
   - **Configured:** the model ids that production's public status addresses report.
   - **The code's defaults.**
   - **Not verified:** no request was observed using these models, and the serving companies, their countries and
     production's routing are unknown.

   It says the owner has three facts left to confirm.

**The owner's three facts,** in the pack's list and the check record:
1. the 2026-11-06 account and payment counts;
2. the hosting provider and its country;
3. where the AI services process the data, if ascertainable. If not, it stays marked as not verified.

**Attachments:**
- this prompt;
- the pack and the check record, as files;
- `review-92-check.txt`.

**The question for the review:** is the pack ready for the owner's Step 7 handoff?
