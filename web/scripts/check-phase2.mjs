// Phase 2 "Done when": switching 2222 to 1120 in one panel updates every panel,
// and a stale panel shows amber with its real timestamp.
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase2.mjs
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  ...(process.env.STAGING_AUTH ? { httpCredentials: parseAuth(process.env.STAGING_AUTH) } : {}),
});
const page = await context.newPage();
const failures = [];
const check = (ok, label) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}`);
  if (!ok) failures.push(label);
};

function parseAuth(s) {
  const i = s.indexOf(":");
  return { username: s.slice(0, i), password: s.slice(i + 1) };
}

// Next keeps the previous route mounted but hidden (React Activity), so only count visible panels.
const switchers = () => page.locator("[data-ticker-switcher]:visible").allInnerTexts();
const waitForPanels = async (symbol) => {
  await page.waitForFunction(
    (sym) => {
      const chips = [...document.querySelectorAll("[data-ticker-switcher]")].filter((c) => c.checkVisibility());
      return chips.length >= 5 && chips.every((c) => c.textContent?.includes(sym));
    },
    symbol,
    { timeout: 20000 },
  );
  await page.locator('[data-panel="overview.metrics"]:visible dl').first().waitFor({ timeout: 20000 });
};

await page.goto(`${BASE_URL}/t/2222`);
await waitForPanels("2222");
const before = await switchers();
check(before.length >= 5 && before.every((s) => s.includes("2222")), `all ${before.length} panels start on 2222`);
const nameBefore = await page.locator("h1").first().innerText();

// Switch in ONE panel (the peers panel's ticker switcher).
await page.locator('[data-panel="overview.peers"]:visible [data-ticker-switcher]').click();
await page.keyboard.type("1120");
await page.getByRole("option").first().waitFor();
await page.keyboard.press("Enter");
await page.waitForURL(/\/t\/1120$/, { timeout: 20000 });
await waitForPanels("1120");
const after = await switchers();
check(after.every((s) => s.includes("1120")), `after switching one panel, all ${after.length} panels show 1120`);
const nameAfter = await page.locator("h1").first().innerText();
check(nameAfter !== nameBefore && /Rajhi|الراجحي/.test(nameAfter), `header follows the group (${nameAfter})`);
const metricsText = await page.locator('[data-panel="overview.metrics"]:visible').innerText();
check(!metricsText.includes("Data unavailable"), "metrics panel loaded 1120 data");

// A peers row click also moves the whole group.
const peer = page.locator('[data-panel="overview.peers"]:visible tr[data-peer]').first();
const peerSlug = await peer.getAttribute("data-peer");
await peer.click();
await page.waitForURL(new RegExp(`/t/${peerSlug}$`), { timeout: 20000 });
await waitForPanels(peerSlug);
check(true, `peers row click moved every panel to ${peerSlug}`);

// Stale panel: amber light with the real timestamp in its tooltip.
await page.goto(`${BASE_URL}/t/2222`);
await waitForPanels("2222");
const light = page.locator('[data-panel="overview.metrics"]:visible [data-freshness]');
const state = await light.getAttribute("data-freshness");
const color = await light.evaluate((el) => getComputedStyle(el).backgroundColor);
check(state === "stale" || state === "fresh", `metrics panel has a freshness light (${state})`);
const stalePanel = page.locator('[data-freshness="stale"]:visible').first();
await stalePanel.hover();
const tip = page.getByText(/Updated .* · next /);
await tip.waitFor({ timeout: 5000 });
const tipText = await tip.innerText();
const staleColor = await stalePanel.evaluate((el) => getComputedStyle(el).backgroundColor);
check(staleColor === "rgb(242, 177, 52)", `stale light is amber #F2B134 (${staleColor})`);
check(/Updated \d{1,2} \w{3}( \d{4})? \d{2}:\d{2} · next/.test(tipText), `tooltip shows the real timestamp: "${tipText}"`);
console.log(`metrics light colour: ${color}`);

await browser.close();
if (failures.length) {
  console.log(`\n${failures.length} check(s) failed`);
  process.exit(1);
}
console.log("\nPhase 2 done-when: all checks passed");
