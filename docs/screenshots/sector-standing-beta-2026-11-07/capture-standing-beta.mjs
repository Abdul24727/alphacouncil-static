// Native-resolution captures of the Fundamentals panel on beta after the sector-standing release (026699b906).
// Uses the web project's playwright-core and the local Chrome. GETs only (the page's own requests).
import { createRequire } from "node:module";
import { writeFile, mkdir } from "node:fs/promises";

const require = createRequire("C:/projects/alphacouncil-platform/web/package.json");
const { chromium } = require("playwright-core");

const BASE = process.env.BASE_URL ?? "http://localhost:3100";
const OUT = process.argv[2];
const SIZES = { 1440: { width: 1440, height: 1000 }, 390: { width: 390, height: 844 } };
const TOOLTIP = { en: "Sector standing, 0 to 100", ar: "الترتيب داخل القطاع، من 0 إلى 100" };

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const record = [];
for (const locale of ["en", "ar"]) {
  for (const [name, viewport] of Object.entries(SIZES)) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await context.newPage();
    await page.goto(`${BASE}${locale === "ar" ? "/ar" : "/en"}/t/2222/financials`, { waitUntil: "networkidle" });
    await page.waitForFunction((t) => [...document.querySelectorAll("[title]")].some((e) => (e.getAttribute("title") || "").startsWith(t)), TOOLTIP[locale], { timeout: 60000 });
    await page.waitForTimeout(800);
    const facts = await page.evaluate((t) => {
      const tips = [...document.querySelectorAll("[title]")].filter((e) => (e.getAttribute("title") || "").startsWith(t));
      return {
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        sideways: document.documentElement.scrollWidth > window.innerWidth,
        tooltip: tips[0]?.getAttribute("title"),
        standings: tips.map((e) => e.innerText.trim()).join(" | "),
        oldLabel: /Sector percentile|المئين/.test(document.body.innerText),
      };
    }, TOOLTIP[locale]);
    const file = `${OUT}/${locale}-${name}-2222.png`;
    const panel = page.locator("[data-panel]").filter({ hasText: locale === "ar" ? "الأساسيات" : "Fundamentals" }).first();
    await panel.scrollIntoViewIfNeeded();
    await page.screenshot({ path: file });
    record.push({ locale, viewport, file: file.split("/").pop(), ...facts });
    await context.close();
  }
}
await browser.close();
await writeFile(`${OUT}/viewports.json`, JSON.stringify(record, null, 1) + "\n");
console.log(JSON.stringify(record.map(({ tooltip, ...r }) => r), null, 1));
