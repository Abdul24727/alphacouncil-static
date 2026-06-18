const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('authenticated harness', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('QA account logs in via API and dashboard renders real holdings', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);

    const me = await context.request.get('/api/auth/me');
    expect(me.ok()).toBeTruthy();
    expect((await me.json()).email).toBe(QA_EMAIL);

    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
    // real seeded holdings should populate the table (not the static skeleton)
    await expect(page.locator('#holdingsTable tbody tr').first()).toBeVisible();
    await shot(page, 'auth-dashboard');

    // Report diagnostics regardless, so the baseline is visible in output.
    console.log('CONSOLE ERRORS:', JSON.stringify(diag.consoleErrors, null, 2));
    console.log('FAILED REQUESTS:', JSON.stringify(diag.failedRequests, null, 2));
    console.log('PAGE ERRORS:', JSON.stringify(diag.pageErrors, null, 2));

    assertClean(diag, expect);
    await context.close();
  });
});
