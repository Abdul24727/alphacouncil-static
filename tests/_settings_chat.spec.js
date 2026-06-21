// Verify the AI adviser chat opens + its input is usable on pages that previously
// double-wired the toggle (founder report: chat window not available on settings).
const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

const PAGES = ['settings.html', 'council-history.html', 'scenarios.html', 'alerts.html'];

for (const p of PAGES) {
  test('chat opens + input usable: ' + p, async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    await apiLogin(ctx, EMAIL, PASSWORD);
    const page = await ctx.newPage();
    await page.goto('/' + p, { waitUntil: 'networkidle' });
    await page.locator('#adviserToggle').click();
    await page.waitForTimeout(600);
    // the sidebar must actually be open (the double-wire bug left it closed)
    await expect(page.locator('#adviserSidebar')).toHaveClass(/open/);
    const input = page.locator('#chatInput');
    await expect(input, 'chat input visible').toBeVisible();
    const box = await input.boundingBox();
    expect(box, 'input has a box').not.toBeNull();
    expect(box.y + box.height, 'input bottom within viewport').toBeLessThanOrEqual(801);
    await input.click();
    await input.fill('test');
    expect(await input.inputValue()).toBe('test');
    await ctx.close();
  });
}
