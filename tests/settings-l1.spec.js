const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;

test.describe('L1 — settings real-or-remove (no security theatre / no USD billing artifacts)', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('placebos gone: fake VISA/invoices/sessions removed; 2FA honestly "coming soon"', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/settings.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(800); // let the load script run

    const html = await page.content();
    expect(html, 'fake VISA card number removed').not.toContain('•••• •••• •••• 4242');
    expect(html, 'fake card expiry removed').not.toContain('Expires 12/2027');
    expect(html, 'fake invoice amount removed').not.toContain('$49.00');
    expect(html, 'fake session device removed').not.toContain('MacBook Pro');
    expect(html, 'fake session device removed').not.toContain('iPhone 15 Pro');

    // 2FA panel is honestly gated — no "Enable 2FA" control that secures nothing
    await expect(page.locator('#twofaSection')).toContainText('Coming soon');
    await expect(page.locator('#twofaSection')).not.toContainText('Enable 2FA');

    // real change-password form exists
    await expect(page.locator('#changePasswordBtn')).toHaveCount(1);
    await expect(page.locator('#signOutBtn')).toHaveCount(1);

    await shot(page, 'l1-settings');
    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('profile Save persists via real PUT /api/account/profile', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    let put = null;
    await page.route('**/api/account/profile', (route) => {
      put = JSON.parse(route.request().postData() || '{}');
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' });
    });

    await page.goto('/settings.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    await page.fill('#firstName', 'QA');
    await page.fill('#lastName', 'Tester');
    await page.selectOption('#language', 'ar');
    await page.click('#saveProfileBtn');

    await expect.poll(() => put, { timeout: 6000 }).toBeTruthy();
    expect(put.first_name).toBe('QA');
    expect(put.last_name).toBe('Tester');
    expect(put.preferred_language).toBe('ar');

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });

  test('change-password posts to real /api/account/change-password (with validation)', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);

    let posted = null;
    await page.route('**/api/account/change-password', (route) => {
      posted = JSON.parse(route.request().postData() || '{}');
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' });
    });

    await page.goto('/settings.html', { waitUntil: 'domcontentloaded' });
    // reveal the Security section
    await page.click('.settings-nav-item[data-section="security"]');
    await page.fill('#currentPassword', 'oldpass123');
    await page.fill('#newPassword', 'newpass456');
    await page.fill('#confirmPassword', 'newpass456');
    await page.click('#changePasswordBtn');

    await expect.poll(() => posted, { timeout: 6000 }).toBeTruthy();
    expect(posted.current_password).toBe('oldpass123');
    expect(posted.new_password).toBe('newpass456');

    expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    await context.close();
  });
});
