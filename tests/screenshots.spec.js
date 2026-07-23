// Screenshot export (review-artifacts/) — captures the acceptance/compliance surfaces as
// named PNG files with recorded viewport dimensions + the commit hash. Runs FULLY OFFLINE
// (file:// pages, stubbed /api/**, Moyasar CDN aborted) — no backend, no production data.
//
//   REVIEW_COMMIT=<hash> npx playwright test -c playwright.review.config.js screenshots
//
// Output: review-artifacts/<name>.png + review-artifacts/manifest.json
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.resolve(ROOT, 'review-artifacts');
fs.mkdirSync(OUT, { recursive: true });
// Relative to baseURL (HTTP origin) so page fetch('/api/...') calls are interceptable.
const fileUrl = (p) => '/' + String(p).replace(/^\//, '');
const COMMIT = process.env.REVIEW_COMMIT || 'unknown';
const DESKTOP = { width: 1280, height: 800 };
const MOBILE = { width: 390, height: 844 };

const manifest = [];
async function shot(page, name, viewport, route, testData) {
  const file = path.join(OUT, name + '.png');
  await page.screenshot({ path: file });
  manifest.push({
    name: name + '.png',
    route: route,
    viewport: { width: viewport.width, height: viewport.height },
    timestamp: new Date().toISOString(),
    test_data: testData,
    // Per-file provenance: the SHA-256 of the EXACT PNG bytes this run produced. A reviewer
    // verifies each file independently (sha256sum <file>) — the manifest can't silently refer
    // to different bytes than the ones on disk.
    sha256: crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
  });
}

// ---- stub fixtures (isolated staging data; not real users/records) ----
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
    terms: { version: '1.0', route: '/legal/terms' }, privacy: { version: '1.0', route: '/legal/privacy' },
    refunds: { version: '1.0', route: '/legal/refunds' }, 'ai-financial-disclaimer': { version: '1.0', route: '/legal/ai-financial-disclaimer' },
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
const SUMMARY_PAID = {
  plan: 'pro', plan_name: 'Pro', price_sar: 79, currency: 'SAR', interval: 'monthly', is_paid: true,
  billing_configured: true, status: 'active', renews_on: '2026-08-21T00:00:00+00:00',
  cancel_at_period_end: false, pending_plan: null, can_upgrade_to: ['elite'], can_downgrade_to: ['free'],
  plans: [{ id: 'free', name: 'Free', rank: 0, price_sar: 0 }, { id: 'pro', name: 'Pro', rank: 1, price_sar: 79 }, { id: 'elite', name: 'Elite', rank: 2, price_sar: 399 }],
  refund_eligible: false, refund_eligible_until: null,
};
function json(route, body, status = 200) { return route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) }); }

// Abort external hosts only (fonts / Turnstile / Moyasar CDN); never the local baseURL origin.
test.beforeEach(async ({ page }) => { await page.route(/googleapis|gstatic|cloudflare|moyasar/, (r) => r.abort()); });
test.afterAll(async () => {
  fs.writeFileSync(path.join(OUT, 'manifest.json'),
    JSON.stringify({
      // Four DISTINCT provenance dimensions, each knowable AT GENERATION TIME. We deliberately do
      // NOT stamp a self-referential "artifact"/"the commit these PNGs are stored under": that
      // commit does not exist until the PNGs are committed, so any value baked in here is either the
      // pre-commit HEAD (wrong once committed) or drifts to a later manifest-only edit (the exact
      // inaccuracy an earlier build shipped). The authoritative byte-storage commit is instead
      // COMPUTED from git — see png_bytes_commit_verify below.
      commits: {
        backend: process.env.REVIEW_BACKEND_COMMIT || 'unknown',        // backend repo HEAD under validation
        frontend_source: process.env.REVIEW_FRONTEND_SOURCE_COMMIT
                         || process.env.REVIEW_APP_COMMIT || COMMIT,     // last commit to the DEPICTED UI source
        screenshot_test: process.env.REVIEW_TEST_COMMIT || COMMIT,       // commit of screenshots.spec.js + review config
        generated_at_head: COMMIT,                                       // static repo HEAD when Playwright ran
      },
      // The exact commit that stores these PNG BYTES is verifiable, not asserted:
      png_bytes_commit_verify: "git -C <static-repo> log -1 --format=%H -- 'review-artifacts/*.png'",
      generated_by: 'playwright',
      screenshots: manifest,
    }, null, 2));
});

test('legal-index-desktop', async ({ page }) => {
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('legal/index.html'));
  await shot(page, 'legal-index-desktop', DESKTOP, '/legal/', 'static legal-suite index (no API)');
});

test('terms desktop + mobile', async ({ page }) => {
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('legal/terms/index.html'));
  await shot(page, 'terms-desktop', DESKTOP, '/legal/terms/', 'static Terms of Service v1.0 (no API)');
  await page.setViewportSize(MOBILE);
  await page.goto(fileUrl('legal/terms/index.html'));
  await shot(page, 'terms-mobile', MOBILE, '/legal/terms/', 'static Terms of Service v1.0 (no API)');
});

test('registration desktop + mobile', async ({ page }) => {
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('signup.html'));
  await page.locator('#terms').evaluate((el) => { el.checked = true; el.dispatchEvent(new Event('change', { bubbles: true })); }); // enabled/accepted state
  await shot(page, 'registration-desktop', DESKTOP, '/signup.html', 'acceptance box ticked -> button enabled');
  await page.setViewportSize(MOBILE);
  await page.goto(fileUrl('signup.html'));
  await shot(page, 'registration-mobile', MOBILE, '/signup.html', 'default state, acceptance box unticked');
});

