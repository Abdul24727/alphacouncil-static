const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('F3 — portfolio Add-Holding + Import (was mock + invented price / dead zone)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('Add Holding: autocomplete resolves a real ticker_key → REAL POST /api/portfolio/holdings (no invented price)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    await page.route('**/api/screening**', (route) => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ meta: {}, data: [
        { ticker_key: '2222_TADAWUL', ticker: '2222', name_en: 'Saudi Aramco', exchange: 'TADAWUL', currency: 'SAR' },
        { ticker_key: '1120_TADAWUL', ticker: '1120', name_en: 'Al Rajhi Bank', exchange: 'TADAWUL', currency: 'SAR' },
      ] }),
    }));

    let posted = null;
    await page.route('**/api/portfolio/holdings', (route) => {
      const req = route.request();
      if (req.method() === 'POST') { posted = JSON.parse(req.postData() || '{}'); route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' }); }
      else route.continue(); // GET loadPortfolio → real QA holdings (no side effect, since POST is stubbed)
    });

    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => AlphaCouncil.openAddHoldingModal());
    await expect(page.locator('#addHoldingModal')).toHaveClass(/open/);

    await page.fill('#stockSearch', 'aramco');
    const result = page.locator('#stockSearchResults .ssr-item', { hasText: 'Saudi Aramco' });
    await expect(result).toBeVisible({ timeout: 6000 });
    await result.click();
    await expect(page.locator('#stockSearch')).toHaveValue(/Saudi Aramco/);

    await page.fill('#sharesInput', '50');
    await page.fill('#costInput', '30.5');
    await page.click('#confirmAddBtn');

    await expect.poll(() => posted, { timeout: 6000 }).toBeTruthy();
    expect(posted.ticker, 'real resolved ticker_key sent (not freeform text)').toBe('2222_TADAWUL');
    expect(posted.shares).toBe(50);
    expect(posted.avg_cost, 'real typed cost, not a Math.random price').toBe(30.5);

    await shot(page, 'f3-add');
    expect(diag.pageErrors, 'no page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('Add Holding: nothing selected → no POST, honest prompt (no fabricated holding)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.route('**/api/screening**', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ data: [{ ticker_key: '2222_TADAWUL', ticker: '2222', name_en: 'Saudi Aramco', exchange: 'TADAWUL', currency: 'SAR' }] }) }));
    let posted = false;
    await page.route('**/api/portfolio/holdings', (route) => { if (route.request().method() === 'POST') posted = true; route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }); });
    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => AlphaCouncil.openAddHoldingModal());
    await page.fill('#sharesInput', '10');
    await page.fill('#costInput', '5');
    await page.click('#confirmAddBtn'); // no stock resolved
    await page.waitForTimeout(600);
    expect(posted, 'no POST without a resolved ticker_key').toBeFalsy();
    expect(diag.pageErrors).toEqual([]);
    await context.close();
  });

  test('Import: upload → review only MATCHED rows → REAL POST /api/portfolio/import-confirm', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    await page.route('**/api/portfolio/import-extract', (route) => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ count: 2, rows: [
        { raw_name: 'Saudi Telecom', matched_ticker_key: '7010_TADAWUL', matched_name: 'stc', shares: 100, avg_cost: 41.5, currency: 'SAR', needs_review: false },
        { raw_name: 'Unknown Co', matched_ticker_key: null, shares: 5, avg_cost: 1, currency: null, needs_review: true },
      ] }),
    }));
    let confirmBody = null;
    await page.route('**/api/portfolio/import-confirm', (route) => { confirmBody = JSON.parse(route.request().postData() || '{}'); route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' }); });
    await page.route('**/api/portfolio/holdings', (route) => { if (route.request().method() === 'GET') route.continue(); else route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }); });

    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });
    await page.click('#importBtn');
    await expect(page.locator('#importModal')).toHaveClass(/open/);

    await page.locator('#portfolioImportFile').setInputFiles({ name: 'statement.png', mimeType: 'image/png', buffer: Buffer.from('stub-image-bytes') });

    const review = page.locator('#importReview');
    await expect(review).toContainText('stc', { timeout: 12000 });
    const reviewHtml = await review.innerHTML();
    expect(reviewHtml, 'unmatched row never offered for import').not.toContain('Unknown Co');
    expect(await review.locator('.imp-row').count(), 'only the matched row is reviewable').toBe(1);

    await page.click('#confirmImportBtn');
    await expect.poll(() => confirmBody, { timeout: 6000 }).toBeTruthy();
    expect(Array.isArray(confirmBody.holdings)).toBeTruthy();
    expect(confirmBody.holdings.length, 'only the matched holding is confirmed').toBe(1);
    expect(confirmBody.holdings[0].ticker_key).toBe('7010_TADAWUL');
    expect(confirmBody.holdings[0].shares).toBe(100);

    await shot(page, 'f3-import');
    expect(diag.pageErrors, 'no page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
