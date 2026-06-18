const { test, expect } = require('@playwright/test');
const { attachDiagnostics, assertClean, shot } = require('./helpers');

// Harness smoke test: the public landing page must load with no console errors and
// no failed network requests. Proves the diagnostics + screenshot plumbing works.
test('harness smoke: index.html loads clean', async ({ page }) => {
  const diag = attachDiagnostics(page);
  await page.goto('/index.html', { waitUntil: 'networkidle' });
  await expect(page.locator('text=AlphaCouncil').first()).toBeVisible();
  await shot(page, 'smoke-index');
  assertClean(diag, expect);
});
