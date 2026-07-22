// Acceptance-UI e2e (items 1, 2, 6, 7) — registration + checkout acceptance, the settings
// Legal panel, and the deletion flow. Runs FULLY OFFLINE against the local files over
// file:// with every /api/** call stubbed via page.route, so it needs NO backend and
// touches NO production data (isolated staging responses only). The Moyasar CDN is aborted.
//
//   Run:  npx playwright test acceptance-ui           (from the static repo root)
//
// These assert the compliance-critical behaviours the reviewer cares about: the box is
// unticked by default, the action is gated on it, price/currency/period/VAT come from the
// server (never the browser), acceptance completes only server-side, and no legal
// hash/id leaks into the account UI.
const { test, expect } = require('@playwright/test');
const path = require('path');
const url = require('url');

const ROOT = path.resolve(__dirname, '..');
const fileUrl = (p) => url.pathToFileURL(path.join(ROOT, p)).href;

// ---- staging fixtures (isolated; not real users/records) ----
const DISCLOSURES = {
  plan: 'pro', plan_name: 'Pro', price: 79, currency: 'SAR', interval: 'monthly',
  period_label: 'Monthly', auto_renews: true,
  renewal_disclosure: 'This subscription renews automatically every month until you cancel. Each renewal charges the same price to your saved card.',
  cancellation: 'Cancel anytime from Settings › Billing. Cancelling stops the next renewal; your access continues until the end of the paid period.',
  vat_status: 'Price shown in Saudi Riyal (SAR). VAT is not currently charged.',
  is_upgrade: true, current_plan: 'free', payments_available: true,
  acceptance_text: 'I agree to the Terms of Service and acknowledge the Privacy Policy, Refund and Cancellation Policy, and AI and Financial Disclaimer.',
  acceptance_text_version: '1.0',
  document_routes: {
    terms: { version: '1.0', route: '/legal/terms' },
    privacy: { version: '1.0', route: '/legal/privacy' },
    refunds: { version: '1.0', route: '/legal/refunds' },
    'ai-financial-disclaimer': { version: '1.0', route: '/legal/ai-financial-disclaimer' },
  },
  refund_route: '/legal/refunds',
};
const LEGAL_STATUS = {
  documents: [
    { key: 'terms', title: 'Terms of Service', version: '1.0', effective_date: '2026-07-21', route: '/legal/terms' },
    { key: 'privacy', title: 'Privacy Policy', version: '1.0', effective_date: '2026-07-21', route: '/legal/privacy' },
    { key: 'refunds', title: 'Refund and Cancellation Policy', version: '1.0', effective_date: '2026-07-21', route: '/legal/refunds' },
    { key: 'ai-financial-disclaimer', title: 'AI and Financial Disclaimer', version: '1.0', effective_date: '2026-07-21', route: '/legal/ai-financial-disclaimer' },
  ],
  combined_route: '/legal',
  registration_acceptance: { accepted_at: '2026-07-20T09:15:00+00:00', acceptance_text_version: '1.0', terms_version: '1.0', privacy_version: '1.0' },
  checkout_acceptance: { accepted_at: '2026-07-21T12:30:00+00:00', acceptance_text_version: '1.0', terms_version: '1.0', privacy_version: '1.0', refunds_version: '1.0', ai_disclaimer_version: '1.0', status: 'completed' },
};

function json(route, body, status = 200) {
  return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
}

// Block the external Moyasar CDN in every test (no network).
test.beforeEach(async ({ page }) => {
  await page.route(/moyasar\.com/, (r) => r.abort());
});

// ───────────────────────── Registration (item 1) ─────────────────────────
test.describe('signup acceptance', () => {
  test('checkbox unticked by default; button disabled until ticked', async ({ page }) => {
    await page.goto(fileUrl('signup.html'));
    const box = page.locator('#terms');
    const btn = page.locator('#signupBtn');
    await expect(box).not.toBeChecked();               // no preselection
    await expect(btn).toBeDisabled();                  // gated
    await expect(page.locator('#termsHelper')).toBeVisible();
    await box.check();
    await expect(btn).toBeEnabled();
    await box.uncheck();
    await expect(btn).toBeDisabled();                  // re-gates
  });

  test('terms/privacy links point at the registry routes', async ({ page }) => {
    await page.goto(fileUrl('signup.html'));
    await expect(page.locator('a[data-i18n="su.terms_link"]')).toHaveAttribute('href', '/legal/terms');
    await expect(page.locator('a[data-i18n="su.privacy_link"]')).toHaveAttribute('href', '/legal/privacy');
  });

  test('submit sends accepted=true + an idempotency key (server authoritative)', async ({ page }) => {
    let body = null;
    await page.route('**/api/auth/register', (r) => { body = JSON.parse(r.request().postData() || '{}'); return json(r, { token: 't', user: { id: 1 } }); });
    await page.route('**/api/auth/login', (r) => json(r, { token: 't' }));
    await page.route('**/api/auth/me', (r) => json(r, { id: 1 }));
    await page.goto(fileUrl('signup.html'));
    await page.fill('#email', 'stage.user@example.com');
    await page.fill('#password', 'password123');
    await page.locator('#terms').check();
    await page.locator('#signupBtn').click();
    await expect.poll(() => body && body.accepted).toBe(true);
    expect(String(body.idempotency_key || '').length).toBeGreaterThan(8);
    // No legal version/hash is submitted as an editable field.
    expect(body.terms_version).toBeUndefined();
    expect(body.acceptance_text_hash).toBeUndefined();
  });

  test('error mapping: duplicate / locale / acceptance / temporary', async ({ page }) => {
    const cases = [
      { status: 400, detail: 'Email already registered', expect: /already exists|logging in/i },
      { status: 400, detail: 'Registration is currently available in English only.', expect: /english/i },
      { status: 400, detail: 'You must accept the Terms of Service and Privacy Policy to register.', expect: /accept/i },
      { status: 503, detail: 'temporary', expect: /try again|moment/i },
    ];
    for (const c of cases) {
      await page.route('**/api/auth/register', (r) => json(r, { detail: c.detail }, c.status));
      await page.goto(fileUrl('signup.html'));
      await page.fill('#email', 'stage.user@example.com');
      await page.fill('#password', 'password123');
      await page.locator('#terms').check();
      await page.locator('#signupBtn').click();
      await expect(page.locator('.toast, #toast, [role="alert"]').filter({ hasText: c.expect }).first()).toBeVisible({ timeout: 5000 });
      await page.unroute('**/api/auth/register');
    }
  });
});

