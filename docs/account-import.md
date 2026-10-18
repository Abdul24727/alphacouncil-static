# Old-site accounts

alphacouncil.tech switched to this app on 2026-10-17 with an empty accounts database, so the old
site's members could not sign in. Their accounts were imported once, with the owner's approval
(2026-10-18), by `api/app/import_old.py`.

## What comes over

From the old backend's `users` table (`BRIEFS_DB`, `/var/lib/alphacouncil/briefs_index.sqlite`, opened
read-only):

| Here | From the old site |
|---|---|
| `email` | `email`, trimmed and lowercased (the old site stored it as typed) |
| `display_name` | `first_name` + `last_name`, none when both are empty |
| `locale` | `preferred_language`: `ar`, anything else `en` |
| `created_at` | `created_at` (a time without a zone is UTC) |
| `consents` | the member's latest `registration_acceptances` row: its date, text version, terms and privacy versions |

Nothing else: no password, plan, risk profile, picture, billing or old id (accounts get new random
ids, as at sign-up).

Left out, and counted: accounts with `is_active = 0`, a pending deletion, a reserved test address
(`example.com/.net/.org`, `.test`, `.example`, `.invalid`, `.localhost`), an invalid address, an
unreadable date, two old accounts that lowercase to one email (the owner decides), and any email
already here (never overwritten). The command prints counts only, never an address or a name.

## Passwords and the acceptance

The old hashes (passlib bcrypt of the bare password, older ones sha256_crypt) cannot verify under
`auth.verify_password`, so an imported account gets `import_old.UNUSABLE_PASSWORD`, which no password
matches. Members set one through "Forgot password?"; the sign-in page says so (`auth.oldSite`).

Sign-up requires the registration acceptance. A member whose old account has none on record
accepts it on the "Choose a new password" page: `POST /v1/auth/reset-password/check` says
`needs_terms`, the page shows the sign-up checkbox, and `/v1/auth/reset-password` saves only with
`accept_terms` (409 without, and the link still works). The acceptance is recorded then, with
today's versions. A member who brought an acceptance is not asked again. Nothing is ever invented.

## Running it

```bash
scripts/old-accounts.sh beta import              # dry run: counts only
scripts/old-accounts.sh beta import --apply
```

`production` in place of `beta` for alphacouncil.tech. It runs in that site's current release with its
`api.env`, as `alphacouncil` (the user both backends run as) through `systemd-run`. A second run imports
nothing new.

Check first with made-up accounts, through the same code (no email is sent: the token is minted on
the server, for `@example.com` accounts only):

```bash
python -I scripts/made-up-old-accounts.py imported-check-$(date +%s) /tmp/made-up.sqlite
scp /tmp/made-up.sqlite root@alphacouncil.tech:/tmp/acp-made-up.sqlite
ssh root@alphacouncil.tech chown alphacouncil: /tmp/acp-made-up.sqlite
scripts/old-accounts.sh beta import --apply --test-addresses /tmp/acp-made-up.sqlite
cd web && BASE_URL=http://localhost:3201 STAGING_AUTH=… IMPORTED=imported-check-… \
  RESET_MINT="bash ../scripts/old-accounts.sh beta mint" node scripts/check-imported.mjs account-import-beta
scripts/old-accounts.sh beta forget imported-check-     # remove the made-up accounts
```

## Done

| | Beta (`acp`) | Production (`acp_prod`) |
|---|---|---|
| Release | | |
| Made-up check | | |
| Old accounts imported | | |
