const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('D1 — stock-detail price chart (was a permanent placeholder)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('renders a real SVG chart from price-history; timeframe + overlays work', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    // a real chart SVG appears (not the "Interactive chart loads here" placeholder)
    await expect(page.locator('#chartHost svg')).toBeVisible({ timeout: 12000 });
    // the close-price polyline carries a real multi-point series
    const pts = await page.locator('#chartHost svg polyline').first().getAttribute('points');
    expect((pts || '').trim().split(/\s+/).length, 'chart has a real series').toBeGreaterThan(20);

    // Volume overlay toggles on real volume bars (count, not visibility — a low bar can be ~0px)
    await page.locator('.overlay-btn[data-ov="volume"]').click();
    await expect.poll(() => page.locator('#chartHost svg rect').count(), { timeout: 8000 }).toBeGreaterThan(10);
    // toggling it off removes them
    await page.locator('.overlay-btn[data-ov="volume"]').click();
    await expect.poll(() => page.locator('#chartHost svg rect').count(), { timeout: 8000 }).toBe(0);

    // timeframe switch re-renders from a fresh fetch
    await page.locator('.chart-tab[data-tf="6M"]').click();
    await expect(page.locator('.chart-tab[data-tf="6M"]')).toHaveClass(/active/);
    await expect(page.locator('#chartHost svg')).toBeVisible();

    await shot(page, 'd1-chart');
    // D1 must not introduce uncaught errors; full stock-detail console-clean is asserted at end of Phase D
    console.log('CONSOLE ERRORS:', JSON.stringify(diag.consoleErrors));
    console.log('FAILED REQUESTS:', JSON.stringify(diag.failedRequests));
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('D2 — recent news is real (not the hardcoded "PIF stake" cards); card → real adviser', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB-NEWS-ADVISER', disclaimer: 'x' }) }); });
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    // wait for the news fetch to resolve (Loading… → real cards or an honest empty state)
    await expect(page.locator('#tickerNewsBody')).not.toContainText('Loading', { timeout: 12000 });
    const html = await page.locator('#tickerNewsBody').innerHTML();
    expect(html, 'no hardcoded PIF card').not.toContain('PIF Increases Stake in Saudi Aramco to 8.2%');
    expect(html, 'no hardcoded McKinsey card').not.toContain('From McKinsey');
    const cards = await page.locator('#tickerNewsBody .news-card').count();
    expect(cards, 'Aramco should surface real news').toBeGreaterThan(0);
    // clicking a real news card routes to the real /api/adviser/ask
    await Promise.all([
      page.waitForRequest('**/api/adviser/ask', { timeout: 6000 }),
      page.locator('#tickerNewsBody .news-card').first().click(),
    ]);
    expect(asked, 'news card asked the real adviser').toBeTruthy();
    await context.close();
  });

  test('D3 — dividends & corporate actions are real (not the hardcoded SAR 0.375 table)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    const tb = page.locator('#dividendsBody');
    await expect(tb).not.toContainText('Loading', { timeout: 12000 });
    const html = await tb.innerHTML();
    // the old hardcoded table is gone
    expect(html, 'no fake 0.375 dividend amount').not.toContain('0.375');
    expect(html, 'no fake "Quarterly Dividend" label').not.toContain('Quarterly Dividend');
    // Aramco pays real dividends → real rows, amount in the stock currency
    const rows = await tb.locator('tr').count();
    expect(rows, 'real corporate rows render').toBeGreaterThan(0);
    expect(html, 'a real dividend amount in SAR').toContain('SAR ');
    expect(html.toLowerCase(), 'a real Dividend row').toContain('dividend');
    await shot(page, 'd3-dividends');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('D4 — Key-Facts gauges, technicals & ownership are real (no hardcoded metrics)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });

    // ---- Gauges: real /fundamentals (no invented "vs Sector Avg" / hardcoded 14.2x / 6.8) ----
    const valDetails = page.locator('.gauge-card[data-group="valuation"] .gauge-details');
    await expect(valDetails).not.toContainText('Loading', { timeout: 12000 });
    const gaugesHTML = await page.locator('.gauges-grid').innerHTML();
    expect(gaugesHTML, 'no invented "vs Sector Avg" row').not.toContain('vs Sector Avg');
    expect(gaugesHTML, 'no hardcoded 14.2x P/E').not.toContain('14.2x');
    expect(gaugesHTML, 'no hardcoded 28.4% net margin').not.toContain('28.4%');
    await expect(valDetails, 'real P/E row present').toContainText('P/E Ratio');
    // valuation ring shows a real 0–10 composite (mean sector-percentile)
    const inner = (await page.locator('.gauge-card[data-group="valuation"] .gauge-inner').textContent() || '').trim();
    expect(Number(inner), 'real gauge composite 0–10').toBeGreaterThanOrEqual(0);
    expect(Number(inner), 'real gauge composite 0–10').toBeLessThanOrEqual(10);

    // ---- Technical table: real d.tech (no fake Support/Resistance/54.2) ----
    const tech = page.locator('#technicalBody');
    await expect(tech).not.toContainText('Loading', { timeout: 12000 });
    const techHTML = await tech.innerHTML();
    expect(techHTML, 'fake Support row gone').not.toContain('Support');
    expect(techHTML, 'fake Resistance row gone').not.toContain('Resistance');
    expect(techHTML, 'fake RSI 54.2 gone').not.toContain('54.2');
    await expect(tech, 'real RSI row').toContainText('RSI (14)');
    await expect(tech, 'real SMA 200 row').toContainText('SMA 200');
    await expect(tech, 'real 52-week extreme row').toContainText('52-Week');

    // ---- Ownership: fabricated mis-scaled bars removed (no real source) ----
    await expect(page.locator('body'), 'fake PIF ownership bar gone').not.toContainText('Saudi Government (PIF)');

    await shot(page, 'd4-gauges-tech');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('D5 — signal from real composite score + the user’s real position (not hardcoded 320 / SAR 9,248)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    // QA seed holds 2222 → position shown with REAL values
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });

    // ---- Signal: derived from the composite score, not a fabricated "High Confidence" ----
    const banner = page.locator('.signal-banner');
    await expect(banner).toBeVisible({ timeout: 12000 });
    await expect(banner, 'no fabricated confidence claim').not.toContainText('High Confidence');
    const sig = (await banner.locator('.signal-badge').textContent() || '').trim();
    expect(['BUY', 'HOLD', 'REDUCE'], 'signal is a real derived label').toContain(sig);
    await expect(banner.locator('.confidence-badge'), 'shows the real composite score').toContainText('/100');

    // ---- Position: the signed-in user's real holding (fakes gone) ----
    const pos = page.locator('.position-card');
    await expect(pos, 'position shown for a held ticker').toBeVisible({ timeout: 12000 });
    const posHTML = await pos.innerHTML();
    expect(posHTML, 'no hardcoded SAR 9,248 value').not.toContain('9,248');
    expect(posHTML, 'no hardcoded SAR 28.15 avg cost').not.toContain('28.15');
    expect(posHTML, 'no hardcoded +SAR 240 P&L').not.toContain('+SAR 240');
    // toast-only stubs are gone (buttons wired to real add/remove)
    const html = await page.content();
    expect(html, 'no Adjust toast stub').not.toContain('Opening position adjustment flow');
    expect(html, 'no Record Sale toast stub').not.toContain('Opening partial sale modal');

    // ---- Adjust Position → real POST /api/portfolio/holdings (stubbed; DB not mutated) ----
    let posted = false;
    await page.route('**/api/portfolio/holdings', (route) => {
      if (route.request().method() === 'POST') { posted = true; route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); }
      else route.continue();
    });
    await page.evaluate(() => { window.prompt = () => '100'; });
    await page.locator('.position-btn', { hasText: 'Adjust Position' }).click();
    await expect.poll(() => posted, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'd5-signal-position');

    // ---- A ticker the QA user does NOT hold → position card hidden (user-specific) ----
    const page2 = await context.newPage();
    await page2.goto('/stock-detail.html?ticker=1120_TADAWUL', { waitUntil: 'domcontentloaded' });
    await expect(page2.locator('.position-card'), 'position hidden when not held').toBeHidden({ timeout: 12000 });

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
