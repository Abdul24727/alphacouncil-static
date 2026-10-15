// Screenshots at 1440px and 390px for the phase done-list (CLAUDE.md standing rules).
//
//   node scripts/screenshots.mjs phase-2            # dev server on BASE_URL (default :3100)
//   BASE_URL=https://beta.alphacouncil.tech STAGING_AUTH=user:pass node scripts/screenshots.mjs staging
//
// Uses the locally installed Chrome through playwright-core; nothing is downloaded.
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const phase = process.argv[2] ?? "latest";
const outDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../docs/screenshots", phase);

const WIDTHS = { desktop: { width: 1440, height: 900 }, phone: { width: 390, height: 844 } };

const openSearch = (query) => async (page) => {
  await page.keyboard.press("Control+k");
  await page.keyboard.type(query);
  await page.getByRole("option").first().waitFor();
};

const waitForPanels = async (page) => {
  await page.locator("[data-panel]:visible").first().waitFor();
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 20000 });
};

// [file name, path, optional interaction]
const SHOTS = {
  "phase-1": [
    ["home", "/home"],
    ["home-ar", "/ar/home"],
    ["search-aramco", "/home", openSearch("aramco")],
    ["search-ar", "/ar/home", openSearch("الراجحي")],
  ],
  "phase-2": [
    ["overview-2222", "/t/2222", waitForPanels],
    ["overview-1120-ar", "/ar/t/1120", waitForPanels],
    ["financials-emaar", "/t/EMAAR_DFM/financials", waitForPanels],
    ["council-2222", "/t/2222/council", waitForPanels],
    ["ownership-2222", "/t/2222/ownership", waitForPanels],
    ["calendar-2222", "/t/2222/calendar", waitForPanels],
    [
      "stale-tooltip",
      "/t/2222",
      async (page) => {
        await waitForPanels(page);
        await page.locator('[data-freshness="stale"]:visible').first().hover();
        await page.getByText(/Updated .* · next /).waitFor();
      },
    ],
  ],
};
SHOTS.latest = Object.values(SHOTS).flat();
SHOTS.staging = SHOTS.latest;

const shots = SHOTS[phase] ?? SHOTS.latest;
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });

for (const [label, viewport] of Object.entries(WIDTHS)) {
  for (const [name, route, act] of shots) {
    // Fresh context per shot: no locale cookie or saved pane sizes carry over.
    const context = await browser.newContext({
      viewport,
      deviceScaleFactor: 1,
      isMobile: label === "phone",
      hasTouch: label === "phone",
      httpCredentials,
    });
    const page = await context.newPage();
    await page.goto(BASE_URL + route, { waitUntil: "domcontentloaded" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(400);
    if (act) await act(page);
    const file = path.join(outDir, `${name}-${viewport.width}.png`);
    await page.screenshot({ path: file, fullPage: label === "phone" && !act?.name?.startsWith("open") });
    console.log(path.relative(process.cwd(), file));
    await context.close();
  }
}

await browser.close();
