#!/usr/bin/env bash
# Install (or update) the nightly database backup on the server (docs/production.md, "Backups"):
# /usr/local/sbin/acp-db-backup and acp-db-restore-check, acp-db-backup.{service,timer}.
#
#   scripts/install-backups.sh          # install the files and start the timer
#   scripts/install-backups.sh --run    # also take a backup now and show its summary
#
# Independent of releases: it can run from any commit of branch `rebuild`.
set -euo pipefail

HOST="${PROD_HOST:-root@alphacouncil.tech}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

scp -q deploy/acp-db-backup.sh "$HOST:/usr/local/sbin/acp-db-backup.new"
scp -q deploy/acp-db-restore-check.sh "$HOST:/usr/local/sbin/acp-db-restore-check.new"
scp -q deploy/acp-db-backup.service deploy/acp-db-backup.timer "$HOST:/etc/systemd/system/"
ssh_ 'bash -s' <<'REMOTE'
set -euo pipefail
for f in acp-db-backup acp-db-restore-check; do
  chmod 700 /usr/local/sbin/$f.new && mv /usr/local/sbin/$f.new /usr/local/sbin/$f
done
install -d -m 700 /var/backups/alphacouncil-platform
systemctl daemon-reload
systemctl enable --now acp-db-backup.timer
systemctl list-timers acp-db-backup.timer --no-pager | head -2
REMOTE

if [[ "${1:-}" == "--run" ]]; then
  ssh_ 'systemctl start acp-db-backup.service && journalctl -u acp-db-backup.service -n 6 --no-pager -o cat'
fi
