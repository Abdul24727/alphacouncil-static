#!/usr/bin/env bash
# Deploy the committed HEAD of this repo to beta.alphacouncil.tech (docs/staging.md).
#
#   scripts/deploy-staging.sh            # deploy HEAD (must be on branch `rebuild`)
#   scripts/deploy-staging.sh --setup    # first time: also install units, env files and the nginx site
#
# Never touches the live site, its backend, the old staging or the pipeline.
set -euo pipefail

HOST="${STAGING_HOST:-root@alphacouncil.tech}"
BASE=/opt/alphacouncil-platform
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "rebuild" ]] || { echo "refusing: on branch '$branch', expected 'rebuild'" >&2; exit 1; }
sha="$(git rev-parse --short=10 HEAD)"
rel="$BASE/releases/$sha"
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

if [[ "${1:-}" == "--setup" ]]; then
  echo "== one-time setup"
  ssh_ "install -d -m 755 $BASE/releases $BASE/data /etc/alphacouncil-platform"
  # Env files: paths only, no secrets. Kept if they already exist.
  scp -q deploy/api.env.example "$HOST:/tmp/acp-api.env"
  ssh_ "test -f /etc/alphacouncil-platform/api.env || install -m 640 -o root -g alphacouncil /tmp/acp-api.env /etc/alphacouncil-platform/api.env; rm -f /tmp/acp-api.env"
  ssh_ "test -f /etc/alphacouncil-platform/web.env || printf 'NODE_ENV=production\nAPI_ORIGIN=http://127.0.0.1:8200\nNEXT_TELEMETRY_DISABLED=1\n' | install -m 640 -o root -g alphacouncil /dev/stdin /etc/alphacouncil-platform/web.env"
  scp -q deploy/acp-api.service deploy/acp-web.service "$HOST:/etc/systemd/system/"
  ssh_ "systemctl daemon-reload && systemctl enable acp-api acp-web"
  scp -q deploy/nginx-beta.conf "$HOST:/etc/nginx/sites-available/alphacouncil-beta"
  ssh_ "ln -sfn /etc/nginx/sites-available/alphacouncil-beta /etc/nginx/sites-enabled/alphacouncil-beta && nginx -t && systemctl reload nginx"
fi

echo "== upload $sha"
git archive --format=tar HEAD | ssh_ "rm -rf $rel && mkdir -p $rel && tar -x -C $rel"

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
sleep 4
ssh_ "systemctl is-active acp-api acp-web; curl -fsS -o /dev/null -w 'api %{http_code}\n' http://127.0.0.1:8200/v1/health; curl -fsS -o /dev/null -w 'web %{http_code}\n' http://127.0.0.1:3200/home"

echo "== prune: keep the 3 newest releases"
ssh_ "cd $BASE/releases && ls -1t | tail -n +4 | xargs -r rm -rf"
echo "deployed $sha"
