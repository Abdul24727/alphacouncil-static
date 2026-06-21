// The email-verification page must exist, call the endpoint, and handle a bad/missing
// token gracefully (regression guard: without this page, verification-enforced signups
// would be permanently locked out).
const { test, expect } = require('@playwright/test');

test('verify-email.html handles an invalid token (error state + resend)', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/verify-email.html?token=bogus-invalid-token', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#stepError')).toBeVisible({ timeout: 8000 });
  await expect(page.locator('#stepLoading')).toBeHidden();
  await expect(page.locator('#resendBtn')).toBeVisible();   // recovery path for expired links
  await ctx.close();
});

test('verify-email.html with no token shows the error/recover state (not stuck loading)', async ({ browser }) => {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto('/verify-email.html', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#stepError')).toBeVisible({ timeout: 6000 });
  await ctx.close();
});
