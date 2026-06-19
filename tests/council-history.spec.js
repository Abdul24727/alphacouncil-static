const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('J1 — council-history.html (real history, was 100% mock)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('renders real history: fresh account → empty state; hardcoded mock reviews gone', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/council-history.html', { waitUntil: 'domcontentloaded' });

    const list = page.locator('#historyList');
    // QA (free plan) has never convened the Council → the loader shows the REAL empty state
    // (the GET /api/adviser/council/history endpoint is live and returns []).
    await expect(list).toContainText('No council reviews yet', { timeout: 12000 });
    const html = await list.innerHTML();
    expect(html, 'hardcoded June-14 mock review gone').not.toContain('June 14, 2026');
    expect(html, 'fabricated 32% concentration card gone').not.toContain('32% of portfolio');
    await expect(list, 'real CTA to run a review').toContainText('Run a Council Review');

    await shot(page, 'j1-council-history');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
