const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('K1 — scenarios.html (honest input → real AI, no fabricated numbers)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('no fabricated before/after figures; Analyze routes to the real adviser', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/scenarios.html', { waitUntil: 'domcontentloaded' });

    // the comparison section is an honest state, not fabricated before/after numbers
    const cmp = page.locator('#comparisonSection');
    await expect(cmp, 'honest comparison state').toContainText('Describe a scenario', { timeout: 12000 });
    const cmpHTML = await cmp.innerHTML();
    expect(cmpHTML, 'no fake SAR 847,250 value').not.toContain('847,250');
    expect(cmpHTML, 'no fake Before/After metrics header').not.toContain('Before / After');

    // saved-card fabricated impact figures (+0.4 Thesis / -5.2% Banking …) are stripped
    expect(await page.locator('.scenario-meta').count(), 'card impact numbers stripped').toBe(0);

    // honest preview banner reflects the real behavior
    await expect(page.locator('body'), 'honest banner').toContainText('no estimated figures are shown');

    // Analyze → real /api/adviser/ask (stubbed), not the old fake "calculated successfully" toast
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB', disclaimer: 'x' }) }); });
    await page.locator('button[onclick="analyzeScenario()"]').click();   // NL-mode Analyze (distinct from the new "Analyze trades")
    await expect.poll(() => asked, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'k1-scenarios');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
