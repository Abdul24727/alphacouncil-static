#!/usr/bin/env bash
# Install or update the production monitor on alphacouncil.tech (docs/production.md, "Monitoring").
#
#   scripts/install-monitoring.sh owner@example.org          # first time: who receives the alerts
#   scripts/install-monitoring.sh                            # update the script and units, same recipient
#   scripts/install-monitoring.sh [owner@example.org] --test # and send one test alert
#
# Puts scripts/prod-monitor.py in /usr/local/lib/acp-monitor (outside the releases, so a deploy
# never changes or breaks it), the units in /etc/systemd/system, the recipient in
# /etc/alphacouncil-platform/prod/monitor.env; then runs one round and prints what it sees.
set -euo pipefail

HOST="${PROD_HOST:-root@alphacouncil.tech}"
ENVDIR=/etc/alphacouncil-platform/prod
LIB=/usr/local/lib/acp-monitor
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

to="" test=false
for arg in "$@"; do
  case "$arg" in
    --test) test=true ;;
    *@*.*) to="$arg" ;;
    *) sed -n '3,6p' "$0" >&2; exit 2 ;;
  esac
done

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "rebuild" ]] || { echo "refusing: on branch '$branch', expected 'rebuild'" >&2; exit 1; }
files=(scripts/prod-monitor.py deploy/acp-prod-monitor.service deploy/acp-prod-monitor.timer)
git diff --quiet HEAD -- "${files[@]}" || { echo "refusing: commit the monitor files first" >&2; exit 1; }
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

echo "== install $(git rev-parse --short=10 HEAD)"
ssh_ "install -d -m 755 $LIB && install -m 644 /dev/stdin $LIB/prod-monitor.py" < scripts/prod-monitor.py
scp -q deploy/acp-prod-monitor.service deploy/acp-prod-monitor.timer "$HOST:/etc/systemd/system/"
if [[ -n "$to" ]]; then
  # The address goes over stdin, so it is in no command line on the server.
  printf 'ALERT_TO=%s\n' "$to" | ssh_ "install -m 640 -o root -g alphacouncil /dev/stdin $ENVDIR/monitor.env"
  echo "recipient set"
fi
ssh_ "test -s $ENVDIR/monitor.env" || { echo "no recipient yet: run again with the owner's address" >&2; exit 1; }

echo "== enable and run one round"
ssh_ "systemctl daemon-reload && systemctl enable --now acp-prod-monitor.timer"
ssh_ "systemctl start acp-prod-monitor.service; echo \"result: \$(systemctl show -p Result --value acp-prod-monitor.service)\"; journalctl -u acp-prod-monitor.service -n 4 -o cat --no-pager"
ssh_ "systemctl list-timers acp-prod-monitor.timer acp-prod-billing.timer --no-pager"
echo "== what the monitor sees now"
ssh_ "/usr/bin/python3 -I $LIB/prod-monitor.py status"

if $test; then
  echo "== test alert"
  ssh_ "/usr/bin/python3 -I $LIB/prod-monitor.py test"
fi
