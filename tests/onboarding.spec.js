const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('G1 — onboarding statement upload (was silent data loss)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('upload does a REAL /import-extract; only ticker-matched rows become holdings (no simulatedHoldings)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    // Stub the vision extract: one MATCHED row + one UNMATCHED row (must be skipped, never fabricated).
    let extractCalled = false;
    await page.route('**/api/portfolio/import-extract', (route) => {
      extractCalled = true;
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          count: 2,
          rows: [
            { raw_name: 'Saudi Telecom', raw_code: '7010', shares: 123, avg_cost: 41.5, currency: 'SAR', matched_ticker_key: '7010_TADAWUL', matched_name: 'stc', matched_code: '7010', match_score: 1, needs_review: false },
            { raw_name: 'Unknown Co', raw_code: 'ZZZZ', shares: 5, avg_cost: 1, currency: null, matched_ticker_key: null, matched_name: null, match_score: 0, needs_review: true },
          ],
        }),
      });
    });

    await page.goto('/onboarding.html', { waitUntil: 'domcontentloaded' });

    // Upload a dummy file → triggers the real extract path (setupUpload wired #fileInput on load).
    await page.locator('#fileInput').setInputFiles({ name: 'statement.png', mimeType: 'image/png', buffer: Buffer.from('not-a-real-png-but-stubbed') });

    // The review shows the REAL matched row (stc), not the old hardcoded simulatedHoldings.
    const body = page.locator('#extractedBody');
    await expect(body).toContainText('stc', { timeout: 12000 });
    expect(extractCalled, 'real /api/portfolio/import-extract was called').toBeTruthy();

    const html = await body.innerHTML();
    expect(html, 'no fabricated ACWA Power (old simulatedHoldings)').not.toContain('ACWA Power');
    expect(html, 'no fabricated First Abu Dhabi Bank (old simulatedHoldings)').not.toContain('First Abu Dhabi Bank');
    expect(html, 'unmatched row is skipped, never fabricated into a holding').not.toContain('Unknown Co');
    expect(await body.locator('tr').count(), 'only the ticker-matched row persists into the review').toBe(1);

    await shot(page, 'g1-import');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
