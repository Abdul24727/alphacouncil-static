const { test, expect } = require('@playwright/test');
const { attachDiagnostics, shot } = require('./helpers');

test.describe('M4 — contact form (was a stub, now a real endpoint)', () => {
  test('submits a REAL POST /api/contact with the typed values; honest success; no "not wired" copy', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    let posted = null;
    await page.route('**/api/contact', (route) => {
      const req = route.request();
      if (req.method() === 'POST') {
        posted = JSON.parse(req.postData() || '{}');
        route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' });
      } else route.continue();
    });

    await page.goto('/contact.html', { waitUntil: 'domcontentloaded' });

    // the old stub copy must be gone (it admitted the form wasn't wired)
    const content = await page.content();
    expect(content, 'old "not fully wired" stub copy removed').not.toContain('fully wired');
    expect(content, 'old "Message noted" stub label removed').not.toContain('Message noted');

    await page.fill('#cf-name', 'QA Tester');
    await page.fill('#cf-email', 'qa@example.com');
    await page.fill('#cf-subject', 'Hello from Playwright');
    await page.fill('#cf-message', 'This is a real contact submission test.');
    await page.click('#contactForm button[type=submit]');

    // a real POST fired, carrying exactly what was typed
    await expect.poll(() => posted, { timeout: 6000 }).toBeTruthy();
    expect(posted.name).toBe('QA Tester');
    expect(posted.email).toBe('qa@example.com');
    expect(posted.subject).toBe('Hello from Playwright');
    expect(posted.message).toContain('real contact submission');

    // honest success state
    await expect(page.locator('#cf-ok')).toContainText('your message is in', { timeout: 6000 });
    await expect(page.locator('#contactForm button[type=submit]')).toHaveText('Message sent');

    await shot(page, 'm4-contact');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('validation: invalid form does NOT POST; honest inline error', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    let posted = false;
    await page.route('**/api/contact', (route) => {
      if (route.request().method() === 'POST') posted = true;
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' });
    });

    await page.goto('/contact.html', { waitUntil: 'domcontentloaded' });
    // submit empty → client-side guard should block the network call
    await page.click('#contactForm button[type=submit]');
    await expect(page.locator('#cf-ok')).toContainText('valid email', { timeout: 4000 });
    expect(posted, 'no network POST on an invalid form').toBeFalsy();

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
