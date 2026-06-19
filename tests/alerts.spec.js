const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('I1 — alerts.html (broken filters removed, rules honest, chat real)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('analyst filter + no-op toggle gone; mock rules honest; chat → real adviser', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/alerts.html', { waitUntil: 'domcontentloaded' });

    // the real feed resolves (loader replaces the "Loading…" placeholder)
    await expect(page.locator('#alertsList')).not.toContainText('Loading your alerts', { timeout: 12000 });

    // the broken analyst-type filter + the no-op "holdings only" toggle are removed
    expect(await page.locator('#analystFilter').count(), 'broken analyst filter removed').toBe(0);
    expect(await page.locator('#holdingsOnly').count(), 'no-op holdings toggle removed').toBe(0);

    // the hardcoded mock "active rules" are stripped; an honest coming-soon note is shown
    expect(await page.locator('.rule-item').count(), 'mock rules removed').toBe(0);
    await expect(page.locator('#rulesComingSoon'), 'honest rules note').toContainText('coming soon');

    // the canned chat responses are gone from the source
    const content = await page.content();
    expect(content, 'no canned concentration reply').not.toContain('Your banking concentration of 32.2% is triggered');

    // the sidebar chat routes to the REAL adviser (stubbed)
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB', disclaimer: 'x' }) }); });
    await page.evaluate(() => { if (window.AlphaCouncil && AlphaCouncil.openSidebar) AlphaCouncil.openSidebar(); });
    await expect(page.locator('#chatSend')).toBeVisible({ timeout: 6000 });
    await page.locator('#chatInput').fill('What is my biggest risk right now?');
    await page.locator('#chatSend').click();
    await expect.poll(() => asked, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'i1-alerts');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
