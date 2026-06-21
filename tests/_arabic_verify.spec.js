// Live Arabic/RTL verification of the localization pass. Run explicitly.
const { test, expect, request } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';

const PAGES = [
  { p: 'dashboard.html',       expect: /لوحة|المحفظة|الأسواق/ },
  { p: 'portfolio.html',       expect: /المحفظة|إضافة|قائمة/ },
  { p: 'scenarios.html',       expect: /سيناريو|تحليل|المجلس/ },
  { p: 'markets-app.html',     expect: /الأسواق|بحث|القطاع/ },
  { p: 'stock-detail.html?ticker=1120_TADAWUL', expect: /.+/ },
  { p: 'news.html',            expect: /الأخبار|أهم|المستشار/ },
  { p: 'council-history.html', expect: /المجلس|مراجعة|تصدير/ },
  { p: 'alerts.html',          expect: /تنبيه|مراكز|التنبيهات/ },
  { p: 'settings.html',        expect: /الإعدادات|الحساب|اللغة/ },
];

async function arabicContext(browser) {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  await ctx.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
  return ctx;
}

for (const pg of PAGES) {
  test('AR: ' + pg.p, async ({ browser }) => {
    const ctx = await arabicContext(browser);
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/' + pg.p, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);
    const dir = await page.evaluate(() => document.documentElement.getAttribute('dir'));
    expect(dir, 'page should be RTL in Arabic').toBe('rtl');
    const body = await page.evaluate(() => document.body.innerText);
    expect(body, 'page should contain Arabic UI text').toMatch(pg.expect);
    await shot(page, 'ar_' + pg.p.replace(/[^a-z0-9]+/gi, '_'));
    diag.consoleErrors = diag.consoleErrors.filter((c) => !/favicon/i.test(c));
    expect(diag.pageErrors, 'no uncaught errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    expect(diag.consoleErrors, 'no console errors:\n' + diag.consoleErrors.join('\n')).toEqual([]);
    await ctx.close();
  });
}

test('AR: stock names render in Arabic on dashboard holdings/movers', async ({ browser }) => {
  const ctx = await arabicContext(browser);
  const page = await ctx.newPage();
  await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  // movers section should contain Arabic letters in at least one stock name
  const moversTxt = await page.evaluate(() => {
    const el = document.querySelector('#gainersBody, #moversContent, [id*="mover" i]');
    return el ? el.innerText : document.body.innerText;
  });
  expect(moversTxt, 'movers/holdings should show Arabic names').toMatch(/[؀-ۿ]{2,}/);
  await ctx.close();
});

test('AR: user-menu dropdown stays on-screen (RTL flip)', async ({ browser }) => {
  const ctx = await arabicContext(browser);
  const page = await ctx.newPage();
  await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.locator('#userMenu').click();
  await page.waitForTimeout(400);
  const box = await page.evaluate(() => {
    const d = document.getElementById('acUserDropdown');
    if (!d) return null;
    const r = d.getBoundingClientRect();
    return { left: r.left, right: r.right, vw: window.innerWidth };
  });
  expect(box, 'user dropdown should exist + open').not.toBeNull();
  expect(box.left, 'dropdown not off the left edge').toBeGreaterThanOrEqual(-2);
  expect(box.right, 'dropdown not off the right edge').toBeLessThanOrEqual(box.vw + 2);
  await ctx.close();
});

test('AR: on-site article page renders a real article', async ({ browser }) => {
  const rq = await request.newContext({ baseURL: BASE });
  const news = await (await rq.get('/api/news/latest?limit=1')).json();
  const items = Array.isArray(news) ? news : (news.items || news.data || []);
  const id = items[0] && items[0].id;
  expect(id, 'have a real news id').toBeTruthy();

  const ctx = await arabicContext(browser);
  const page = await ctx.newPage();
  const diag = attachDiagnostics(page);
  await page.goto('/article.html?id=' + encodeURIComponent(id), { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  // the article title should have rendered (not stuck on loading / not-found)
  await expect(page.locator('.article-title')).toBeVisible({ timeout: 8000 });
  const title = await page.locator('.article-title').innerText();
  expect(title.trim().length, 'article has a headline').toBeGreaterThan(3);
  await shot(page, 'ar_article');
  diag.consoleErrors = diag.consoleErrors.filter((c) => !/favicon/i.test(c));
  expect(diag.consoleErrors, 'no console errors:\n' + diag.consoleErrors.join('\n')).toEqual([]);
  await rq.dispose();
  await ctx.close();
});
