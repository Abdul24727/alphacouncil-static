# Output 72: the sector-standing fix is on production (the owner's go-ahead)

**The owner's go-ahead** (in chat, 2026-11-07): "Yes, deploy to production", to "Deploy the sector-standing fix
(026699b906) to production?". Review 77 had accepted beta and named this as owner item 1.

**What was done** (`release-production-sector-standing-2026-11-07.md`, attached):
1. **Review 77's preflight, rerun right before:**
   - the script was unchanged since `c3bcff6`;
   - the checkout was clean;
   - the exact-commit `--check` exited 0, with beta now `026699b906`, prod now `b5655a5064`, prune `2e44ee6fbf`, and
     rollback `b5655a5064 (kept)`.
2. **The release's own command** (`deploy-production.log`):
   - **Upload, build and switch:** the commit was uploaded and built. The live site kept serving `b5655a5064` until
     the switch.
   - **The restart:** `acp-prod-api` and `acp-prod-web` restarted and answered 200.
   - **The prune:** it removed `2e44ee6fbf`.
   - **The exit:** 0.
3. **Not done:** nothing was pushed, and nothing was paid for. nginx, the databases, the pipeline and billing were not
   touched.

**The checks after** (`prod-checks.txt` from `prod-checks-harness.sh`; read-only ssh and signed-out GETs on the live
site):
- **What runs:** production `prod/releases/026699b906` and beta `releases/026699b906`, all four services active.
- **The files:** the eight changed files and all 3,566 committed files on production are equal by sha256 to the
  commit. The manifest is beta's `tree-sha256.txt`, which was made from the commit. The prototype is absent.
- **The live wording, before and after on the same pages** (`before-labels.txt`, read at 09:45 UTC on `b5655a5064`):
  - **English:** "Sector percentile" went from 6 to 0, and "Sector standing" from 0 to 6.
  - **Arabic:** "المئين" went from 8 to 0, and "الترتيب داخل القطاع" from 0 to 2.
  - **The other public pages:** no public page checked carries the old phrases. The bare word "percentile" remains
    only as the message key name.
- **The Arabic check:** 48 views, 0 English strings outside the allow-list.
- **The monitor** (`monitor-status.txt`, the read-only `status`):
  - **15 of 15 ok**, including "Moyasar for renewals", which was "–" on 2026-11-06.
  - **Alerts:** the two emailed in the last 24 hours date from 2026-11-06. None came from the restart.
- **Step 10's signed-out checks, rerun on this release** (`launch-check-2026-11-07.md` and its outputs, attached):
  - SEO 62/0;
  - advisors visitor 24/0;
  - data fixes 44/0 with 1 INFO, and a 714-ticker sweep with `eps_bad` 0;
  - 20 page views, all 200 with no sideways scroll.
  - Every count equals 2026-11-06's.

**What could not be seen, and why:**
- **The panel signed out:** on production, the Fundamentals panel is Pro-only for a signed-out visitor
  (`signed-out-panel.txt`: the Pro lock in en and ar at 1440 and 390).
- **The captures:** the beta capture script timed out against production for that reason, and it was not kept.
- **The rendered panel with the new labels:** it is shown on beta, which runs the same commit, in four captures
  (accepted in review 77).
- **A Pro member's view on production:** not captured, because Claude makes no accounts on the live site. The owner
  can confirm it signed in.

**The question for the review:** is the production release verified, and is the sector-standing fix (the owner's
"Keep it, take the fix") now closed? What is the next step on the plan?
