#!/usr/bin/env bash
# Read-only preflight of the exact-commit guard. Every --check reads the server over SSH and changes nothing.
# Refusal cases without --check point at an unreachable host, so even a failed guard could not upload.
set -u
STG=/c/projects/alphacouncil-platform/scripts/deploy-staging.sh
PRD=/c/projects/alphacouncil-platform/scripts/deploy-production.sh
REB=/c/projects/alphacouncil-platform
CAND=/c/AlphaCouncil-Staging/deploy-026699b
ADV="$1"
SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42
WRONG=$(git -C "$REB" rev-parse b5655a5)
NOHOST=nobody@deploy-guard.invalid
run() {
  local label="$1" dir="$2"; shift 2
  echo "### $label"
  echo "\$ cd $dir && $*"
  ( cd "$dir" && env -u DEPLOY_BRANCH -u DEPLOY_SHA "$@" ) 2>&1 | sed 's/^/    /'
  echo "exit: ${PIPESTATUS[0]}"
  echo
}
echo "== checkouts"
echo "rebuild:   $(git -C "$REB" rev-parse --abbrev-ref HEAD) $(git -C "$REB" rev-parse HEAD)"
echo "candidate: $(git -C "$CAND" rev-parse --abbrev-ref HEAD) $(git -C "$CAND" rev-parse HEAD), status: $(git -C "$CAND" status --porcelain | wc -l) changed paths"
echo "advanced:  $(git -C "$ADV" rev-parse --abbrev-ref HEAD) $(git -C "$ADV" rev-parse HEAD) (a throwaway clone whose release/sector-standing is one empty commit past $SHA)"
echo "wrong SHA used below: $WRONG (b5655a5, today's live release)"
echo
echo "== syntax"
bash -n "$STG"; echo "bash -n deploy-staging.sh: exit $?"
bash -n "$PRD"; echo "bash -n deploy-production.sh: exit $?"
echo
echo "== staging, --check (read-only)"
run "S1 rebuild, default (no DEPLOY_* set)" "$REB" bash "$STG" --check
run "S2 candidate, no DEPLOY_BRANCH" "$CAND" bash "$STG" --check
run "S3 candidate, DEPLOY_BRANCH but no DEPLOY_SHA" "$CAND" DEPLOY_BRANCH=release/sector-standing bash "$STG" --check
run "S4 candidate, short DEPLOY_SHA" "$CAND" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b bash "$STG" --check
run "S5 candidate, wrong full DEPLOY_SHA" "$CAND" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$WRONG bash "$STG" --check
run "S6 different branch: rebuild checkout with the candidate's DEPLOY_BRANCH and DEPLOY_SHA" "$REB" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$STG" --check
run "S7 advanced release-branch HEAD, the approved DEPLOY_SHA" "$ADV" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$STG" --check
run "S8 rebuild pinned to a wrong DEPLOY_SHA" "$REB" DEPLOY_SHA=$WRONG bash "$STG" --check
run "S9 candidate, DEPLOY_BRANCH and the exact DEPLOY_SHA" "$CAND" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$STG" --check
echo "== staging, the deploy path itself (no --check), host unreachable: each must refuse before '== upload'"
run "S2' candidate, no DEPLOY_BRANCH" "$CAND" STAGING_HOST=$NOHOST bash "$STG"
run "S3' candidate, no DEPLOY_SHA" "$CAND" STAGING_HOST=$NOHOST DEPLOY_BRANCH=release/sector-standing bash "$STG"
run "S5' candidate, wrong DEPLOY_SHA" "$CAND" STAGING_HOST=$NOHOST DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$WRONG bash "$STG"
run "S6' different branch" "$REB" STAGING_HOST=$NOHOST DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$STG"
run "S7' advanced HEAD" "$ADV" STAGING_HOST=$NOHOST DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$STG"
echo "== production, --check (read-only)"
run "P1 candidate, DEPLOY_BRANCH and the exact DEPLOY_SHA (beta still runs b5655a5064)" "$CAND" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$PRD" --check
run "P2 candidate, no DEPLOY_SHA" "$CAND" DEPLOY_BRANCH=release/sector-standing bash "$PRD" --check
run "P3 advanced release-branch HEAD" "$ADV" DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$SHA bash "$PRD" --check
run "P4 rebuild, default" "$REB" bash "$PRD" --check
echo "== the servers afterwards (read-only)"
ssh -o BatchMode=yes root@alphacouncil.tech 'B=/opt/alphacouncil-platform; echo "beta current: $(readlink -f $B/current)"; echo "prod current: $(readlink -f $B/prod/current)"; echo "beta releases: $(ls -1t $B/releases | paste -sd " " -)"; echo "prod releases: $(ls -1t $B/prod/releases | paste -sd " " -)"; echo "active: $(systemctl is-active acp-api acp-web acp-prod-api acp-prod-web | paste -sd " " -)"'
