// Verify auth pages render Arabic when the visitor arrives from the Arabic version
// of the site (persisted via localStorage ac.lang='ar') — the founder's exact flow.
const { test, expect } = require('@playwright/test');
const { shot } = require('./helpers');

const PAGES = [
  { f: 'login.html', en: ['Welcome back', 'Email address', 'Password'] },
  { f: 'signup.html', en: ['Create', 'Email'] },
  { f: 'forgot-password.html', en: ['Email'] },
  { f: 'reset-password.html', en: ['password'] },
];

for (const p of PAGES) {
  test('AR auth (persisted): ' + p.f, async ({ browser }) => {
    const ctx = await browser.newContext();
    // simulate having chosen Arabic elsewhere on the site
    await ctx.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
    const page = await ctx.newPage();
    await page.goto('/' + p.f, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    await expect(page.locator('html'), p.f + ' should be RTL').toHaveAttribute('dir', 'rtl');
    const stats = await page.evaluate(() => {
      const els = Array.prototype.slice.call(document.querySelectorAll('[data-i18n]'));
      let ar = 0, en = 0;
      for (const el of els) { const t = (el.textContent || '').trim(); if (!t) continue; if (/[؀-ۿ]/.test(t)) ar++; else en++; }
      return { total: els.length, ar, en };
    });
    expect(stats.total, p.f + ': content tagged').toBeGreaterThan(8);
    expect(stats.ar, p.f + ': Arabic dominates').toBeGreaterThan(stats.en);
    // the language toggle exists
    await expect(page.locator('.lang-toggle')).toHaveCount(1);
    await shot(page, 'ar_auth_' + p.f.replace(/[^a-z]/gi, '_'));
    await ctx.close();
  });

  test('EN auth (default) still English: ' + p.f, async ({ browser }) => {
    const ctx = await browser.newContext(); // no ac.lang → default EN
    const page = await ctx.newPage();
    await page.goto('/' + p.f, { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    const body = await page.evaluate(() => document.body.innerText);
    for (const en of p.en) expect(body, p.f + ' EN intact: ' + en).toContain(en);
    await ctx.close();
  });
}
