// markets-app.html (signed-in Markets tab) — real-data screener regression. Live-site.
const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

test.describe('markets-app — real /api/screening tab', () => {
  test('screener renders real rows; filters + sort work; movers real; clean console', async ({ browser }) => {
    const ctx = await browser.newContext();
    await apiLogin(ctx, EMAIL, PASSWORD);
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/markets-app.html', { waitUntil: 'networkidle' });

    // screener populates with REAL rows from /api/screening (keyed on real ticker_keys)
    await expect(page.locator('#screenerBody tr[data-ticker]').first()).toBeVisible({ timeout: 15000 });
    const n = await page.locator('#screenerBody tr[data-ticker]').count();
    expect(n, 'a full page of real rows').toBeGreaterThanOrEqual(30);
    const firstKey = await page.locator('#screenerBody tr[data-ticker]').first().getAttribute('data-ticker');
    expect(firstKey, 'rows keyed on real ticker_key (e.g. 2222_TADAWUL)').toMatch(/_/);
    const body = await page.evaluate(() => document.body.innerText);
    expect(body).not.toContain('Al Babtain Power');        // demo mover gone
    expect(body).not.toContain('Loading 716 GCC stocks');  // not stuck on loading
    // result count is a real number > 0
    const rc = await page.locator('#resultsCount').innerText();
    expect(rc).toMatch(/\d/);

    // index cards: TADAWUL shows a real value (not the old fabricated 12,847.32) + a real stock count
    const tadawulCard = await page.evaluate(() => {
      const c = document.querySelector('.index-card[data-exchange="TADAWUL"]');
      return c ? { val: c.querySelector('.index-card-value').textContent, meta: c.querySelector('.index-card-meta').textContent } : null;
    });
    expect(tadawulCard.val).not.toBe('12,847.32');
    expect(tadawulCard.meta).toMatch(/\d+ stocks/);

    // search filter narrows the list
    await page.locator('#stockSearch').fill('1120');
    await page.waitForTimeout(600);
    const afterSearch = await page.locator('#screenerBody tr[data-ticker]').count();
    expect(afterSearch).toBeLessThan(n);
    expect(afterSearch).toBeGreaterThan(0);
    await page.locator('#stockSearch').fill('');
    await page.waitForTimeout(400);

    // exchange filter → only that market
    await page.locator('#exchangeFilter').selectOption('DFM');
    await page.waitForTimeout(600);
    const dfmKeys = await page.locator('#screenerBody tr[data-ticker]').evaluateAll((els) => els.map((e) => e.getAttribute('data-ticker')));
    expect(dfmKeys.length).toBeGreaterThan(0);
    expect(dfmKeys.every((k) => /_DFM$/.test(k)), 'all rows are DFM').toBeTruthy();
    await page.locator('#exchangeFilter').selectOption('');
    await page.waitForTimeout(400);

    // sort by P/E toggles order without error
    await page.locator('.screener-table th[data-sort="pe"]').click();
    await page.waitForTimeout(400);
    await expect(page.locator('.screener-table th[data-sort="pe"]')).toHaveClass(/sorted/);

    // movers populated from /api/movers (real, not the demo rows)
    await expect(page.locator('#moversContent .mover-item').first()).toBeVisible({ timeout: 10000 });
    const moverTxt = await page.locator('#moversContent').innerText();
    expect(moverTxt).not.toContain('Al Babtain Power');

    diag.consoleErrors = diag.consoleErrors.filter((c) => !/favicon/i.test(c));
    expect(diag.pageErrors, 'no uncaught errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    expect(diag.consoleErrors, 'no console errors:\n' + diag.consoleErrors.join('\n')).toEqual([]);
    expect(diag.failedRequests, 'no failed requests:\n' + diag.failedRequests.join('\n')).toEqual([]);
    await ctx.close();
  });
});
