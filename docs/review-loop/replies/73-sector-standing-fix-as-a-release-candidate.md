# Review 73: Sector-standing fix as a release candidate

2026-11-07 00:36 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High, with the attached files.
Output reviewed: `67-sector-standing-release-candidate.md`.

VERDICT: FIX

ISSUES:

1. The recommended fix-only release candidate has not been built or tested.
`docs/release-readiness-sector-standing-2026-11-07.md`, lines 65–71, explicitly confirms this.

The eight-file patch is consistent with the intended correction. I independently executed the extracted `_standing()` function and confirmed that Al Rajhi's debt-to-equity value remains `1.7165282723300337`, its standing remains `22.7`, and only the field name changes. The supplied pipeline excerpt also confirms the inversion for lower-is-better metrics.

However, the successful tests were run against `rebuild`, not an isolated release constructed from production `b5655a5064` plus the two fix commits. The proposed release artifact is therefore not yet qualified. Do not ship `rebuild` as it stands: it contains the rejected presenter prototype.

2. The desktop screenshot evidence does not establish native 1440 px captures.
In `67-evidence.zip`, both files named `en-1440-2222.jpg` and `ar-1440-2222.jpg` are actually 800 × 555 pixels. Both mobile files are correctly 390 × 844 pixels.

I inspected all four images. English and Arabic layouts show the new standing labels, corresponding metric values, and no visually apparent horizontal overflow. The desktop images may have been resized from a 1440 px viewport, but the archive does not establish that. The tooltip wording is supported by the supplied diff and transcript, although the tooltip itself is not visible in the screenshots.

Supply original-resolution captures or an explicit viewport-size record with the captures.

3. The required final Git evidence is incomplete.
`67-checks.txt`, lines 1–46, reports the test results, build success, and `git show --check`, but does not contain the requested `git diff --check` or `git status -sb` output.

The readiness report claims a clean diff, but the attached transcript does not independently establish it. The API's 596 passing tests, 129 focused tests, and web's 68 passing tests are reported results; the complete repository and test environment were not attached, so I cannot independently rerun those suites or authenticate the Git history.

These are release-verification gaps, not demonstrated failures in the sector-standing calculation.

DRIFT:

The correction stays within the owner's approved plan: today's advisors' room remains selected, underlying market values are unchanged, and no new feature or paid comparison is introduced. Shipping the current `rebuild` tree would depart from the decision to reject option 2; the fix-only tree is the correct choice.

NEXT STEP:

On the local AlphaCouncil repository, prepare and verify an isolated fix-only release candidate, starting from deployed production commit `b5655a5064` and applying only the changes from `867f944` and `e2eecc3`.

Use a temporary local worktree or equivalent isolated build. Do not modify the running site, include the rejected presenter prototype, push, deploy, or make paid model calls.

This is the highest-value pre-approved next step because it converts an otherwise verified correction into a specific, testable release artifact that can safely be submitted for the owner's beta approval.

DONE WHEN:

Claude supplies one amended release-readiness report demonstrating:

1. `git diff --name-status b5655a5064 <candidate>` contains exactly the eight intended files, without `presenter.py`, the rejected `debate_engine` integration, or unrelated changes.
2. The isolated candidate passes the API suite, focused tests, web typecheck, lint, 68 web tests, and production build.
3. `git show --check` for both fix commits, `git diff --check`, and `git status -sb` are recorded with actual command output.
4. Al Rajhi's frozen P2 example preserves `22.7` as `sector_standing`, identifies the metric as lower-is-better, and never describes that standing as outperforming approximately 77% of peers.
5. English and Arabic desktop and mobile screenshots are supplied with verified 1440 and 390 px viewport dimensions, showing the intended wording, with no sideways overflow.
6. The report identifies the exact candidate revision, confirms no rejected prototype code is included, and records that beta and production remain unchanged.

No deployment is authorized by this review.

OWNER ITEMS:

1. Highest priority — Step 7, legal review. Send `docs/lawyer-review-pack-2026-11-06.md` to the lawyer for evaluation of the published site. Record the written advice and ensure required corrections are implemented before legal closeout.
2. Sector-standing release authorization. Once the isolated candidate passes the checks above, separately authorize beta deployment. Review the beta evidence before separately authorizing production. Do not approve deployment of the existing `rebuild` tree.
3. Step 18, item 4 — real subscription renewal. This remains open until a genuine customer renewal is verified on production. An empty renewal run or green monitor alone does not prove completion.

Response complete
