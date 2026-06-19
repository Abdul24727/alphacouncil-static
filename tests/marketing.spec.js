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

// M2 — no fabricated testimonials; ticker strip wired to real /api/ticker-tape (no fake fallback).
test.describe('M2 — index testimonials + ticker strip', () => {
  test('fabricated testimonials are gone', async ({ page }) => {
    await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
    const html = await page.content();
    for (const marker of ['What investors are saying', 'Ahmad', 'Fatima', 'Khalid']) {
      expect(html, 'fabricated testimonial "' + marker + '" removed').not.toContain(marker);
    }
  });

  test('ticker strip renders REAL /api/ticker-tape data, not the old hardcoded prices', async ({ page }) => {
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.route('**/api/ticker-tape', (route) => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ groups: [ { market: 'TASI', stocks: [
        { t: 'Saudi Aramco', p: 27.18, c: 0.44 },
        { t: 'Kingdom Holding', p: 14.42, c: -2.5 },
      ] } ] }),
    }));
    await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
    const track = page.locator('#tickerTrack');
    await expect(track).toContainText('Saudi Aramco', { timeout: 6000 });
    await expect(track).toContainText('+0.44%');
    await expect(track).toContainText('-2.50%');
    const html = await track.innerHTML();
    expect(html, 'old hardcoded fake "+1.2%" gone').not.toContain('+1.2%');
    expect(html, 'down move tagged .negative').toContain('ticker-change negative');
    expect(errs, 'no page errors:\n' + errs.join('\n')).toEqual([]);
  });

  test('ticker strip HIDES on API failure — no fake fallback prices', async ({ page }) => {
    await page.route('**/api/ticker-tape', (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }));
    await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('.ticker-strip')).toBeHidden({ timeout: 6000 });
  });
});
