// Guard: the top market ticker is a live, ANIMATED marquee on every app page — incl.
// council-history + alerts, which are self-styled (no shared css link) and previously
// lacked the .indices-track marquee CSS, so the ticker rendered static + non-moving.
const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

for (const p of ['dashboard.html', 'council-history.html', 'alerts.html', 'markets-app.html']) {
  test('live animated ticker: ' + p, async ({ browser }) => {
    const ctx = await browser.newContext();
    await apiLogin(ctx, EMAIL, PASSWORD);
    const page = await ctx.newPage();
    await page.goto('/' + p, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3500);
    const s = await page.evaluate(() => {
      const bar = document.querySelector('.indices-bar');
      const inner = bar && bar.querySelector('.indices-inner');
      const track = bar && bar.querySelector('.indices-track');
      return {
        isTicker: bar ? bar.classList.contains('is-ticker') : false,
        items: bar ? bar.querySelectorAll('.index-item').length : 0,
        innerOverflow: inner ? getComputedStyle(inner).overflow : null,
        trackAnim: track ? getComputedStyle(track).animationName : null,
      };
    });
    expect(s.isTicker, 'bar should be in ticker mode').toBe(true);
    expect(s.items, 'ticker populated from the live tape').toBeGreaterThan(10);
    expect(s.trackAnim, 'track scrolls (ac-ticker-scroll)').toBe('ac-ticker-scroll');
    expect(s.innerOverflow, 'marquee clips').toBe('hidden');
    await ctx.close();
  });
}