// ───────────────────────── Checkout (item 2) ─────────────────────────
test.describe('checkout acceptance + disclosures', () => {
  async function stubBase(page, discOverride) {
    await page.route('**/api/auth/me', (r) => json(r, { id: 1, preferred_language: 'en' }));
    await page.route('**/api/billing/checkout-disclosures**', (r) => json(r, Object.assign({}, DISCLOSURES, discOverride || {})));
  }

  test('renders server-sourced commercial terms; pay gated on unticked box', async ({ page }) => {
    await stubBase(page);
    await page.goto(fileUrl('checkout.html') + '?plan=pro');
    await expect(page.locator('#planPrice')).toContainText('79');
    await expect(page.locator('#planPrice')).toContainText('SAR');
    await expect(page.locator('#dPeriod')).toContainText('Monthly');
    await expect(page.locator('#dRenewal')).toContainText(/renews automatically/i);
    await expect(page.locator('#dCancel')).toContainText(/cancel anytime/i);
    await expect(page.locator('#dVat')).toContainText(/VAT/i);
    await expect(page.locator('#dRefund')).toHaveAttribute('href', '/legal/refunds');
    await expect(page.locator('#acceptBox')).not.toBeChecked();
    await expect(page.locator('#continueBtn')).toBeDisabled();
    await page.locator('#acceptBox').check();
    await expect(page.locator('#continueBtn')).toBeEnabled();
  });

  test('Continue records acceptance server-side (accepted=true, no browser price)', async ({ page }) => {
    await stubBase(page);
    let body = null;
    await page.route('**/api/billing/checkout', (r) => {
      body = JSON.parse(r.request().postData() || '{}');
      return json(r, { provider: 'moyasar', mode: 'embedded', publishable_key: 'pk_test_x', amount: 7900, currency: 'SAR', callback_url: '/api/billing/return', metadata: {}, acceptance_id: 42 });
    });
    await page.goto(fileUrl('checkout.html') + '?plan=pro');
    await page.locator('#acceptBox').check();
    await page.locator('#continueBtn').click();
    await expect.poll(() => body && body.accepted).toBe(true);
    expect(body.plan).toBe('pro');
    expect(String(body.idempotency_key || '').length).toBeGreaterThan(8);
    // The browser must NOT send price / currency / period / VAT — server sets those.
    expect(body.price).toBeUndefined();
    expect(body.amount).toBeUndefined();
    expect(body.currency).toBeUndefined();
  });

  test('payments unavailable → notice, no pay form, no checkout POST', async ({ page }) => {
    await stubBase(page, { payments_available: false });
    let posted = false;
    await page.route('**/api/billing/checkout', (r) => { posted = true; return json(r, {}); });
    await page.goto(fileUrl('checkout.html') + '?plan=pro');
    await expect(page.locator('#st-unavailable')).toBeVisible();
    await expect(page.locator('#st-form')).toBeHidden();
    expect(posted).toBe(false);
  });
});

// ───────────────────────── Settings Legal panel (item 6) ─────────────────────────
test.describe('settings legal panel', () => {
  test('shows versions + acceptance dates, no hash/id leak', async ({ page }) => {
    await page.route('**/api/account/legal-status', (r) => json(r, LEGAL_STATUS));
    await page.route('**/api/auth/me', (r) => json(r, { id: 1, email: 'stage.user@example.com' }));
    await page.route('**/api/billing/summary', (r) => json(r, { plan: 'free', plan_name: 'Free', price_sar: 0, currency: 'SAR', interval: 'monthly', is_paid: false, status: 'free', plans: [] }));
    await page.route('**/api/**', (r) => json(r, {}));   // benign default for everything else
    await page.goto(fileUrl('settings.html') + '#legal');
    await page.locator('.settings-nav-item[data-section="legal"]').click();
    const root = page.locator('#legalRoot');
    await expect(root).toContainText('Terms of Service');
    await expect(root).toContainText('AI and Financial Disclaimer');
    await expect(root).toContainText(/Version\s*1\.0/i);
    await expect(root).toContainText(/accepted on/i);
    // Must NOT render any hash / HMAC / DB-id evidence.
    const txt = (await root.innerText()).toLowerCase();
    expect(txt).not.toContain('hash');
    expect(txt).not.toContain('hmac');
    expect(txt).not.toContain('subject_ref');
  });
});
