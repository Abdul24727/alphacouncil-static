# Review 64: Review 63 step: analyst-and-presenter prototype (off by default) and its 60-session dry comparison

2026-11-06 16:45 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `57-presenter-prototype.md`.

VERDICT: FIX

ISSUES:

1. `api/app/debate/presenter.py:214` converts an advisor’s reply with `dict(...)` before the fallback handler. The round validator at line 270 accepts non-object values. Reproduced offline: a string-valued Buffett opening aborts the session with zero fallbacks; $0.10 is billed but only $0.05 reaches the saved usage records.
2. `api/app/debate/presenter.py:54–66`: `combine()` hides unknown costs. Combining an unreported charge with a known $0.01 returns $0.01 as the total. Unknown must remain explicitly unknown, preserving the earlier review’s accounting requirement.
3. `api/eval/probe_run.py:407–408` saves turns and statistics but discards the analyst’s plan. Consequently, the audit promised in `docs/council-cost-options-2026-11-06.md:92–94` cannot establish which claims the presenter introduced beyond that analysis.
4. The cost brief needs reconciliation: line 8 says nothing is built, line 86 says transcripts are not retained, and line 78 calls approximately 41% “at” the 40% limit. The prototype and transcripts exist; the provisional ratio is **41.3%, above the criterion**.

DRIFT: The work stays within the owner’s approved room-cost direction and preserves the existing product scope. The goal remains alphacouncil.tech finished, published and polished under `PROJECT.md`; these defects need correction before the paid comparison is ready.

NEXT STEP: On `rebuild`, repair and revalidate the existing arm-P prototype and its audit records in `presenter.py`, `probe_run.py` and the cost brief, addressing the issues above while keeping it off by default. This is the most valuable pre-approved step because it prevents spending on results with broken recovery or incomplete evidence.

DONE WHEN: Offline regression tests prove malformed advisor values fall back individually, every known charge is recorded exactly once, mixed known/unknown costs stay explicit, and saved P results retain the analyst plan. Run the focused pytest checks and `git diff --check`, then repeat the isolated 60-session dry comparison without changing historical records. This review independently confirmed the saved 60-session totals and 29 tests passed; three filesystem-writing tests were excluded, and the full-suite claim was not independently rerun.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for review of the live site; return written advice for `docs/legal-advisors-<date>.md`.
2. After these corrections are reviewed, approve the necessary paid A/P comparison per run. Pushes and releases require separate go-aheads; changed room mechanics and wording must reach the lawyer before release.
3. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
