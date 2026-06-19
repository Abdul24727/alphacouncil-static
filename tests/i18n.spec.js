const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('O1/O2 — i18n engine + EN/AR toggle (dashboard shared chrome)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('toggle flips nav to Arabic + RTL, persists, and back to English; zero errors', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    let langPut = null;
    await page.route('**/api/account/profile', (route) => {
      if (route.request().method() === 'PUT') { langPut = JSON.parse(route.request().postData() || '{}'); route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' }); }
      else route.continue();
    });

    // Force a deterministic EN starting point regardless of the account's stored preference.
    await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'en'); } catch (e) {} });
    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });

    const dashLink = page.locator('.app-nav-links a[data-i18n="nav.dashboard"]');
    await expect(dashLink).toHaveText('Dashboard');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    // flip to Arabic
    await page.click('#langToggle button[data-lang="ar"]');
    await expect(dashLink).toHaveText('لوحة التحكم', { timeout: 4000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await expect(page.locator('#langToggle button[data-lang="ar"]')).toHaveClass(/active/);
    // other nav items translated too
    await expect(page.locator('.app-nav-links a[data-i18n="nav.portfolio"]')).toHaveText('المحفظة');

    // persisted to the account (real PUT) + localStorage
    await expect.poll(() => langPut, { timeout: 4000 }).toBeTruthy();
    expect(langPut.preferred_language).toBe('ar');
    expect(await page.evaluate(() => localStorage.getItem('ac.lang'))).toBe('ar');

    await shot(page, 'o1-arabic-rtl');

    // flip back to English
    await page.click('#langToggle button[data-lang="en"]');
    await expect(dashLink).toHaveText('Dashboard', { timeout: 4000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
