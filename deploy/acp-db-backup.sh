#!/usr/bin/env bash
# Nightly dump of the app databases in the acp-postgres container (docs/production.md, "Backups").
# Installed as /usr/local/sbin/acp-db-backup by scripts/install-backups.sh, run by acp-db-backup.timer.
#
#   daily/<db>-<UTC time>.dump     pg_dump custom format, the newest 14 per database
#   weekly/<db>-<ISO week>.dump    the first dump of each week (a hard link), the newest 8 per database
#   daily/globals-<UTC time>.sql   roles (password hashes) and other cluster-wide settings, same retention
#   LAST_OK                        time and files of the last run that finished without an error
#
# Dumps hold personal data: everything here is root-only (directories 0700, files 0600) and this
# script never prints their contents.
set -euo pipefail

DIR="${ACP_BACKUP_DIR:-/var/backups/alphacouncil-platform}"
CONTAINER=acp-postgres
DATABASES=(acp_prod acp)
KEEP_DAILY=14
KEEP_WEEKLY=8

umask 077
exec 9>/run/acp-db-backup.lock
flock -n 9 || { echo "another backup is running" >&2; exit 1; }

install -d -m 700 "$DIR" "$DIR/daily" "$DIR/weekly"
trap 'rm -f -- "$DIR"/daily/*.partial' EXIT
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
week="$(date -u +%G-W%V)"
pg() { docker exec "$CONTAINER" "$@"; }

# Keep the newest $2 files matching $1, delete the rest.
prune() { { ls -1t $1 2>/dev/null || true; } | tail -n +"$(($2 + 1))" | xargs -r rm -f --; }

made=()
for db in "${DATABASES[@]}"; do
  out="$DIR/daily/$db-$stamp.dump"
  pg pg_dump -U acp -Fc "$db" > "$out.partial"
  # The archive must be readable by pg_restore (its table of contents) before it counts.
  docker exec -i "$CONTAINER" pg_restore --list < "$out.partial" > /dev/null
  mv "$out.partial" "$out"
  [[ -e "$DIR/weekly/$db-$week.dump" ]] || ln "$out" "$DIR/weekly/$db-$week.dump"
  prune "$DIR/daily/$db-*.dump" "$KEEP_DAILY"
  prune "$DIR/weekly/$db-*.dump" "$KEEP_WEEKLY"
  made+=("$out")
  echo "$db: $(stat -c %s "$out") bytes -> $out"
done

pg pg_dumpall -U acp --globals-only > "$DIR/daily/globals-$stamp.sql.partial"
mv "$DIR/daily/globals-$stamp.sql.partial" "$DIR/daily/globals-$stamp.sql"
prune "$DIR/daily/globals-*.sql" "$KEEP_DAILY"
made+=("$DIR/daily/globals-$stamp.sql")

printf '%s\n' "$(date -u +%FT%TZ)" "${made[@]}" > "$DIR/LAST_OK"
echo "backup ok: ${#made[@]} files, $(du -sh "$DIR" | cut -f1) in $DIR"
