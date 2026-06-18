const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('B2 — adviser chat is real (no canned templates)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('clicking a news card routes to the real /api/adviser/ask, not a template', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();

    // Intercept the adviser endpoint so we prove the wiring without LLM cost/quota.
    let askBody = null;
    await page.route('**/api/adviser/ask', async (route) => {
      askBody = route.request().postDataJSON();
      await route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ answer: 'REAL-ADVISER-STUB-OK', disclaimer: 'Not financial advice.' }) });
    });

    await page.goto('/stock-detail.html?ticker=2222_TADAWUL', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#userMenu')).toHaveText('QP');   // wait until the real user loaded
    await page.locator('.news-card').first().click();

    // The real (stubbed) answer renders; the old canned template must NOT appear.
    await expect(page.locator('#chatMessages')).toContainText('REAL-ADVISER-STUB-OK', { timeout: 10000 });
    await expect(page.locator('#chatMessages')).not.toContainText('Institutional buying often signals');
    expect(askBody, 'POST /api/adviser/ask body present').toBeTruthy();
    expect(String(askBody.question || '')).toMatch(/news mean for/i);

    // The chat user-avatar shows the real initials, not "SK".
    await expect(page.locator('#chatMessages .chat-message.user .chat-avatar').first()).toHaveText('QP');
    await context.close();
  });

  test('adviser-core.js served bundle contains no canned-template signatures', async ({ request }) => {
    const js = await (await request.get('/adviser-core.js')).text();
    for (const s of ['function generateResponse', 'Institutional buying often signals',
      'Net margin: Above sector', 'Banking concentration (32.2%)', 'Council Review Summary']) {
      expect(js, `served adviser-core.js still contains: ${s}`).not.toContain(s);
    }
  });
});
