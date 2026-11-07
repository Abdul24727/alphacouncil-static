# Output 66: review 71's closeout of the comparison audit

**Commit:** `26d1d4f` on `rebuild`, with no paid call. Nothing was pushed or deployed, and the room's code is
unchanged.

**1. The stale counts (issue 1).** Each of the three references now gives the retained count and keeps the earlier
one as history:
- **`PROJECT.md` (the hand-audit entry):** "265 at first, 264 since review 70 took one out (`excluded-claims.json`)".
- **`PROJECT.md` (the review-68 entry):** "`tools/verify_quotes.py` checked all 265 against their stated turns. That
  was the count then; 264 are retained since review 70."
- **`MASTER-PLAN.md`:** "the counted claims (264 retained; 265 before review 70 took one out)".
- **What else still says 265:** only those labelled earlier counts, and the 265 flags of A's planted runs, which are
  a separate count.

**2. The evidence and its limits (issue 2).**
- **The overstatement:** output 65 said the claims' `why` fields carry the pack facts. That was too broad: some are
  only a label, such as "invented".
- **`audit.md` §1, "The evidence, and its limits", now says:**
  - **Reproducible by script from the repository:** that each quote sits in its attributed turn, that the flag
    classes follow their rules, and every count and cost.
  - **Resting on judgment:** whether each claim is wrong on the pack. An auditor made each judgment, and I checked it
    against the five frozen packs. A reader re-checks one by reading the turn beside its pack, and no script does it.
- **To close the gap for this review,** `66-evidence.zip` attaches everything the scripts need, under their
  repository paths:
  - the run record `probe-results.jsonl`;
  - `flag-classifications.json`, `verified-claims.json` and `excluded-claims.json`;
  - the scripts (`tally.py`, `verify_quotes.py`, `classify_flags.py`, `audit_dump.py`) and the auditors' brief;
  - the five frozen packs, `docs/eval/packs/*.en.json`.

  Unzipped as is, `python -X utf8 docs/eval/presenter-comparison/tools/tally.py` and the others run unchanged, and
  any claim can be checked against its pack.

**The checks from review 71's DONE WHEN** (`66-checks.txt`, run before the commit):
- **Flags:** `classify_flags.py` reports 587 classified, and every rule matched a flag.
- **Quotes:** `verify_quotes.py` reports 264 checked against their stated turns, with 0 missing.
- **Counts** (`tally.py`):
  - **Wrong claims:** A 209 and P 55.
  - **Inventions:** A has 23 invented figures and 24 invented statements, 47 in all; P has 0 and 2.
  - **Asserted wrong or invented figures:** A 72 + 49 = 121, P 0.
  - **Cost:** P is 62.4 % of A, and the analyst $0.1094 a session.
- **Whitespace:** `git diff --check` is clean.
- **The records:** `git diff --quiet 24f94d7` exits 0, with the working tree included, for the historical records,
  the comparison's `probe-results.jsonl` and `flag-classifications.json`.
- **Not repeated:** `git status -sb` in the transcript shows the closeout's edits before they were committed in
  `26d1d4f`.

**The focused diff:** `66-diff-31e7211-26d1d4f.diff`.

**The question for the review:** may the comparison audit now be closed?
