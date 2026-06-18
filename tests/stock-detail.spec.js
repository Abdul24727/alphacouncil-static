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

  test("D6 — Analyst Forecast is real (price targets + EPS by year, not the 18-analyst / Q1'25 fakes)", async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });

    const sec = page.locator('#forecastSection');
    await expect(sec, 'forecast shown (2222 has analyst data)').toBeVisible({ timeout: 12000 });

    // ---- Price Target: real low/avg/high + real analyst count (not the 18 / SAR 32.50 fakes) ----
    const secHTML = await sec.innerHTML();
    expect(secHTML, 'no fake SAR 32.50 average').not.toContain('32.50');
    expect(secHTML, 'no fake 18-analyst count').not.toContain('18 analyst');
    const avg = (await sec.locator('.target-stat .value.avg').textContent() || '').trim();
    expect(avg, 'real average target in SAR').toMatch(/^SAR \d/);
    await expect(sec.locator('.analyst-count'), 'real analyst-target caption').toContainText('analyst price targets');

    // ---- Earnings Trend: real EPS by YEAR (not the hardcoded Q1'25 quarters) ----
    const bars = sec.locator('.earnings-bars');
    await expect(bars).not.toContainText('Loading', { timeout: 12000 });
    const barsHTML = await bars.innerHTML();
    expect(barsHTML, "no hardcoded Q1'25 quarter").not.toContain("Q1'25");
    expect(barsHTML, 'real 4-digit year labels').toMatch(/20\d\d/);
    expect(await bars.locator('.earnings-bar').count(), 'real EPS bars render').toBeGreaterThan(2);

    await shot(page, 'd6-forecast');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('D7 — Set Alert is honest (no fake "Alert Created") + dimension explanations real/absent', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });

    // ---- Dead canned dimension map gone; thesis is on-demand (CTA), no fabricated scores ----
    await expect(page.locator('#thesisBody'), 'thesis is on-demand').toContainText('Generate AI Thesis', { timeout: 12000 });
    const content = await page.content();
    expect(content, 'dead canned dimension map removed').not.toContain('dimensionExplanations');
    expect(content, 'real dimension wiring present').toContain('askAboutDimension');
    // the static fabricated dimension cards (e.g. "P/E of 14.2x") are gone from the live thesis card
    await expect(page.locator('.thesis-card'), 'no fabricated dimension scores shown').not.toContainText('14.2x');

    // ---- Set Alert: honest modal (no fake price-alert form / "Create Alert") ----
    await page.locator('button.action-btn', { hasText: 'Set Alert' }).click();
    const modal = page.locator('#alertModal');
    await expect(modal).toBeVisible();
    await expect(modal, 'honest monitoring copy').toContainText('automatically monitors');
    await expect(modal, 'no fake custom-alert form').not.toContainText('Alert Type');
    await expect(modal.locator('.btn-primary'), 'real watchlist action').toContainText('Add to Watchlist');

    // ---- "Add to Watchlist" → real POST /api/watchlist (stubbed; no fake "Alert Created") ----
    let added = false;
    await page.route('**/api/watchlist**', (route) => {
      if (route.request().method() === 'POST') { added = true; route.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":true}' }); }
      else route.continue();
    });
    await modal.locator('.btn-primary', { hasText: 'Add to Watchlist' }).click();
    await expect.poll(() => added, { timeout: 6000 }).toBeTruthy();
    await expect(page.locator('body'), 'no fabricated "Alert Created"').not.toContainText('Alert Created');

    await shot(page, 'd7-alert-dimensions');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
