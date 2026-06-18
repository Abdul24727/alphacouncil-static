const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('E — dashboard (de-faked: real metrics, greeting, snapshot, council)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('greeting/metrics/snapshot/council are real; fakes (847,250 / Sami / Risk 64) gone', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/dashboard.html', { waitUntil: 'domcontentloaded' });

    // The fabricated literals are gone from the source entirely (so a logged-out user can't see them).
    const content = await page.content();
    expect(content, 'no fake SAR 847,250 total').not.toContain('847,250');
    expect(content, 'no fake "Good morning, Sami"').not.toContain('Good morning, Sami');
    expect(content, 'no fabricated banking 32.2% synthesis').not.toContain('32.2');
    expect(content, 'Risk Score metric replaced').not.toContain('Overall Risk Score');
    expect(content, 'Thesis Score column dropped').not.toContain('Thesis Score');

    // Greeting: real time-of-day + real current date (not "Monday, June 16, 2026").
    const greet = (await page.locator('#greetingHeading').textContent() || '').trim();
    expect(greet, 'real time-of-day greeting').toMatch(/^Good (morning|afternoon|evening)/);
    await expect(page.locator('#greetingDate'), 'real current-year date').toContainText('2026');

    // Metrics: real total value for the signed-in user (QA has seeded holdings).
    const mv0 = page.locator('.metrics-row .metric-value').first();
    await expect(mv0, 'real total portfolio value').toContainText('SAR', { timeout: 12000 });
    // 4th metric is the real "Today's Change", not the fabricated Risk Score.
    await expect(page.locator('.metrics-row .metric-card').nth(3)).toContainText("Today's Change");

    // Portfolio Snapshot quick-stats: real holdings count (QA seed has >=1).
    const qs0 = (await page.locator('.quick-stats .quick-stat-value').first().textContent() || '').trim();
    expect(Number(qs0), 'real holdings count').toBeGreaterThan(0);

    // Council card is a neutral CTA — no invented percentages.
    await expect(page.locator('.council-synthesis')).toContainText('Convene');

    await shot(page, 'e-dashboard');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
