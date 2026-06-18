const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;
// 1 unit of each currency in SAR (must match backend/portfolio/currency.py SAR_PER).
const PEG = { SAR: 1, AED: 1.0211, QAR: 1.0302, KWD: 12.22, OMR: 9.753, BHD: 9.9734 };

test.describe('B4 — multi-currency SAR roll-up', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('each holding converts to SAR at its correct GCC peg (QNBK=QAR, not SAR)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const holdings = await (await context.request.get('/api/portfolio/holdings')).json();
    expect(holdings.length).toBeGreaterThan(0);

    // The regression: a Qatar (QSE) holding used to resolve to SAR.
    const qnbk = holdings.find((h) => String(h.ticker_short).startsWith('QNBK'));
    expect(qnbk, 'QNBK holding present').toBeTruthy();
    expect(qnbk.currency, 'QNBK is Qatari riyal').toBe('QAR');

    // Every holding's SAR value must equal native × its peg.
    for (const h of holdings) {
      if (h.market_value_native == null) continue;
      expect(PEG[h.currency], `known peg for ${h.currency}`).toBeTruthy();
      const expected = h.market_value_native * PEG[h.currency];
      expect(Math.abs(h.market_value_sar - expected), `${h.ticker_short} ${h.currency} roll-up`).toBeLessThan(0.05);
    }
    await context.close();
  });

  test('portfolio page renders mixed-currency holdings + SAR total cleanly', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/portfolio.html', { waitUntil: 'networkidle' });
    await expect(page.locator('#holdingsTable tbody tr').first()).toBeVisible();
    await shot(page, 'b4-portfolio-multicurrency');
    assertClean(diag, expect);
    await context.close();
  });
});
