// Investment Preferences actually persist (founder bug: they reset to defaults on return).
const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';

const SEL = {
  goal: '#preferences .segmented-control[aria-label="Primary Investment Goal"]',
  horizon: '#preferences .segmented-control[aria-label="Investment Time Horizon"]',
  risk: '#preferences .segmented-control[aria-label="Risk Tolerance"]',
};
const btn = (ctrl, key) => `${ctrl} .segment-btn:has([data-i18n="${key}"])`;

async function openPrefs(page) {
  await page.locator('a.settings-nav-item[data-section="preferences"]').click();
  await expect(page.locator('#preferences')).toBeVisible();
}

test('investment preferences persist across reload + to the API', async ({ browser }) => {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();
  await page.goto('/settings.html', { waitUntil: 'networkidle' });
  await openPrefs(page);
  await page.waitForTimeout(800); // let loadPrefs settle

  // pick NON-default values (defaults are income / medium / moderate)
  await page.locator(btn(SEL.goal, 'set.goal_growth')).click();
  await page.locator(btn(SEL.horizon, 'set.hz_long')).click();
  await page.locator(btn(SEL.risk, 'set.risk_agg')).click();
  await page.locator('#savePrefsBtn').click();
  await page.waitForTimeout(1500); // let the PUT complete

  // verify it persisted to the backend
  const rp = await ctx.request.get(BASE + '/api/adviser/risk-profile').then((r) => r.json());
  expect(rp.investment_goal, 'goal saved').toBe('growth');
  expect(rp.time_horizon, 'horizon saved').toBe('long');
  expect(rp.risk_tolerance, 'risk saved').toBe('aggressive');
  expect(rp.risk_style, 'risk_style derived for the Council').toBe('aggressive');

  // reload → the choices must come back (not reset to defaults)
  const page2 = await ctx.newPage();
  await page2.goto('/settings.html', { waitUntil: 'networkidle' });
  await openPrefs(page2);
  await page2.waitForTimeout(1200); // loadPrefs round-trip
  await expect(page2.locator(btn(SEL.goal, 'set.goal_growth'))).toHaveClass(/active/);
  await expect(page2.locator(btn(SEL.horizon, 'set.hz_long'))).toHaveClass(/active/);
  await expect(page2.locator(btn(SEL.risk, 'set.risk_agg'))).toHaveClass(/active/);
  // and the old defaults are NOT active anymore
  await expect(page2.locator(btn(SEL.goal, 'set.goal_income'))).not.toHaveClass(/active/);

  await ctx.close();
});
