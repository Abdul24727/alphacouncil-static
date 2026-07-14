# AlphaCouncil — Launch Checklist
**As of:** 2026-07-14 · **Site:** alphacouncil.tech · **Prepared after Phase 2 fixes**

This is your run-book: what's still blocking launch, what to verify by hand, how to go live, and how to roll back. Commands assume SSH access as root (`ssh alphacouncil-vps` or the Hostinger browser terminal).

---

## 1. Launch status at a glance

**14 findings fixed & verified this session** (5 of 6 P0s + the no-input P1s). **Do not launch until the 5 gates in §2 are cleared** — most are quick, but two (Turnstile secret, legal) are hard blockers.

Fixed: P0-1 AI outage · P0-2 exposed backend · P0-3 uncapped Council endpoint · P0-4 fabricated as_of_date · P0-6 fabricated advice · P1-1 freshness banner · P1-2 checkout legal links · P1-3 watchlist (non-issue) · P1-7 error leak · P1-8/SEO (404, robots, sitemap, meta) · SEC-04 CORS · INT-03/04 portfolio validation · Q3 BUY badge.

---

## 2. PRE-LAUNCH GATES — must clear before go-live

| # | Gate | Owner | Action |
|---|---|---|---|
| G1 | **SEC-08 Turnstile secret** — signup is broken until fixed | You | On the VPS, set `.env`'s `TURNSTILE_SECRET_KEY` to the secret paired with signup widget `0x4AAAAAADoxyhgLIaK5NH5B`, then `systemctl restart alphacouncil-backend`. **Verify with a real signup (§3.1).** |
| G2 | **P0-5 legal binding + entity** | You + counsel | Remove the "not yet binding" line in `legal.html`; insert **Insight Lane Establishment**, CR number and address into Terms/Privacy/footer. Have counsel confirm the analysis-not-advice wording given the open CMA question. |
| G3 | **P1-4 contact details** | You | Replace the placeholder phone/email on `contact.html` with real support details. |
| G4 | **Observability** (P1-5/P1-6) | You | Add a Sentry DSN (backend `.env` `SENTRY_DSN=…`, then `pip install sentry-sdk` in the venv) and put an **off-box** uptime monitor on `https://alphacouncil.tech/healthz` + `/healthz/deep`. |
| G5 | **Payments provider** (PAY-02) | You | Payments are in **sandbox** (`BILLING_LIVE=false`, test keys). Either (a) finish choosing/wiring a provider and do the live-key swap, or (b) **launch with paid plans disabled** and enable later. Decide before launch so pricing/checkout don't offer a purchase that can't complete. |

**Recommended (not hard blockers):** Q4 palette decision (still on the old dark-violet theme, not warm-ivory); Q7 Argaam demo-news headlines on `features.html`; per-page meta on non-landing marketing pages.

---

## 3. Manual verification (run these yourself right before launch)

### 3.1 Real signup — the critical path (do AFTER G1)
1. Open `https://alphacouncil.tech/signup.html` in a private window, use a **fresh real email**.
2. Complete the Turnstile challenge, submit. **Expect:** account created, verification email arrives.
3. Verify the email link works and you land signed-in.
4. If signup fails with a CAPTCHA error → G1 secret is still wrong; recheck.

### 3.2 One test-mode payment (only if G5 = wiring a provider)
- With **test keys**, buy a plan using the provider's test card. Confirm: access granted only after the confirmation page, billing page shows the plan, and a **cancel** path works. Never use a real card.

### 3.3 Spot-check 6 tickers across markets
Load each `stock-detail.html?ticker=<key>` and confirm real, dated data + correct bilingual name + a signal badge that reads Positive/Neutral/Cautious (never BUY/SELL):
- `1120_TADAWUL` (Saudi) · `2222_TADAWUL` (Saudi) · `ADPORTS_ADX` (Abu Dhabi) · `SALAMA_DFM` (Dubai) · `QGRI_QSE` (Qatar) · `235_KSE` (Kuwait)
- Also open the **screener** (`markets-app.html`): a few rows should show "—" for day change (stale-priced names) rather than a fabricated number. That's the P0-4 fix working.

