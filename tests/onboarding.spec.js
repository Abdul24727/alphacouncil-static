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

  test('G2 — real success tiles + multi-currency FX; profile persists to risk-profile', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/onboarding.html', { waitUntil: 'domcontentloaded' });

    // fabricated success tiles removed; real ones + real FX pegs present
    const content = await page.content();
    expect(content, 'no fake +8.4% return tile').not.toContain('+8.4%');
    expect(content, 'no fake Avg Dividend tile').not.toContain('Avg Dividend');
    expect(content, 'real Markets tile').toContain('previewMarkets');
    expect(content, 'real multi-currency FX pegs (incl. OMR/BHD)').toContain('OMR');

    // profile persists → real PUT /api/adviser/risk-profile
    let saved = false;
    await page.route('**/api/adviser/risk-profile', (route) => {
      if (route.request().method() === 'PUT') { saved = true; route.fulfill({ status: 200, contentType: 'application/json', body: '{"risk_style":"balanced"}' }); }
      else route.continue();
    });
    await page.evaluate(() => { if (typeof goToStep === 'function') goToStep(4); });
    await page.locator('.option-buttons[data-question="goal"] .option-btn[data-value="balanced"]').click();
    await page.locator('.option-buttons[data-question="timeline"] .option-btn[data-value="long"]').click();
    await page.locator('.profile-actions .btn-primary', { hasText: 'Continue' }).click();
    await expect.poll(() => saved, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'g2-onboarding');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
