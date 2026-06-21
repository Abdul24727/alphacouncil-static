// Verify marketing pages render Arabic on the AR version: most tagged copy is Arabic,
// dir=rtl, and key nav/CTA English is gone. Public pages — no auth.
const { test, expect } = require('@playwright/test');
const { shot } = require('./helpers');

const PAGES = ['index.html', 'pricing.html', 'how-it-works.html', 'methodology.html', 'about.html', 'contact.html'];

for (const p of PAGES) {
  test('AR marketing: ' + p, async ({ browser }) => {
    const ctx = await browser.newContext();
    await ctx.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
    const page = await ctx.newPage();
    await page.goto('/' + p, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');

    const stats = await page.evaluate(() => {
      const els = Array.prototype.slice.call(document.querySelectorAll('[data-i18n]'));
      let ar = 0, en = 0;
      for (const el of els) {
        const t = (el.textContent || '').trim();
        if (!t) continue;
        if (/[؀-ۿ]/.test(t)) ar++; else en++;
      }
      return { total: els.length, ar, en };
    });
    // content is actually tagged + overwhelmingly Arabic (a few brand/code labels may stay EN)
    expect(stats.total, p + ': has tagged content').toBeGreaterThan(15);
    expect(stats.ar, p + ': Arabic dominates tagged content (ar>' + stats.en + ')').toBeGreaterThan(stats.en * 2);

    // nav/CTA chrome translated → these English strings should be gone
    const body = await page.evaluate(() => document.body.innerText);
    for (const en of ['Start free', 'Sign in', 'How it works']) {
      expect(body, '"' + en + '" should be translated in AR').not.toContain(en);
    }
    await shot(page, 'ar_mkt_' + p.replace(/[^a-z]/gi, '_'));
    await ctx.close();
  });
}
