# Staging: beta.alphacouncil.tech

The rebuilt app runs beside the live site on the production VPS (srv1556505, Ubuntu 24.04), as its own nginx site and services. The live site (`alphacouncil`), its backend (`alphacouncil-backend`, port 8001), the old staging (`alphacouncil-staging`, ports 8101/8089) and the pipeline are not modified.

## What gets added

| Piece | Where | Notes |
| --- | --- | --- |
| DNS | Cloudflare: `beta` A record → 72.60.91.24, DNS only (grey cloud) | Added by the owner in the Cloudflare dashboard |
| Code | `/opt/alphacouncil-platform/releases/<commit>`, `current` symlink | Uploaded with `git archive` from branch `rebuild`; no GitHub remote needed |
| API | `acp-api.service`, uvicorn on 127.0.0.1:8200 | Python 3.12 venv; runs as `alphacouncil` with `/var/lib/alphacouncil` and the price files mounted read-only by systemd |
| Web | `acp-web.service`, `next start` on 127.0.0.1:3200 | Node 20.20 (Next 16 needs ≥ 20.9); built on the server |
| App data (Phase 4–5) | Docker: `acp-postgres` (127.0.0.1:5433), `acp-redis` (127.0.0.1:6380) | Volumes under `/opt/alphacouncil-platform/data`; not reachable from outside |
| nginx | `/etc/nginx/sites-available/alphacouncil-beta` + symlink | `server_name beta.alphacouncil.tech`; basic auth; `X-Robots-Tag: noindex`; proxies to :3200 |
| TLS | `certbot --nginx -d beta.alphacouncil.tech` | Touches only the beta site file |
| Password | `/etc/nginx/.htpasswd-staging` | The existing old-staging logins, reused by the owner's choice; never written by Claude |

Market data is read live from the pipeline's files: `/var/lib/alphacouncil/{briefs_index,screening,evidence}.sqlite` and `/opt/alphacouncil/backend/argaam/default_universe/*/price_history_10y.csv`. The databases are WAL files that `publish_dbs.sh` replaces atomically, so the API opens them per request with `mode=ro&immutable=1`: it never creates `-wal`/`-shm` files next to the live data, and systemd mounts that directory read-only for the service.

## Order of operations

1. Owner adds the DNS record.
2. Claude (`scripts/deploy-staging.sh --setup`): create `/opt/alphacouncil-platform`, upload the release, build web and API, install the two systemd units (not yet exposed).
3. Claude: write the nginx site with basic auth, `nginx -t`, then `systemctl reload nginx` (a reload, so the live site keeps serving; a failed `nginx -t` stops here).
4. Claude: `certbot --nginx -d beta.alphacouncil.tech` once the DNS record resolves, then add `add_header Strict-Transport-Security "max-age=31536000" always;` to the TLS server block certbot writes (`nginx -t`, reload). The app sends its other security headers itself (`web/next.config.ts`).
5. Phase 4–5: start the Postgres and Redis containers.

## Deploying a new version

```bash
scripts/deploy-staging.sh
```

Uploads the current `rebuild` commit as a new release, builds it, switches `current`, restarts `acp-api` and `acp-web`.

## Rollback / removal

```bash
rm /etc/nginx/sites-enabled/alphacouncil-beta && nginx -t && systemctl reload nginx
systemctl disable --now acp-web acp-api
docker rm -f acp-postgres acp-redis
rm -rf /opt/alphacouncil-platform /etc/systemd/system/acp-*.service
```
