// Agentic adviser: the chat performs real site actions. Live-site. Run explicitly.
const { test, expect } = require('@playwright/test');
const { apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

async function ctxPage(browser) {
  const ctx = await browser.newContext();
  await apiLogin(ctx, EMAIL, PASSWORD);
  const page = await ctx.newPage();
  await page.goto('/dashboard.html', { waitUntil: 'networkidle' });
  await page.locator('#adviserToggle').click();
  await expect(page.locator('#adviserSidebar')).toHaveClass(/open/);
  return { ctx, page };
}
async function send(page, msg, wait = 2500) {
  const inp = page.locator('#chatInput');
  await inp.click();
  await inp.fill(msg);
  await inp.press('Enter');
  await page.waitForTimeout(wait);
}
function lastAdviser(page) {
  return page.locator('#chatMessages .chat-message.adviser .chat-bubble').last();
}

test('agentic: help lists capabilities', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  await send(page, 'what can you do?');
  await expect(lastAdviser(page)).toContainText(/watchlist|portfolio|council|price/i);
  await ctx.close();
});

test('agentic: price quote returns a number', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  await send(page, 'what is the price of Al Rajhi', 4000); // first cmd loads the universe
  await expect(lastAdviser(page)).toContainText(/\d/);
  await ctx.close();
});

test('agentic: navigation command changes page', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  await send(page, 'open my portfolio', 1500);
  await page.waitForURL(/portfolio\.html/, { timeout: 6000 });
  expect(page.url()).toContain('portfolio.html');
  await ctx.close();
});

test('agentic: watchlist add then remove (real writes)', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  await send(page, 'add Aramco to my watchlist', 4000);
  await expect(lastAdviser(page)).toContainText(/watchlist|متابعة/i);
  await send(page, 'remove Aramco from my watchlist', 3000); // cleanup
  await expect(lastAdviser(page)).toContainText(/removed|أزال|متابعت/i);
  await ctx.close();
});

test('agentic: destructive sell asks for confirmation (no auto-remove)', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  await send(page, 'sell Aramco', 4000);
  // a confirm button wired to AlphaCouncil.confirmAction must appear; we do NOT click it
  await expect(page.locator('#chatMessages button[onclick*="confirmAction"]')).toBeVisible();
  await ctx.close();
});

test('agentic: a real question is NOT hijacked (falls through to the adviser)', async ({ browser }) => {
  const { ctx, page } = await ctxPage(browser);
  // stub the LLM so we don't spend the 10/day adviser quota — we only assert routing.
  await page.route('**/api/adviser/ask', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ answer: 'STUB', disclaimer: 'x' }) }));
  // "should I sell Aramco?" must NOT trigger a sell-confirm; it should go to the LLM.
  await send(page, 'should I sell Aramco?', 2000);
  await expect(page.locator('#chatMessages button[onclick*="confirmAction"]')).toHaveCount(0);
  expect(page.url()).toContain('dashboard.html'); // didn't navigate away either
  await ctx.close();
});
