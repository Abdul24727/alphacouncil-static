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

  test('D2 — recent news is real (not the hardcoded "PIF stake" cards); card → real adviser', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB-NEWS-ADVISER', disclaimer: 'x' }) }); });
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    // wait for the news fetch to resolve (Loading… → real cards or an honest empty state)
    await expect(page.locator('#tickerNewsBody')).not.toContainText('Loading', { timeout: 12000 });
    const html = await page.locator('#tickerNewsBody').innerHTML();
    expect(html, 'no hardcoded PIF card').not.toContain('PIF Increases Stake in Saudi Aramco to 8.2%');
    expect(html, 'no hardcoded McKinsey card').not.toContain('From McKinsey');
    const cards = await page.locator('#tickerNewsBody .news-card').count();
    expect(cards, 'Aramco should surface real news').toBeGreaterThan(0);
    // clicking a real news card routes to the real /api/adviser/ask
    await Promise.all([
      page.waitForRequest('**/api/adviser/ask', { timeout: 6000 }),
      page.locator('#tickerNewsBody .news-card').first().click(),
    ]);
    expect(asked, 'news card asked the real adviser').toBeTruthy();
    await context.close();
  });

  test('D3 — dividends & corporate actions are real (not the hardcoded SAR 0.375 table)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    const tb = page.locator('#dividendsBody');
    await expect(tb).not.toContainText('Loading', { timeout: 12000 });
    const html = await tb.innerHTML();
    // the old hardcoded table is gone
    expect(html, 'no fake 0.375 dividend amount').not.toContain('0.375');
    expect(html, 'no fake "Quarterly Dividend" label').not.toContain('Quarterly Dividend');
    // Aramco pays real dividends → real rows, amount in the stock currency
    const rows = await tb.locator('tr').count();
    expect(rows, 'real corporate rows render').toBeGreaterThan(0);
    expect(html, 'a real dividend amount in SAR').toContain('SAR ');
    expect(html.toLowerCase(), 'a real Dividend row').toContain('dividend');
    await shot(page, 'd3-dividends');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
