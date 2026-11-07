// Step 10's five pages, signed out, in English and Arabic at 1440 and 390: status, sideways scroll, screenshot.
// GETs only: no account, no session, no form submitted.
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
const require = createRequire("C:/projects/alphacouncil-platform/web/package.json");
const { chromium } = require("playwright-core");
const BASE = process.env.BASE ?? "https://alphacouncil.tech";
const OUT = process.env.OUT;
await mkdir(OUT, { recursive: true });
const PAGES = [["landing", ""], ["pricing", "/pricing"], ["home", "/home"], ["t2222", "/t/2222"], ["advisors", "/t/2222/advisors"]];
const browser = await chromium.launch({ channel: "chrome" });
const lines = [];
let bad = 0;
for (const locale of ["en", "ar"]) {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: width === 390 ? 844 : 900 } });
    for (const [name, path] of PAGES) {
      const url = `${BASE}/${locale}${path}`;
      const res = await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
      await page.waitForTimeout(800);
      const sideways = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      const file = `${name}.${locale}.${width}.png`;
      await page.screenshot({ path: `${OUT}/${file}`, fullPage: false });
      const status = res ? res.status() : 0;
      if (status !== 200 || sideways > 0) bad++;
      lines.push(`${status}  ${url}  sideways ${sideways}px  -> ${file}`);
    }
    await page.close();
  }
}
await browser.close();
lines.push("", `${lines.length} views; ${bad === 0 ? "every one 200 with no sideways scroll" : `${bad} with a problem`}`);
await writeFile(`${OUT}/pages.txt`, lines.join("\n") + "\n");
console.log(lines.join("\n"));
