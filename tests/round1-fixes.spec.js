// Regression tests for Round-1 audit fixes. Live-site target.
const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, apiLogin } = require('./helpers');
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

// R1-01 — stock-detail no longer ships fabricated header/thesis on every page.
// Tested signed-in (the primary case) so the page's authed calls don't 401.
test('R1-01 stock-detail: real header, no fabricated change/freshness/thesis', async ({ browser }) => {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();
  const diag = attachDiagnostics(page);
  await page.goto('/stock-detail.html?ticker=EMAAR_DFM', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const body = await page.evaluate(() => document.body.innerText);
  for (const fake of ['Updated 2 min ago', '+0.45 (+1.58%)', '2222.SR', '7.8/10', 'ROE of 32.1%', 'PIF) maintains 98%']) {
    expect(body, `fabricated literal still present: ${fake}`).not.toContain(fake);
  }
  const logo = await page.evaluate(() => (document.getElementById('stockLogo') || {}).textContent || '');
  expect(logo.trim(), 'logo must not be the hardcoded 2222').not.toBe('2222');
  const h1 = await page.evaluate(() => (document.querySelector('h1') || {}).innerText || '');
  expect(h1).toMatch(/EMAAR/i);              // real name resolved
  assertClean(diag, expect);                  // zero console errors / failed requests
  await ctx.close();
});

// R1-01b — invalid ticker → honest "Stock not found", not a fabricated Aramco fallback.
// Scope the fabrication check to the main content (the ticker-tape legitimately lists
// real movers like Saudi Aramco).
test('R1-01b stock-detail: invalid ticker shows honest not-found, no Aramco fabrication', async ({ page }) => {
  await page.goto('/stock-detail.html?ticker=ZZZZ_TADAWUL', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const main = await page.evaluate(() => (document.getElementById('mainContent') || document.body).innerText);
  expect(main).toContain('Stock not found');
  expect(main).not.toContain('Saudi Aramco');
  expect(main).not.toContain('7.8/10');
});

// R1-02 — the fabricated Sample-Dashboard is gone (the file was deleted; the SPA
// try_files fallback now serves index.html, so the fabricated dashboard markup is
// absent) and no CTA links to it.
test('R1-02 Sample-Dashboard fabrication removed + no CTA references', async ({ request }) => {
  const r = await request.get(`${BASE}/Sample-Dashboard.html`);
  const dash = await r.text();
  for (const marker of ['Good morning, Sami', 'Hello, Sami', '32.2% weight', 'Strategic Synthesis']) {
    expect(dash, `fabricated dashboard markup still served: ${marker}`).not.toContain(marker);
  }
  for (const p of ['index.html', 'features.html', 'how-it-works.html', 'markets.html']) {
    const html = await (await request.get(`${BASE}/${p}`)).text();
    expect(html, `${p} still links the sample dashboard`).not.toContain('Sample-Dashboard.html');
    expect(html, `${p} still has a sample-dashboard CTA`).not.toContain('View sample dashboard');
  }
});

// R1-03 — fundamentals returns honest-empty 200 (not 404) for a briefs-known ticker.
test('R1-03 fundamentals: briefs-known ticker without stocks row → 200 honest-empty (not 404)', async ({ request }) => {
  const r = await request.get(`${BASE}/api/ticker/ABRAAJ_BSE/fundamentals`);
  expect(r.status(), 'ABRAAJ_BSE fundamentals should be 200 honest-empty').toBe(200);
  const j = await r.json();
  expect(j.valuation, 'response keeps the group structure').toBeTruthy();
  // a truly-unknown ticker still 404s
  const bad = await request.get(`${BASE}/api/ticker/ZZZZ_TADAWUL/fundamentals`);
  expect(bad.status()).toBe(404);
});

// R1-04 — portfolio: no orphaned fabricated council synthesis / stale toast / 847,250.
test('R1-04 portfolio: no fabricated 32.2% council / stale toast / 847,250 (authed)', async ({ browser }) => {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();
  const diag = attachDiagnostics(page);
  await page.goto('/portfolio.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  const body = await page.evaluate(() => document.body.innerText);
  expect(body).not.toContain('32.2%');
  expect(body).not.toContain('847,250');
  expect(body).not.toContain('Action completed');
  expect(body).not.toContain('Constructive with Concentration');
  assertClean(diag, expect);
  await ctx.close();
});

// R1-06 — dead footer links resolved on forgot-password; onboarding help link real.
test('R1-06 dead links resolved', async ({ request }) => {
  const fp = await (await request.get(`${BASE}/forgot-password.html`)).text();
  expect(fp).toContain('legal.html#privacy');
  expect(fp).toContain('legal.html#terms');
  expect(fp).not.toMatch(/<a href="#">(Privacy Policy|Terms of Service|Help)<\/a>/);
  const ob = await (await request.get(`${BASE}/onboarding.html`)).text();
  expect(ob).not.toContain('<a href="#" class="header-help"');
});

// R1-07 — settings ships no fake identity defaults.
test('R1-07 settings: no Saeed/Al-Khalidi identity defaults', async ({ request }) => {
  const html = await (await request.get(`${BASE}/settings.html`)).text();
  expect(html).not.toContain('value="Saeed"');
  expect(html).not.toContain('value="Al-Khalidi"');
});
