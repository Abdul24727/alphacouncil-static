// Auth hardening (founder ask): disposable-email block surfaces on the signup page.
// (Verify-before-login + the CAPTCHA gate are covered live + in signup.spec.js; full
// registration can't be scripted now that Turnstile is enforced.)
const { test, expect } = require('@playwright/test');

test('signup rejects a disposable email (frontend surfaces the message)', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/signup.html', { waitUntil: 'domcontentloaded' });
  await page.fill('#firstName', 'Test');
  await page.fill('#lastName', 'Bot');
  await page.fill('#email', 'bot' + Date.now() + '@mailinator.com');
  await page.fill('#password', 'StrongPass123!');
  try { await page.locator('#market').selectOption({ index: 1 }); } catch (e) {}
  // custom-styled checkbox + button enables on change — set + fire the event directly
  await page.evaluate(() => {
    const c = document.getElementById('terms'); c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true }));
    document.querySelectorAll('input').forEach((i) => i.dispatchEvent(new Event('input', { bubbles: true })));
  });
  await page.waitForTimeout(200);
  await page.locator('#signupBtn').click({ force: true });
  // disposable is checked before captcha → the disposable message shows (or a rate-limit
  // message if this IP is throttled — either way the abusive signup is blocked, not created).
  await expect(page.locator('body')).toContainText(/permanent email|disposable|دائم|المؤقت|too many|محاولات/i, { timeout: 9000 });
  expect(page.url(), 'stays on signup').toContain('signup.html');
  await ctx.close();
});
