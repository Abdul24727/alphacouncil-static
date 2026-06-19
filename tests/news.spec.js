const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('H1 — news.html (real Top Stories, real Summarize, one tab handler)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('Top Stories from the feed; Summarize → real adviser; legacy tab toast gone', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/news.html', { waitUntil: 'domcontentloaded' });

    // Top Stories populated from the real feed (not the hardcoded TASI / hydrogen headlines)
    const top = page.locator('#topStoriesList');
    await expect(top).not.toContainText('Loading', { timeout: 12000 });
    const topHTML = await top.innerHTML();
    expect(topHTML, 'no fake TASI headline').not.toContain('TASI Reaches 3-Month High');
    expect(topHTML, 'no fake hydrogen headline').not.toContain('100B Green Hydrogen');
    expect(await top.locator('.top-story-item').count(), 'real top stories render').toBeGreaterThan(0);

    // the legacy toast-only tab handler is removed (one real handler remains)
    const content = await page.content();
    expect(content, 'legacy tab toast removed').not.toContain('Showing news for your holdings only');

    // Summarize → real /api/adviser/ask (stub), not the canned PIF/Aramco summary
    let asked = false;
    await page.route('**/api/adviser/ask', (route) => { asked = true; route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB', disclaimer: 'x' }) }); });
    await page.locator('.summarize-btn').click();
    await expect.poll(() => asked, { timeout: 6000 }).toBeTruthy();

    await shot(page, 'h1-news');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
