// Link-integrity + nav-consistency regression. Live-site target.
const { test, expect } = require('@playwright/test');
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';
const get = async (request, p) => (await request.get(`${BASE}/${p}`)).text();

const KNOWN = [
  'about.html', 'alerts.html', 'contact.html', 'council-history.html', 'dashboard.html',
  'features.html', 'forgot-password.html', 'how-it-works.html', 'index.html', 'legal.html',
  'login.html', 'markets.html', 'markets-app.html', 'methodology.html', 'news.html', 'onboarding.html',
  'portfolio.html', 'pricing.html', 'reset-password.html', 'scenarios.html', 'settings.html',
  'signup.html', 'stock-detail.html',
];
const APP_PAGES = ['dashboard', 'portfolio', 'news', 'alerts', 'council-history', 'scenarios', 'settings', 'stock-detail', 'markets-app'];

// Every app page's top nav is consistent + correctly targeted (the old Watchlist->portfolio
// mislink is gone; the previously-orphaned Scenarios page is reachable from each).
test('app nav is consistent + correctly linked on every app page', async ({ request }) => {
  for (const p of APP_PAGES) {
    const html = await get(request, p + '.html');
    expect(html, `${p}: Scenarios nav link missing`).toMatch(/href="scenarios\.html"[^>]*>\s*Scenarios\s*<\/a>/);
    expect(html, `${p}: stale Watchlist->portfolio nav mislink present`).not.toMatch(/<a[^>]*href="portfolio\.html"[^>]*>\s*Watchlist\s*<\/a>/);
  }
});

// No internal .html link anywhere points to a page that does not exist.
test('no internal link targets a missing page', async ({ request }) => {
  const missing = [];
  for (const p of KNOWN) {
    const html = await get(request, p);
    const targets = new Set();
    for (const m of html.matchAll(/href="([^"]+)"/g)) targets.add(m[1]);
    for (const m of html.matchAll(/(?:window\.open|location\.href\s*=|location\.assign|location\.replace)\s*\(?\s*['"]([^'"]+\.html[^'"]*)['"]/g)) targets.add(m[1]);
    for (const raw of targets) {
      if (/^(https?:|mailto:|tel:|#|javascript:|data:)/i.test(raw)) continue;
      const path = raw.split('#')[0].split('?')[0].replace(/^\.?\//, '');
      if (!path || !path.endsWith('.html')) continue;
      if (!KNOWN.includes(path)) missing.push(`${p} -> ${raw}`);
    }
  }
  expect(missing, 'links to missing pages:\n' + missing.join('\n')).toEqual([]);
});

// markets.html has all 6 market section anchors the footer deep-links to.
test('markets.html has all market section anchors', async ({ request }) => {
  const html = await get(request, 'markets.html');
  for (const a of ['saudi', 'uae', 'qatar', 'kuwait', 'oman', 'bahrain']) {
    expect(html, `markets.html missing #${a} anchor`).toContain(`id="${a}"`);
  }
});
