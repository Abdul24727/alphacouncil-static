const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('B3 — honest indices freshness (no fake "Live")', () => {
  test('/api/ticker-tape exposes a real as_of timestamp', async ({ request }) => {
    const j = await (await request.get('/api/ticker-tape')).json();
    expect(j.as_of, 'ticker-tape as_of present').toBeTruthy();
    expect(new Date(j.as_of).getTime()).toBeGreaterThan(0);
  });

  test('indices bar shows an honest "As of <date>", never "Live"', async ({ browser }) => {
    test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
    const t = page.locator('.indices-bar .indices-time');
    await expect(t).toHaveText(/^As of /);
    await expect(t).not.toContainText('Live');
    await context.close();
  });
});
