# Output 36: the owner's 2026-11-06 go-aheads, executed, and the lawyer's review pack

**The owner's answers, in chat:**
- "yes go ahead" to the keep-14 snapshot retention;
- "push";
- "finish every thing first the lawer needs to check and test the site to make all documents";
- then one question with four answers:
  - release beta, then production;
  - retire D1/D3/D6 and run the $66 pilot;
  - copy the app's key for F-14;
  - delete the test accounts.

**Commits:** `5a46b8b`, `f7b7de3`, `8923238` and `eb639d8`. The record is in `PROJECT.md`: the changelog's 2026-11-06
"go-aheads executed" entry, and §9's owner list, where each item is struck with its outcome.

1. **Push** `ccfe063..b5655a5` (65 commits).
   - **Before it:** Step 2's scans re-run over that exact range, and every hit read. None is a value: 9 diff hits are
     prose naming Moyasar, value-shaped keys are 0, and the Argaam account appears 0 times.
   - **After it:** four sha-pinned anonymous fetches, hash-equal to `git cat-file`.
2. **Release `b5655a5064`** (app code = `dfc7a3d`; no commit between the two deploys).
   - **Beta:** every candidate check run against beta itself through the tunnel, all PASS. The sweep reads 714/714 and
     40,811 lines; check 15's gaps are 19 / 12 / 26 / 14 px.
   - **Production:**
     - services active, health 200;
     - `BILLING_OPEN` and `api.env` hash-equal before and after;
     - the labels' chunk byte-identical to beta's and hash-equal on the public site;
     - `check-billing-public.mjs` all passed.
   - **Rollback:** `5c18a3ae46`.
   - **Evidence:** `docs/screenshots/release-b5655a5064/` and the readiness report's "Released, 2026-11-06".
3. **Disk:** `scripts/server/prune-rebuild-snapshots.sh`, which is identical to the installed copy.
   - **Dry run:** listed exactly the recorded decision, 129 snapshots, oldest kept `20261024-014734`.
   - **The run:** freed 80.44 GiB; disk 83 % → 41 %.
   - **Nightly:** one crontab line at 11:15 UTC, with the crontab backed up first.
4. **F-14:** the app's key copied into the pipeline's `.env`, which was backed up first; the key was never printed.
   - **Result:** 401 → 200, and a two-item run wrote 2 rows.
   - **Disclosed:** the same key restarts step 19's KPI extraction (about 33 calls a night), which the new site does
     not read.
5. **Test accounts:** 24 removed on production and 158 on beta, all `@example.com` and listed first. 0 are left.
   Production's 4 real accounts and its one refunded payment are untouched.
6. **`owns` fix** applied. **D1/D3/D6 retired:** their definitions are kept and they never run; 15 probes run.
   **`--only` takes a list**, so the pilot keeps its first design of 3 derivation and 3 inference probes: D2, D4,
   D5, I1, I2, I3. Suite 543 passed, 10 skipped.
7. **The pilot is running**, capped at $66: 36 runs, the forecast $5.17. Its result will be output 37. Two findings
   are recorded:
   - **`RUN_BOUND` is stale.** The dry run measured $67.28 against $65.37, because the repaired packs are larger.
     The per-call cap still holds at $66. It must be re-measured before the $393 run is quoted.
   - **The OpenRouter balance was $13.47.** The live site shares it, so it is the owner's to top up.
8. **The lawyer's pack** (`docs/lawyer-review-pack-2026-11-06.md`). It is the owner's Step 7 instruction made
   concrete: the lawyer tests the site and drafts every document. It contains:
   - a one-hour test walk-through;
   - the six documents with their versions and consents;
   - the data inventory, processors and cookies, all checked against the code;
   - questions (a)–(e), updated, and new questions (f)–(i): the data's source, AI-written news, transfers abroad,
     renewal.

**Still the owner's:**
- Step 7, the lawyer;
- F-12's webhook, in Moyasar's dashboard;
- the OpenRouter top-up;
- the $393 run;
- a push go-ahead for these commits.

**The question for the review:** is this sound, and what is the single next pre-approved step?
