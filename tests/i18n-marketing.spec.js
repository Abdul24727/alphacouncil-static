const { test, expect } = require('@playwright/test');

// O4 (marketing) — public pages: the engine injects an EN/AR toggle into .nav-actions and
// auto-translates the .nav-links; each page also tags its own content. EN is the default.
test.describe('O4 marketing — toggle injection + nav/content translation', () => {
  const PAGES = [
    { path: '/index.html',   name: 'index',   body: { sel: '.hero-badge', ar: 'تغطية حيّة' } },
    { path: '/contact.html', name: 'contact', body: { sel: 'h1[data-i18n="contact.hero_h1"]', ar: 'نحن هنا لمساعدتك' } },
    { path: '/about.html',   name: 'about',   body: { sel: 'h1[data-i18n="about.hero_h1"]', ar: 'نفهم أسواق الخليج' } },
    { path: '/how-it-works.html', name: 'how-it-works', body: { sel: '[data-i18n="hiw.hero_t1"]', ar: 'كيف يحوّل' } },
    { path: '/features.html', name: 'features', body: { sel: '[data-i18n="ft.hero_t1"]', ar: 'مزايا قوية' } },
    { path: '/pricing.html', name: 'pricing', body: { sel: '.hero-title[data-i18n="pr.hero"]', ar: 'ذكاء يتوسّع' } },
    { path: '/markets.html', name: 'markets', body: { sel: '.hero-title[data-i18n="mk.hero"]', ar: 'مبنيّ لأسواق الخليج' } },
  ];

  for (const pg of PAGES) {
    test(`${pg.name}: engine injects toggle; nav + content → Arabic + RTL; zero errors`, async ({ browser }) => {
      const context = await browser.newContext();
      const page = await context.newPage();
      const errs = [];
      page.on('pageerror', (e) => errs.push(String(e)));

      await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'en'); } catch (e) {} });
      await page.goto(pg.path, { waitUntil: 'domcontentloaded' });

      await expect(page.locator('.lang-toggle.ac-injected')).toHaveCount(1, { timeout: 6000 });
      const features = page.locator('.nav-links a[data-i18n="mnav.features"]');
      await expect(features).toHaveText('Features');
      await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');

      await page.locator('.lang-toggle button[data-lang="ar"]').click();
      await expect(features).toHaveText('المزايا', { timeout: 4000 });
      await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
      await expect(page.locator(pg.body.sel).first()).toContainText(pg.body.ar);

      expect(errs, pg.name + ' page errors:\n' + errs.join('\n')).toEqual([]);
      await context.close();
    });
  }
});
