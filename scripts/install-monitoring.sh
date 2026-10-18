#!/usr/bin/env bash
# Install or update the production monitor on alphacouncil.tech (docs/production.md, "Monitoring").
#
#   scripts/install-monitoring.sh owner@example.org          # first time: who receives the alerts
#   scripts/install-monitoring.sh                            # update the script and units, same recipient
#   scripts/install-monitoring.sh [owner@example.org] --test # and send one test alert
#   scripts/install-monitoring.sh --ping                     # asks for the outside check's ping URL
#
# Creates the system user acp-monitor (no login, no home) if missing, puts scripts/prod-monitor.py
# in /usr/local/lib/acp-monitor (outside the releases, so a deploy never changes or breaks it),
# the units in /etc/systemd/system, the recipient (ALERT_TO) and the ping URL (PING_URL) in
# /etc/alphacouncil-platform/prod/monitor.env; then runs one round and prints what it sees.
set -euo pipefail

HOST="${PROD_HOST:-root@alphacouncil.tech}"
ENVDIR=/etc/alphacouncil-platform/prod
LIB=/usr/local/lib/acp-monitor
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

to="" test=false ping=false
for arg in "$@"; do
  case "$arg" in
    --test) test=true ;;
    --ping) ping=true ;;
    *@*.*) to="$arg" ;;
    *) sed -n '3,7p' "$0" >&2; exit 2 ;;
  esac
done

ping_url=""
if $ping; then
  # Read here, not taken as an argument: the URL is the check's key, so it stays out of shell history.
  read -rsp "Ping URL of the Healthchecks.io check (https://hc-ping.com/...; empty: keep the current one): " ping_url
  echo
  if [[ -n "$ping_url" && ! "$ping_url" =~ ^https://[^[:space:]/]+/[^[:space:]]+$ ]]; then
    echo "refusing: not an https:// URL" >&2; exit 2
  fi
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "rebuild" ]] || { echo "refusing: on branch '$branch', expected 'rebuild'" >&2; exit 1; }
files=(scripts/prod-monitor.py deploy/acp-prod-monitor.service deploy/acp-prod-monitor.timer)
git diff --quiet HEAD -- "${files[@]}" || { echo "refusing: commit the monitor files first" >&2; exit 1; }
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }
# Sets one KEY=value line of monitor.env and keeps the others. The line goes over stdin, so it is
# in no command line on the server.
set_env_line() {
  ssh_ "set -e; umask 077; f=$ENVDIR/monitor.env; IFS= read -r line; key=\${line%%=*}
        { grep -v \"^\$key=\" \$f 2>/dev/null || true; printf '%s\n' \"\$line\"; } > \$f.new
        chown root:alphacouncil \$f.new; chmod 640 \$f.new; mv \$f.new \$f"
}

echo "== install $(git rev-parse --short=10 HEAD)"
ssh_ "id -u acp-monitor >/dev/null 2>&1 || useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin acp-monitor"
ssh_ "install -d -m 755 $LIB && install -m 644 /dev/stdin $LIB/prod-monitor.py" < scripts/prod-monitor.py
scp -q deploy/acp-prod-monitor.service deploy/acp-prod-monitor.timer "$HOST:/etc/systemd/system/"
if [[ -n "$to" ]]; then
  printf 'ALERT_TO=%s\n' "$to" | set_env_line
  echo "recipient set"
fi
ssh_ "grep -q '^ALERT_TO=.' $ENVDIR/monitor.env" || { echo "no recipient yet: run again with the owner's address" >&2; exit 1; }
if [[ -n "$ping_url" ]]; then
  printf 'PING_URL=%s\n' "$ping_url" | set_env_line
  echo "ping URL set"
fi

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
