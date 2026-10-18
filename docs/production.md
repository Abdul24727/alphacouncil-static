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

## Backups

Every night at 01:30 UTC, `acp-db-backup.timer` runs `/usr/local/sbin/acp-db-backup`
(`deploy/acp-db-backup.sh`). It writes a `pg_dump -Fc` of `acp_prod` and of `acp` from the
`acp-postgres` container, plus the roles with their password hashes (`pg_dumpall --globals-only`).
A dump only counts once `pg_restore --list` can read it.

- **Where**: `/var/backups/alphacouncil-platform/` on the server, outside the Postgres data directory.
  `daily/` keeps the newest 14 dumps per database (and 14 `globals-*.sql`). `weekly/` keeps the first
  dump of each ISO week as a hard link, the newest 8 per database. Directories are 0700 and files
  0600, root only.
- **Contents**: personal data and Moyasar's saved-card token ids. Never print a dump, and copy one only
  to the off-server destination.
- **Off the server**: an encrypted copy goes to the owner's S3-compatible bucket (see "Off-server copy"
  below).
- **Install or update**: run `scripts/install-backups.sh`. It copies the three scripts and the units,
  installs rclone if it is missing, and starts the timer. Add `--run` to take a backup right away. It
  does not depend on releases.
- **Status**: installed 2026-10-18 with the owner's approval. The timer is enabled, and its first run
  through systemd (09:15 UTC) succeeded. The restore check passed that day for `acp_prod` and `acp`
  (`screenshots/backup-restore-check-production.txt`).

Check the last run:

```bash
systemctl list-timers acp-db-backup.timer          # last and next run
systemctl status acp-db-backup.service             # result of the last run
journalctl -u acp-db-backup.service -n 20 -o cat   # its output: sizes and file names only
cat /var/backups/alphacouncil-platform/LAST_OK     # time and files of the last complete run
cat /var/backups/alphacouncil-platform/LAST_OFFSITE_OK   # time of the last complete upload to the bucket
```

Check that a backup restores: `acp-db-restore-check` (newest `acp_prod` dump), `acp-db-restore-check acp`
(beta), or `acp-db-restore-check acp_prod <file>`. It restores the dump into a throwaway database
`acp_restorecheck_<time>` in the same container, compares every table's row count with the live
database, and drops the throwaway. It prints counts only. Run it right after
`systemctl start acp-db-backup` for an exact match. Before the install, run the repo copy instead:
`ssh root@alphacouncil.tech 'bash -s' < deploy/acp-db-restore-check.sh`.

Restore production from a dump (the damaged database is kept under another name):

```bash
systemctl stop acp-prod-billing.timer acp-prod-billing.service acp-prod-api
f=$(ls -1t /var/backups/alphacouncil-platform/daily/acp_prod-*.dump | head -1)   # or an older or weekly one
docker exec acp-postgres psql -U acp -d acp -c "ALTER DATABASE acp_prod RENAME TO acp_prod_damaged_$(date -u +%Y%m%d%H%M)"
docker exec acp-postgres psql -U acp -d acp -c "CREATE DATABASE acp_prod OWNER acp_prod" -c "REVOKE ALL ON DATABASE acp_prod FROM PUBLIC"
docker exec -i acp-postgres pg_restore -U acp -d acp_prod --exit-on-error < "$f"
systemctl start acp-prod-api acp-prod-billing.timer
```

Anything written after the dump is gone. Look in Moyasar's dashboard for payments made after the
dump's time, and restore those members' Pro by hand (`app.billing grant`, see Pro billing). If the
container or its data directory is lost, follow these steps:

1. Recreate the container with the `docker run` line of `scripts/staging-appdb.sh`. Give it the `acp`
   password from beta's `api.env` (`DATABASE_URL`), not a new one.
2. Load the roles: `docker exec -i acp-postgres psql -U acp -d postgres < daily/globals-<time>.sql`.
   "role acp already exists" is expected. Both roles keep their passwords, so both `api.env` files
   still work.
3. Create each database with its owner, as above, and `pg_restore` into it.

### Off-server copy (S3-compatible bucket)

