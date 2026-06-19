const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

const stubProfilePut = (page) => page.route('**/api/account/profile', (route) =>
  route.request().method() === 'PUT'
    ? route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' })
    : route.continue());

test.describe('O1/O2 — i18n engine + EN/AR toggle (dashboard, detailed)', () => {
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

    await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'en'); } catch (e) {} });
    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });

    const dashLink = page.locator('.app-nav-links a[data-i18n="nav.dashboard"]');
    await expect(dashLink).toHaveText('Dashboard', { timeout: 8000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    await page.click('.lang-toggle button[data-lang="ar"]');
    await expect(dashLink).toHaveText('لوحة التحكم', { timeout: 4000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await expect(page.locator('.app-nav-links a[data-i18n="nav.portfolio"]')).toHaveText('المحفظة');

    await expect.poll(() => langPut, { timeout: 4000 }).toBeTruthy();
    expect(langPut.preferred_language).toBe('ar');
    expect(await page.evaluate(() => localStorage.getItem('ac.lang'))).toBe('ar');

    await shot(page, 'o1-arabic-rtl');

    await page.locator('.lang-toggle button[data-lang="en"]').click();
    await expect(dashLink).toHaveText('Dashboard', { timeout: 4000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});

// O4 (shared chrome) — the engine auto-tags the nav + auto-wires the toggle on every app
// page that includes js/i18n.js. Verify EN→AR flip + RTL + zero console errors on each.
test.describe('O4 — i18n shared chrome rolled out across app pages', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  const PAGES = [
    { path: '/portfolio.html',        name: 'portfolio' },
    { path: '/news.html',             name: 'news' },
    { path: '/settings.html',         name: 'settings' },
    { path: '/alerts.html',           name: 'alerts' },
    { path: '/council-history.html',  name: 'council-history' },
    { path: '/scenarios.html',        name: 'scenarios' },
  ];

  for (const pg of PAGES) {
    test(`${pg.name}: nav auto-translates to Arabic + RTL on toggle, zero errors`, async ({ browser }) => {
      const context = await browser.newContext();
      await apiLogin(context, QA_EMAIL, QA_PASSWORD);
      const page = await context.newPage();
      const diag = attachDiagnostics(page);
      await stubProfilePut(page);
      await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'en'); } catch (e) {} });
      await page.goto(pg.path, { waitUntil: 'domcontentloaded' });

      // Engine auto-tagged the shared nav by text → the Dashboard link carries nav.dashboard.
      const dash = page.locator('.app-nav-links a[data-i18n="nav.dashboard"]');
      await expect(dash).toHaveText('Dashboard', { timeout: 8000 });
      await shot(page, `o4-${pg.name}-en`);

      await page.locator('.lang-toggle button[data-lang="ar"]').click();
      await expect(dash).toHaveText('لوحة التحكم', { timeout: 4000 });
      await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
      await shot(page, `o4-${pg.name}-ar`);

      expect(diag.pageErrors, pg.name + ' page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
      await context.close();
    });
  }
});
