# Review 68: Paid comparison result and hand audit

2026-11-06 23:14 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `61-comparison-result.md`.

VERDICT: FIX

ISSUES:

1. `audit.md:113–117,169` incorrectly calls all 34 entries “invented figures” tagged P9. `verified-claims.json:115` counts the nonnumeric claim “The system’s reason is a loss”; line 2563 counts an invented 1.5× threshold explicitly cited to P6. Separate invented claims from numeric inventions and correct the P9 generalization.
2. `audit.md:28` says `tools/tally.py` reproduces every count. It reproduces the 210/55 claim totals, but reads no per-flag classifications and cannot reproduce the **122/0** result at line 127. Preserve those classifications and reconcile that result, or mark it unverified.
3. `RESULT.md:23` and the output describe **$0.086** as the analyst’s average cost. Including retries and the failed session, recorded analyst spend is **$3.281672 / 30 = $0.10939 per session**, approximately **47% of A**, not 37%. Label $0.086 explicitly as the single-attempt figure.

DRIFT: The output stayed within the owner’s authorized room-cost comparison; the goal remains alphacouncil.tech finished, published and polished under PROJECT.md. Rejecting this prototype is correct: the independently reproduced cost ratio is 62.35%, exceeding the prewritten 40% limit.

NEXT STEP: On `rebuild`, correct the existing audit package in `docs/eval/presenter-comparison/` and its project summaries using the saved records. This completes the required evidence review without further spending and gives the owner an accurate basis for choosing the product fix.

DONE WHEN: `python -X utf8 docs/eval/presenter-comparison/tools/tally.py` reproduces the corrected claim categories and retained figure classifications; the analyst-cost calculation includes failed attempts; all 265 quotes still match their stated turns; the reports agree and historical run records remain unchanged.

OWNER ITEMS:

1. Send `docs/lawyer-review-pack-2026-11-06.md` for review of the live site; return advice for `docs/legal-advisors-<date>.md`.
2. Any further paid comparison, adoption, beta showing or release requires separate owner authorization.
3. Step 18 item 4 still awaits a real customer’s renewal.

Response complete
