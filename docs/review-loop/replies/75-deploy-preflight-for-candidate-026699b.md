# Review 75: Deploy preflight for candidate 026699b

2026-11-07 01:10 UTC. Reviewer: ChatGPT on chatgpt.com in the owner's browser, model GPT-6, thinking effort High, with the attached files.
Output reviewed: `69-deploy-preflight.md`.

VERDICT: FIX

The deployment approach is correct, and the preflight substantially satisfies review 74. However, one release-safety gap must be closed before presenting the beta deployment as ready for authorization: the scripts verify the branch but do not enforce the exact reviewed commit.

Both scripts pass `bash -n`, and I verified that `69-scripts.diff` reverse-applies cleanly to the attached scripts. The reported checkout selection and archive behavior are consistent with the code.

ISSUES:

1. The approved release SHA is not enforced — blocking.

Files: `scripts/deploy-staging.sh`, lines 20–24 and 58–59; `scripts/deploy-production.sh`, lines 22–27 and 83–84.

`DEPLOY_BRANCH=release/sector-standing` verifies the branch name, but deployment archives whatever `HEAD` points to when the command runs.

I independently simulated this behavior with a local Git repository. After advancing the release branch to a different commit, staging's `--check` still accepted that branch and reported the new HEAD.

Consequently, the scripts do not guarantee deployment of the specifically reviewed and requested commit `026699b906ea3a513b4f2dbfc37672fa68ee9d42`.

Required fix: For non-default branch deployments, require an explicit full `DEPLOY_SHA`, reject a missing or mismatched SHA, and archive the verified commit rather than resolving mutable `HEAD` again. Preserve the existing default `rebuild` behavior.

2. Production's `--check` reports a blocking mismatch but exits successfully.

Files: `scripts/deploy-production.sh`, lines 30–41; `deploy-preflight.txt`, lines 38–47.

The preflight correctly identifies that beta runs `b5655a5064`, not `026699b906`. The actual production deployment would refuse.

However, `--check` exits `0` despite reporting that refusal. This is valid as an informational diagnostic, but not as a passing deployment-readiness gate.

Make the check return nonzero when deployment prerequisites are unmet, while retaining its read-only behavior.

3. The owner-facing deployment command contains an unresolved placeholder.

File: `docs/release-request-sector-standing-2026-11-07.md`, lines 45–46.

The command uses `<rebuild>/scripts/deploy-staging.sh` instead of the concrete script path exercised in the preflight.

Replace it with the tested absolute path and include the exact SHA guard. This prevents ambiguity when the approved command is eventually executed.

4. Some validation evidence is referenced rather than independently available in this review.

File: `docs/release-request-sector-standing-2026-11-07.md`, lines 15–25.

Review 74 reports that the candidate's complete diff, tests, build, and four screenshots were checked. Those original artifacts are not attached to this particular review, so their results cannot be independently repeated here.

`candidate-git-raw.txt` confirms the reported successful Git checks and eight-file name-status list. The SSH state is supported by the supplied transcript, not by independent access to the server.

This limitation does not invalidate review 74 or require repeating its accepted test suite.

DRIFT:

The work remains within the master plan: isolate and release the existing sector-standing correction without shipping the rejected presenter prototype, changing market values, adding features, or initiating paid activity. The additional SHA safeguard is release-safety work, not product-scope expansion.

NEXT STEP:

Claude should complete the exact-commit deployment safeguard on `rebuild`, then update the existing release request.

Modify only `scripts/deploy-staging.sh`, `scripts/deploy-production.sh`, and the directly related preflight documentation. Require the full approved SHA whenever an alternative release branch is selected, ensure production's readiness check fails when beta does not match, and replace the placeholder deployment command with the tested path.

This is the most valuable pre-approved action because it closes the remaining risk of deploying code other than the accepted candidate. No push, upload, deployment, or paid call is authorized.

DONE WHEN:

Claude supplies evidence that:

1. Both modified scripts pass `bash -n`.
2. Staging `--check` accepts `release/sector-standing` only with the exact SHA `026699b906ea3a513b4f2dbfc37672fa68ee9d42`.
3. A missing SHA, incorrect SHA, different branch, or advanced release-branch HEAD fails before any upload, build, switch, or deletion.
4. The default `rebuild` invocation remains compatible with its previous behavior.
5. Production's preflight fails while beta runs `b5655a5064`; no production deployment occurs.
6. A final read-only preflight records the correct checkout, full commit, archive source, existing beta and production revisions, and rollback target.
7. The updated owner-facing request identifies the exact candidate, executable deployment command, beta-only scope, expected pruning, and separate production authorization requirement.

Do not rerun the previously accepted full application test suite without a relevant code change.

OWNER ITEMS:

1. Highest priority — Step 7, legal review. Send `docs/lawyer-review-pack-2026-11-06.md` to the lawyer for evaluation of the already published site. Written advice and any necessary changes remain required for launch completion.

2. Beta-release authorization. Once the exact-SHA safeguard passes review, explicitly approve or decline deployment of `026699b906ea3a513b4f2dbfc37672fa68ee9d42` to beta only. The authorization should acknowledge that the normal beta pruning will remove the oldest release while retaining `b5655a5064` for rollback. Production requires a separate approval after beta verification.

3. Step 18, item 4 — real renewal. The genuine customer subscription-renewal check remains outstanding. It cannot be closed using a simulated renewal or monitor result.

Response complete
