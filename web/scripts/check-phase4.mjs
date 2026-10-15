// Phase 4 "Done when": asking about the dividend with the metrics panel
// attached returns an answer whose citation scrolls to that panel.
// Also checks reasoning steps, follow-ups and pinning to My dashboards.
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase4.mjs
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, httpCredentials });
const page = await context.newPage();
const failures = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) failures.push(label);
};

const status = await (await context.request.get(`${BASE_URL}/api/v1/copilot/status`)).json();
console.log(`Copilot model: ${status.model}${status.stand_in ? " (stand-in, no AI key configured)" : ""}`);

// A real model answers signed-in users only.
if (status.sign_in_required) {
  await page.goto(`${BASE_URL}/signup?next=/home`);
  await page.getByLabel("Email").fill(`phase4-${Date.now()}@example.com`);
  await page.getByLabel("Password").fill("a long test password");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();
  await page.waitForURL((u) => u.pathname === "/home", { timeout: 30000 });
  check(true, "signed in (the model requires an account)");
}

await page.goto(`${BASE_URL}/t/2222`);
const metrics = page.locator('[data-panel="overview.metrics"]:visible');
await metrics.locator("dl").first().waitFor({ timeout: 30000 });

// Attach the metrics panel with its add-to-Copilot button.
await metrics.getByRole("button", { name: "Add to Copilot" }).click();
const chip = page.locator('[data-context-chip="overview.metrics"]');
check((await chip.count()) === 1, "metrics panel shows as a context chip");

// Ask about the dividend.
const composer = page.locator("[data-copilot-pane] textarea");
await composer.fill("Is the dividend safe?");
await composer.press("Enter");
const answer = page.locator('[data-copilot-pane] [data-message="assistant"]').last();
const citation = answer.locator('[data-citation="overview.metrics"]').first();
// User testing allows 3 minutes per task: the whole answer must finish within that.
const asked = Date.now();
await citation.waitFor({ timeout: 180000 });
check(true, "answer cites the metrics panel");
await page.waitForFunction(() => !document.querySelector('[data-copilot-pane] button[aria-label="Stop"]'), null, {
  timeout: Math.max(1000, 180000 - (Date.now() - asked)),
});
check(true, `answer finished in ${Math.round((Date.now() - asked) / 1000)} s (limit 180 s)`);

const summary = await answer.locator("summary").innerText().catch(() => "");
// The label is styled in caps, so compare without case.
check(/reasoning · \d+ step/i.test(summary), `reasoning is collapsible (${summary.replace(/\s+/g, " ").trim()})`);
const followUps = await answer.locator('[aria-label="Follow-up questions"] button').count();
check(followUps >= 2 && followUps <= 3, `${followUps} follow-up questions`);

// Scroll the work area so the panel is out of view, then click the citation.
await page.evaluate(() => {
  const scroller = [...document.querySelectorAll("main .overflow-y-auto")].find((e) => e.checkVisibility());
  if (scroller) scroller.scrollTop = scroller.scrollHeight;
});
await page.waitForTimeout(300);
const before = await metrics.boundingBox();
await citation.click();
await page.waitForTimeout(900);
const after = await metrics.boundingBox();
const flashed = await metrics.getAttribute("data-flash");
const inView = after && after.y >= 0 && after.y < 900;
check(Boolean(inView), `citation scrolled the metrics panel into view (top ${Math.round(before?.y ?? 0)} -> ${Math.round(after?.y ?? 0)})`);
check(flashed === "1", "the cited panel is highlighted");

// Pin the answer's table, if any, and find it on My dashboards.
const pin = answer.getByRole("button", { name: "Pin to dashboard" }).first();
if (await pin.count()) {
  await pin.click();
  await page.goto(`${BASE_URL}/dashboards`);
  await page.locator('[data-panel^="pinned."]').first().waitFor({ timeout: 20000 });
  check(true, "pinned table appears on My dashboards");
} else {
  console.log("note  this answer had no table to pin");
}

await browser.close();
if (failures.length) {
  console.log(`\n${failures.length} check(s) failed`);
  process.exit(1);
}
console.log(
  status.stand_in
    ? "\nPhase 4 mechanics pass with the stand-in. The done-when stays pending until a real AI model answers."
    : "\nPhase 4 done-when: all checks passed",
);
