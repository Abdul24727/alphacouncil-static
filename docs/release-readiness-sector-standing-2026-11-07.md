# Release readiness: the sector-standing fix (2026-11-07)

**What it fixes:**
- **The field:** the API's `sector_percentile` is the pipeline's standing score. It is flipped for metrics where lower
  is better (`compute_gauge_scores.py`: `pct = 1 - pct`), so 22.7 on debt to equity means more debt than about 77 %
  of the peer class.
- **How it was read:** in the paid comparison of 2026-11-07 both versions of the room read it the other way in at
  least 67 turns (`docs/eval/presenter-comparison/audit.md` §5).
- **On the site:** the page shows the same number to members as "Sector percentile" / "P23".
- **The decision:** the owner's, in chat: "Keep it, take the fix".

**The fix:** commits `867f944` and `e2eecc3` on `rebuild`. No value changes anywhere.
- **The site** (`web/messages/en.json`, `ar.json`):
  - **The labels:** "Sector percentile" / "P23" become "Sector standing", with a tooltip that higher is better on
    every measure, and that where lower is better (debt to equity) a high standing means a low value.
  - **The figures:** each group's score reads "Standing 56" ("الترتيب 56"), and each metric's figure is the bare number.
  - **Unchanged:** the bars and their colours.
- **The room's pack** (`api/app/debate/pack.py`): P2's field reaches the advisors as `sector_standing`, and the
  header defines it.
- **The Copilot** (`api/app/copilot/engine.py`, `tools.py`): its prompt and its fundamentals tool say the same.
- **P9's notes** (`api/app/evidence.py`): they call it a "sector standing (percentile)", where higher is better.

## Checks (pre-approved, no paid calls, nothing deployed)

| Check | Result |
|---|---|
| `git show --check 867f944`, `e2eecc3` | clean |
| API suite (`pytest -q`) | 596 passed, 10 skipped |
| The affected tests (`test_debate.py`, `test_copilot.py`, `test_evidence.py`) | 129 passed, including the two new tests |
| `ruff check .` | at its baseline, nothing new |
| Web `typecheck`, `lint`, `npm test` | clean, clean, 68 of 68 |
| Web production build (`npm run build`) | exit 0 |
| `git diff --check` | clean |

## Evidence

- **The room reads Al Rajhi correctly.** The frozen 1120 pack's P2, passed through the new code:
  - **The field:** `debt_equity` keeps value 1.7165 with `higher_is_better: false`, and its 22.7 is now
    `sector_standing`. Every value equals the one it replaces.
  - **The header now says:** "HIGHER IS BETTER for every metric: where higher_is_better is false (debt_equity,
    ev_ebitda, ps, payout), a high standing means a LOW value, so a standing of 20 on debt_equity means more debt
    relative to equity than about 80 per cent of the peer class." So 22.7 can no longer read as beating 77 % of
    peers.
- **The site, rendered locally:**
  - **How:** `next dev` at `localhost:3100`, with `API_ORIGIN` through a read-only tunnel to beta's API and GET
    requests only, on Aramco's `/financials` page.
  - **The screenshots** are in `docs/screenshots/sector-standing-2026-11-07/`: `en-1440`, `ar-1440`, `en-390` and
    `ar-390`.
  - **What they show:** "Standing 28 / 82 / 74 / 47" ("الترتيب …"), bare figures under the bars, and the new
    tooltip, read from the page in both languages. The old Arabic word المئين is gone, and nothing scrolls sideways
    at 390.
- **Live context:**
  - **Al Rajhi:** its ranks are withheld on the site since 2026-10-29 (the disputed bank peer class), so its 22.7 is
    the frozen pack's example.
  - **Where the fix matters:** every company whose ranks are shown, wherever a metric is lower-is-better (debt to
    equity, EV/EBITDA, P/S, payout).

## Remaining failures

None found.
- **The console notice:** the only message is Next's dev-only `generateMetadata` notice (the "1 Issue" badge), the
  same since 2026-11-03 and unrelated.
- **Not seen yet:** the change on beta itself. That waits for the release go-ahead.

## What a release would carry: the owner's choice

1. **The fix alone (recommended):** today's live release `b5655a5064` plus `867f944` and `e2eecc3`. It changes
   exactly what the owner approved. This candidate is not yet built or tested as a separate tree.
2. **`rebuild` as it stands:** the fix plus the presenter prototype (`presenter.py`, the `debate_engine` setting, ten
   router lines), which the owner has rejected. With the default `debate_engine = "room"` the only effect is an
   unused import, but it ships code the decision retired.

**Either way it goes to beta first, then production, each on its own go-ahead,** with the screenshots repeated on beta.
