// The scenario page's "Run Council" must send the ACTUAL scenario text to the Council
// endpoint (previously it ran a generic portfolio-wide question, ignoring the scenario).
const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

test('Run Council on a scenario sends the scenario text to /council/ask', async ({ browser }) => {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();

  // stub the (expensive, Pro/Elite-gated) convening; capture what was sent
  let askBody = null;
  await page.route('**/api/adviser/council/ask', async (route) => {
    askBody = route.request().postDataJSON();
    await route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ answer: 'STUB SYNTHESIS', chairman_model: 'deepseek/deepseek-v4-pro', analysts: [{ model: 'm', response: 'r' }], rankings: [], tickers_detected: [], disclaimer: 'x' }) });
  });

  await page.goto('/scenarios.html', { waitUntil: 'domcontentloaded' });
  const MARKER = 'ZTEST move 22% of Saudi banks into Qatar dividend names';
  await page.fill('#scenarioInput', MARKER);
  await page.locator('.council-cta-btn').first().click();

  await expect.poll(() => askBody, { timeout: 8000 }).toBeTruthy();
  expect(String(askBody.question || ''), 'scenario text reaches the Council').toContain(MARKER);
  // the modal labels it as a Scenario convening (not Portfolio-Wide)
  await expect(page.locator('#councilBadge')).toContainText(/Scenario/i);
  await ctx.close();
});
