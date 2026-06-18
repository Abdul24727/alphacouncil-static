// Shared Playwright helpers — diagnostics (console errors + failed requests + page
// errors) and programmatic auth. Used by every spec to enforce the constitution's
// "zero console errors, zero failed network requests" rule.
const fs = require('fs');

// URLs that don't count as failures (benign / third-party / expected-optional).
const ALLOW_URL = [/favicon\.ico/i];

function attachDiagnostics(page) {
  const consoleErrors = [];
  const failedRequests = [];
  const pageErrors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', (err) => pageErrors.push(String(err)));
  page.on('response', (res) => {
    const s = res.status();
    if (s >= 400 && !ALLOW_URL.some((re) => re.test(res.url()))) {
      failedRequests.push(s + ' ' + res.request().method() + ' ' + res.url());
    }
  });
  return { consoleErrors, failedRequests, pageErrors };
}

// Assert the page produced no console errors, no uncaught page errors, and no failed
// network requests. `extraAllow` is an array of RegExp to tolerate specific requests
// (e.g. a deliberately-unauthenticated probe in a signed-out test).
function assertClean(diag, expect, extraAllow = []) {
  const allow = (s) => extraAllow.some((re) => re.test(s));
  const fails = diag.failedRequests.filter((f) => !allow(f));
  // A deliberately-tested HTTP error (e.g. an invalid-token 400) makes Chromium log
  // "Failed to load resource: … 4xx" to the console — benign when the request itself
  // is in extraAllow, so filter those console lines the same way.
  const cerrs = diag.consoleErrors.filter((c) => !allow(c));
  expect(diag.pageErrors, 'uncaught page errors:\n' + diag.pageErrors.join('\n')).toEqual([]);
  expect(cerrs, 'console errors:\n' + cerrs.join('\n')).toEqual([]);
  expect(fails, 'failed network requests:\n' + fails.join('\n')).toEqual([]);
}

// Programmatic login on a browser context (sets the session cookie in the context's
// jar; subsequent page.goto in that context is authenticated). Avoids typing the
// password into the login form.
async function apiLogin(context, email, password) {
  const r = await context.request.post('/api/auth/login', { data: { email, password, remember: true } });
  if (!r.ok()) throw new Error('apiLogin failed: ' + r.status() + ' ' + (await r.text()));
  return r;
}

// Capture an evidence screenshot to test-results/screens/<name>.png.
async function shot(page, name) {
  const dir = 'test-results/screens';
  fs.mkdirSync(dir, { recursive: true });
  const path = `${dir}/${name}.png`;
  await page.screenshot({ path, fullPage: true });
  return path;
}

module.exports = { attachDiagnostics, assertClean, apiLogin, shot };
