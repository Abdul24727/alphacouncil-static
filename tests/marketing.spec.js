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

// M3 — markets.html real coverage: per-market counts + sectors live from /api/screening;
// invented counts/market-caps gone; "real-time" OHLCV claim corrected to end-of-day.
test.describe('M3 — markets.html real coverage', () => {
  test('per-market counts + sectors are live from /api/screening; no invented figures', async ({ page }) => {
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.route('**/api/screening**', (route) => route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ meta: {}, data: [
        { exchange: 'TADAWUL', sector_en: 'Banks' },
        { exchange: 'TADAWUL', sector_en: 'Energy' },
        { exchange: 'TADAWUL', sector_en: 'Banks' },
        { exchange: 'ADX', sector_en: 'Real Estate' },
        { exchange: 'DFM', sector_en: 'Real Estate' },
        { exchange: 'DFM', sector_en: 'Utilities' },
      ] }),
    }));
    await page.goto('/markets.html', { waitUntil: 'domcontentloaded' });

    const saudi = page.locator('#saudi .market-stat-value');
    await expect(saudi.nth(0)).toHaveText('3', { timeout: 6000 });   // 3 TADAWUL rows
    await expect(saudi.nth(1)).toHaveText('2');                       // {Banks, Energy}
    const uae = page.locator('#uae .market-stat-value');
    await expect(uae.nth(0)).toHaveText('3');                        // ADX(1) + DFM(2)
    await expect(uae.nth(1)).toHaveText('2');                        // {Real Estate, Utilities} deduped across ADX+DFM

    const html = await page.content();
    expect(html, 'invented Saudi count "280+" gone').not.toContain('280+');
    expect(html, 'invented Saudi cap "$2.8T" gone').not.toContain('$2.8T');
    expect(html, '"Market Cap" label replaced by "Sectors"').not.toContain('Market Cap');
    expect(html, 'OHLCV no longer claims real-time').not.toContain('Real-time and 15+');
    expect(html, 'OHLCV corrected to end-of-day').toContain('End-of-day and 15+');
    expect(errs, 'no page errors:\n' + errs.join('\n')).toEqual([]);
  });

  test('cards show "—" (no fake) when the screening API fails', async ({ page }) => {
    await page.route('**/api/screening**', (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }));
    await page.goto('/markets.html', { waitUntil: 'domcontentloaded' });
    const saudi = page.locator('#saudi .market-stat-value');
    await expect(saudi.nth(0)).toHaveText('—', { timeout: 6000 });
    await expect(saudi.nth(1)).toHaveText('—');
  });

  test('live page renders real numeric counts (not the old "NNN+")', async ({ page }) => {
    await page.goto('/markets.html', { waitUntil: 'domcontentloaded' });
    const saudi = page.locator('#saudi .market-stat-value').first();
    await expect(saudi).toHaveText(/^\d+$/, { timeout: 8000 });   // a real integer, not "280+" / "$2.8T"
  });
});
