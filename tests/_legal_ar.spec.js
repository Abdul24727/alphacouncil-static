// Verify the Legal & Compliance page renders Arabic from the AR site, keeps the
// convenience-translation note + all inline links, and still defaults to English.
const { test, expect } = require('@playwright/test');
const { shot } = require('./helpers');

test('legal.html: Arabic when arriving from the AR site', async ({ browser }) => {
  const ctx = await browser.newContext();
  await ctx.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
  const page = await ctx.newPage();
  await page.goto('/legal.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  const stats = await page.evaluate(() => {
    const els = Array.prototype.slice.call(document.querySelectorAll('[data-i18n]'));
    let ar = 0, en = 0; for (const el of els) { const t = (el.textContent || '').trim(); if (!t) continue; if (/[؀-ۿ]/.test(t)) ar++; else en++; }
    return { total: els.length, ar, en, links: document.querySelectorAll('.legal-block a, a').length };
  });
  expect(stats.total, 'legal content tagged').toBeGreaterThan(40);
  expect(stats.ar, 'Arabic dominates legal copy').toBeGreaterThan(stats.en);
  expect(stats.links, 'inline links preserved').toBeGreaterThanOrEqual(30);
  await expect(page.locator('.lang-toggle')).toHaveCount(1);
  // the convenience-translation disclaimer is present in Arabic
  const body = await page.evaluate(() => document.body.innerText);
  expect(body, 'convenience-translation note shown').toContain('يُعتمد النص الإنجليزي');
  await shot(page, 'ar_legal');
  await ctx.close();
});

test('legal.html: still English by default', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/legal.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  const body = await page.evaluate(() => document.body.innerText);
  for (const en of ['Terms of Service', 'Privacy Policy', 'Disclaimer']) expect(body, 'EN intact: ' + en).toContain(en);
  await ctx.close();
});
