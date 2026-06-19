const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('F1 — portfolio allocation charts (real, SAR-weighted)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('sector + country allocation computed from real holdings (not Banking 32.2% / Saudi 51.6%)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });

    const sector = page.locator('#sectorAllocItems');
    await expect(sector).not.toContainText('Loading', { timeout: 12000 });

    // fabricated allocations + flags are gone
    const allocHTML = await page.locator('.allocation-grid').innerHTML();
    expect(allocHTML, 'no fake 32.2% sector').not.toContain('32.2%');
    expect(allocHTML, 'no fake 51.6% country').not.toContain('51.6%');
    expect(allocHTML, 'no fake peer-median flag').not.toContain('above peer median');

    // sector bars are real and sum to ~100% of the portfolio
    const items = await sector.locator('.allocation-item').count();
    expect(items, 'real sector rows render').toBeGreaterThan(0);
    const pcts = await sector.locator('.allocation-pct').allTextContents();
    const sum = pcts.reduce(function (s, t) { return s + (parseFloat(t) || 0); }, 0);
    expect(sum, 'sector allocation sums to ~100%').toBeGreaterThan(98);
    expect(sum, 'sector allocation sums to ~100%').toBeLessThan(102);

    // country allocation reflects the real held markets (QA seed holds Saudi 2222)
    await expect(page.locator('#countryAllocItems')).toContainText('Saudi Arabia');

    await shot(page, 'f1-allocation');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('F2 — alerts + holdings-news panels render real data (not Brent/SABIC/Aramco-Q2 fakes)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });

    const alerts = page.locator('#alertsCardBody');
    await expect(alerts).not.toContainText('Loading', { timeout: 12000 });
    const alertsHTML = await alerts.innerHTML();
    expect(alertsHTML, 'no fake banking-concentration alert').not.toContain('Banking concentration exceeds 30%');
    expect(alertsHTML, 'no fake Brent alert').not.toContain('Brent crude below $83');
    expect(alertsHTML, 'no fake SABIC alert').not.toContain('SABIC trading below intrinsic');

    const news = page.locator('#holdingsNewsGrid');
    await expect(news).not.toContainText('Loading', { timeout: 12000 });
    const newsHTML = await news.innerHTML();
    expect(newsHTML, 'no fake Aramco-Q2 headline').not.toContain('Saudi Aramco Q2 profits decline amid lower oil prices');
    expect(newsHTML, 'no fake Al Rajhi headline').not.toContain('Al Rajhi Bank reports strong digital growth');

    await shot(page, 'f2-alerts-news');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('F4 — commentary/council/chat real (no 32.2% fakes); Export CSV + chat work', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/portfolio.html', { waitUntil: 'domcontentloaded' });

    // wait for real holdings to load (allocation renders from them)
    await expect(page.locator('#sectorAllocItems')).not.toContainText('Loading', { timeout: 12000 });

    // commentary + council synthesis no longer show fabricated 32.2% / SABIC
    await expect(page.locator('.commentary-text'), 'commentary de-faked').not.toContainText('32.2%');
    await expect(page.locator('.commentary-text')).not.toContainText('SABIC');
    await expect(page.locator('.council-synthesis'), 'council synthesis de-faked').not.toContainText('32.2%');
    await expect(page.locator('.council-synthesis')).toContainText('Convene');
    const bodyHtml = await page.locator('body').innerHTML();
    expect(bodyHtml, 'no fake "SAR 847,250" chat intro').not.toContain('total value of <strong>SAR 847,250</strong>');

    // Export CSV downloads the user's real holdings
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 8000 }),
      page.locator('.card-action', { hasText: 'Export CSV' }).click(),
    ]);
    expect(download.suggestedFilename(), 'CSV download').toContain('holdings');

    // the sidebar chat routes to the REAL adviser (no canned responses)
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB', disclaimer: 'x' }) }); });
    await page.evaluate(() => { if (window.AlphaCouncil && AlphaCouncil.openSidebar) AlphaCouncil.openSidebar(); });
    await expect(page.locator('#chatSend')).toBeVisible({ timeout: 6000 });
    await page.locator('#chatInput').fill('How concentrated is my portfolio?');
    await page.locator('#chatSend').click();
    await expect.poll(() => asked, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'f4-portfolio');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
