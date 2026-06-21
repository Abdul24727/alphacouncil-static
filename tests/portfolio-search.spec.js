// Top-nav "Search stocks..." bar on portfolio.html + stock-detail.html — was dead
// (missing id="searchBtn" so adviser-core never wired it). Live-site functional regression.
const { test, expect } = require('@playwright/test');
const { attachDiagnostics, apiLogin } = require('./helpers');
const EMAIL = process.env.QA_EMAIL, PASSWORD = process.env.QA_PASSWORD;

test.describe('top-nav stock search bar', () => {
  test('portfolio: clicking the search bar opens a working stock search', async ({ browser }) => {
    const ctx = await browser.newContext();
    await apiLogin(ctx, EMAIL, PASSWORD);
    const page = await ctx.newPage();
    const diag = attachDiagnostics(page);
    await page.goto('/portfolio.html', { waitUntil: 'networkidle' });

    // the bar is wired (adviser-core gives it role=button on init)
    const bar = page.locator('#searchBtn');
    await expect(bar).toBeVisible();
    await expect(bar).toHaveAttribute('role', 'button');

    // clicking it opens the real search modal
    await bar.click();
    await expect(page.locator('#acSearchOverlay.open')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('#acSearchInput')).toBeFocused();

    // typing a real name returns real, ticker-keyed results
    await page.locator('#acSearchInput').fill('Rajhi');
    await expect(page.locator('#acSearchResults .ac-search-result').first()).toBeVisible({ timeout: 10000 });
    const firstKey = await page.locator('#acSearchResults .ac-search-result').first().getAttribute('data-ticker');
    expect(firstKey, 'result keyed on a real ticker_key').toMatch(/_/);

    // selecting a result navigates to that stock
    await page.locator('#acSearchResults .ac-search-result').first().click();
    await page.waitForURL(/stock-detail\.html\?ticker=/, { timeout: 8000 });
    expect(page.url()).toContain('stock-detail.html?ticker=');

    diag.consoleErrors = diag.consoleErrors.filter((c) => !/favicon/i.test(c));
    expect(diag.pageErrors, 'no uncaught errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
    expect(diag.consoleErrors, 'no console errors:\n' + diag.consoleErrors.join('\n')).toEqual([]);
    await ctx.close();
  });

  test('stock-detail: the search bar is wired + opens', async ({ browser }) => {
    const ctx = await browser.newContext();
    await apiLogin(ctx, EMAIL, PASSWORD);
    const page = await ctx.newPage();
    await page.goto('/stock-detail.html?ticker=1120_TADAWUL', { waitUntil: 'networkidle' });
    const bar = page.locator('#searchBtn');
    await expect(bar).toBeVisible();
    await expect(bar).toHaveAttribute('role', 'button');
    await bar.click();
    await expect(page.locator('#acSearchOverlay.open')).toBeVisible({ timeout: 8000 });
    await page.locator('#acSearchInput').fill('Aramco');
    await expect(page.locator('#acSearchResults .ac-search-result').first()).toBeVisible({ timeout: 10000 });
    await ctx.close();
  });
});
