// Dedicated config for the offline acceptance-UI review run (assertions + screenshot export).
// Runs ONLY the two review specs against local file:// pages with stubbed APIs — no live site,
// no backend, no production data. Used by: npx playwright test -c playwright.review.config.js
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  testMatch: ['acceptance-ui.spec.js', 'screenshots.spec.js'],
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: {
    headless: true,
    screenshot: 'off',
    trace: 'off',
  },
  projects: [{ name: 'chromium', use: {} }],
});
