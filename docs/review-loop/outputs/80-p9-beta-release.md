# Output 80: the P9 fix released to beta (review 85's step, on the owner's go-ahead)

**The go-ahead:** the owner answered "Yes, deploy to beta" to "Deploy the P9 fix (ea51de796c) to beta only?".

**What was done** (the record: `docs/release-beta-p9-2026-11-07.md`, committed on `rebuild` as `41d27c1`):
1. **The preflight, rerun:** `deploy-staging.sh` equals the reviewed `c3bcff6`'s, the checkout is clean at
   `ea51de796c`, and `--check` exits 0 with prune `5c18a3ae46` and rollback `026699b906` (`preflight-rerun.txt`).
2. **Before the switch:** P9's notes for all 714 tickers were read on beta while it still served `026699b906`, GET only
   (`p9-notes-sweep.py`, giving `p9-notes-before.json`). `sweep-before-serving.txt` shows the release before and after
   the read.
3. **The deploy:** the readiness report's own command, nothing added. It exited 0, "deployed ea51de796c"
   (`deploy-beta.log`).
4. **The checks** (`beta-checks.txt` from `beta-checks-harness.sh`, every step exit 0; read-only, GET only, no
   model):
   1. **What runs:** beta runs `releases/ea51de796c`, and production is unchanged on `026699b906`.
   2. **What changed:** the release differs from production's commit in exactly the four P9 files.
   3. **The files on beta:** they equal the commit, the four by sha256 and all 3,566 by `tree-sha256.txt`.
   4. **The prototype:** absent.
   5. **Beta answers:** the API and six pages answer 200.
   6. **P9's notes:** compared word for word before and after (below).
   7. **The pack note:** what the room is told, from beta's own P9.
   8. **Production:** `--check` for this commit passes, and approves nothing.
   9. **The monitor's status:** 14 ok.

**Check 7, the comparison** (`p9-notes-compare.py p9-notes-before.json p9-notes-after.json`):
- **The data:** the statement data is the same in both sweeps for every ticker.
- **Unchanged word for word:** 638 tickers.
- **Changed:** 76, in five before/after pairs, all in the groups the fix names, in the numbers found on 2026-11-07.
  - **No statements:** 48.
  - **One year and no quarters:** 25, split 24 and 1 by the window's date.
  - **Quarters only:** 2.
  - **A balance sheet and quarters:** 1, company 232.
- **Other notes:** in no ticker did a note other than the statement notes change.

**Not measured:** whether the advisors now stop inventing statement figures needs a paid session, and none was run.

**What waits:** production, on the owner's separate go-ahead. The exact command, its preflight and the rollback are in
the record.

**Attachments:** this prompt and one zip, laid out by repository path:
- the record and the readiness report;
- the evidence folder `docs/screenshots/p9-beta-2026-11-07/`: the check log and its harness, the deploy log, the
  preflight, the two sweeps (JSON) and the two scripts;
- the candidate's `api/app/evidence.py` and `api/app/debate/pack.py`.

**The question for the review:** is the beta release done and right, and is it ready to put the production go-ahead to
the owner?
