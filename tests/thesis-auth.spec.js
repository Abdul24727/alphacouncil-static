const { test, expect } = require('@playwright/test');

// N1 — POST /api/thesis/{key} generation (paid LLM ~60-200s) and the cache admin ops
// must not be open to anonymous traffic; cached reads stay public.
const BASE = 'https://alphacouncil.tech';

test.describe('N1 — thesis generation auth-gated (anon abuse blocked, cached reads public)', () => {
  test('anon: cached read public; force-generate + cache ops are 401', async ({ request }) => {
    // A plain read (no force_refresh) is served from cache to anyone — never 401.
    const cached = await request.post(`${BASE}/api/thesis/2222_TADAWUL`, { data: {} });
    expect([200, 404], 'cached read stays public (200 cached / 404 none) — not gated').toContain(cached.status());

    // Forcing a fresh (paid) generation requires a signed-in user.
    const gen = await request.post(`${BASE}/api/thesis/2222_TADAWUL`, { data: { force_refresh: true } });
    expect(gen.status(), 'anonymous generation must be blocked').toBe(401);

    // Cache invalidation + stats are admin-only.
    const del = await request.delete(`${BASE}/api/thesis/cache/2222_TADAWUL`);
    expect(del.status(), 'anonymous cache invalidation blocked').toBe(401);
    const stats = await request.get(`${BASE}/api/thesis/cache/stats`);
    expect(stats.status(), 'anonymous cache stats blocked').toBe(401);
  });
});
