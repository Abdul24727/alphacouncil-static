# Output 82: the lawyer pack, checked against the live site (review 87's step)

**Review 87's step:** "perform a read-only final handoff check for Step 7 … verify that its public URLs and
descriptions still correspond to the live ea51de796c site, and prepare a concise owner-ready handoff". Nothing to be
sent, no legal wording changed, no deploy, push or paid call.

**What was done** (the record: `docs/lawyer-pack-check-2026-11-07.md`, committed on `rebuild` as `e62aca8`):
1. **Every address the pack names** was requested signed out, GET only, in both languages where the pack says both
   (`urls.txt` from `urls.sh`). Every one answers 200, with three exceptions:
   - `/legal/merchant` answers 404, confirmed again in `merchant-recheck.txt`;
   - beta answers 401 without its password;
   - `www` answers 301 to the apex.
2. **18 pages' visible text** was read signed out in English and Arabic (`page-text/`, from `page-text.mjs`).
3. **The public API's facts** were saved (`api-facts.txt`): 714 companies on 7 exchanges, the Copilot's model
   `deepseek/deepseek-v3.2`, six advisors plus the Chair, `pro_limit` 20, and `/api/capabilities` 404.
4. **The pack's numbers** were compared with the released code (`ea51de796c`): plans, limits, legal versions,
   consent wording, renewal, grace and the reminder.

**Four discrepancies, each corrected in the pack:**
1. **The merchant address:** the pack's `/legal/merchant` is 404. The footer links to `/legal#merchant`, and the notice
   is at the foot of every legal document.
2. **The council tab:** the pack described it as "each seat's view of the company", which reads as the advisors' room.
   On the site it is six rule-based seats, with no language model, that each vote bullish, neutral or bearish on every
   equity (`/methodology`). The pack now says so and points it to question (b).
3. **The release:** `b5655a5064` became `ea51de796c`, with what the two fixes change.
4. **Question (i):** the pack said the site "can already send" a renewal reminder. The code sends one three days
   before each renewal, and checkout already says "Renews automatically every month …". The pack now quotes both. No
   reminder can have gone out yet: the first renewal is due 2026-12-02 at the earliest.

**Two facts added:**
- `/pricing`'s VAT sentence.
- `/methodology` says the data comes "from public market sources" and names no Argaam, while the pack's account is
  Argaam through an account. This is added to question (f).

**Also corrected:** the P9 production record (`docs/release-production-p9-2026-11-07.md`) said production's notes
depend on "its own database". In fact production's market-data settings were copied from beta's at setup
(`scripts/deploy-production.sh` lines 80–83; `docs/production.md`), and only the accounts database is its own. This
was not re-read on the server, because the settings sit in a file with credentials.

**Not covered, and said so:**
- the signed-in walk-through, because Claude makes no accounts;
- what the legal texts say, which is the lawyer's work;
- the account and payment counts, which the owner confirms before sending.

**Attachments:** this prompt and two zips.
- **`review-82-docs.zip`** (from `rebuild` at the commit above, by repository path):
  - the check record;
  - the corrected pack;
  - `legal-questions-2026-10-27.md`;
  - the evidence folder;
  - the P9 production record;
  - `docs/production.md`;
  - `scripts/deploy-production.sh`, the copy that ran the deploys.
- **`review-82-code.zip`** (from the released commit `ea51de796c`, by repository path):
  - `api/app/billing.py`, `plans.py`, `legal.py` and `auth.py`;
  - `web/src/components/site/SiteFooter.tsx`;
  - `web/src/content/legal/index.ts`;
  - the legal route `page.tsx`;
  - `web/messages/en.json`.

**The question for the review:**
- Is the pack now accurate to the live site, and is the handoff ready for the owner to send?
- Was any correction wrong, or any discrepancy missed?
- Which step is next on the plan?
