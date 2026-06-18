const { test, expect } = require('@playwright/test');

test.describe('C2 — signup persists name + market (previously discarded)', () => {
  test('register with name+market → stored and returned by /auth/me', async ({ request }) => {
    const email = `qa-c2-${Date.now()}@alphacouncil.tech`;
    const reg = await request.post('/api/auth/register', {
      data: { email, password: 'testpassword123', first_name: 'Sami', last_name: 'AlKhouri', market: 'SA', preferred_language: 'en' },
    });
    expect(reg.ok(), 'register status ' + reg.status()).toBeTruthy();

    // register sets the session cookie on this request context → /auth/me is authed
    const meResp = await request.get('/api/auth/me');
    expect(meResp.ok(), 'me status ' + meResp.status()).toBeTruthy();
    const u = await meResp.json();
    expect(u.email).toBe(email);
    expect(u.first_name).toBe('Sami');
    expect(u.last_name).toBe('AlKhouri');
    expect(u.market).toBe('SA');
  });
});