test('checkout desktop + mobile + unavailable', async ({ page }) => {
  await page.route('**/api/auth/me', (r) => json(r, { id: 1, preferred_language: 'en' }));
  await page.route('**/api/billing/checkout-disclosures**', (r) => json(r, DISCLOSURES));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('checkout.html') + '?plan=pro');
  await expect(page.locator('#dVat')).toContainText('VAT');
  await shot(page, 'checkout-desktop', DESKTOP, '/checkout.html?plan=pro', 'stubbed disclosures: Pro 79 SAR/mo, payments_available=true');
  await page.setViewportSize(MOBILE);
  await page.goto(fileUrl('checkout.html') + '?plan=pro');
  await expect(page.locator('#dVat')).toContainText('VAT');
  await shot(page, 'checkout-mobile', MOBILE, '/checkout.html?plan=pro', 'stubbed disclosures: Pro 79 SAR/mo, payments_available=true');
  // unavailable state
  await page.unroute('**/api/billing/checkout-disclosures**');
  await page.route('**/api/billing/checkout-disclosures**', (r) => json(r, Object.assign({}, DISCLOSURES, { payments_available: false })));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('checkout.html') + '?plan=pro');
  await expect(page.locator('#st-unavailable')).toBeVisible();
  await shot(page, 'checkout-unavailable', DESKTOP, '/checkout.html?plan=pro', 'stubbed payments_available=false');
});

test('settings-legal', async ({ page }) => {
  await page.route('**/api/**', (r) => json(r, {}));                 // catch-all first (lowest priority)
  await page.route('**/api/account/legal-status', (r) => json(r, LEGAL_STATUS));
  await page.route('**/api/auth/me', (r) => json(r, { id: 1, email: 'stage.user@example.com' }));
  await page.route('**/api/billing/summary', (r) => json(r, SUMMARY_PAID));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('settings.html') + '#legal');
  await page.locator('.settings-nav-item[data-section="legal"]').click();
  await expect(page.locator('#legalRoot')).toContainText('AI and Financial Disclaimer');
  await shot(page, 'settings-legal', DESKTOP, '/settings.html#legal', 'stubbed legal-status: v1.0 docs + acceptance dates');
});

test('settings-renewal-off', async ({ page }) => {
  // Tokenization-failed state (Finding C): the sub is active but NON-renewing because no card
  // token was saved. The account must SHOW this + the access-end date + the renew/update-payment
  // flow (server permits a same-plan repair checkout in exactly this state).
  const SUMMARY_NO_TOKEN = Object.assign({}, SUMMARY_PAID, {
    cancel_at_period_end: true, auto_renew: false, renewal_token_missing: true,
    access_until: '2026-08-21T00:00:00+00:00',
  });
  await page.route('**/api/**', (r) => json(r, {}));                 // catch-all first (lowest priority)
  await page.route('**/api/auth/me', (r) => json(r, { id: 1, email: 'stage.user@example.com' }));
  await page.route('**/api/billing/summary', (r) => json(r, SUMMARY_NO_TOKEN));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('settings.html') + '#billing');
  await page.locator('.settings-nav-item[data-section="billing"]').click();
  await expect(page.locator('#billingRoot .bill-renewfix')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('#billingRoot')).toContainText('Auto-renewal is OFF');
  await expect(page.locator('[data-renewfix]')).toBeVisible();
  await shot(page, 'settings-renewal-off', DESKTOP, '/settings.html#billing',
             'stubbed renewal_token_missing=true: non-renewing banner + access-end date + renew/update-payment action');
});

test('cancellation-confirmation', async ({ page }) => {
  await page.route('**/api/**', (r) => json(r, {}));                 // catch-all first (lowest priority)
  await page.route('**/api/auth/me', (r) => json(r, { id: 1, email: 'stage.user@example.com' }));
  await page.route('**/api/billing/summary', (r) => json(r, SUMMARY_PAID));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('settings.html') + '#billing');
  await page.locator('.settings-nav-item[data-section="billing"]').click();
  // Wait for the billing panel to render, then open the cancel/downgrade-to-Free dialog.
  await expect(page.locator('#billingRoot [data-down="free"]')).toBeVisible({ timeout: 15000 });
  await page.locator('[data-down="free"]').first().click();
  await expect(page.locator('text=/keep your current plan until/i')).toBeVisible();
  await shot(page, 'cancellation-confirmation', DESKTOP, '/settings.html#billing', 'stubbed active Pro sub; cancel dialog open');
});

test('deletion-confirmation', async ({ page }) => {
  await page.route('**/api/**', (r) => json(r, {}));                 // catch-all first (lowest priority)
  await page.route('**/api/auth/me', (r) => json(r, { id: 1, email: 'stage.user@example.com' }));
  await page.route('**/api/billing/summary', (r) => json(r, SUMMARY_PAID));
  await page.setViewportSize(DESKTOP);
  await page.goto(fileUrl('settings.html') + '#export');
  await page.locator('.settings-nav-item[data-section="export"]').click();
  await page.getByRole('button', { name: /delete account/i }).click();
  await expect(page.locator('#deleteModal')).toBeVisible();
  await shot(page, 'deletion-confirmation', DESKTOP, '/settings.html#export', 'deletion modal open (typed-DELETE gate)');
});
