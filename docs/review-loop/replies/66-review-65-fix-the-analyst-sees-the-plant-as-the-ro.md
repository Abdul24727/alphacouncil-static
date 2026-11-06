# Review 66: Review 65 fix: the analyst sees the plant as the room's Chair does; dry comparison repeated

2026-11-06 21:22 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `59-plant-equivalence.md`.

VERDICT: FIX

ISSUES:

1. [presenter.py:132](C:/projects/alphacouncil-platform/api/app/debate/presenter.py:132) tells the analyst to “write no opening” for pinned seats, but `check_plan` at line 191 requires an `opening` object for every seat. Reproduced: removing Buffett’s opening from an otherwise accepted planted plan raises `ValueError`; supplying `{}` passes. This can cause unnecessary paid retries or failed sessions. The stand-in always supplies an opening, so the 21 passing focused tests and reproduced 60-session dry comparison miss this mismatch.

DRIFT: The output stays within the owner’s room-cost direction and preserves the existing presentation. The goal remains alphacouncil.tech finished, published and polished under `PROJECT.md`.

NEXT STEP: On `rebuild`, align the pinned-seat prompt and validation in `api/app/debate/presenter.py`: accept an omitted opening for pinned seats while retaining validation for other seats, and add the regression in `api/tests/test_eval_probe_run.py`. This small, pre-approved correction removes an avoidable failure before spending on the comparison.

DONE WHEN: The regression accepts omitted/empty pinned openings, rejects missing unpinned openings, and preserves identical planted claims across all 15 probes. Run `python -m pytest tests/test_eval_probe_run.py -q` from `api`, pass `git diff --check`, and repeat the isolated 60-session dry comparison with historical records unchanged. The owner’s existing approval stands for the unchanged paid comparison once the correction is accepted.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for review of the live site; return advice for `docs/legal-advisors-<date>.md`.
2. After audited results, decide adoption and separately approve any beta showing or release; changed mechanics and wording must reach the lawyer before release.
3. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
