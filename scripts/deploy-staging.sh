#!/usr/bin/env bash
# Deploy a committed revision of this repo to beta.alphacouncil.tech (docs/staging.md).
#
#   scripts/deploy-staging.sh            # deploy HEAD (must be on branch `rebuild`)
#   scripts/deploy-staging.sh --setup    # first time: also install units, env files and the nginx site
#   scripts/deploy-staging.sh --check    # read-only: say what would be deployed and from where, then stop
#
# Another reviewed branch (such as a fix-only release branch) is deployed only when named explicitly, together
# with the full commit that was approved, from a checkout of that branch:
#   DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=<full 40-character commit> scripts/deploy-staging.sh --check
# then the same without --check. It refuses unless HEAD is exactly DEPLOY_SHA. DEPLOY_SHA may also pin a
# `rebuild` deploy. The commit checked here is the one archived and built; HEAD is not read again.
#
# Never touches the live site, its backend, the old staging or the pipeline.
set -euo pipefail

HOST="${STAGING_HOST:-root@alphacouncil.tech}"
BASE=/opt/alphacouncil-platform
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

refuse() { echo "refusing: $*" >&2; exit 1; }
expected="${DEPLOY_BRANCH:-rebuild}"
branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "$expected" ]] || refuse "on branch '$branch', expected '$expected' (DEPLOY_BRANCH names another reviewed branch)"
[[ "$expected" == rebuild || -n "${DEPLOY_SHA:-}" ]] || refuse "DEPLOY_BRANCH=$expected needs DEPLOY_SHA, the full commit approved for it"
commit="$(git rev-parse --verify "HEAD^{commit}")"
if [[ -n "${DEPLOY_SHA:-}" ]]; then
  [[ "$DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]] || refuse "DEPLOY_SHA must be a full 40-character commit, got '$DEPLOY_SHA'"
  [[ "$commit" == "$DEPLOY_SHA" ]] || refuse "HEAD of '$branch' is $commit, not the approved DEPLOY_SHA $DEPLOY_SHA"
fi
sha="${commit:0:10}"
rel="$BASE/releases/$sha"
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

if [[ "${1:-}" == "--check" ]]; then
  now="$(ssh_ "readlink -f $BASE/current")"
  existing="$(ssh_ "ls -1t $BASE/releases")"
  # A deploy makes $sha the newest release, then keeps the 3 newest.
  prune="$( { grep -vx "$sha" <<<"$existing" || true; } | tail -n +3)"
  rollback="$(basename "$now")"
  echo "checkout: $ROOT"
  echo "branch:   $branch"
  echo "commit:   $commit${DEPLOY_SHA:+ (equals DEPLOY_SHA)}"
  echo "archive:  $(git archive --format=tar "$commit" | tar -t | wc -l) paths from $commit (committed files only)"
  echo "release:  $rel"
  echo "beta now: $now"
  echo "releases: $(tr '\n' ' ' <<<"$existing")"
  echo "prune:    $(tr '\n' ' ' <<<"${prune:-nothing}")(a deploy keeps the 3 newest, $sha first)"
  echo "nothing uploaded, built or switched (--check)"
  if [[ "$rollback" == "$sha" ]]; then
    echo "rollback: beta already runs $sha"
  elif grep -qx "$rollback" <<<"$prune"; then
    echo "NOT READY: the rollback release $rollback would be pruned" >&2; exit 1
  else
    echo "rollback: releases/$rollback (kept)"
  fi
  echo "ready"
  exit 0
fi

if [[ "${1:-}" == "--setup" ]]; then
  echo "== one-time setup"
  ssh_ "install -d -m 755 $BASE/releases $BASE/data /etc/alphacouncil-platform"
  # Env files: paths only, no secrets. Kept if they already exist.
  scp -q deploy/api.env.example "$HOST:/tmp/acp-api.env"
  ssh_ "test -f /etc/alphacouncil-platform/api.env || install -m 640 -o root -g alphacouncil /tmp/acp-api.env /etc/alphacouncil-platform/api.env; rm -f /tmp/acp-api.env"
  ssh_ "test -f /etc/alphacouncil-platform/web.env || printf 'NODE_ENV=production\nAPI_ORIGIN=http://127.0.0.1:8200\nNEXT_TELEMETRY_DISABLED=1\n' | install -m 640 -o root -g alphacouncil /dev/stdin /etc/alphacouncil-platform/web.env"
  scp -q deploy/acp-api.service deploy/acp-web.service deploy/acp-billing.service deploy/acp-billing.timer "$HOST:/etc/systemd/system/"
  ssh_ "systemctl daemon-reload && systemctl enable acp-api acp-web && systemctl enable --now acp-billing.timer"
  # The site file is the template only until certbot adds TLS to it; never overwrite that.
  if ssh_ "grep -q 'managed by Certbot' /etc/nginx/sites-available/alphacouncil-beta 2>/dev/null"; then
    echo "nginx site has TLS (certbot): left as it is"
  else
    scp -q deploy/nginx-beta.conf "$HOST:/etc/nginx/sites-available/alphacouncil-beta"
    ssh_ "ln -sfn /etc/nginx/sites-available/alphacouncil-beta /etc/nginx/sites-enabled/alphacouncil-beta && nginx -t && systemctl reload nginx"
  fi
fi

echo "== upload $sha ($commit)"
git archive --format=tar "$commit" | ssh_ "rm -rf $rel && mkdir -p $rel && tar -x -C $rel"

echo "== build"
ssh_ "bash -s" <<EOF
set -euo pipefail
set -a; . /etc/alphacouncil-platform/web.env; set +a
cd $rel/api
python3 -m venv .venv
.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt
cd $rel/web
npm ci --include=dev --no-audit --no-fund --loglevel=error
NODE_ENV=production npx next build
install -d -o alphacouncil -g alphacouncil .next/cache
EOF

echo "== switch and restart"
ssh_ "ln -sfn $rel $BASE/current.new && mv -T $BASE/current.new $BASE/current && systemctl restart acp-api acp-web"
# Both services take a few seconds to start: wait up to 30 s for each before reporting.
ssh_ 'for u in http://127.0.0.1:8200/v1/health http://localhost:3200/home; do for i in $(seq 1 30); do curl -fsS -o /dev/null "$u" && break; sleep 1; done; done'
ssh_ "systemctl is-active acp-api acp-web; curl -fsS -o /dev/null -w 'api %{http_code}\n' http://127.0.0.1:8200/v1/health; curl -fsS -o /dev/null -w 'web %{http_code}\n' http://localhost:3200/home"

echo "== prune: keep the 3 newest releases"
ssh_ "cd $BASE/releases && ls -1t | tail -n +4 | xargs -r rm -rf"
echo "deployed $sha"
