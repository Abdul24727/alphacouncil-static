# Output 84: review 89's two points, fixed (the lawyer pack and its records)

**Review 89 said FIX**, with two claims that went further than the evidence. Its step: one documentation-only
correction in the pack, the check record and the P9 production record. Nothing to be sent, released, pushed or
paid for.

**What was done** (committed on `rebuild` as `48c6693`). The exact diff from the reviewed `ac35f28` is
`docs/screenshots/lawyer-pack-check-2026-11-07/review-89-diff.txt`.

1. **Where the AI data is processed, and how it is routed** (pack §5.2 and question (h)).
   - **Now:** the data "may be processed outside the Kingdom". Three things are stated as not verified: which companies
     serve the requests, the countries where they process them, and production's routing settings.
   - **The code's defaults, marked as defaults** (`api/app/settings.py` lines 34–54): OpenRouter, with a latency sort,
     and an optional host order for the Copilot. The Copilot can be set to Anthropic directly, and any compatible
     service can stand in for OpenRouter.
   - **Confirmed live:** only the Copilot's model id.
   - **For the owner:** where the data is processed is added as a fourth fact to confirm, if they can find out.
2. **Production's data settings** (pack §2, the check record's discrepancy 6, the P9 production record).
   - **Now:** the deploy script is written to copy beta's market-data settings when it first creates production's
     settings file, and to leave an existing file alone (`scripts/deploy-production.sh` lines 79–99).
   - **Not established:** that the copy ran (no output of that setup is on record), and that the settings match today.
   - **Kept:** the P9 record still says production's notes are not established to equal beta's.

**Kept unchanged, as review 89 asked:**
- the contact-page issue;
- the Arabic privacy-email issue;
- the model defaults;
- release `ea51de796c`;
- the renewal facts.

**Checks:**
- **`git diff --check`:** clean.
- **Files changed:** only documents under `docs/` and `PROJECT.md`. No application code and no server files.
- **The plan files:**
  - **`docs/review-loop/MASTER-PLAN.md`:** unchanged in this pass.
  - **`PROJECT.md`:** one new status bullet, recording review 89 and its fix. It touches no objective, rule, approval or
    decision, and its diff is in `review-89-diff.txt`. The owner's standing instruction is to write each step's
    outcome to the plan file as it finishes, so that bullet is required.

**Attachments:** this prompt and two zips.
- **`review-84-docs.zip`** (from `rebuild` at `48c6693`, by repository path):
  - the pack, the check record and the P9 production record;
  - `review-89-diff.txt`;
  - `scripts/deploy-production.sh`.
- **`review-84-code.zip`** (from `ea51de796c`): `api/app/settings.py` and `api/app/copilot/openai_compat.py`.

**The question for the review:**
- Are both points fixed, and is the pack ready for the owner to send once they confirm the four marked facts?
- Which step is next on the plan?
