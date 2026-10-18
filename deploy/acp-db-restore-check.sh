#!/usr/bin/env bash
# Prove a backup restores (docs/production.md, "Backups"): restore the newest dump of a database
# into a throwaway database in the same container, compare every table's row count with the live
# database, then drop the throwaway database. Prints table names and counts only, never rows.
# Installed as /usr/local/sbin/acp-db-restore-check by scripts/install-backups.sh.
#
#   acp-db-restore-check            # newest acp_prod dump
#   acp-db-restore-check acp        # newest beta dump
#   acp-db-restore-check acp_prod /var/backups/alphacouncil-platform/weekly/acp_prod-2026-W42.dump
#
# Rows written to the live database after the dump was taken show up as differences; run it right
# after a backup (systemctl start acp-db-backup) for an exact comparison.
set -euo pipefail
export LC_ALL=C

DIR="${ACP_BACKUP_DIR:-/var/backups/alphacouncil-platform}"
CONTAINER=acp-postgres
db="${1:-acp_prod}"
dump="${2:-$(ls -1t "$DIR"/daily/"$db"-*.dump 2>/dev/null | head -1)}"
[[ -n "$dump" && -f "$dump" ]] || { echo "no dump of $db in $DIR/daily" >&2; exit 1; }
tmp="acp_restorecheck_$(date -u +%Y%m%d%H%M%S)"

# -i only where a query comes on stdin: otherwise docker would read this script's own stdin.
psql_() { docker exec "$CONTAINER" psql -q -X -v ON_ERROR_STOP=1 -U acp "$@"; }
drop() { psql_ -d acp -c "DROP DATABASE IF EXISTS $tmp WITH (FORCE)" && echo "dropped $tmp"; }
trap drop EXIT

echo "restoring $dump ($(stat -c %s "$dump") bytes, $(date -u -r "$dump" +%FT%TZ)) into $tmp"
psql_ -d acp -c "CREATE DATABASE $tmp" -c "REVOKE ALL ON DATABASE $tmp FROM PUBLIC"
docker exec -i "$CONTAINER" pg_restore -U acp -d "$tmp" --exit-on-error < "$dump"

# Exact row count of every user table, as "schema.table count" lines.
counts() {
  docker exec -i "$CONTAINER" psql -q -X -v ON_ERROR_STOP=1 -U acp -d "$1" -At -F' ' <<'SQL'
SELECT format('SELECT %L, count(*) FROM %I.%I;', schemaname || '.' || tablename, schemaname, tablename)
FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY 1 \gexec
SQL
}
live="$(counts "$db")"
restored="$(counts "$tmp")"

printf '%-40s %10s %10s\n' table live restored
join -a1 -a2 -e missing -o 0,1.2,2.2 <(sort <<<"$live") <(sort <<<"$restored") |
  awk '{ printf "%-40s %10s %10s%s\n", $1, $2, $3, ($2 == $3 ? "" : "   DIFFERENT"); if ($2 != $3) bad++ }
       END { print (bad ? bad " table(s) differ" : NR " tables, every row count matches"); exit (bad > 0) }'
