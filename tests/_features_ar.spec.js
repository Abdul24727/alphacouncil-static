// Verify features.html is fully Arabic on the AR version (marketing page, no auth).
const { test, expect } = require('@playwright/test');
const { shot } = require('./helpers');

test('features.html renders Arabic content (no leftover key English)', async ({ browser }) => {
  const ctx = await browser.newContext();
  await ctx.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
  const page = await ctx.newPage();
  await page.goto('/features.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  const body = await page.evaluate(() => document.body.innerText);

  // Arabic marketing copy is present (hero + a card + a stack/footer area)
  expect(body, 'hero translated').toContain('قرارات أوضح');
  expect(body, 'has substantial Arabic copy').toMatch(/[؀-ۿ]{4,}/);

  // Specific strings that were English and are now translated must NOT appear
  for (const en of ['Start free', 'Source-linked', 'Portfolio Score', 'Strategic Synthesis']) {
    expect(body, `"${en}" should be translated, not shown in AR`).not.toContain(en);
  }

  await shot(page, 'features_ar');
  await ctx.close();
});
