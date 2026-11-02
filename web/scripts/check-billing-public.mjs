// Billing open on a live site, checked signed out only: no account is made and nothing is paid
// (Claude makes no accounts on production, 2026-10-23). The signed-in half — the live card form,
// a real payment and its refund — is the owner's (PROJECT.md Step 18).
//
//   BASE_URL=https://alphacouncil.tech node scripts/check-billing-public.mjs
//   (OUT=../docs/screenshots/billing-open-<date> to choose the folder)
import { mkdir } from "node:fs/promises";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "https://alphacouncil.tech";
const OUT = process.env.OUT ?? "../docs/screenshots/billing-open";
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) failures.push(label);
};
const info = (label) => console.log(`INFO  ${label}`);

async function context(width = 1440) {
  return browser.newContext({
    viewport: { width, height: width < 768 ? 844 : 900 },
    ...(width < 768 ? { isMobile: true, hasTouch: true } : {}),
  });
}

async function lockedPanels(page, path) {
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle" });
  await page.locator("[data-panel]:visible").first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(1500);
  return page.locator("[data-panel]:visible [data-pro-locked]").count();
}

const api = await (await context()).request;
const plans = await (await api.get(`${BASE_URL}/api/v1/plans`)).json();
check(plans.checkout_open === true, `/api/v1/plans: checkout_open=${plans.checkout_open}`);
const plan = await (await api.get(`${BASE_URL}/api/v1/billing/plan`)).json();
check(plan.billing_open === true && plan.plan === "free", `a visitor is on Free with billing open (plan ${plan.plan}, billing_open ${plan.billing_open}, pro_only ${plan.pro_only?.join(",")})`);

// /pricing: a buy link, no early-access note, no sideways scroll — both languages, both widths.
for (const locale of ["en", "ar"]) {
  for (const width of [1440, 390]) {
    const ctx = await context(width);
    const page = await ctx.newPage();
    const res = await page.goto(`${BASE_URL}${locale === "ar" ? "/ar" : ""}/pricing`, { waitUntil: "networkidle" });
    const text = await page.locator("main").innerText();
    const buy = await page.locator('main a[href*="checkout"]:visible, main button:visible:has-text("Get Pro")').count();
    const early = /early access|not open yet|الوصول المبكر|غير مفتوح/i.test(text);
    const scroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    const label = buy ? (await page.locator('main a[href*="checkout"]:visible, main button:visible:has-text("Get Pro")').first().innerText()).trim() : "";
    check(res.status() === 200 && buy >= 1 && !early && !scroll, `/pricing ${locale} ${width}: ${res.status()}, buy control ${buy} ("${label}"), early-access note ${early}, sideways scroll ${scroll}`);
    await page.screenshot({ path: `${OUT}/pricing-${locale}-${width}.png`, fullPage: true });
    await ctx.close();
  }
}

// Signed out = Free: Pro panels locked, free metrics still shown.
{
  const ctx = await context();
  const page = await ctx.newPage();
  const overview = await lockedPanels(page, "/t/2222");
  check(overview >= 1, `signed out EN 1440: overview has Pro panels locked (${overview})`);
  check((await page.locator('[data-panel="overview.metrics"]:visible dl').count()) >= 1, "signed out EN 1440: key metrics stay free");
  await page.screenshot({ path: `${OUT}/free-overview-en-1440.png` });
  const fin = await lockedPanels(page, "/t/2222/financials");
  check(fin >= 2, `signed out EN 1440: financials locked (${fin} panels)`);
  await page.screenshot({ path: `${OUT}/free-financials-en-1440.png` });
  await page.goto(`${BASE_URL}/t/2222/advisors`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  info(`signed out EN 1440: advisors page answered, Pro locks on it ${await page.locator("[data-pro-locked]:visible").count()}`);
  await page.screenshot({ path: `${OUT}/free-advisors-en-1440.png` });
  await page.goto(`${BASE_URL}/checkout`, { waitUntil: "networkidle" });
  check((await page.getByRole("link", { name: "Sign in" }).count()) >= 1, "signed out: /checkout asks to sign in first");
  await page.screenshot({ path: `${OUT}/checkout-signed-out-en-1440.png` });
  await ctx.close();
}
{
  const ctx = await context(390);
  const page = await ctx.newPage();
  const n = await lockedPanels(page, "/ar/t/2222/ownership");
  check(n >= 1, `signed out AR 390: ownership locked (${n})`);
  await page.screenshot({ path: `${OUT}/free-ownership-ar-390.png` });
  await ctx.close();
}

await browser.close();
console.log(failures.length ? `\nBilling (public) checks: ${failures.length} FAILED` : "\nBilling (public) checks: all passed");
process.exit(failures.length ? 1 : 0);
