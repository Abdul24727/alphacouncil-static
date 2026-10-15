// Phase 5 "Done when": every link in the sidebar opens a working page.
// Also walks user-testing task 1: sign up and add three stocks to My Portfolio.
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase5.mjs
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) failures.push(label);
};

async function settle(page) {
  // A working page: header rendered, no loading bars left, no error overlay.
  await page.locator("main h1, main header").first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(500);
}

for (const [label, viewport] of [["desktop", { width: 1440, height: 900 }], ["phone", { width: 390, height: 844 }]]) {
  const context = await browser.newContext({ viewport, httpCredentials, isMobile: label === "phone", hasTouch: label === "phone" });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text().split("\n")[0].slice(0, 160)));
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message.slice(0, 160)}`));
  await page.goto(`${BASE_URL}/home`);
  await settle(page);

  const nav = label === "desktop" ? 'aside[aria-label="Sidebar"] nav a, aside[aria-label="Sidebar"] a[href$="/settings"]' : 'nav[aria-label="Tabs"] a';
  const links = await page.locator(nav).evaluateAll((as) => as.map((a) => ({ href: a.getAttribute("href"), text: a.textContent?.trim() })));
  for (const { href, text } of links) {
    errors.length = 0;
    const scope = label === "desktop" ? 'aside[aria-label="Sidebar"]' : 'nav[aria-label="Tabs"]';
    await page.locator(`${scope} a[href="${href}"]`).first().click();
    await page.waitForURL((u) => u.pathname === href, { timeout: 30000 }).catch(() => {});
    await settle(page);
    const unavailable = await page.locator('main [data-panel]:visible :text("Data unavailable")').count();
    const panels = await page.locator("main [data-panel]:visible, main [data-signin-prompt]").count();
    const ok = new URL(page.url()).pathname === href && panels > 0 && errors.length === 0;
    check(ok, `${label}: ${text} (${href}) — ${panels} panel(s)${unavailable ? `, ${unavailable} labelled unavailable` : ""}${errors.length ? `, errors: ${errors.join(" | ")}` : ""}`);
  }
  await context.close();
}

// User-testing task 1: sign up, then add three stocks you own.
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, httpCredentials });
const page = await context.newPage();
const email = `check-${Date.now()}@example.com`;
await page.goto(`${BASE_URL}/signup?next=/portfolio`);
await page.getByLabel("Email").fill(email);
await page.getByLabel("Password").fill("a long test password");
await page.getByRole("button", { name: "Create account" }).click();
await page.waitForURL(/\/portfolio$/, { timeout: 30000 });
await page.locator("[data-add-holding]").waitFor();
await page.waitForLoadState("networkidle");
check(true, "sign-up lands on My Portfolio");
for (const [query, qty] of [["2222", "100"], ["1120", "50"], ["FAB", "200"]]) {
  await page.locator("[data-holding-ticker]").click();
  const picker = page.locator('[role="listbox"] [role="option"]');
  await page.locator('[role="dialog"] input[role="combobox"]').waitFor();
  await page.keyboard.type(query);
  await picker.first().waitFor();
  await page.keyboard.press("Enter");
  await page.locator("[data-holding-qty]").fill(qty);
  await page.getByRole("button", { name: "Add", exact: true }).click();
  await page.waitForTimeout(800);
}
const rows = await page.locator('[data-panel="portfolio.holdings"]:visible tbody tr').count();
check(rows === 3, `three holdings listed (${rows})`);
const exposure = await page.locator('[data-panel="portfolio.exposure"]:visible').innerText();
check(/SAR/.test(exposure) && /AED/.test(exposure), "exposure grouped per currency (SAR and AED)");
await context.close();

await browser.close();
if (failures.length) {
  console.log(`\n${failures.length} check(s) failed`);
  process.exit(1);
}
console.log("\nPhase 5 done-when: all checks passed");