Once `/etc/alphacouncil-platform/backup-offsite.env` exists, `acp-db-backup` runs
`/usr/local/sbin/acp-db-offsite` (`deploy/acp-db-offsite.sh`) after each backup. It encrypts every new
dump with gpg (AES-256, the owner's passphrase) and uploads it with rclone to
`<bucket>/alphacouncil-platform/{daily,weekly}/<file>.gpg`. The bucket keeps daily copies for 15 days and
weekly copies for 60 days, counted from upload, so an emptied local directory does not empty the
bucket. If the upload fails, the backup run fails, and the monitoring emails about it.

The owner creates the bucket and writes the file. Claude never writes or reads it.

```bash
install -m 600 -o root -g root /dev/null /etc/alphacouncil-platform/backup-offsite.env
nano /etc/alphacouncil-platform/backup-offsite.env
```

```bash
# The provider's S3 endpoint, e.g. https://<account id>.r2.cloudflarestorage.com,
# https://s3.eu-central-003.backblazeb2.com, https://s3.me-central-1.amazonaws.com
S3_ENDPOINT=
# The bucket's region as the provider names it (Cloudflare R2: auto)
S3_REGION=
S3_BUCKET=
# A key limited to this one bucket, allowed to list, read, write and delete
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
# Long and random (e.g. openssl rand -base64 33); also kept in the owner's password manager
BACKUP_PASSPHRASE=
```

Keep each value right after `=` with comments on their own lines. The script refuses a file that is not
root-owned 0600 or that lacks a value. **Without the passphrase the bucket copies cannot be decrypted**,
and a disk failure would take the server's copy of it too, so it must also be kept off the server.

Check it: `acp-db-offsite --check` fetches the newest `acp_prod` copy back from the bucket, decrypts it
and compares it byte for byte with the local dump. `acp-db-offsite` alone uploads whatever is missing.

Restore from the bucket when the server is gone: download a `.gpg` file (from the provider's web console,
or with rclone), run `gpg --decrypt -o acp_prod.dump acp_prod-<time>.dump.gpg` (it asks for the
passphrase; on Windows use Gpg4win), then restore as above.

Status (2026-10-18): installed, and waiting for the owner's bucket and settings file. It was tested on the
server against a local directory standing in for the bucket: 13 files were encrypted and uploaded, a
second run sent nothing, the round trip matched byte for byte, and a group-readable file or a missing
value was refused.

## Monitoring

Every 5 minutes `acp-prod-monitor.timer` runs `/usr/local/lib/acp-monitor/prod-monitor.py check`
(`scripts/prod-monitor.py`, Python standard library only, outside the releases so a broken deploy
cannot break it). It runs as the system user `acp-monitor` (no login, no home; the installer creates
it) in the groups `alphacouncil` (to read the SMTP lines of `prod/api.env` and `prod/monitor.env`) and
`systemd-journal` (to read the services' logs), and keeps its state in `/var/lib/acp-monitor/state.json`.
Not `DynamicUser=`: dbus-daemon drops dynamic users, and `systemctl show` needs the bus.

| Check | A problem when | Emailed |
|---|---|---|
| `https://alphacouncil.tech/home` | not HTTP 200 within 20 s (TLS verified) | after 2 rounds in a row |
| `https://alphacouncil.tech/api/v1/health` | not 200 with `status: "ok"` | after 2 rounds |
| market data | the health answer's `market_data` is not `ok` | after 2 rounds |
| `acp-prod-api`, `acp-prod-web` | not active, or 3+ automatic restarts in 15 minutes | after 2 rounds |
| Pro renewals job (`acp-prod-billing.service`) | the last run did not exit 0 (timeout, crash) | after 2 rounds |
| Pro renewals timer | `acp-prod-billing.timer` not active | after 2 rounds |
| Moyasar for renewals | a run's output has `unreachable=` above 0 | at the first such run |
| renewal declined, plan ended | a run's output has `failed=` or `ended=` above 0 | at that run (an event, not a state) |
| database backup (`acp-db-backup`) | the last run did not exit 0, or its timer stopped; skipped until installed | after 2 rounds |
| every disk (ext4, xfs, …) | more than 85% used; fixed again at 83% | after 2 rounds |
| certificate alphacouncil.tech serves | invalid, or expires within 14 days | after 2 rounds |

- **Only changes are emailed**: a problem once when it starts and once when it clears ("Recovered"),
  nothing in between. Everything that changed in a round goes in one email; problems with a service
  or a job include its last 15 log lines with every secret of `api.env` replaced by `[redacted]`.
- **Mail budget**: at most 8 alerts in 24 hours and 60 in 30 days, because MailerSend's free plan
  (about 500 a month) is shared with the old backend and the app's own emails. Over a limit, or when
  the mail server refuses, nothing is lost: the round leaves its state as it was and the next round
  tries again (`systemctl --failed` shows the monitor while SMTP fails).
- **Mail settings**: `SMTP_*` from `/etc/alphacouncil-platform/prod/api.env`, the same as the API's;
  read by the script and never printed or logged. The recipient is `ALERT_TO` in
  `/etc/alphacouncil-platform/prod/monitor.env` (root:alphacouncil 0640; several addresses:
  comma-separated). To change it, run the installer with the new address.
- **What it cannot see**: it runs on the server it watches, so if the whole server, its network or
  MailerSend is down, it cannot email. The outside check (below) covers that: Healthchecks.io emails
  when the rounds stop pinging, or when a round had an alert it could not send. Still not covered: the
  site unreachable from elsewhere while the server and its outgoing connections work (a provider
  firewall, DNS seen from other networks), because the monitor's own fetch of `/home` starts on the
  server. An outside HTTP check would add that; UptimeRobot's free plan is for non-commercial use only,
  so there is none.

Install or update (copies the script and units, enables the timer, runs one round, prints the checks):

```bash
scripts/install-monitoring.sh owner@address --test   # first time: recipient, and one test alert
scripts/install-monitoring.sh                        # later updates: same recipient
scripts/install-monitoring.sh --ping                 # asks for the outside check's ping URL (below)
```

A new address or ping URL replaces only its own line in `monitor.env`.

On the server:

```bash
python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status   # every check now; sends nothing
systemctl list-timers acp-prod-monitor.timer                    # last and next round
journalctl -u acp-prod-monitor -n 20 -o cat                     # one line per round, plus alerts sent
python3 -I /usr/local/lib/acp-monitor/prod-monitor.py test     # one test alert to ALERT_TO
```

To pause it: `systemctl disable --now acp-prod-monitor.timer`.

**Status (2026-10-18)**: installed on alphacouncil.tech (`b14fc67`). The alerts go to the address the owner
chose (kept in `monitor.env`, not in git). The test alert went out at 09:19 UTC and arrived in the owner's
inbox. From 09:25 the timer's rounds pass all 13 checks as `acp-monitor`. The first install used
`DynamicUser=`, so the `systemctl` checks could not run, and one false alert went out at 09:20
("Problem: acp-prod-api check (+3 more)"). "Recovered" followed at 09:22, after the switch to `acp-monitor`.

### Outside check (Healthchecks.io)

A free [Healthchecks.io](https://healthchecks.io) check watches the monitor from outside (a dead-man's
switch). When `PING_URL` is in `prod/monitor.env`, every round ends with a ping:

| The round | Ping | Healthchecks.io emails |
|---|---|---|
| ran, and emailed everything it found (or found nothing new) | `PING_URL` | nothing, or "up" after a "down" |
| had an alert it could not email (MailerSend refused, or the 8-a-day or 60-a-month limit) | `PING_URL/fail`, with the round's summary and the unsent subject | "down" at once |
| did not run or did not finish: server off, network down, timer stopped, settings unreadable, crash | none | "down" 15 minutes after the last ping (period 5 + grace 10) |

- Healthchecks.io emails only when the check's state changes (down, then up), from its own servers, so
  these emails do not count against the MailerSend budget. The free plan (20 checks, email alerts) is
  enough.
- The URL is the check's key: it is kept in `monitor.env` (root:alphacouncil 0640), not in git, and
  is never printed or logged. A ping that fails only logs `outside check not pinged: …` in the round's
  journal; the next round pings again 5 minutes later, inside the grace time.

Setting it up (the owner, once; Claude does not create accounts or handle the URL):

1. Sign up at healthchecks.io (free). Add a check named `alphacouncil.tech monitor`, schedule "Simple",
   period 5 minutes, grace time 10 minutes. Its email integration goes to the account's address;
   choose an address that is not hosted on this server.
2. Copy the check's ping URL (`https://hc-ping.com/…`).
3. In the repository, on `rebuild`: `scripts/install-monitoring.sh --ping`, then paste the URL at the
   prompt (hidden, and not in the shell history). This also installs the current script. It runs one
   round, so the check turns "up" on Healthchecks.io within a minute, and `status` ends with
   `outside check: PING_URL is set…`.

Test (once, after setting it up): stop the rounds until the "down" email arrives, then start them again:

```bash
ssh root@alphacouncil.tech systemctl stop acp-prod-monitor.timer                            # "down" email about 15 minutes after the last ping
ssh root@alphacouncil.tech systemctl start acp-prod-monitor.timer acp-prod-monitor.service  # pings at once: "up" email
```

Nothing is monitored while the timer is stopped, so start it again as soon as the email arrives. To
retire the outside check, pause it on Healthchecks.io first (otherwise it emails "down"), then delete
the `PING_URL` line from `monitor.env`.

**Status (2026-10-18)**: live on alphacouncil.tech (`064d670`). The owner created the Healthchecks.io check
(period 5 minutes, grace 10) and ran `scripts/install-monitoring.sh --ping`. In the test above, the stopped
timer brought Healthchecks.io's "down" email, and starting it again brought the "up" email (as the owner
reported; the emails went to the owner's alert address, not checked from here). Before that it was tested
locally against a fake ping server: a plain ping, `/fail` when the mail fails or a limit is reached, no ping
after a crash, and the URL never in the output.

## Search engines and link previews

- `/robots.txt` (`web/src/app/robots.ts`): the site is open; account pages (`/portfolio`, `/settings`,
  `/dashboards`, `/checkout`, `/billing/`, `/verify-email`, `/reset-password`, and their `/ar` twins) and
  `/api/` are disallowed. Same file on every host; beta stays out of search engines by its password and
  nginx's `X-Robots-Tag: noindex, nofollow`.
- `/sitemap.xml` (`web/src/app/sitemap.ts`), built per request: the public pages in English and Arabic,
  each with en/ar/x-default alternates, then every stock page `/t/<slug>` from `/v1/tickers`. A stock's
  `lastmod` is the last bar of its daily price file (`prices_as_of`), a legal page's its "updated" date;
  other pages have none. If the API cannot answer, the site pages are still listed.
- Every page's `<head>` comes from `web/src/lib/seo.ts`: title and description in the page's language,
  canonical and hreflang on `https://alphacouncil.tech` whatever host served it, Open Graph and Twitter
  cards with `public/og/{en,ar}.png`. Stock pages: "Saudi Aramco (2222) · Tadawul" from the API; every
  tab and every other address of a stock has the canonical `/t/<slug>`; an unknown ticker and the account
  pages are `noindex`. No price or other figure goes into metadata.
- Stock-page metadata depends on the ticker, so ordinary visitors get it streamed; crawlers on Next's
  list plus Googlebot (`htmlLimitedBots` in `next.config.ts`) get it in `<head>`.
- The preview cards are drawn by `node scripts/capture-og.mjs` (web dev server running) from
  `messages/*.json`; re-run it after changing the hero title or the exchange names.
- Check: `BASE_URL=… SHOTS_DIR=… node scripts/check-seo.mjs` (robots, sitemap against the API's ticker
  list, a sample of heads in both languages, the cards, screenshots at 1440 and 390 px).
- Google Search Console (owner's Google account): Domain property `alphacouncil.tech`, verified
  2026-10-18 by the "domain name provider" method (a `google-site-verification` TXT record at
  Cloudflare; never remove it). `https://alphacouncil.tech/sitemap.xml` submitted the same day; Googlebot
  fetched it at 18:16 UTC (200, `crawl-66-249-66-164.googlebot.com` in nginx's access log). Search Console
  first showed "Couldn't fetch" (what it shows until it processes a new sitemap), then the same day: type
  Sitemap, status Success, 1,464 discovered pages.
- Bing Webmaster Tools (owner's account): the site imported from Search Console on 2026-10-18 (verified
  through it, no record of its own); the import brought no sitemap, so it was submitted by hand: Success,
  about 1.5K URLs, no errors or warnings, the same day.

**Status (2026-10-18)**: live since release `cde2b0e629` (owner's approval). `check-seo.mjs` passes 62/62 on
beta (through the tunnel) and on https://alphacouncil.tech; robots.txt and sitemap.xml (1,464 URLs: 16 pages
and 716 stock pages, each in both languages) answer 200; beta still answers 401 with `X-Robots-Tag: noindex,
nofollow`. The full phase checks passed on beta at `e72fe62` (`screenshots/seo-check-all-beta.txt`); the
one app change after it (next-intl's Link header off) was rechecked on beta with `check-seo.mjs` and Phase 6,
and Phase 6 passed on production after the release. Results and screenshots (1440/390 px): `screenshots/seo-check-*.txt`,
`screenshots/seo-{beta,production}/`.

## Advisors' room (Pro)

The stock page's Advisors tab (`/t/<slug>/advisors`; the Council tab links to it): a Pro member asks a
question about the stock, four simulated advisors debate it and a neutral Chair returns a scored assessment
of the data. Code: `api/app/debate/`, `api/app/routers/debate.py`, `web/src/components/debate/`.

- **Seats**: one markdown file each in `api/app/advisors/` (Buffett, Lynch, Dalio, Marks and the Chair);
  the README there says how to swap an advisor (`DEBATE_ADVISORS`). The Chair's file holds the stage
  instructions and the scoring scale. Portraits: initials on a graphite disc until the owner's caricatures
  go into `web/public/advisors/` (README there) and are named in the seat files.
- **Stages**: Brief (Chair) → Openings (advisors at once) → Fault lines (Chair) → Debate (`DEBATE_ROUNDS`,
  advisors at once) → Vote (advisors score each option 0–10) → Verdict (Chair). The averages are computed by
  the API, never by a model. Every seat reads the same data pack: the Copilot's database tools for the
  stock (overview, fundamentals, dividends, council, peers, news, 1- and 5-year price summaries), tagged
  P1–P8. Each line is checked with the Copilot's number checks: untagged figures get their dataset's tag,
  figures found nowhere in the data are marked on screen, and sentences that read as advice (buy, sell,
  hold, targets) are removed; option labels and the verdict headline with advice words are sent back.
- **Models** (settings in each `api.env`, see `deploy/api.env.example`): advisors `DEBATE_ADVISOR_MODEL`,
  Chair `DEBATE_CHAIR_MODEL`, through OpenRouter with the Copilot's key and host order. Without
  `OPENROUTER_API_KEY` the room runs a labelled stand-in.
- **Allowance**: 20 sessions per calendar month (UTC) on Pro (`plans.LIMITS`), shown under the question
  box; a failed session does not count. One session at a time per account. Free and signed-out visitors
  see the room locked.
- **Sessions** are saved per account (`debate_sessions`, `debate_turns`; removed with the account) and run
  to the end even if the browser leaves; "Past sessions" reopens them. A session still marked running
  after 15 minutes (an API restart) is marked failed.
- **Time and cost**: each session's seconds, tokens and OpenRouter's own cost are stored, and one line
  per session goes to the service log (`journalctl -u acp-prod-api | grep debate`). Summary of the last
  30 days: `sudo -E -u alphacouncil .venv/bin/python -m app.debate stats` in the release's `api/` with the
  environment of its `api.env`.
- **Check**: `BASE_URL=http://localhost:3201 node scripts/check-advisors.mjs` (beta through the tunnel)
  convenes a session in English and in Arabic and writes screenshots of every stage at 1440 and 390 px to
  `docs/screenshots/advisors/`; `LOCKED=1` against an API with billing open checks the Free preview.
- **Legal**: the screen carries the disclaimer (simulated advisors built from public work, drawn as
  caricatures, not the people) in both languages. The owner is getting a lawyer's view on using living
  people's names before the feature is advertised.

**Status (2026-10-18)**: live on alphacouncil.tech since release `3f403b2ef7` (owner's approval: beta, then
production; not advertised until the lawyer's view). On beta, six real sessions on 2222 (three in English,
three in Arabic) took 33–53 s and cost $0.165–0.198 each (OpenRouter's figures; 137–155k tokens in,
4–6k out): the Chair (Claude Sonnet 5.5, 3 calls) $0.087–0.107, the advisors (DeepSeek V4 Pro, 12 calls)
$0.071–0.091. Arabic runs about 15–35% longer and dearer. A member using all 20 sessions costs about $4 a
month. `check-advisors.mjs` passed on beta at `3f403b2` (`screenshots/advisors/`, every stage live at 1440 px
and replayed at 1440 and 390 px, both languages) and in visitor mode on production
(`screenshots/advisors-production/`); the Free preview was checked locally with billing open
(`screenshots/advisors-free-local/`). Claude Sonnet 5.5 refuses requests with reasoning switched off, so the
Chair runs at low reasoning effort. The number check flags figures the advisors work out themselves (an
annualised dividend, a payout percentage): they show underlined as not found in the data.

## Not in production yet

- `www.alphacouncil.tech` has no DNS record; when one is added, add `www` to the certificate.
