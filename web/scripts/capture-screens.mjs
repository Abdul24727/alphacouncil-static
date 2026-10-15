// Real screens of the app for the landing page and /templates (src/assets/screens/).
//
//   node scripts/capture-screens.mjs        # API + web dev servers running (BASE_URL, default :3100)
//
// Every number in these images comes from our database on the day they are taken; re-run
// after a data refresh or a UI change and commit the new files. Uses the local Chrome.
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const outDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../src/assets/screens");

const DESKTOP = { width: 1440, height: 900 };
const PHONE = { width: 390, height: 844 };

const QUESTION = { en: "Is Aramco's dividend safe?", ar: "هل توزيعات أرامكو آمنة؟" };
const CLOSE_COPILOT = { en: "Close Copilot", ar: "إغلاق المساعد" };

async function settle(page) {
  await page.locator("[data-panel]:visible").first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 });
  await page.waitForTimeout(1200); // charts draw on the next frames
}

const askCopilot = (locale) => async (page) => {
  await settle(page);
  const box = page.locator("[data-copilot-pane] textarea:visible");
  await box.fill(QUESTION[locale]);
  await box.press("Enter");
  await page.locator('[data-copilot-pane] [data-message="assistant"]:visible').first().waitFor({ timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector("[data-copilot-pane] button[aria-label='Stop'], [data-copilot-pane] button[aria-label='إيقاف']"));
  await page.waitForTimeout(800);
};

const withoutCopilot = (locale) => async (page) => {
  const close = page.getByRole("button", { name: CLOSE_COPILOT[locale] });
  if (await close.isVisible()) await close.click();
  await settle(page);
};

// [file stem, path, viewport, device scale, action]
const SHOTS = (locale) => {
  const p = locale === "ar" ? "/ar" : "";
  return [
    [`app-desktop.${locale}`, `${p}/t/2222`, DESKTOP, 2, askCopilot(locale)],
    [`app-phone.${locale}`, `${p}/t/2222`, PHONE, 2, settle],
    [`tadawul-stock.${locale}`, `${p}/t/2222`, DESKTOP, 1.5, withoutCopilot(locale)],
    [`earnings-season.${locale}`, `${p}/templates/earnings-season`, DESKTOP, 1.5, withoutCopilot(locale)],
    [`dividend-hunter.${locale}`, `${p}/templates/dividend-hunter`, DESKTOP, 1.5, withoutCopilot(locale)],
    [`sector-vs-sector.${locale}`, `${p}/templates/sector-vs-sector`, DESKTOP, 1.5, withoutCopilot(locale)],
  ];
};

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });
const taken = {};

for (const locale of ["en", "ar"]) {
  for (const [stem, route, viewport, deviceScaleFactor, act] of SHOTS(locale)) {
    const context = await browser.newContext({ viewport, deviceScaleFactor, locale: locale === "ar" ? "ar-SA" : "en-US" });
    const page = await context.newPage();
    await page.goto(BASE_URL + route, { waitUntil: "networkidle" });
    await act(page);
    const file = path.join(outDir, `${stem}.jpg`);
    await page.screenshot({ path: file, type: "jpeg", quality: 82 });
    taken[stem] = { route, viewport, takenAt: new Date().toISOString() };
    console.log("saved", path.relative(process.cwd(), file));
    await context.close();
  }
}

await writeFile(path.join(outDir, "screens.json"), JSON.stringify(taken, null, 2) + "\n");
await browser.close();
