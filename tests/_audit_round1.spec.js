// Independent QA audit instrument (Round 1). Read-only: visits every page
// authenticated, captures console/network diagnostics, a full-page screenshot, and
// scans the RENDERED DOM for fabricated literals. Writes test-results/_audit_round1.json.
// Run explicitly:  npx playwright test _audit_round1 --reporter=list
const { test } = require('@playwright/test');
const { attachDiagnostics, apiLogin, shot } = require('./helpers');
const fs = require('fs');

const EMAIL = process.env.QA_EMAIL;
const PASSWORD = process.env.QA_PASSWORD;

// Fabricated literals that must NOT appear in rendered text on a real page.
const FAKE = [
  ['total_847250', /847,?250/],
  ['banking_32_2', /32\.2\s*%/],
  ['identity_saeed', /Saeed|Al-Khalidi/],
  ['greeting_sami', /(Good (morning|afternoon|evening)|Hello),?\s*Sami/],
  ['unrealized_38912', /38,?912/],
  ['shares_5470', /5,?470/],
  ['shares_320', /320 shares/],
  ['last_sync', /Last sync/i],
  ['live_gst', /Live\s*[·•].*GST/i],
  ['plus_8_4', /\+8\.4\s*%/],
  ['fab_canned', /McKinsey CSO|PIF stake 8\.2/i],
];

const PAGES = [
  // marketing / public
  { name: 'index', url: '/index.html', auth: false },
  { name: 'features', url: '/features.html', auth: false },
  { name: 'how-it-works', url: '/how-it-works.html', auth: false },
  { name: 'markets', url: '/markets.html', auth: false },
  { name: 'methodology', url: '/methodology.html', auth: false },
  { name: 'pricing', url: '/pricing.html', auth: false },
  { name: 'about', url: '/about.html', auth: false },
  { name: 'contact', url: '/contact.html', auth: false },
  { name: 'legal', url: '/legal.html', auth: false },
  { name: 'login', url: '/login.html', auth: false },
  { name: 'signup', url: '/signup.html', auth: false },
  { name: 'forgot-password', url: '/forgot-password.html', auth: false },
  { name: 'reset-password', url: '/reset-password.html', auth: false },
  // app (authed)
  { name: 'dashboard', url: '/dashboard.html', auth: true },
  { name: 'portfolio', url: '/portfolio.html', auth: true },
  { name: 'news', url: '/news.html', auth: true },
  { name: 'alerts', url: '/alerts.html', auth: true },
  { name: 'council-history', url: '/council-history.html', auth: true },
  { name: 'scenarios', url: '/scenarios.html', auth: true },
  { name: 'settings', url: '/settings.html', auth: true },
  { name: 'onboarding', url: '/onboarding.html', auth: true },
  // stock-detail variants
  { name: 'sd-2222-aramco', url: '/stock-detail.html?ticker=2222_TADAWUL', auth: true },
  { name: 'sd-EMAAR-aed', url: '/stock-detail.html?ticker=EMAAR_DFM', auth: true },
  { name: 'sd-1120-rajhi', url: '/stock-detail.html?ticker=1120_TADAWUL', auth: true },
  { name: 'sd-POLTRY-missing', url: '/stock-detail.html?ticker=POLTRY_BSE', auth: true },
  { name: 'sd-ABRAAJ-404fund', url: '/stock-detail.html?ticker=ABRAAJ_BSE', auth: true },
  { name: 'sd-ZZZZ-badticker', url: '/stock-detail.html?ticker=ZZZZ_TADAWUL', auth: true },
];

test('audit round 1: capture diagnostics + screenshots + fake-literal scan', async ({ browser }) => {
  test.setTimeout(600_000);
  const ctxAuth = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await apiLogin(ctxAuth, EMAIL, PASSWORD);
  const ctxAnon = await browser.newContext({ viewport: { width: 1440, height: 900 } });

  const report = [];
  for (const p of PAGES) {
    const ctx = p.auth ? ctxAuth : ctxAnon;
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    let gotoErr = null;
    try {
      await page.goto(p.url, { waitUntil: 'networkidle', timeout: 45_000 });
    } catch (e) { gotoErr = String(e).split('\n')[0]; }
    await page.waitForTimeout(2500); // let late XHR render
    let bodyText = '';
    try { bodyText = await page.evaluate(() => document.body.innerText); } catch {}
    const fakeHits = FAKE.filter(([, re]) => re.test(bodyText)).map(([k]) => k);
    // visible dead-ish anchors (href="#") with their text
    let deadLinks = [];
    try {
      deadLinks = await page.evaluate(() => {
        const out = [];
        document.querySelectorAll('a[href="#"], a[href=""], a:not([href])').forEach((a) => {
          const r = a.getBoundingClientRect();
          if (r.width > 0 && r.height > 0) out.push((a.innerText || a.getAttribute('aria-label') || '').trim().slice(0, 40));
        });
        return out.filter(Boolean);
      });
    } catch {}
    const shotPath = await shot(page, `r1-${p.name}`);
    report.push({
      name: p.name, url: p.url, auth: p.auth, gotoErr,
      consoleErrors: diag.consoleErrors, failedRequests: diag.failedRequests, pageErrors: diag.pageErrors,
      fakeHits, deadLinks, shot: shotPath,
    });
    // eslint-disable-next-line no-console
    console.log(`[${p.name}] fake=${JSON.stringify(fakeHits)} cerr=${diag.consoleErrors.length} netfail=${diag.failedRequests.length} perr=${diag.pageErrors.length} dead=${deadLinks.length}`);
    if (diag.failedRequests.length) console.log('   NETFAIL: ' + diag.failedRequests.slice(0, 8).join(' | '));
    if (diag.consoleErrors.length) console.log('   CERR: ' + diag.consoleErrors.slice(0, 8).join(' | '));
    if (diag.pageErrors.length) console.log('   PERR: ' + diag.pageErrors.slice(0, 5).join(' | '));
    await page.close();
  }
  fs.mkdirSync('test-results', { recursive: true });
  fs.writeFileSync('test-results/_audit_round1.json', JSON.stringify(report, null, 2));
  await ctxAuth.close(); await ctxAnon.close();
});
