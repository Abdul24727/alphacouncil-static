// @ts-check
const { defineConfig, devices } = require('@playwright/test');
require('dotenv').config({ path: '.env.test' }); // QA creds + BASE_URL (gitignored); absent is fine

module.exports = defineConfig({
  testDir: './tests',
  // The _audit_* specs are slow read-only AUDIT INSTRUMENTS (screenshot every page,
  // mobile + RTL sweeps), not pass/fail regressions — exclude them from the default
  // run for a fast, deterministic suite. Run explicitly: `npx playwright test _audit_round1`.
  testIgnore: ['**/_audit_round1.spec.js', '**/_audit_round2.spec.js'],
  fullyParallel: false,   // tests share one QA account's holdings/watchlist state
  workers: 1,             // → run serially for deterministic live-site state
  retries: 1,             // live backend can transiently 502/timeout under load; one retry absorbs hiccups (not logic failures)
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'https://alphacouncil.tech',
    headless: true,
    viewport: { width: 1440, height: 900 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
