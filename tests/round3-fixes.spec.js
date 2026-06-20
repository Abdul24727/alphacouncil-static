// Regression tests for Round-3 audit fixes (3 blockers + majors). Live-site target.
const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin } = require('./helpers');
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;
const get = async (request, p) => (await request.get(`${BASE}/${p}`)).text();

// R3-M1 — index stats: 12 Thesis Dimensions, 6 GCC Markets (was 11 / 7). + js/api.js comment.
test('R3-M1 index dimension count + GCC markets consistent', async ({ request }) => {
  const html = (await get(request, 'index.html')).replace(/\s+/g, ' ');
  expect(html).toContain('stat-value">12</div> <div class="stat-label">Thesis Dimensions');
  expect(html).toContain('stat-value">6</div> <div class="stat-label">GCC Markets');
  expect(html).not.toContain('stat-value">11</div> <div class="stat-label">Thesis Dimensions');
  expect(html).not.toContain('stat-value">7</div> <div class="stat-label">GCC Markets');
  const api = await get(request, 'js/api.js');
  expect(api).not.toContain('11-dimension');
  expect(api).toContain('12-dimension');
});

// R3-M2 — reset-password shows an honest message (not "[object Object]") on an invalid token.
test('R3-M2 reset-password invalid token → honest message, not [object Object]', async ({ page }) => {
  await page.goto('/reset-password.html?token=invalid-qa-token-zzz', { waitUntil: 'networkidle' });
  // fill the new-password form if present and submit
  const pw = page.locator('input[type="password"]');
  if (await pw.count() >= 2) {
    await pw.nth(0).fill('TestPass123!');
    await pw.nth(1).fill('TestPass123!');
    await page.locator('button[type="submit"], button:has-text("Update password"), button:has-text("Reset")').first().click();
    await page.waitForTimeout(2500);
  }
  const body = await page.evaluate(() => document.body.innerText);
  expect(body).not.toContain('[object Object]');
  expect(body.toLowerCase()).toMatch(/expired|invalid|request a new/);
});

// R3-M3 — news featured story is real (not the hardcoded PIF/Aramco), no fabricated flash persists.
test('R3-M3 news featured is real, not the fabricated PIF story', async ({ page }) => {
  await page.goto('/news.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const featured = await page.evaluate(() => (document.querySelector('.featured-story') || {}).innerText || '');
  expect(featured).not.toContain('PIF Increases Stake in Saudi Aramco to 8.2');
  expect(featured).not.toContain('June 16, 2026 · 09:45 GST');
  // a real story rendered (non-empty, non-placeholder) OR honest empty
  expect(featured.length, 'featured shows real content or honest empty').toBeGreaterThan(0);
});

// R3-B1 — council-history insights panel honest (no fabricated per-user analytics).
test('R3-B1 council-history insights panel is honest-empty', async ({ request }) => {
  const html = await get(request, 'council-history.html');
  for (const fake of ['4 of your last 6 reviews', 'average thesis of', '8.1/10', 'thesis has declined', '7.1 to 7.4']) {
    expect(html, `fabricated insight still present: ${fake}`).not.toContain(fake);
  }
  expect(html).toContain("Trends across your Council reviews will appear here");
});

// R3-B2 — council-history chat: canned fake answers + 'SK' + static demo reviews gone.
test('R3-B2 council-history canned chat + static demo reviews removed', async ({ request }) => {
  const html = await get(request, 'council-history.html');
  expect(html).not.toContain('stc (7010) +0.6 points');
  expect(html).not.toContain('chat-avatar">SK');
  expect(html).not.toContain('June 14, 2026 · 10:23 AM GST'); // static demo card gone
});

// R3-M4 — council-history Date/Sort: dead "Highest conviction" option gone, real option present.
test('R3-M4 council-history sort options real', async ({ request }) => {
  const html = await get(request, 'council-history.html');
  expect(html).not.toContain('Highest conviction');
  expect(html).toMatch(/Most analyst perspectives|Most signals/); // relabeled to a real backing field
});

// R3-M5/M6 — scenarios: structured-trades wired (Analyze), compare-multiple removed.
test('R3-M5/M6 scenarios structured-analyze wired + compare-multiple removed', async ({ request }) => {
  const html = await get(request, 'scenarios.html');
  expect(html).not.toContain('multiCompareToggle');
  expect(html).toMatch(/analyzeStructuredTrades|Analyze trades/);
});

// R3-B3/M7/M8/m5 — settings: canned chat gone, no SK avatar, methodology cards wired, freshness honest.
test('R3-B3/M7/M8 settings canned chat + SK avatar gone; methodology cards wired', async ({ request }) => {
  const html = await get(request, 'settings.html');
  expect(html).not.toContain('All data is encrypted and stored securely');
  expect(html).not.toContain('avatar-preview">SK');
  expect(html).not.toContain('saeed.khalidi@example.com');
  expect(html).not.toContain('>Real-time<');
  // all 4 methodology cards open methodology.html
  const cards = (html.match(/methodology-card/g) || []).length;
  const opens = (html.match(/window\.open\('methodology\.html'/g) || []).length;
  expect(opens, 'every methodology card wired').toBeGreaterThanOrEqual(4);
});

// R3-M7 (rendered) — settings avatar shows real initials (not SK) for the QA user.
test('R3-M7 settings avatar renders real initials, not SK', async ({ browser }) => {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();
  await page.goto('/settings.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const av = await page.evaluate(() => (document.querySelector('.avatar-preview') || {}).textContent || '');
  expect(av.trim()).not.toBe('SK');
  await ctx.close();
});

// R3-M9 — onboarding P&L is NaN-guarded (no unconditional +NaN%).
test('R3-M9 onboarding success P&L is guarded (no +NaN%)', async ({ request }) => {
  const html = await get(request, 'onboarding.html');
  expect(html).toMatch(/Number\.isFinite/);              // guard added
  expect(html).not.toMatch(/\+\$\{\(\(h\.price - h\.avgPrice\)/); // old unguarded expr gone
});

// R3-M10 — alerts header/tab counts neutralized (no fabricated static counts).
test('R3-M10 alerts fabricated header/tab counts removed', async ({ request }) => {
  const html = await get(request, 'alerts.html');
  expect(html).not.toContain('12 active');
  expect(html).not.toContain('3 new today');
  expect(html).toMatch(/resetStats/);
});
