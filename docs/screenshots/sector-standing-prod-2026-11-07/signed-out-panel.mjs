// What a signed-out visitor sees of the Fundamentals panel on production (alphacouncil.tech), en and ar, at 1440
// and 390. GET only, no sign-in. On production the panel is Pro-only, so its standings are not shown signed out.
import { createRequire } from "node:module";
const require = createRequire("C:/projects/alphacouncil-platform/web/package.json");
const { chromium } = require("playwright-core");
const browser = await chromium.launch({ channel: "chrome" });
for (const [locale, prefix, heading] of [["en", "", "Fundamentals"], ["ar", "/ar", "الأساسيات"]]) {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const res = await page.goto(`https://alphacouncil.tech${prefix}/t/2222/financials`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    const panel = page.locator("[data-panel]").filter({ hasText: heading }).first();
    const facts = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      standingTitles: [...document.querySelectorAll("[title]")].filter((e) => /standing|percentile|الترتيب|المئين/i.test(e.getAttribute("title") || "")).length,
      oldLabelVisible: /Sector percentile|المئين/.test(document.body.innerText),
    }));
    console.log(`${locale} ${viewport.width}: HTTP ${res.status()} | panel: ${(await panel.innerText()).replace(/\s+/g, " ").trim()} | ${JSON.stringify(facts)}`);
    await context.close();
  }
}
await browser.close();
