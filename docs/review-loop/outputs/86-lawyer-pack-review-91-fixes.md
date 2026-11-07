# Output 86: review 91's points, fixed (the AI status evidence, and the diff record)

**Review 91 said FIX.** Its step was a final evidence reconciliation. It asked for three things:
- capture both public AI status addresses;
- separate configuration from tested requests in pack §5.2;
- describe the diff evidence accurately.

**What was done** (commit `83704b0`, then the evidence commit with this output):

1. **Both status addresses are captured in full**, signed out, GET only, at 2026-11-07 20:52:53 UTC
   (`docs/screenshots/lawyer-pack-check-2026-11-07/status-endpoints.txt`, from `status-endpoints.sh`):
   - **`/api/v1/copilot/status`:** `{"model":"deepseek/deepseek-v3.2","stand_in":false,"sign_in_required":true}`.
   - **`/api/v1/debate/status`:** `"stand_in":false` and
     `"models":{"advisors":"deepseek/deepseek-v4-pro","chair":"anthropic/claude-sonnet-5.5"}`. These are the code's
     defaults. The capture also has its seven seats and its three rounds.
   - **What this changes:** the seats' and the Chair's production models are now on record as configured, so that
     fact leaves the owner's list. Three remain: the counts, the hosting provider, and where the AI data is processed.
2. **Pack §5.2: configuration, not tested requests.**
   - **What the status addresses report** is labelled as "how the service is set up", and the pack says they run no
     model.
   - **A new "Not tested" line:** no signed-in question was asked, so no request was seen reaching an outside
     provider, and the configured models were not seen answering.
   - **Routing** is introduced as "what the settings and code define, not what production was seen doing". The
     request code (`api/app/debate/llm.py`, `api/app/copilot/openai_compat.py`) is attached this time.
3. **The diff record.** `PROJECT.md` no longer says the full diff was recorded for `ac35f28..e521082`. It names the
   checks that `full-diff-check.txt` holds.
   - **This range:** `full-diff-check-2.txt` holds review 91's three commands, run over `ac35f28..83704b0`.
     - **`git diff --check`:** exit 0.
     - **`--name-status`:** 17 paths, all under `docs/` or `PROJECT.md`, with none under `api/`, `web/`, `scripts/`,
       `deploy/`, and not `MASTER-PLAN.md`.
     - **`PROJECT.md`:** its diff has 0 removed lines, only status bullets.
   - **The complete patch is kept too:** `range-ac35f28-83704b0.diff`, every file except the generated browser-prompt
     copies and the earlier check file.

**Kept intact:**
- review 89's production-data limitation;
- the contact-page and Arabic privacy-email issues;
- release `ea51de796c`;
- the renewal facts;
- `docs/legal-questions-2026-10-27.md` as the companion document, now attached.

**Attachments:** this prompt and two zips.
- **`review-86-docs.zip`** (from `rebuild`, by repository path):
  - the pack, the check record and the P9 production record;
  - `docs/legal-questions-2026-10-27.md`;
  - the evidence files: `status-endpoints.*`, `full-diff-check-2.txt`, `range-ac35f28-83704b0.diff` and
    `api-facts.txt`;
  - `PROJECT.md` and `docs/review-loop/MASTER-PLAN.md`.
- **`review-86-code.zip`** (from `ea51de796c`):
  - `api/app/settings.py`;
  - `api/app/routers/debate.py` and `api/app/routers/copilot.py`;
  - `api/app/debate/llm.py`;
  - `api/app/copilot/openai_compat.py`.

**The question for the review:**
- Is the pack now accurate, and ready for the owner to confirm the three marked facts and send with
  `legal-questions`?
- Which step is next on the plan?
