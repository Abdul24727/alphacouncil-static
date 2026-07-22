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
  // Serve the static site over HTTP so relative fetch('/api/...') calls are real network
  // requests that page.route can intercept (a file:// origin blocks fetch to file:// URLs).
  webServer: {
    command: 'python3 -m http.server 8199 --bind 127.0.0.1',
    url: 'http://127.0.0.1:8199/signup.html',
    cwd: __dirname,
    reuseExistingServer: true,
    timeout: 30_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:8199',
    headless: true,
    screenshot: 'off',
    trace: 'off',
  },
  projects: [{ name: 'chromium', use: {} }],
});
