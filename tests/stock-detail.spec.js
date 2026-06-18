const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('D1 — stock-detail price chart (was a permanent placeholder)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('renders a real SVG chart from price-history; timeframe + overlays work', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    // a real chart SVG appears (not the "Interactive chart loads here" placeholder)
    await expect(page.locator('#chartHost svg')).toBeVisible({ timeout: 12000 });
    // the close-price polyline carries a real multi-point series
    const pts = await page.locator('#chartHost svg polyline').first().getAttribute('points');
    expect((pts || '').trim().split(/\s+/).length, 'chart has a real series').toBeGreaterThan(20);

    // Volume overlay toggles on real volume bars (count, not visibility — a low bar can be ~0px)
    await page.locator('.overlay-btn[data-ov="volume"]').click();
    await expect.poll(() => page.locator('#chartHost svg rect').count(), { timeout: 8000 }).toBeGreaterThan(10);
    // toggling it off removes them
    await page.locator('.overlay-btn[data-ov="volume"]').click();
    await expect.poll(() => page.locator('#chartHost svg rect').count(), { timeout: 8000 }).toBe(0);

    // timeframe switch re-renders from a fresh fetch
    await page.locator('.chart-tab[data-tf="6M"]').click();
    await expect(page.locator('.chart-tab[data-tf="6M"]')).toHaveClass(/active/);
    await expect(page.locator('#chartHost svg')).toBeVisible();

    await shot(page, 'd1-chart');
    // D1 must not introduce uncaught errors; full stock-detail console-clean is asserted at end of Phase D
    console.log('CONSOLE ERRORS:', JSON.stringify(diag.consoleErrors));
    console.log('FAILED REQUESTS:', JSON.stringify(diag.failedRequests));
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
