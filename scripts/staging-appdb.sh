#!/usr/bin/env bash
# One-time (idempotent): app database for beta.alphacouncil.tech (docs/staging.md).
#
# - Starts Postgres 17 in Docker, bound to 127.0.0.1:5433 only, data under
#   /opt/alphacouncil-platform/data/postgres.
# - Its password is generated on the server and written straight into
#   /etc/alphacouncil-platform/api.env (root:alphacouncil 0640); it is never printed.
# - Adds any missing api.env lines (DATABASE_URL, ALLOWED_ORIGINS, COOKIE_SECURE,
#   MARKET_INDICES_DB) and restarts acp-api.
set -euo pipefail
HOST="${STAGING_HOST:-root@alphacouncil.tech}"

ssh -o BatchMode=yes "$HOST" 'bash -s' <<'REMOTE'
set -euo pipefail
ENV=/etc/alphacouncil-platform/api.env
DATA=/opt/alphacouncil-platform/data/postgres
install -d -m 700 "$DATA"

if ! docker inspect acp-postgres >/dev/null 2>&1; then
  PASS="$(openssl rand -hex 24)"
  docker run -d --name acp-postgres --restart unless-stopped \
    -e POSTGRES_USER=acp -e POSTGRES_DB=acp -e POSTGRES_PASSWORD="$PASS" \
    -p 127.0.0.1:5433:5432 -v "$DATA":/var/lib/postgresql/data \
    postgres:17-alpine >/dev/null
  grep -q '^DATABASE_URL=' "$ENV" && sed -i '/^DATABASE_URL=/d' "$ENV"
  echo "DATABASE_URL=postgresql+psycopg://acp:${PASS}@127.0.0.1:5433/acp" >> "$ENV"
  unset PASS
  echo "postgres container created"
else
  echo "postgres container already exists"
fi

add() { grep -q "^$1=" "$ENV" || echo "$1=$2" >> "$ENV"; }
add ALLOWED_ORIGINS "https://beta.alphacouncil.tech,http://localhost:3201"
add COOKIE_SECURE "true"
add MARKET_INDICES_DB "/var/lib/alphacouncil/market_indices.sqlite"
chown root:alphacouncil "$ENV" && chmod 640 "$ENV"

for i in $(seq 1 30); do
  docker exec acp-postgres pg_isready -U acp -d acp >/dev/null 2>&1 && break
  sleep 1
done
docker exec acp-postgres pg_isready -U acp -d acp
grep -c '' "$ENV" | sed 's/^/api.env lines: /'
grep -oE '^[A-Z_]+=' "$ENV" | tr '\n' ' '; echo
REMOTE
