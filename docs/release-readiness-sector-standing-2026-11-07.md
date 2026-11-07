# Release readiness: the sector-standing fix (2026-11-07, amended after review 73)

**The candidate:** `026699b` on local branch `release/sector-standing`. It is today's production release
`b5655a5` (deployed as `b5655a5064`) plus two commits:
- `cae5578`, the same change as `867f944` on `rebuild`;
- `026699b`, the same change as `e2eecc3`.

Their patch ids are identical (`candidate-git.txt`). It contains no code from the rejected analyst-and-presenter
prototype. Per review 73, `rebuild` as it stands is not offered.

**What it fixes:**
- **The field:** the API's `sector_percentile` is the pipeline's standing score. It is flipped for lower-is-better
  metrics (`compute_gauge_scores.py`: `pct = 1 - pct`), so 22.7 on debt to equity means more debt than about 77 % of
  the peer class.
- **How it was read:** in the paid comparison of 2026-11-07 both versions of the room read it the other way in at
  least 67 turns (`docs/eval/presenter-comparison/audit.md` §5).
- **On the site:** the page shows the same number to members as "Sector percentile" / "P23".
- **The decision:** the owner's, in chat: "Keep it, take the fix".

**What it changes:** no value, anywhere.
- **The site** (`web/messages/en.json`, `ar.json`):
  - **The labels:** "Sector percentile" / "P23" become "Sector standing", with a tooltip that higher is better on
    every measure, and that where lower is better (debt to equity) a high standing means a low value.
  - **The figures:** the group scores read "Standing 56" ("الترتيب 56"), and each metric's figure is the bare number.
  - **Unchanged:** the bars and their colours.
- **The room's pack** (`api/app/debate/pack.py`): P2's field reaches the advisors as `sector_standing`, defined in
  the header.
- **The Copilot** (`api/app/copilot/engine.py`, `tools.py`): its prompt and its fundamentals tool say the same.
- **P9's notes** (`api/app/evidence.py`): "sector standing (percentile)", where higher is better.

## The DONE WHEN of review 73, item by item

1. **`git diff --name-status b5655a5 026699b`** lists exactly the eight intended files:
   - `api/app/copilot/engine.py`, `api/app/copilot/tools.py`, `api/app/debate/pack.py` and `api/app/evidence.py`;
   - `api/tests/test_copilot.py` and `api/tests/test_debate.py`;
   - `web/messages/ar.json` and `web/messages/en.json`.

   The candidate has no `presenter.py`, no `debate_engine` setting and no change to `routers/debate.py` or
   `settings.py` (`candidate-git.txt`).
2. **The candidate passes every check, run in its own worktree** (`candidate-checks.txt`):

   | Check | Result |
   |---|---|
   | API suite (`app` imported from the candidate's own tree) | 578 passed, 11 skipped |
   | `test_debate.py`, `test_copilot.py`, `test_evidence.py` | 129 passed |
   | `ruff`, each changed Python file against production's | identical (engine 1/1, tools 0/0, pack 0/0, evidence 10/10, the two tests 2/2 and 4/4) |
   | Web production build | exit 0 |
   | Web typecheck | exit 0 |
   | Web lint | exit 0 |
   | Web tests | 68 of 68 |

   - **The test count:** `rebuild`'s 596 includes the prototype's tests; the candidate has none of them.
   - **The type check:** before the first build, it could not find Next's generated `PageProps` / `LayoutProps` in
     the fresh worktree. The build generates them, and it then passed. This is the environment, not the code.
3. **The git evidence, as command output** (`candidate-git.txt`):
   - `git show --check` is clean for `867f944`, `e2eecc3`, `cae5578` and `026699b`.
   - `git diff --check b5655a5 026699b` is clean.
   - `git status -sb` reads `## release/sector-standing`, with nothing else.
4. **Al Rajhi's frozen example, run on the candidate's own code:**
   - `debt_equity` keeps value 1.7165 and `higher_is_better: false`.
   - The 22.7 is preserved as `sector_standing`, and no value changed.
   - The header says that higher is better on every metric, that a high standing on a lower-is-better metric means a
     LOW value, and that a standing of 20 on debt_equity means more debt than about 80 % of the peer class.
   - Nothing in it describes the standing as beating or outperforming about 77 % of peers.
   - On the live site, Al Rajhi's ranks are withheld (the bank peer class), so the example is the frozen pack's.
5. **The screenshots at native size:**
   - **How:** the candidate's production build (`next start`), with its API calls through a read-only tunnel to
     beta's API and GET requests only.
   - **The captures:** Aramco's Financials page in Chrome, by `playwright-core`, at a device scale of 1.
   - **Where:** `docs/screenshots/sector-standing-2026-11-07/`:
     - `en-1440-2222.png` and `ar-1440-2222.png` are 1440 × 1000 px;
     - `en-390-2222.png` and `ar-390-2222.png` are 390 × 844 px.
   - **The viewport record** (`viewports.json`) gives each capture's innerWidth (1440 or 390), its scrollWidth (equal,
     so no sideways scroll), the tooltip read from the page, and the panel's texts:
     - "Standing 28 | … | Standing 82 | … | Standing 74 | … | Standing 47";
     - "الترتيب 28 | …" in Arabic.

     No old label ("Sector percentile", المئين) remains. The earlier 800 px pane captures are replaced.
6. **Revision and state:**
   - **The revision:** the candidate is `026699b`.
   - **No prototype code:** see item 1.
   - **The servers are unchanged** (read-only SSH): beta `/opt/alphacouncil-platform/current` and production
     `/opt/alphacouncil-platform/prod/current` both point to `releases/b5655a5064`, and production's api and web are
     active. Nothing was deployed, pushed or paid for.

## Remaining failures

None.
- **The console notice:** the only console message seen locally is Next's dev-only `generateMetadata` notice, the
  same since 2026-11-03 and unrelated.

## Release, on the owner's go-ahead only

- **Beta first:** release `026699b` to beta. `scripts/deploy-staging.sh` archives `HEAD` of the checkout it runs in
  (`git archive --format=tar HEAD`), so it runs from a checkout of `release/sector-standing` and needs no push.
  Pushing stays a separate go-ahead. Then repeat these captures on beta.
- **Then production,** on its own go-ahead.
- **Rollback:** `b5655a5064` is kept on both tiers.
