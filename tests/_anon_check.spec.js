// One-off: what does an ANONYMOUS (logged-out) visitor see on the app pages?
// Checks for persisted fabricated data when no holdings load.
const { test } = require('@playwright/test');
const { attachDiagnostics, shot } = require('./helpers');
const PAGES = ['dashboard.html', 'portfolio.html'];
const FAKE = [['847250', /847,?250/], ['aramco_row', /Saudi Aramco|Al Rajhi Bank/], ['shares_5470', /5,?470/], ['banking_322', /32\.2\s*%/], ['greeting_sami', /(Good (morning|afternoon|evening)|Hello),?\s*Sami/]];
test('anon app pages: no persisted fabricated data', async ({ browser }) => {
  test.setTimeout(120000);
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  for (const p of PAGES) {
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/' + p, { waitUntil: 'networkidle', timeout: 40000 }).catch(() => {});
    await page.waitForTimeout(3000);
    const url = page.url();
    let body = ''; try { body = await page.evaluate(() => document.body.innerText); } catch {}
    const hits = FAKE.filter(([, re]) => re.test(body)).map(([k]) => k);
    await shot(page, 'anon-' + p.replace('.html', ''));
    console.log(`[anon ${p}] finalURL=${url} fake=${JSON.stringify(hits)} cerr=${diag.consoleErrors.length} netfail=${diag.failedRequests.length}`);
    await page.close();
  }
  await ctx.close();
});
