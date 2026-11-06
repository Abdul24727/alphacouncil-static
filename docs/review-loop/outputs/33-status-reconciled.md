# Output 33: PROJECT.md's stale status lines reconciled (review 32's step)

Commit `12f73c9`. `PROJECT.md` only. `git diff --check` is clean. Historical outcomes and owner gates are
untouched; each correction is either a replaced status sentence with a correction note, or a dated note added
after the original text.

**§6, Current State:**
- **F-15:** "**(open, fix prepared)** … lands with the 2026-11-04 05:00 UTC publish, to be checked then" now reads
  "**F-15 (CLOSED, verified live 2026-11-04 after the 05:03:45 UTC publish; it was)**". It gives the evidence
  §9's Goal 2 row and Step F-15's outcome already held: all five companies have TTM income plus
  FY 2025-12 / Q 2026-06 balance sheets, and Tasheel's total assets read 3,197.89 / 3,365.01. It also carries a
  correction note.
- **The Gulf English-page follow-up:** "done on `rebuild` (2026-11-06, not released): 0 rows stay Arabic once
  F-16 is published" now reads "**done on `rebuild` and NOT released**". Candidate `dfc7a3d` passes the sweep
  over the 2026-11-06 published data, 714/714 companies and 40,811 lines, and waits on the owner's release
  go-ahead (`docs/release-readiness-2026-11-06.md`).
- **F-16:** already said CLOSED and verified live (13/13, sweep 714/714). Unchanged.

**§9, Next Up:**
- **The 2026-11-04 review's follow-up** ("8,099 Gulf rows … still show in Arabic on English pages, and nothing
  checks that direction") is kept as written, with a dated note: done on `rebuild` and NOT released. 79
  English-page pairs were added; the sweep (`SWEEP=1`) checks that direction and fails closed; it passes 714/714
  companies and 40,811 lines on `dfc7a3d`.
- **The owner's go-aheads list** gains the item it lacked:
  - **release candidate `dfc7a3d`** to beta, then production;
  - **what it ships:** Gulf statement lines in English on English pages, newest-first columns, bank sub-lines,
    the unconfirmed-currency caption, phone tables and capital-panel spacing;
  - **checks:** every candidate check passes;
  - **rollback:** `5c18a3ae46` in both tiers.
- **The "unpushed since then" line** now names Step 2's audit of `ccfe063..9712418` (45 commits, every hit read,
  none a value), and says the scans run again over the exact range at push time.

**Agreement with the readiness report:**
- **Candidate:** `dfc7a3d`.
- **Sweep:** 714/714 companies, 40,811 lines.
- **F-16:** verified live.
- **Rollback:** `5c18a3ae46`.
- **Audit range:** `ccfe063..9712418`.
- **Status:** awaiting the owner's release and push go-aheads.

**The question for the review:** is this sound, and what is the single next pre-approved step?
