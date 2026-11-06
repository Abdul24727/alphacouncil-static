# Output 64: the owner's decision, and the sector-percentile fix on `rebuild`

**The owner's decision (2026-11-07, in chat):** "Keep it, take the fix". It was the answer to "Which way for the
advisors' room?", with the options "Keep it, take the fix" and "Test a one-model version".
- **The room:** today's room stays. Option 2 is not adopted; `presenter.py` stays a prototype, off by default.
- **Not in the decision:**
  - releasing the fix, which needs its own go-ahead;
  - the paid live-pack check of inventions, which is not approved.

**The defect** (found by the comparison's audit, `audit.md` §5.1):
- **What the field is:** the API's `sector_percentile` is the pipeline's standing score, passed through at
  `ticker_research.py:274`. It is flipped for lower-is-better metrics (`compute_gauge_scores.py`: `pct = 1 - pct`).
- **What 22.7 means:** on debt to equity it means more debt than about 77 % of the peer class.
- **How it was read:** both arms read it the other way in at least 67 turns.
- **What members see:** the site shows the same number to them as "Sector percentile" / "P23".

**The fix (commits `867f944` and `e2eecc3`; the branch it was built on is merged and
deleted):**
1. **The site** (`web/messages/en.json`, `ar.json`, `stock.fundamentals`):
   - **The label:** "Sector percentile" becomes a tooltip that defines it: "Sector standing, 0 to 100: higher is
     better on every measure. Where a lower value is better, such as debt to equity, a high standing means a low
     value." The Arabic says the same.
   - **The figures:** each metric's "P23" becomes "23", and each group's "P56" becomes "Standing 56" ("الترتيب 56").
   - **The withheld and narrowed notes** say "sector standing(s)".
   - **Unchanged:** the bar and its colours, which already read as a score (67 and up green, under 40 red).
2. **The room's pack** (`api/app/debate/pack.py`):
   - **The field:** `_standing` passes P2's `sector_percentile` and each group's `score` as `sector_standing`, with
     no value changed.
   - **The header** defines it: "HIGHER IS BETTER for every metric: where higher_is_better is false (debt_equity,
     ev_ebitda, ps, payout), a high standing means a LOW value, so a standing of 20 on debt_equity means more debt
     relative to equity than about 80 per cent of the peer class."
   - **The title:** P2 reads "Fundamentals, with each metric's sector standing where the peer group supports
     one".
   - **Saved eval packs** keep their own header and data, so past runs are unchanged.
3. **The Copilot** (`api/app/copilot/engine.py`, `tools.py`): its system prompt and the `get_fundamentals` tool
   description say that a sector percentile is a standing from 0 to 100 where higher is better on every metric.
4. **P9's notes** (`api/app/evidence.py`): `RANKING_WITHHELD` and `RANKING_NARROWED` now say "sector standing
   (percentile)". The second adds "higher is better on every metric", because the room and the Copilot both read
   these notes.

**Checks:**
- **The API:** suite 596 passed, 10 skipped. New tests:
  - `test_the_room_reads_the_sector_percentile_as_a_standing_where_higher_is_better`;
  - `test_the_copilot_is_told_which_way_the_sector_percentile_runs`.
- **Lint:** at its baseline.
- **The web:** typecheck clean, lint clean, 68 tests passed.
- **Whitespace:** `git diff --check` is clean.

**Not yet seen on screen:** the panel is Pro-only, so its look in both languages at 1440 and 390 will be checked on
beta after a release go-ahead, before production.

**The question for the review:** is the fix right and complete, and may it be offered to the owner for release to
beta and then production?
