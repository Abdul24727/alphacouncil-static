const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, apiLogin, shot } = require('./helpers');

const QA_EMAIL = process.env.QA_EMAIL;
const QA_PASSWORD = process.env.QA_PASSWORD;
const APP_PAGES = ['dashboard.html', 'portfolio.html', 'news.html', 'alerts.html',
  'stock-detail.html', 'settings.html', 'scenarios.html', 'council-history.html'];

test.describe('B1 — real nav identity', () => {
  test.skip(!QA_EMAIL || !QA_PASSWORD, 'QA creds not set in .env.test');

  test('top-bar avatar shows the real user initials, not "SK"', async ({ browser }) => {
    const context = await browser.newContext();
    await apiLogin(context, QA_EMAIL, QA_PASSWORD);
    const page = await context.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
    const menu = page.locator('#userMenu');
    await expect(menu).toHaveText('QP');                 // qa-playwright → QP
    await expect(menu).toHaveAttribute('aria-label', /qa-playwright@/);
    await shot(page, 'b1-nav-identity');
    assertClean(diag, expect);
    await context.close();
  });

  test('no fake "SK"/"Sami" identity literals are served on any app page', async ({ request }) => {
    for (const p of APP_PAGES) {
      const html = await (await request.get('/' + p)).text();
      expect(html, `${p} :: "User menu for Sami"`).not.toContain('User menu for Sami');
      expect(html, `${p} :: ">SK</button>"`).not.toContain('>SK</button>');
      expect(html, `${p} :: "Notifications, N unread"`).not.toMatch(/Notifications, \d+ unread/);
    }
  });
});
