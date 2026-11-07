# Output 85: review 90's two points, fixed (the lawyer pack's AI wording, and the full diff)

**Review 90 said FIX.** It accepted the production-data-settings correction, and asked for two things:
1. AI wording in pack §5.2 that separates production's behaviour, the code's defaults and unverified processing.
2. The full `git diff --check` and `--name-status` from `ac35f28`.

**1. Pack §5.2, now in three parts** (commit `e521082`):
- **What production confirms** (`api-facts.txt`, read from the live site 2026-11-07):
  - **Not the stand-in:** both `/api/v1/copilot/status` and `/api/v1/debate/status` report `"stand_in": false`, so
    neither feature runs on the labelled rule-based stand-in.
  - **The Copilot's model:** `deepseek/deepseek-v3.2`.
  - **The room:** by `api/app/routers/debate.py` `uses_models`, `stand_in: false` means an OpenRouter key is set on
    production and `COPILOT_PROVIDER` is not `standin`.
- **What the code does by default** (`api/app/settings.py`):
  - **The Copilot's service:** `COPILOT_PROVIDER=auto` picks OpenRouter when its key is set, otherwise Anthropic, otherwise
    the stand-in.
  - **The room:** it uses the same OpenRouter client and key.
  - **The address:** `openrouter_base_url` defaults to OpenRouter's, and "any OpenAI-compatible endpoint" can stand in.
  - **Host routing:** OpenRouter picks the host, with a latency sort by default and an optional host order for the
    Copilot.
- **Not verified:**
  - the seats' and the Chair's production models;
  - the serving companies;
  - the processing countries;
  - production's routing settings.
- **The opening sentence:** it now reads "when the Copilot or the room uses an externally hosted model, the member's
  question goes to the configured AI service, together with the company's data".
- **Question (h):** unchanged in substance, as the review said.

**2. The full-range checks** (`docs/screenshots/lawyer-pack-check-2026-11-07/full-diff-check.txt`, range
`ac35f28..e521082`):
- **`git diff --check ac35f28..e521082`:** exit 0.
- **`git diff --name-status`:** 11 paths, all under `docs/` or `PROJECT.md`.
  - **Modified:** the pack, the check record, the P9 production record, `LOG.md` and `PROJECT.md`.
  - **Added:** two browser prompts, output 84, replies 89 and 90, and `review-89-diff.txt`.
- **Not in the range:** no file under `api/`, `web/`, `scripts/` or `deploy/`, and not `docs/review-loop/MASTER-PLAN.md`.
- **`PROJECT.md` in the range:** 16 added lines and 0 removed. They are the status bullets recording reviews 89 and 90,
  shown in full in the file.

**Kept intact:**
- review 89's corrections, including the production market-data limitation;
- the contact-page and Arabic privacy-email issues;
- release `ea51de796c`;
- the renewal facts;
- the four owner facts;
- `docs/legal-questions-2026-10-27.md` as the companion document.

**Attachments:** this prompt and two zips.
- **`review-85-docs.zip`** (from `rebuild` at the commit of this output, by repository path):
  - the pack, the check record and the P9 production record;
  - `full-diff-check.txt` and `api-facts.txt`;
  - `PROJECT.md` and `docs/review-loop/MASTER-PLAN.md`, in full.
- **`review-85-code.zip`** (from `ea51de796c`): `api/app/settings.py`, `api/app/routers/debate.py` and
  `api/app/routers/copilot.py`.

**The question for the review:**
- Is the pack now accurate and ready for the owner to confirm the four facts and send?
- Which step is next on the plan?
