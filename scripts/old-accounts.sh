#!/usr/bin/env bash
# The one-time import of the old site's accounts, and its checks (docs/account-import.md).
#
#   scripts/old-accounts.sh beta|production import             # dry run: counts only
#   scripts/old-accounts.sh beta|production import --apply
#   scripts/old-accounts.sh beta|production import --apply --test-addresses /tmp/made-up.sqlite
#   scripts/old-accounts.sh beta|production mint <name@example.com>    # a reset token for a check
#   scripts/old-accounts.sh beta|production forget <prefix>            # removes made-up accounts
#
# Runs in that site's current release with its own api.env, as the user both backends run as
# (alphacouncil), through systemd-run: the same environment as the service, and anything SQLite
# opens beside the old file stays the old backend's. The old file is opened read-only.
set -euo pipefail

HOST="${STAGING_HOST:-root@alphacouncil.tech}"
OLD_DB=/var/lib/alphacouncil/briefs_index.sqlite
case "${1:-}" in
  beta) code=/opt/alphacouncil-platform/current; env=/etc/alphacouncil-platform/api.env ;;
  production) code=/opt/alphacouncil-platform/prod/current; env=/etc/alphacouncil-platform/prod/api.env ;;
  *) sed -n '2,8p' "$0" >&2; exit 2 ;;
esac
what="${2:-}"
shift 2 || true

case "$what" in
  import)
    # A path given last replaces the old backend's file (a made-up one for the check).
    args=("$@")
    if [[ ${#args[@]} -gt 0 && "${args[-1]}" == /* ]]; then old="${args[-1]}"; unset 'args[-1]'; else old="$OLD_DB"; fi
    cmd=(app.import_old "$old" "${args[@]}") ;;
  mint|forget) cmd=(app.check_accounts "$what" "$@") ;;
  *) sed -n '2,8p' "$0" >&2; exit 2 ;;
esac

ssh -o BatchMode=yes "$HOST" \
  "systemd-run --quiet --pipe --wait --collect -p User=alphacouncil -p EnvironmentFile=$env" \
  "-p WorkingDirectory=$code/api $code/api/.venv/bin/python -m $(printf '%q ' "${cmd[@]}")"
