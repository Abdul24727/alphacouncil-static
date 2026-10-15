// Screenshots at 1440px and 390px for the phase done-list (CLAUDE.md standing rules).
//
//   node scripts/screenshots.mjs phase-1            # dev server on BASE_URL (default :3100)
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

// [file name, path, optional interaction]
const SHOTS = [
  ["home", "/home"],
  ["home-ar", "/ar/home"],
  ["stock-1120", "/t/1120"],
  [
    "search-aramco",
    "/home",
    async (page) => {
      await page.keyboard.press("Control+k");
      await page.keyboard.type("aramco");
      await page.getByRole("option").first().waitFor();
    },
  ],
  [
    "search-ar",
    "/ar/home",
    async (page) => {
      await page.keyboard.press("Control+k");
      await page.keyboard.type("الراجحي");
      await page.getByRole("option").first().waitFor();
    },
  ],
];

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });

for (const [label, viewport] of Object.entries(WIDTHS)) {
  for (const [name, route, act] of SHOTS) {
    // Fresh context per shot: no locale cookie or saved pane sizes carry over.
    const context = await browser.newContext({
      viewport,
      deviceScaleFactor: 1,
      isMobile: label === "phone",
      hasTouch: label === "phone",
    });
    const page = await context.newPage();
    await page.goto(BASE_URL + route, { waitUntil: "domcontentloaded" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(400);
    if (act) await act(page);
    const file = path.join(outDir, `${name}-${viewport.width}.png`);
    await page.screenshot({ path: file });
    console.log(path.relative(process.cwd(), file));
    await context.close();
  }
}

await browser.close();
