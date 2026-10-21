// Billing open (BILLING_OPEN=true): Free locks Pro data, complimentary Pro unlocks it, and the
// checkout guards (signed in, email confirmed). With CHECKOUT_EMAIL/CHECKOUT_PASSWORD (a
// confirmed account on beta, Moyasar TEST keys), it also pays with Moyasar's published test
// cards: a declined card, then a paid one, and checks Pro and the saved card.
//
//   BASE_URL=http://localhost:3201 PRO_EMAIL=... PRO_PASSWORD=... node scripts/check-billing.mjs
//   (+ CHECKOUT_EMAIL=... CHECKOUT_PASSWORD=... for the payment part)
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3201";
const OUT = process.env.OUT ?? "../docs/screenshots/accounts-billing";
const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) failures.push(label);
};

async function context(width = 1440) {
  return browser.newContext({
    viewport: { width, height: width < 768 ? 844 : 900 },
    ...(width < 768 ? { isMobile: true, hasTouch: true } : {}),
  });
}

async function signIn(page, email, password) {
  await page.goto(`${BASE_URL}/login?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(email);
  await page.locator("input[type=password]:visible").fill(password);
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 });
}

async function lockedPanels(page, path) {
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle" });
  await page.locator("[data-panel]:visible").first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(1500);
  return page.locator("[data-panel]:visible [data-pro-locked]").count();
}

const plan = await (await (await context()).request.get(`${BASE_URL}/api/v1/billing/plan`)).json();
check(plan.billing_open === true, `billing is open on ${BASE_URL} (plan for a visitor: ${plan.plan})`);

// Signed out = Free.
{
  const ctx = await context();
  const page = await ctx.newPage();
  const overview = await lockedPanels(page, "/t/2222");
  check(overview >= 1, `signed out: council panel on the overview is locked (${overview} locked)`);
  check((await page.locator('[data-panel="overview.metrics"]:visible dl').count()) >= 1, "signed out: key metrics stay free");
  await page.screenshot({ path: `${OUT}/free-overview-en-1440.png` });
  const fin = await lockedPanels(page, "/t/2222/financials");
  check(fin >= 2, `signed out: financials are locked (${fin} panels)`);
  await page.screenshot({ path: `${OUT}/free-financials-en-1440.png` });
  await page.goto(`${BASE_URL}/checkout`, { waitUntil: "networkidle" });
  check((await page.getByRole("link", { name: "Sign in" }).count()) >= 1, "signed out: checkout asks to sign in first");
  await ctx.close();
}

// Arabic phone, signed out.
{
  const ctx = await context(390);
  const page = await ctx.newPage();
  const n = await lockedPanels(page, "/ar/t/2222/ownership");
  check(n >= 1, `Arabic, 390 px: ownership locked (${n})`);
  await page.screenshot({ path: `${OUT}/free-ownership-ar-390.png` });
  await ctx.close();
}

// A new Free account: the checkout asks to confirm the email first (test addresses get no email).
{
  const ctx = await context();
  const page = await ctx.newPage();
  await page.goto(`${BASE_URL}/signup?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(`billing-free-${Date.now()}@example.com`);
  await page.locator("input[type=password]:visible").fill("a long test password");
  await page.locator("input[type=checkbox]:visible").check();
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 });
  await page.goto(`${BASE_URL}/checkout`, { waitUntil: "networkidle" });
  const body = await page.locator("main").innerText();
  // Without Moyasar keys the checkout is closed, which it says before anything else.
  check(
    plan.checkout_open ? /Confirm your email address first/.test(body) : /Checkout is not open yet/.test(body),
    plan.checkout_open ? "Free account, email not confirmed: checkout asks to confirm it" : "no Moyasar keys: checkout says it is not open yet",
  );
  await page.goto(`${BASE_URL}/settings`, { waitUntil: "networkidle" });
  await page.locator("[data-billing]").waitFor();
  check((await page.locator("[data-plan=free]").count()) === 1, "Settings › Billing says Free");
  await page.screenshot({ path: `${OUT}/free-settings-en-1440.png` });
  await ctx.close();
}

// Complimentary Pro (python -m app.billing grant): everything unlocked, no card.
if (process.env.PRO_EMAIL) {
  const ctx = await context();
  const page = await ctx.newPage();
  await signIn(page, process.env.PRO_EMAIL, process.env.PRO_PASSWORD);
  check((await lockedPanels(page, "/t/2222")) === 0, "Pro: nothing locked on the overview");
  check((await lockedPanels(page, "/t/2222/financials")) === 0, "Pro: financials unlocked");
  await page.goto(`${BASE_URL}/settings`, { waitUntil: "networkidle" });
  await page.locator("[data-plan=pro]").waitFor({ timeout: 15000 });
  check(true, "Settings › Billing says Pro");
  await page.screenshot({ path: `${OUT}/pro-settings-en-1440.png` });
  await ctx.close();
}

