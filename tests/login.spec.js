const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, shot } = require('./helpers');

test.describe('C3 — login: dead 2FA removed', () => {
  test('login page loads clean; the fake-2FA UI is gone', async ({ page }) => {
    const diag = attachDiagnostics(page);
    await page.goto('/login.html', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('#loginForm')).toBeVisible();
    await expect(page.locator('#step-2fa')).toHaveCount(0);
    await expect(page.locator('#twofaForm')).toHaveCount(0);
    await shot(page, 'c3-login');
    assertClean(diag, expect);
  });

  test('served login.html has no fake-2FA code + real footer links', async ({ request }) => {
    const html = await (await request.get('/login.html')).text();
    for (const s of ['twofaForm', 'useBackupCode', 'code-input', 'Two-factor authentication']) {
      expect(html, 'login.html still contains: ' + s).not.toContain(s);
    }
    expect(html).toContain('legal.html#privacy');   // dead footer href="#" replaced
    expect(html).toContain('contact.html');
  });
});
