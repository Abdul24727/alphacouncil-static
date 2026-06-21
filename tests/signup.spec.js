const { test, expect } = require('@playwright/test');

// Signup is protected by Cloudflare Turnstile, so automated registration is intentionally
// blocked — the former "register persists name+market" E2E (C2) can no longer run against
// prod and is verified manually. This guards that the CAPTCHA gate is actually enforced:
// a register with no valid token must be rejected (400 captcha), never created.
test.describe('C2 — signup is CAPTCHA-protected', () => {
  test('register without a Turnstile token is rejected', async ({ request }) => {
    const email = `qa-c2-${Date.now()}@example.com`;
    const reg = await request.post('/api/auth/register', {
      data: { email, password: 'testpassword123', first_name: 'Sami', last_name: 'AlKhouri', market: 'SA', preferred_language: 'en' },
    });
    expect(reg.status(), 'must not create an account without a captcha token').not.toBe(200);
    expect([400, 429], 'rejected (captcha 400, or 429 if IP rate-limited)').toContain(reg.status());
    if (reg.status() === 400) {
      const body = await reg.json().catch(() => ({}));
      expect(((body.detail || '') + ''), 'captcha rejection').toMatch(/captcha/i);
    }
  });
});