### 3.4 Mobile check on a real phone
- Signup, pricing, markets/screener, a ticker page, and the "My holdings only" toggle at phone width. Confirm no horizontal overflow and Arabic (AR toggle) reads right-to-left cleanly.

### 3.5 Quick honesty pass
- Dashboard/alerts with a brand-new account should show honest empty states ("No alerts yet", "—"), never invented holdings or percentages.

---

## 4. Go-live sequence
1. Clear all §2 gates; run all §3 checks on the live site.
2. Confirm services green: `ssh alphacouncil-vps 'systemctl is-active alphacouncil-backend nginx; ufw status | head -1'` → `active / active / active`.
3. Confirm the AI is funded: OpenRouter balance > a safe buffer (each Council review ≈ 9 model calls). Set a low-balance alert.
4. Announce. Watch logs for the first hour: `ssh alphacouncil-vps 'journalctl -u alphacouncil-backend -f'`.

---

## 5. Rollback procedures (exact commands)

**All Phase-2 changes have per-file backups** in `/opt/alphacouncil/backups/*.20260714-*.bak`, and code is committed to GitHub branch `vps-production-sync-20260714` on both repos.

**Roll back a single static page** (e.g. a bad checkout):
```bash
ssh alphacouncil-vps
cp /opt/alphacouncil/backups/checkout.html.20260714-batch2.bak /opt/alphacouncil/static-v2/checkout.html
# (static files are served directly — no restart needed)
```

**Roll back a backend code change** (e.g. revert the as_of_date change):
```bash
cp /opt/alphacouncil/backups/frontend_api.py.20260714-asofdate.bak \
   /opt/alphacouncil/backend/llm-council/backend/frontend_api.py
systemctl restart alphacouncil-backend
```

**Roll back the nginx 404 change:**
```bash
cp /opt/alphacouncil/backups/nginx.alphacouncil.20260714-404.bak /etc/nginx/sites-enabled/alphacouncil
nginx -t && systemctl reload nginx
```

**Full backend revert to pre-Phase-2 state** (nuclear — reverts every backend fix):
```bash
cd /opt/alphacouncil/backend/llm-council && cd "$(git rev-parse --show-toplevel)"
git checkout 4f81e90 -- llm-council/backend/    # pre-Phase-2 backend snapshot
systemctl restart alphacouncil-backend
```

**Restart / health:**
```bash
systemctl restart alphacouncil-backend    # backend
systemctl reload nginx                     # nginx config
curl -s -o /dev/null -w '%{http_code}\n' https://alphacouncil.tech/healthz   # expect 200
```

**⚠️ Do NOT roll back these two** (they are the security fixes): the uvicorn `--host 127.0.0.1` bind and the `ufw` firewall. Reverting them re-exposes the backend to the public internet (P0-2).

---

## 6. Data / DB safety
- User DB: `/opt/alphacouncil/backend/llm-council/portfolio_inputs/briefs_index.sqlite`.
- Automated backup runs daily 23:45 (cron → `/opt/alphacouncil/bin/backup_user_db.sh`); ~14 kept. A pre-cleanup snapshot from today: `/opt/alphacouncil/backups/briefs_index.sqlite.20260714-pre-market-cleanup.bak`.
- **Gap (recommend fixing):** backups are **on-box only**. Add an off-box copy before launch so a VPS loss doesn't lose user data.
- Restore a DB: stop the service, `cp <backup> …/briefs_index.sqlite`, restart. Never edit the live DB by hand while the service is running.

---

## 7. Known post-launch backlog (safe to launch with, fix soon)
P2: Turnstile only on signup (add to login/forgot/reset/contact); JWT not invalidated on password change/logout; email verification optional; CSP has no script-src; Tap webhook signature (dormant); duplicate payment-audit-row race; per-row data-age badge on the screener (backend already exposes `price_stale`/`as_of_date` — frontend badge is a nice-to-have); gzip_types disabled; old-violet palette. P3: sha256_crypt vs bcrypt; contact-form global rate limit; misc i18n key gaps. Full list in `AUDIT_REPORT.md`.
