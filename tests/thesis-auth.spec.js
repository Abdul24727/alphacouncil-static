const { test, expect } = require('@playwright/test');

// N1 — POST /api/thesis/{key} generation (paid LLM ~60-200s) and the cache admin ops
// must not be open to anonymous traffic. NOTE: cached reads are keyed on (model,
// as_of_date); as_of_date rolls forward with each nightly data refresh, so a
// pre-generated thesis goes stale and an anonymous empty-body read becomes a cache
// MISS → 401 (generation is gated). That is by design, so this test asserts the real
// security invariant rather than assuming 2222 is always cache-warm.
const BASE = process.env.BASE_URL || 'https://alphacouncil.tech';

test.describe('N1 — thesis generation auth-gated (anon abuse blocked)', () => {
  test('anon: empty-body read never triggers generation; force-gen + cache ops are 401', async ({ request }) => {
    // A plain (no force_refresh) anon read is served from cache when warm (200),
    // gated when the cache is cold (401), or 404 if the ticker is unknown — but it
    // must NEVER run a paid generation (no 5xx, no long hang) and never 500.
    const cached = await request.post(`${BASE}/api/thesis/2222_TADAWUL`, { data: {} });
    expect([200, 401, 404], `unexpected status ${cached.status()}`).toContain(cached.status());
    if (cached.status() === 200) {
      const j = await cached.json();
      // a real cached thesis, not a fabricated stub
      expect(j.thesis || j.scores, 'a 200 read must return a real cached thesis').toBeTruthy();
    }

    // Forcing a fresh (paid) generation always requires a signed-in user.
    const gen = await request.post(`${BASE}/api/thesis/2222_TADAWUL`, { data: { force_refresh: true } });
    expect(gen.status(), 'anonymous generation must be blocked').toBe(401);

    // Cache invalidation + stats are admin-only.
    const del = await request.delete(`${BASE}/api/thesis/cache/2222_TADAWUL`);
    expect(del.status(), 'anonymous cache invalidation blocked').toBe(401);
    const stats = await request.get(`${BASE}/api/thesis/cache/stats`);
    expect(stats.status(), 'anonymous cache stats blocked').toBe(401);
  });
});
