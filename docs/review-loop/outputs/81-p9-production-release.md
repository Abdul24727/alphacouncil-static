# Output 81: the P9 fix released to production (review 86's step, on the owner's go-ahead)

**The go-ahead:** the owner answered "Yes, deploy to production" to "Deploy the P9 fix (ea51de796c) to production?",
put to them after review 86 accepted the beta release.

**What was done** (the record: `docs/release-production-p9-2026-11-07.md`, committed on `rebuild` as `4b79eba`):
1. **The preflight, rerun after the go-ahead** (`preflight-rerun.txt`, 19:21:58 UTC): `deploy-production.sh` equals
   the reviewed `c3bcff6`'s, the checkout is clean with HEAD equal to `DEPLOY_SHA`, beta runs `ea51de796c`, production
   runs `026699b906`, and `--check` exits 0 with prune `5c18a3ae46` and rollback `026699b906`.
2. **The deploy:** the beta record's production command, nothing added. It exited 0 at 19:35:11 UTC, "deployed
   ea51de796c to production" (`deploy-production.log`).
3. **The checks** (`prod-checks.txt` from `prod-checks-harness.sh`; read-only ssh, GETs on the public site, no model):
   1. **What runs:** production `prod/releases/ea51de796c`; releases `ea51de796c 026699b906 b5655a5064`; beta the same.
   2. **The processes:** both production services started at 19:34:54 UTC, with working folders in the new release.
   3. **What changed:** exactly the four P9 files; `web/` and `api/app/routers` identical.
   4. **The files:** the four by sha256, and all 3,566 against the commit's manifest from the beta release.
   5. **The prototype:** absent.
   6. **The site:** nine URLs answer 200, and health reports 714 tickers as of 2026-11-07.
   7. **The evidence endpoint:** still `403 pro_required` signed out.
   8. **The monitor's status:** 14 ok, and one with nothing to check.
4. **Step 10's signed-out checks, rerun** (`launch-check/`): SEO 62 PASS, Arabic 48 views with 0 English strings,
   advisors (visitor) 24 PASS, data fixes 44 PASS with the morning's sweep line field for field, and 20 page views at
   200. All equal this morning's run on `026699b906`.
   - **A connection drop:** at about 19:39 UTC two scripts stopped (`ECONNRESET`, `ERR_CONNECTION_TIMED_OUT`). Their
     outputs are kept as `*-attempt1.txt`.
   - **The server's side** (`connection-drop.txt`): no nginx error, no 5xx, no fail2ban action, services active, and
     its monitor at 15 of 15 at 19:35 and 19:40.
   - **The rerun:** both scripts, unchanged, passed. The cause is not known.

**Not checked, and said so in the record:**
- **P9's notes on production itself:** the endpoint is Pro-only, Claude makes no accounts, and a tunnel to production's
  API was refused earlier today. The stand-in is production's files equal to the commit, plus beta's word-for-word
  comparison, which review 86 accepted.
- **Whether the advisors stop inventing figures:** this needs a paid session, and none was run.

**What is left on the plan** (owner's, unchanged):
- Step 7: send the lawyer pack (`docs/lawyer-review-pack-2026-11-06.md`).
- Step 18 item 4: a real renewal.
- Pushing the 76 unpushed commits on `rebuild`, each push on its own go-ahead.
- Any paid run.

**Attachments:** this prompt and one zip, laid out by repository path:
- the record;
- the beta record (for the command and the comparison);
- the evidence folder `docs/screenshots/p9-production-2026-11-07/`;
- the manifest `docs/screenshots/p9-beta-2026-11-07/tree-sha256.txt`;
- `docs/launch-check-2026-11-07.md`.

**The question for the review:** is the production release done and right? And what is the next step on the plan?
As far as Claude can see, everything left on the plan is the owner's (above), and Claude's next work is to apply the
lawyer's advice when it comes. If anything on Claude's side remains that the plan supports, name it.
