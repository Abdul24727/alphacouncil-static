#!/usr/bin/env bash
# Deploy a committed revision of this repo to production, alphacouncil.tech (docs/production.md).
#
#   scripts/deploy-production.sh            # deploy HEAD (on branch `rebuild`, already live on beta)
#   scripts/deploy-production.sh --setup    # first time: env files, units and the app database
#   scripts/deploy-production.sh --check    # read-only: say what would be deployed and whether it may be, then
#                                           # stop; exits 1 when a deploy would refuse
#
# Another reviewed branch is deployed only when named explicitly, together with the full commit approved for it
# (DEPLOY_BRANCH=<branch> DEPLOY_SHA=<full 40-character commit>), from a checkout of it, and only once beta runs
# that same commit. DEPLOY_SHA may also pin a `rebuild` deploy. The commit checked is the one archived and built.
#
# Production only gets what staging already runs: the commit must be the release behind
# beta.alphacouncil.tech. Pointing alphacouncil.tech at this app (nginx) is a separate,
# manual step with its rollback in docs/production.md.
set -euo pipefail

HOST="${PROD_HOST:-root@alphacouncil.tech}"
BASE=/opt/alphacouncil-platform/prod
ENVDIR=/etc/alphacouncil-platform/prod
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

refuse() { echo "refusing: $*" >&2; exit 1; }
expected="${DEPLOY_BRANCH:-rebuild}"
branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "$expected" ]] || refuse "on branch '$branch', expected '$expected' (DEPLOY_BRANCH names another reviewed branch)"
[[ "$expected" == rebuild || -n "${DEPLOY_SHA:-}" ]] || refuse "DEPLOY_BRANCH=$expected needs DEPLOY_SHA, the full commit approved for it"
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || refuse "uncommitted changes"
commit="$(git rev-parse --verify "HEAD^{commit}")"
if [[ -n "${DEPLOY_SHA:-}" ]]; then
  [[ "$DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]] || refuse "DEPLOY_SHA must be a full 40-character commit, got '$DEPLOY_SHA'"
  [[ "$commit" == "$DEPLOY_SHA" ]] || refuse "HEAD of '$branch' is $commit, not the approved DEPLOY_SHA $DEPLOY_SHA"
fi
sha="${commit:0:10}"
rel="$BASE/releases/$sha"
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

staged="$(ssh_ 'basename "$(readlink -f /opt/alphacouncil-platform/current)"')"
if [[ "${1:-}" == "--check" ]]; then
  now="$(ssh_ "readlink -f $BASE/current")"
  existing="$(ssh_ "ls -1t $BASE/releases")"
  # A deploy makes $sha the newest release, then keeps the 3 newest.
  prune="$( { grep -vx "$sha" <<<"$existing" || true; } | tail -n +3)"
  rollback="$(basename "$now")"
  echo "checkout: $ROOT"
  echo "branch:   $branch"
  echo "commit:   $commit${DEPLOY_SHA:+ (equals DEPLOY_SHA)}"
  echo "release:  $rel"
  echo "beta now: $staged"
  echo "prod now: $now"
  echo "prune:    $(paste -sd ' ' - <<<"${prune:-nothing}") (a deploy keeps the 3 newest, $sha first)"
  echo "nothing uploaded, built or switched (--check)"
  ready=1
  if [[ "$rollback" == "$sha" ]]; then
    echo "rollback: production already runs $sha"
  elif grep -qx "$rollback" <<<"$prune"; then
    echo "NOT READY: the rollback release $rollback would be pruned" >&2; ready=0
  else
    echo "rollback: releases/$rollback (kept)"
  fi
  [[ "$staged" == "$sha" ]] || { echo "NOT READY: beta runs $staged, not $sha. Deploy to staging and check it first." >&2; ready=0; }
  (( ready )) || exit 1
  echo "preconditions met (this check approves nothing; deploying needs the owner's go-ahead)"
  exit 0
fi
[[ "$staged" == "$sha" ]] || refuse "beta runs $staged, the commit is $sha. Deploy to staging and check it first."

if [[ "${1:-}" == "--setup" ]]; then
  echo "== one-time setup"
  scp -q deploy/acp-prod-api.service deploy/acp-prod-web.service deploy/acp-prod-billing.service deploy/acp-prod-billing.timer "$HOST:/etc/systemd/system/"
  ssh_ 'bash -s' <<'REMOTE'
set -euo pipefail
ENVDIR=/etc/alphacouncil-platform/prod
STAGING=/etc/alphacouncil-platform/api.env
install -d -m 755 /opt/alphacouncil-platform/prod/releases
install -d -m 750 -o root -g alphacouncil "$ENVDIR"

if [[ ! -f "$ENVDIR/api.env" ]]; then
  # Market data paths and the Copilot settings are the same as staging's (copied on the
  # server, never printed); accounts get their own database, origins and cookies.
  umask 027
  grep -E '^(BRIEFS_DB|SCREENING_DB|EVIDENCE_DB|MARKET_INDICES_DB|MARKET_DB_IMMUTABLE|UNIVERSE_ROOT|TICKER_NAMES_CSV|SAUDI_EN_NAMES_CSV|COPILOT_[A-Z_]+|OPENROUTER_[A-Z_]+)=' "$STAGING" > "$ENVDIR/api.env"
  PASS="$(openssl rand -hex 24)"
  docker exec -i acp-postgres psql -q -v ON_ERROR_STOP=1 -U acp -d acp <<SQL
CREATE ROLE acp_prod LOGIN PASSWORD '${PASS}';
CREATE DATABASE acp_prod OWNER acp_prod;
REVOKE ALL ON DATABASE acp_prod FROM PUBLIC;
SQL
  echo "DATABASE_URL=postgresql+psycopg://acp_prod:${PASS}@127.0.0.1:5433/acp_prod" >> "$ENVDIR/api.env"
  unset PASS
  # localhost:3301 is the SSH tunnel used to check production before and after the switch.
  echo "ALLOWED_ORIGINS=https://alphacouncil.tech,http://localhost:3301" >> "$ENVDIR/api.env"
  echo "COOKIE_SECURE=true" >> "$ENVDIR/api.env"
  chown root:alphacouncil "$ENVDIR/api.env" && chmod 640 "$ENVDIR/api.env"
  echo "api.env created"
else
  echo "api.env already exists: left as it is"
fi
if [[ ! -f "$ENVDIR/web.env" ]]; then
  printf 'NODE_ENV=production\nAPI_ORIGIN=http://127.0.0.1:8300\nNEXT_TELEMETRY_DISABLED=1\n' > "$ENVDIR/web.env"
  chown root:alphacouncil "$ENVDIR/web.env" && chmod 640 "$ENVDIR/web.env"
fi
grep -oE '^[A-Z_]+=' "$ENVDIR/api.env" | tr '\n' ' '; echo
systemctl daemon-reload && systemctl enable acp-prod-api acp-prod-web && systemctl enable --now acp-prod-billing.timer
REMOTE
fi

echo "== upload $sha ($commit)"
git archive --format=tar "$commit" | ssh_ "rm -rf $rel && mkdir -p $rel && tar -x -C $rel"

echo "== build"
ssh_ "bash -s" <<EOF
set -euo pipefail
set -a; . $ENVDIR/web.env; set +a
cd $rel/api
python3 -m venv .venv
.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt
cd $rel/web
npm ci --include=dev --no-audit --no-fund --loglevel=error
NODE_ENV=production npx next build
install -d -o alphacouncil -g alphacouncil .next/cache
EOF

echo "== switch and restart"
ssh_ "ln -sfn $rel $BASE/current.new && mv -T $BASE/current.new $BASE/current && systemctl restart acp-prod-api acp-prod-web"
ssh_ 'for u in http://127.0.0.1:8300/v1/health http://localhost:3300/home; do for i in $(seq 1 30); do curl -fsS -o /dev/null "$u" && break; sleep 1; done; done'
ssh_ "systemctl is-active acp-prod-api acp-prod-web; curl -fsS -o /dev/null -w 'api %{http_code}\n' http://127.0.0.1:8300/v1/health; curl -fsS -o /dev/null -w 'web %{http_code}\n' http://localhost:3300/home"

echo "== prune: keep the 3 newest releases"
ssh_ "cd $BASE/releases && ls -1t | tail -n +4 | xargs -r rm -rf"
echo "deployed $sha to production (alphacouncil.tech serves it once nginx points at port 3300)"
