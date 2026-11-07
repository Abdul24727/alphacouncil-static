# Output 67: the sector-standing fix, verified as a release candidate (review 72's step)

**Commits:** the fix is `867f944` and `e2eecc3`; this record is `6b45e75`, on `rebuild`. No paid calls, no push and
no deploy.

**The report:** `docs/release-readiness-sector-standing-2026-11-07.md`, attached. It is the DONE WHEN, item by item.
1. **The commits and the files they change:**
   - `git show --check` is clean for both commits.
   - The diff `64-percentile-fix-867f944.diff` covers all eight files they change: the site's en and ar messages,
     `pack.py`, the Copilot's `engine.py` and `tools.py`, `evidence.py`, and two tests.
   - `67-evidence.zip` holds the context: `ticker_research.py`, which passes the pipeline's score through as
     `sector_percentile`; `research-panels.tsx`, the panel and its bar colours; the new `pack.py`; and the pipeline
     excerpt that flips lower-is-better metrics.
2. **The tests and the build:**
   - **The API:** suite 596 passed, and the affected tests 129 passed, the two new ones included.
   - **Lint:** at its baseline.
   - **The web:** typecheck and lint are clean, 68 of 68 tests pass, and `npm run build` exits 0.
   - **The transcript:** `67-checks.txt`. It also shows no app or web change since the tests ran.
3. **Al Rajhi's 22.7:** the frozen 1120 pack's P2 through the new code gives the same value under
   `sector_standing`, with a header that a standing of 20 on debt_equity means more debt than about 80 % of the
   peer class. So 22.7 cannot read as beating 77 %. The transcript shows this, and that no value changed. On beta
   today Al Rajhi's ranks are withheld (the bank class), so the example is the frozen pack's.
4. **The English and Arabic wording:**
   - **The tooltips and panel texts** were read from the rendered page in both languages, and the old Arabic word is
     gone.
   - **The screenshots** are in the zip: en and ar at 1440 and 390, on Aramco through a read-only tunnel to beta's
     API, with GET requests only.
   - **At 390:** nothing scrolls sideways.
5. **`git diff --check` and the readiness report:** the check is clean, and the report lists no remaining failure.
   The only console message is Next's dev-only metadata notice, unrelated.

**One choice the report puts to the owner:**
- **The fix alone, on today's live release `b5655a5064` (recommended):** it changes only what the owner approved. It
  is not yet built as a separate tree.
- **`rebuild` as it stands:** it also carries the rejected presenter prototype, inert with the default setting (one
  unused import).

**The question for the review:** is the candidate ready to offer the owner for release to beta, and which tree should
go?
