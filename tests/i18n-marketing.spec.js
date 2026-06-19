const { test, expect } = require('@playwright/test');

// O4 (marketing) — public pages have no toggle/app-nav, so the engine injects an EN/AR
// toggle into .nav-actions and auto-translates the .nav-links. index.html also tags its hero.
test.describe('O4 marketing — index.html toggle injection + nav/hero translation', () => {
  test('engine injects toggle; nav + hero flip to Arabic + RTL; zero errors', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));

    await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'en'); } catch (e) {} });
    await page.goto('/index.html', { waitUntil: 'domcontentloaded' });

    // the engine injected an EN/AR toggle into the public nav
    await expect(page.locator('.lang-toggle.ac-injected')).toHaveCount(1, { timeout: 6000 });
    const features = page.locator('.nav-links a[data-i18n="mnav.features"]');
    await expect(features).toHaveText('Features');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

    await page.locator('.lang-toggle button[data-lang="ar"]').click();
    await expect(features).toHaveText('المزايا', { timeout: 4000 });
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('.hero-badge')).toContainText('تغطية حيّة');
    await expect(page.locator('.hero-subtitle')).toContainText('أضِف مراكزك');

    expect(errs, 'page errors:\n' + errs.join('\n')).toEqual([]);
    await context.close();
  });
});
