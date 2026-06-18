const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, shot } = require('./helpers');

test.describe('C1 — reset-password page (was missing → reset emails dead-ended)', () => {
  test('loads clean and shows the new-password form when a token is present', async ({ page }) => {
    const diag = attachDiagnostics(page);
    await page.goto('/reset-password.html?token=sometoken', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#stepForm')).toBeVisible();
    await expect(page.locator('#newPassword')).toBeVisible();
    await shot(page, 'c1-reset-form');
    assertClean(diag, expect);
  });

  test('missing token → shows the invalid-link state immediately', async ({ page }) => {
    await page.goto('/reset-password.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#stepError')).toBeVisible();
    await expect(page.locator('#stepForm')).toBeHidden();
  });

  test('client validation blocks weak + mismatched passwords (no request sent)', async ({ page }) => {
    await page.goto('/reset-password.html?token=t', { waitUntil: 'domcontentloaded' });
    await page.fill('#newPassword', 'short');
    await page.fill('#confirmPassword', 'short');
    await page.click('#submitBtn');
    await expect(page.locator('#hint')).toContainText('at least 8');
    await page.fill('#newPassword', 'longenough123');
    await page.fill('#confirmPassword', 'different123');
    await page.click('#submitBtn');
    await expect(page.locator('#hint')).toContainText("don't match");
  });

  test('invalid token → real backend 400 → honest "Link expired" state', async ({ page }) => {
    const diag = attachDiagnostics(page);
    await page.goto('/reset-password.html?token=definitely-bogus-token', { waitUntil: 'domcontentloaded' });
    await page.fill('#newPassword', 'newpassword123');
    await page.fill('#confirmPassword', 'newpassword123');
    await page.click('#submitBtn');
    await expect(page.locator('#stepError')).toBeVisible({ timeout: 10000 });
    await shot(page, 'c1-reset-expired');
    // the expected/handled 400 from the reset endpoint is not a defect (the browser
    // logs "Failed to load resource … 400" for it — allow that + the request itself)
    assertClean(diag, expect, [/reset-password/, /Failed to load resource/i, /status of 4\d\d/i]);
  });

  test('valid token (stubbed) → "Password updated" success state', async ({ page }) => {
    await page.route('**/api/auth/reset-password', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok', message: 'Password updated.' }) }));
    await page.goto('/reset-password.html?token=whatever', { waitUntil: 'domcontentloaded' });
    await page.fill('#newPassword', 'newpassword123');
    await page.fill('#confirmPassword', 'newpassword123');
    await page.click('#submitBtn');
    await expect(page.locator('#stepSuccess')).toBeVisible({ timeout: 10000 });
  });
});