// Paying with Moyasar's test cards (test keys only).
if (process.env.CHECKOUT_EMAIL) {
  const ctx = await context();
  const page = await ctx.newPage();
  await signIn(page, process.env.CHECKOUT_EMAIL, process.env.CHECKOUT_PASSWORD);
  const key = await (await ctx.request.post(`${BASE_URL}/api/v1/billing/checkout`, { data: { accept_terms: true }, headers: { Origin: BASE_URL } })).json();
  if (!String(key.publishable_key ?? "").startsWith("pk_test_")) {
    check(false, "the payment part runs only with Moyasar TEST keys");
  } else {
    // Moyasar returns the browser to the site's public address; through the tunnel that is beta's
    // password-gated host, so the return page is loaded from BASE_URL instead (same app).
    await page.route(/\/billing\/return/, (route) => {
      const url = new URL(route.request().url());
      if (url.origin === new URL(BASE_URL).origin) return route.continue();
      return route.fulfill({ status: 302, headers: { location: `${BASE_URL}${url.pathname}${url.search}` } });
    });
    for (const [card, outcome] of [["4123120001090000", "declined"], ["4111111111111111", "paid"]]) {
      await page.goto(`${BASE_URL}/checkout`, { waitUntil: "networkidle" });
      await page.locator("[data-checkout] input[type=checkbox]").check();
      await page.getByRole("button", { name: "Continue to payment" }).click();
      const form = page.locator("[data-moyasar-form]");
      await form.locator("input").first().waitFor({ timeout: 30000 });
      await page.screenshot({ path: `${OUT}/checkout-form-${outcome}-en-1440.png` });
      const pay = await form.locator("button[type=submit]").evaluate((b) => [getComputedStyle(b).backgroundColor, getComputedStyle(b).fontFamily.split(",")[0]]);
      check(pay[0] === "rgb(255, 106, 26)" && !/system-ui|ui-sans-serif/.test(pay[1]), `Moyasar's Pay button in the brand (${pay.join(", ")})`);
      // Typed key by key: Moyasar's form formats the number and the expiry as they are typed.
      await form.locator("#mysr-cc-name").pressSequentially("Test Card");
      await form.locator("#mysr-cc-number").pressSequentially(card);
      await form.locator("#mysr-cc-exp").pressSequentially("1230");
      await form.locator("#mysr-cc-csc").pressSequentially("123");
      await form.locator("button[type=submit]").click();
      // Test mode: Moyasar's 3-D Secure emulator stands in for the bank; "(Y)" approves.
      await page.waitForURL((u) => u.pathname.endsWith("/billing/return") || u.pathname.endsWith("/acs_emulator"), { timeout: 90000 });
      if (page.url().includes("/acs_emulator")) {
        const choice = page.locator("select");
        if (await choice.count()) await choice.first().selectOption({ label: await choice.first().locator("option", { hasText: "(Y)" }).first().innerText() });
        else await page.getByText("(Y) Authentication/Account Verification Successful").click();
        await page.locator("input[type=submit], button[type=submit]").first().click();
        await page.waitForURL((u) => u.pathname.endsWith("/billing/return"), { timeout: 90000 });
      }
      if (outcome === "paid") {
        await page.locator("[data-pro-started]").waitFor({ timeout: 60000 });
        check(true, "test card 4111…1111: paid, Pro started");
      } else {
        await page.getByRole("heading", { name: "Payment not completed" }).waitFor({ timeout: 60000 });
        check(true, `test card 4123…0000: declined (${(await page.locator("main p[role=alert]").innerText()).slice(0, 90)})`);
      }
      await page.screenshot({ path: `${OUT}/return-${outcome}-en-1440.png` });
    }
    const s = await (await ctx.request.get(`${BASE_URL}/api/v1/billing`)).json();
    check(s.plan === "pro" && s.renews && s.card_last4 === "1111", `Pro renews with the saved card (${s.card_brand} ${s.card_last4}, through ${s.paid_through})`);
  }
  await ctx.close();
}

await browser.close();
if (failures.length) {
  console.log(`\n${failures.length} check(s) failed`);
  process.exit(1);
}
console.log("\nBilling checks: all passed");
