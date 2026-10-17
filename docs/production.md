# Production: alphacouncil.tech

The rebuilt app serves alphacouncil.tech (switched 2026-10-17; release `e11327b`; checks after the switch in
`screenshots/production/check-live-after-switch.txt`). beta.alphacouncil.tech stays the password-protected
staging copy: every release goes there first, and production only takes what beta runs.

| | Staging (beta.alphacouncil.tech) | Production (alphacouncil.tech) |
|---|---|---|
| Code | `/opt/alphacouncil-platform/current` | `/opt/alphacouncil-platform/prod/current` |
| Settings | `/etc/alphacouncil-platform/{api,web}.env` | `/etc/alphacouncil-platform/prod/{api,web}.env` |
| Services | `acp-api` (:8200), `acp-web` ([::1]:3200) | `acp-prod-api` (:8300), `acp-prod-web` ([::1]:3300) |
| Accounts database | `acp` in the `acp-postgres` container (:5433) | `acp_prod` in the same container, its own role |
| Market data | the pipeline's files, read-only | the same files, read-only |
| nginx | `sites-available/alphacouncil-beta` (password) | `sites-available/alphacouncil-platform` |

The old site stays installed for rollback: its pages in `/opt/alphacouncil/static-v2`, its backend
`alphacouncil-backend` (:8001). `api.alphacouncil.tech` keeps pointing at the old backend.

## Releasing

```bash
scripts/deploy-staging.sh        # 1. beta gets HEAD
# 2. check beta (web/scripts/check-all.mjs through the tunnel)
scripts/deploy-production.sh     # 3. production gets the same commit (refuses anything else)
```

First time only: `scripts/deploy-production.sh --setup` creates the settings (market data and
Copilot lines copied from staging on the server, never printed), the `acp_prod` database with a
generated password, and the two services.

Check production privately before or after a release through a tunnel:

```bash
ssh -fN -L 3301:[::1]:3300 root@alphacouncil.tech
```

then open http://localhost:3301 (the API accepts that origin for sign-in).

## Switching alphacouncil.tech to the new app (done 2026-10-17)

```bash
# on the server
cp /etc/nginx/sites-enabled/alphacouncil /etc/nginx/alphacouncil.old-site.bak    # rollback copy
sed -i 's/server_name alphacouncil.tech www.alphacouncil.tech api.alphacouncil.tech;/server_name api.alphacouncil.tech;/' /etc/nginx/sites-enabled/alphacouncil
cp deploy/nginx-production.conf /etc/nginx/sites-available/alphacouncil-platform   # from the repo
ln -s /etc/nginx/sites-available/alphacouncil-platform /etc/nginx/sites-enabled/alphacouncil-platform
nginx -t && systemctl reload nginx
```

## Rollback (old site back on alphacouncil.tech)

```bash
rm /etc/nginx/sites-enabled/alphacouncil-platform
cp /etc/nginx/alphacouncil.old-site.bak /etc/nginx/sites-enabled/alphacouncil
nginx -t && systemctl reload nginx
```

Nothing else changes in a rollback: the old backend and pages were never stopped or edited.

## Forgot password

`/forgot-password` emails a link to `/reset-password#token=…` (the token stays in the fragment, so
no server or proxy log sees it). The API stores only the token's SHA-256; a link works once, for an
hour, and a reset ends every session of the account. Email goes over SMTP with the variables in
`deploy/api.env.example` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`), set in each
`api.env`; links point at the first `ALLOWED_ORIGINS` entry unless `SITE_URL` is set. Without
`SMTP_HOST` the pages still answer the same and the API logs `email is not configured`
(`journalctl -u acp-prod-api`). Check the flow with `web/scripts/check-reset.mjs`.

## Not in production yet

- Checkout (Moyasar) and Pro billing: until it opens, every account gets the Pro features
  (the pricing page says so).
- Email verification and social sign-in (the old site had them).
- `www.alphacouncil.tech` has no DNS record; when one is added, add `www` to the certificate.
