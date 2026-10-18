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

Live since release `2ed8823d96` (checks in `screenshots/password-reset-check-{beta,production}.txt`).
Both `api.env` files carry the old backend's MailerSend SMTP lines, copied on the server with the
owner's approval (the files before that are kept as `api.env.bak-<time>`); the old backend's own
`.env` was not changed. MailerSend's free plan is shared with the old backend, which still runs.

## Old-site accounts

The old site's members were imported once (email, name, language, sign-up date and any registration
acceptance; no password): see `docs/account-import.md`. They set a password through "Forgot password?",
and accept the terms on that page if the old site had no acceptance on record for them.

## Email confirmation

Sign-up emails a link to `/verify-email#token=…` (same scheme as the reset link; 48 hours, once).
A reset link or Google also confirms the address. Until then the app shows a banner, and buying Pro
needs it (receipts and renewal reminders go there). Automated emails to reserved test addresses
(`example.com`, `.test`, …) are skipped, so the checks do not spend the mail plan's allowance.

## Sign in with Google

`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` in each `api.env` (the old site's Google web client, copied
on the server with the owner's approval). Google sends people back to
`https://alphacouncil.tech/auth/google/callback`, the address registered for that client; nginx passes
it to the API (`deploy/nginx-production.conf`). beta's address is not registered with Google, so the
sign-in only completes on alphacouncil.tech. A new account (or an imported one without an acceptance)
ticks the terms on `/signup` first.

## Pro billing (Moyasar)

Monthly, renewing until cancelled (`api/app/billing.py`):

- The first payment is taken by Moyasar's form on `/checkout` (card details go to Moyasar only; the
  card is saved there as a token). `/billing/return` asks the API to confirm, and the API acts only on
  Moyasar's own record of the payment.
- Renewals: `acp-prod-billing.timer` (beta: `acp-billing.timer`) runs `python -m app.billing renew`
  hourly: reminders 3 days before, the charge at the period end, a failed charge retried daily three
  times with Pro kept, then the plan ends and the saved card is deleted.
- Moyasar's webhook: the two live webhooks in the dashboard point at
  `https://api.alphacouncil.tech/api/billing/webhook/moyasar` (seen 2026-10-18). That one path on the
  api host goes to the new API (`sites-enabled/alphacouncil`, the old site's server block, backup
  `/etc/nginx/alphacouncil.api-host.bak-*`); the rest of `api.alphacouncil.tech` stays the old backend.
  `https://alphacouncil.tech/api/billing/webhook/moyasar` reaches the same handler. Both check
  `MOYASAR_WEBHOOK_SECRET`. It confirms payments for payers who closed the browser, and a refund made in
  Moyasar's dashboard ends Pro. Each event arrives twice (two webhooks); each payment is applied once.
- Tested on beta with the account's Moyasar **test** keys (2026-10-18, `screenshots/accounts-billing/`):
  declined card refused, paid card starts Pro with the card saved, and a renewal charged the saved
  card through Moyasar and moved Pro a month on.
- Settings: `BILLING_OPEN` (off = early access, everyone has Pro), `MOYASAR_PUBLISHABLE_KEY`,
  `MOYASAR_SECRET_KEY`, `MOYASAR_WEBHOOK_SECRET`. Production has the old site's live keys (copied on the
  server with the owner's approval); beta needs Moyasar **test** keys, and `web/scripts/check-billing.mjs`
  pays there with Moyasar's published test cards.
- **Opening billing ends early access**: Free locks the council, financials, ownership, calendar,
  indicators and pins, and limits holdings (20), alerts (5) and Copilot questions (10 a day). The
  phase checks read Pro data, so run them with billing closed (beta) or with a Pro account.
- Complimentary Pro (owner, partners, test accounts), no card, ends by itself:
  `sudo -E -u alphacouncil .venv/bin/python -m app.billing grant <email> <days>` in the release's `api/`
  with the environment of its `api.env`.

### Billing is open (since 2026-10-18)

`BILLING_OPEN=true` in `/etc/alphacouncil-platform/prod/api.env` (the file before that is
`api.env.bak-20261018082735`). Checked live over HTTPS (`screenshots/billing-live/`): /pricing shows
"Get Pro" and no early-access note; the council, financials, ownership and calendar panels are locked
for signed-out and Free visitors (EN 1440, AR 390); a new account is Free and is asked to confirm its
email before paying; the live card form (no test-mode banner, orange "Pay 79.00") loads in both
languages. No live payment was made by these checks.

To close billing again (everyone back to Pro, checkout closed): delete the `BILLING_OPEN` line, then
`systemctl restart acp-prod-api`.

## Not in production yet

- `www.alphacouncil.tech` has no DNS record; when one is added, add `www` to the certificate.
