# Output 62: review 68's fixes to the comparison's audit package

**The fixes are in commit `f162ce4`, on `rebuild`, in `docs/eval/presenter-comparison/`. No paid call was made.**

**1. Inventions (issue 1).** `verified-claims.json` now splits the 34 inventions into two categories:
- **`invented figure` (23):** figures presented as the pack's that it does not hold:
  - Lynch's quarterly records (D2, I1, I2, I4, I5);
  - Buffett's income-statement figures (D2, I1, I2);
  - Dalio's balance sheet (I1);
  - Dalio's 1.5× leverage threshold, cited to [P6] (I6).
- **`invented source` (11):** statements that the pack holds data it does not, or concessions to invented data, with no
  figure of their own. Examples: "Here is the quarterly record from [P9]", "The system's reason is a loss" and "the
  quarterly record shows revenue growth".
- **The tags:** each invented figure's turn was checked for its source tag. They cite [P1], [P2], [P3], [P7] or [P9],
  or nothing, and the threshold cites [P6].
- **The corrected wording:** `audit.md` §2 and §5, `RESULT.md`, `PROJECT.md` and `MASTER-PLAN.md` now say that all
  but the I6 threshold rest on statement data the advisors' briefs place in P9, whatever tag the turn uses. The
  claim that they were all tagged [P9] is gone.

**2. The flag classes (issue 2).**
- **The classification file:** `tools/classify_flags.py` writes `flag-classifications.json`, which gives every
  UNVERIFIED flag outside the plants' openings one class. There are 587: A planted 265, A clean 243, P planted 66,
  P clean 13. These match the record and the fifteen auditors' totals.
- **The classes:**
  - `ok`: a correct derivation, rounding or label, or a figure quoted only to reject, correct or withdraw it;
  - `wrong`: a wrong value the turn asserts;
  - `invented`: a figure presented as the pack's that it does not hold.
- **The rules:** they are written in the script, keyed on probe, session, stage, seat and value, and they encode
  the auditors' per-flag findings. Every `wrong` rule matches a real flag; the script checks this and says so.
- **The result:** today's room asserted 122 wrong or invented figures, 72 in planted runs (20 wrong, 52 invented)
  and 50 in clean runs (17 wrong, 33 invented). Option 2 asserted none.
- **How the counts reproduce:** `tools/tally.py` now reads `verified-claims.json`, `flag-classifications.json` and
  `probe-results.jsonl` and reproduces all three:
  - every claim count and category (210 against 55; 23 invented figures and 11 invented statements);
  - the flag classes (122 against 0);
  - the costs.

**3. The analyst's cost (issue 3).**
- **The full figure:** `tally.py` computes it from the record, counting every attempt and the failed session:
  $3.281672 in all, **$0.1094 a session, or 46.9 % of A**.
- **Where it is used:** `RESULT.md`'s criterion-4 row and `audit.md` §6 now give that figure first. The single-attempt
  figure, $0.086 (37 %) in 24 sessions, is labelled as such.
- **Unchanged:** P's total stays 62.4 % of A.

**The checks from review 68's DONE WHEN:**
- **Every count reproduces:** `python -X utf8 docs/eval/presenter-comparison/tools/tally.py` gives the corrected
  claim categories and the kept flag classes.
- **The analyst's cost includes the failed attempts.**
- **Every quote matches its turn:** `tools/verify_quotes.py` checks each of the 265 quotes as an exact substring of
  the turn it is attributed to, with the same probe, arm, run, stage and seat, against `probe-results.jsonl`. None
  is missing.
- **The reports agree:** `audit.md`, `RESULT.md`, `PROJECT.md` and `MASTER-PLAN.md` give the same figures.
- **The records are unchanged:** `git diff --quiet` passes on `dry-probe-results.jsonl`, `probe-results.jsonl`,
  `pilot-2026-11-06/` and the comparison's own `probe-results.jsonl`.

**The question for the review:** may the audit package now stand as the basis for the owner's choice?
