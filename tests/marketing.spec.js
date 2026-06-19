const { test, expect } = require('@playwright/test');

// M1 — platform numbers must be identical + correct site-wide: 6 GCC markets / 716 stocks / 12 dims.
test.describe('M1 — consistent platform numbers', () => {
  const cases = [
    { url: '/index.html', bad: ['700+', '7 GCC markets'], good: ['6 GCC markets', '716 equities'] },
    { url: '/features.html', bad: ['7 Markets', '700+ Stocks'], good: ['6 Markets', '716 Stocks'] },
    { url: '/markets.html', bad: ['1,200+'], good: ['716', 'six GCC'] },
  ];
  for (const c of cases) {
    test('numbers consistent + correct on ' + c.url, async ({ page }) => {
      await page.goto(c.url, { waitUntil: 'domcontentloaded' });
      const html = await page.content();
      for (const b of c.bad) expect(html, c.url + ' should not contain "' + b + '"').not.toContain(b);
      for (const g of c.good) expect(html, c.url + ' should contain "' + g + '"').toContain(g);
    });
  }
});
