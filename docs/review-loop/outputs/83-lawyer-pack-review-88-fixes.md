# Output 83: review 88's four points, fixed (the lawyer pack and its check)

**Review 88 said FIX.** Its step: one documentation-only correction pass on the pack and the check record, adding the
contact-link issue and verifying the plan-file diffs. Nothing to be sent, released, pushed or paid for.

**What was done** (committed on `rebuild` as `ea59b9d`):

1. **The AI models** (pack §5.2; review 88 issue 1).
   - **Now:**
     - **The Copilot, confirmed live:** `deepseek/deepseek-v3.2`, from the public `/api/v1/copilot/status`.
     - **The seats and the Chair:** marked not confirmed, with the code's defaults named, for the owner to confirm.
   - **Added:** OpenRouter picks the hosting company per request, so the company that runs a request is not
     necessarily the model's maker. This bears on question (h).
     - **The code** (`api/app/copilot/openai_compat.py`, `host_routing`): its default sorts hosts by latency, and
       `COPILOT_PROVIDER_ORDER` can name hosts for the Copilot to try first, with fallbacks.
     - **Not read:** production's values for both.
2. **"The same data"** (pack §2 and the P9 production record; issue 2).
   - **Now:** production's market-data settings were copied from beta's at setup (`scripts/deploy-production.sh`
     80–83), and that they still match was not checked again.
   - **The P9 record:** it now says it is not established that production's notes equal beta's.
3. **The missed contact-page issue** (issue 3; `contact-check.txt` from `contact-check.mjs`).
   - **What the texts say:** all five legal texts, in en and ar, give "Contact page:
     https://alphacouncil.tech/contact.html".
   - **Where it leads:** nginx answers 301 to `/legal` (`deploy/nginx-production.conf` line 65). `/legal`, the legal
     index, has its only contact details in the merchant notice: the address, telephone and emails.
   - **Other addresses:** `/ar/contact.html` and `/contact` answer 404. The texts name no other site address than the
     bare domain.
   - **One more issue found:** the Arabic merchant notice lacks the privacy email that the English one gives
     (`web/src/content/legal/merchant.{en,ar}.json`; `page-text/legal-index.{en,ar}.txt`).
   - **In the pack:** both are listed under question (e) as known issues in the imported texts. The texts themselves
     are left alone until the lawyer advises.
4. **The plan files** (issue 4; `plan-diffs.txt`, the full diff since `5a44457`).
   - **Six lines removed, each replaced by its updated form.**
   - **The hunks:** PROJECT.md line 2 (the deployed release) and new P9 history bullets in §5; MASTER-PLAN's Goal 4
     state cell, the "site is published" sentence, and P9 bullets.
   - **Untouched:** the objective, scope, Done-when, §4's rules and approvals, and the owner's decisions.
   - **Attached in full:** both files, so the diff can be checked against them.
5. **The handoff** (check record, top).
   - **Two documents:** the pack, and `docs/legal-questions-2026-10-27.md`.
   - **Three facts the owner must confirm,** each marked in the pack:
     - the 2026-11-06 account and payment counts;
     - the hosting provider and its country;
     - the seats' and the Chair's production models.
   - **The pack's three kinds of statement:** confirmed live, read from code, and the owner's to confirm.
6. **`git diff --check` is clean.** Two whitespace-only edits were needed:
   - one trailing space in review 88's saved reply;
   - the blank context lines in `plan-diffs.txt`.

   Only `docs/` and `PROJECT.md` changed.

**Kept, as review 88 asked:**
- `/legal#merchant`;
- the council described as rule-based votes, separate from the AI room;
- release `ea51de796c`;
- the VAT sentence;
- the renewal-reminder facts.

**Attachments:** this prompt and two zips.
- **`review-83-docs.zip`** (from `rebuild` at `ea59b9d`, by repository path):
  - the pack and the check record;
  - the check's evidence folder: `plan-diffs.txt`, `contact-check.*`, `page-text/` and the rest;
  - the P9 production record;
  - `PROJECT.md` and `docs/review-loop/MASTER-PLAN.md`;
  - `deploy/nginx-production.conf` and `scripts/deploy-production.sh`;
  - `docs/legal-questions-2026-10-27.md`.
- **`review-83-code.zip`** (from `ea51de796c`):
  - `api/app/copilot/openai_compat.py` and `api/app/settings.py`;
  - `web/src/content/legal/merchant.en.json` and `merchant.ar.json`.

**The question for the review:**
- Are the four points fixed, and is the handoff ready for the owner?
- Was anything still missed?
- Which step is next on the plan?
