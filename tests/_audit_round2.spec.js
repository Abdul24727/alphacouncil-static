// Round-2 audit: mobile/responsive overflow + AR/RTL rendering + per-page console
// health. Read-only. Writes test-results/_audit_round2.json + screenshots.
// Run: npx playwright test _audit_round2 --reporter=list
const { test } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');
const fs = require('fs');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

const PAGES = [
  { name: 'index', url: '/index.html', auth: false },
  { name: 'pricing', url: '/pricing.html', auth: false },
  { name: 'markets', url: '/markets.html', auth: false },
  { name: 'methodology', url: '/methodology.html', auth: false },
  { name: 'login', url: '/login.html', auth: false },
  { name: 'signup', url: '/signup.html', auth: false },
  { name: 'dashboard', url: '/dashboard.html', auth: true },
  { name: 'portfolio', url: '/portfolio.html', auth: true },
  { name: 'news', url: '/news.html', auth: true },
  { name: 'alerts', url: '/alerts.html', auth: true },
  { name: 'council-history', url: '/council-history.html', auth: true },
  { name: 'scenarios', url: '/scenarios.html', auth: true },
  { name: 'settings', url: '/settings.html', auth: true },
  { name: 'onboarding', url: '/onboarding.html', auth: true },
  { name: 'stock-detail', url: '/stock-detail.html?ticker=2222_TADAWUL', auth: true },
];

async function measure(page) {
  return await page.evaluate(() => ({
    sw: document.documentElement.scrollWidth,
    iw: window.innerWidth,
    dir: document.documentElement.getAttribute('dir') || 'ltr',
    lang: document.documentElement.getAttribute('lang') || 'en',
    hasArabic: /[؀-ۿ]/.test(document.body.innerText),
  }));
}

test('round2: mobile responsive overflow + console health', async ({ browser }) => {
  test.setTimeout(600000);
  const ctxA = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await apiLogin(ctxA, EMAIL, PASSWORD);
  const ctxN = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const report = [];
  for (const p of PAGES) {
    const ctx = p.auth ? ctxA : ctxN;
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    try { await page.goto(p.url, { waitUntil: 'networkidle', timeout: 40000 }); } catch {}
    await page.waitForTimeout(2000);
    const m = await measure(page);
    const overflow = m.sw - m.iw;
    await shot(page, `r2-mobile-${p.name}`);
    report.push({ name: p.name, mobileOverflowPx: overflow, cerr: diag.consoleErrors.length, netfail: diag.failedRequests.length, perr: diag.pageErrors.length });
    console.log(`[m ${p.name}] overflow=${overflow}px cerr=${diag.consoleErrors.length} netfail=${diag.failedRequests.length} perr=${diag.pageErrors.length}` + (diag.failedRequests.length ? ('  NET:' + diag.failedRequests.slice(0,4).join(' | ')) : '') + (diag.consoleErrors.length ? ('  CE:' + diag.consoleErrors.slice(0,3).join(' | ')) : ''));
    await page.close();
  }
  fs.writeFileSync('test-results/_audit_round2_mobile.json', JSON.stringify(report, null, 2));
  await ctxA.close(); await ctxN.close();
});

test('round2: AR/RTL rendering + console health (desktop)', async ({ browser }) => {
  test.setTimeout(600000);
  const ctxA = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await apiLogin(ctxA, EMAIL, PASSWORD);
  const ctxN = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const report = [];
  for (const p of PAGES) {
    const ctx = p.auth ? ctxA : ctxN;
    const page = await ctx.newPage();
    await page.addInitScript(() => { try { localStorage.setItem('ac.lang', 'ar'); } catch (e) {} });
    const diag = attachDiagnostics(page);
    try { await page.goto(p.url, { waitUntil: 'networkidle', timeout: 40000 }); } catch {}
    await page.waitForTimeout(2200);
    const m = await measure(page);
    await shot(page, `r2-ar-${p.name}`);
    report.push({ name: p.name, dir: m.dir, lang: m.lang, hasArabic: m.hasArabic, cerr: diag.consoleErrors.length, netfail: diag.failedRequests.length });
    console.log(`[ar ${p.name}] dir=${m.dir} lang=${m.lang} arabic=${m.hasArabic} cerr=${diag.consoleErrors.length} netfail=${diag.failedRequests.length}` + (diag.consoleErrors.length ? ('  CE:' + diag.consoleErrors.slice(0,3).join(' | ')) : ''));
    await page.close();
  }
  fs.writeFileSync('test-results/_audit_round2_ar.json', JSON.stringify(report, null, 2));
  await ctxA.close(); await ctxN.close();
});
