// Auth hardening (founder ask): disposable-email block + verify-before-login.
const { test, expect, request } = require('@playwright/test');
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';

test('signup rejects a disposable email (frontend surfaces the message)', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/signup.html', { waitUntil: 'networkidle' });
  await page.fill('#firstName', 'Test');
  await page.fill('#lastName', 'Bot');
  await page.fill('#email', 'bot' + Date.now() + '@mailinator.com');
  await page.fill('#password', 'StrongPass123!');
  try { await page.locator('#market').selectOption({ index: 1 }); } catch (e) {}
  // custom-styled checkbox + button enable on change — set + fire the event directly
  await page.evaluate(() => {
    const c = document.getElementById('terms'); c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true }));
    document.querySelectorAll('input').forEach((i) => i.dispatchEvent(new Event('input', { bubbles: true })));
  });
  await page.waitForTimeout(200);
  await page.locator('#signupBtn').click({ force: true });
  await expect(page.locator('body')).toContainText(/permanent email|disposable|دائم|المؤقت/i, { timeout: 9000 });
  expect(page.url(), 'stays on signup').toContain('signup.html');
  await ctx.close();
});

test('a brand-new account is blocked at login until verified (verify notice shown)', async ({ browser }) => {
  const email = 'authtest+' + Date.now() + '@example.com';
  const pw = 'StrongPass123!';
  const rq = await request.newContext({ baseURL: BASE });
  const reg = await rq.post('/api/auth/register', { data: { email, password: pw, first_name: 'A', last_name: 'B', market: 'SA' } });
  expect(reg.status(), 'register succeeds (no captcha configured)').toBe(200);
  await rq.dispose();

  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/login.html', { waitUntil: 'networkidle' });
  await page.fill('#email', email);
  await page.fill('#password', pw);
  await page.click('#loginBtn');
  await expect(page.locator('body')).toContainText(/verify your email|please verify|وثّق|توثيق/i, { timeout: 9000 });
  expect(page.url(), 'not redirected to dashboard').toContain('login.html');
  await ctx.close();
});
