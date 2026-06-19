const { test, expect } = require('@playwright/test');

// N2 — /api/evidence/search 503'd on prod because the router's DB-path candidates
// missed the web host's CWD-relative portfolio_inputs/evidence.sqlite. Fixed → real FTS hits.
const BASE = 'https://alphacouncil.tech';

test.describe('N2 — evidence FTS search returns real results (was 503)', () => {
  test('GET /api/evidence/search → 200 with real hits (no 503); stats → 200', async ({ request }) => {
    const res = await request.get(`${BASE}/api/evidence/search?q=debt`);
    expect(res.status(), 'evidence search no longer 503').toBe(200);
    const body = await res.json();
    expect(Array.isArray(body.results), 'results array present').toBeTruthy();
    expect(body.results.length, 'real FTS hits returned').toBeGreaterThan(0);
    expect(body.results[0], 'hit carries a ticker_key').toHaveProperty('ticker_key');

    const stats = await request.get(`${BASE}/api/evidence/stats`);
    expect(stats.status(), 'evidence stats no longer 503').toBe(200);
  });
});
