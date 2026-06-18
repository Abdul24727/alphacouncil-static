// @ts-check
const { defineConfig, devices } = require('@playwright/test');
require('dotenv').config({ path: '.env.test' }); // QA creds + BASE_URL (gitignored); absent is fine

module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: false,   // tests share one QA account's holdings/watchlist state
  workers: 1,             // → run serially for deterministic live-site state
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
