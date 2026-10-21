# Checkout in Moyasar test mode on beta, 2026-10-22

PROJECT.md Step 16 (QA audit row 10b). Owner's go-ahead in chat on 2026-10-22: "run the checkout tests in
Moyasar test mode on beta (Step 16)".

## Setup

- **Beta:** release `d356a3c` (the billing code is unchanged on `rebuild` since). Before: `BILLING_OPEN` absent;
  Moyasar keys by prefix only: 1 `sk_test_`, 1 `pk_test_`, no `sk_live_`/`pk_live_`; no `MOYASAR_WEBHOOK_SECRET`.
- **For the test:** `/etc/alphacouncil-platform/api.env` backed up as `api.env.bak-20261021231949` (UTC), then
  `BILLING_OPEN=true` and a random `MOYASAR_WEBHOOK_SECRET` (made on the server, never printed) added,
  `systemctl restart acp-api`. **After:** the backup restored (both lines gone), `acp-api` restarted; see "Closed again".
- **Tool:** `web/scripts/check-checkout.mjs` through the tunnel `localhost:3201`. It stops unless the checkout hands
  out a `pk_test_` key. Cards: Moyasar's published test cards only (`4111 1111 1111 1111` paid,
  `4123 1200 0109 0000` declined), expiry 12/30, CVC 123. Accounts: `checkout-<case>-<time>@example.com`,
  address confirmed in beta's database (test addresses get no email).
- **Two things the test does for Moyasar, because beta's password gate stands between them and Moyasar:**
  1. Moyasar sends the payer back to beta's public address (`https://beta.alphacouncil.tech/billing/return?...`),
     which asks for the gate's password; the test browser follows the same address through the tunnel instead.
  2. Moyasar's own webhooks cannot reach beta (the gate answers 401). The test delivers each notification to
     beta's API from the server with the body Moyasar sends (`type`, `secret_token`, `data.id`); the handler then
     fetches the payment from Moyasar's test API, so what it applies is Moyasar's record. Production's live
     webhooks were seen arriving on 2026-10-18 (runbook, "Pro billing (Moyasar)").
- **Refund:** made through Moyasar's test API with beta's test secret key (the script refuses a key that is not
  `sk_test_`), as the owner would in the test dashboard.

## Results: 13 of 13 PASS

One run, 2026-10-21 23:47–23:48 UTC (02:47 Riyadh, 22 Oct). Evidence: `docs/screenshots/checkout-test-2026-10-22/`
(`results.json` and the screenshots named below). Payment ids are Moyasar's test-mode ids.

| # | case | steps | expected | result | evidence |
|---|---|---|---|---|---|
| 0 | test mode only | `/v1/plans`; start a checkout | checkout open, key `pk_test_` | PASS | `results.json` |
| 1 | declined card | EN 1440: card 4123…0000, 3-D Secure (Y) | refused, no Pro | PASS — "The payment was not completed: INSUFFICIENT FUNDS", plan Free | `A1-declined-en-1440-*.png`, payment `749a96a5…` |
| 2 | 3-D Secure fails | card 4111…1111, emulator (N) | not paid, no Pro | PASS — "3DS: Card authentication declined.", plan Free | `A2-3ds-refused-en-1440-*.png`, `3d11ba18…` |
| 3 | success | card 4111…1111, emulator (Y) | paid; `/billing/return` confirms with Moyasar; Pro; card saved | PASS — "Welcome to Pro… paid through 21 Nov 2026 and renews monthly", Visa 1111, renews | `A3-paid-en-1440-*.png`, `A5-settings-pro-en-1440.png`, `fbd5ca98…` |
| 4 | return page trusts Moyasar, not the address | open `/billing/return?id=<declined payment>&status=paid&message=APPROVED` | no Pro | PASS — "Payment not completed" | `A4-forged-return-en-1440.png` |
| 5 | renewal | paid month set to end now (beta database), `systemctl start acp-billing.service` (`python -m app.billing renew`) | saved card charged, Pro a month on | PASS — `renewed=1`; payments `first:paid, renewal:paid`; Pro through 2026-11-21 | `61a84840…` |
| 6 | cancel | Settings › Billing › Cancel renewal | Pro to the end of the period, no renewal | PASS — status `canceled`, renews false, Pro through 2026-11-21 | `A6-cancelled-en-1440.png` |
| 7 | refund ends Pro | full refund of the renewal (the payment for the current month) in Moyasar test mode, then Moyasar's `payment_refunded` | Pro ends, card forgotten | PASS — Moyasar `200 refunded`; plan Free, status `expired` | `61a84840…` |
| 8 | browser closed after paying | AR 390: pay (Y); the return page never loads; then Moyasar's `payment_paid` | Pro starts from the notification | PASS — Free before, Pro through 2026-11-21 after | `B1-ar-390-form.png`, `B2-settings-pro-ar-390.png`, `cb5c3c91…` |
| 9 | duplicate notification | the same `payment_paid` again | applied once | PASS — Pro end unchanged, 1 payment row | `cb5c3c91…` |
| 10 | English, 390 px | pay (Y) | Pro; no sideways scroll | PASS — 0 px | `C-paid-en-390-*.png`, `24925966…` |
| 11 | Arabic, 1440 px | pay (Y) | Pro; no sideways scroll | PASS — 0 px | `D-paid-ar-1440-*.png`, `3aca69e1…` |
| 12 | forged notification | `payment_paid` with a wrong `secret_token` | refused | PASS — HTTP 403 | `results.json` |

English and Arabic each ran at 1440 and 390 px (A: EN 1440, B: AR 390, C: EN 390, D: AR 1440). Moyasar's form
shows its red test-mode notice in both languages.

### `web/scripts/check-billing.mjs` on beta

"Billing checks: all passed" (2026-10-21 23:50 UTC; log lines: billing open; signed out the council, financials and
Arabic ownership are locked and key metrics stay free; checkout asks a visitor to sign in and a new account to confirm
its email; Settings says Free; Moyasar's Pay button in the brand colour and font; test card 4123…0000 declined
"INSUFFICIENT FUNDS"; test card 4111…1111 paid, Pro started; Pro renews with the saved card, Visa 1111). Its
complimentary-Pro part (a Pro account: nothing locked, Settings says Pro) passed on the run before, which stopped at
the return address (fixed below). Screenshots: `checkout-test-2026-10-22/check-billing/`.

## Found and fixed during the test (test scripts only, no app change)

- Moyasar returns the browser to beta's public address, which the password gate blocks for a browser without its
  login. Both scripts now load that return page through the tunnel. Production has no gate.
- Moyasar's edge (Cloudflare, error 1010) refuses Python's default user agent; the refund call sends the app's own,
  as `app/http.py` does.
- Sign-ups and sign-ins share one limit, 10 per 15 minutes per address, and everything through the tunnel is one
  address; the first full run stopped at its 11th. The run above stayed under it.

## Closed again

`api.env` restored from `api.env.bak-20261021231949`, `systemctl restart acp-api` (active since 2026-10-21 23:50:40 UTC):
`grep -c '^BILLING_OPEN=' /etc/alphacouncil-platform/api.env` → 0, `MOYASAR_WEBHOOK_SECRET` → 0, the test keys
unchanged; `/v1/plans` → `"checkout_open":false`, and a visitor's plan is Pro again.

Left on beta: the test accounts `checkout-*@example.com` and their test-mode subscriptions (three renew on Moyasar test
cards each month; no real money). Deleting them is the owner's call.
