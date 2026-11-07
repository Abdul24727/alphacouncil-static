// The visible text of the pages the lawyer pack describes, signed out, in English and Arabic (1440 wide).
// GETs only: no account, no session, no form submitted, no click. Writes one text file per page and language.
import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
const require = createRequire("C:/projects/alphacouncil-platform/web/package.json");
const { chromium } = require("playwright-core");
const BASE = process.env.BASE ?? "https://alphacouncil.tech";
const OUT = process.env.OUT;
await mkdir(OUT, { recursive: true });
const PAGES = [
  ["landing", ""], ["home", "/home"], ["t2222", "/t/2222"], ["financials", "/t/2222/financials"],
  ["ownership", "/t/2222/ownership"], ["calendar", "/t/2222/calendar"], ["council", "/t/2222/council"],
  ["advisors", "/t/2222/advisors"], ["pricing", "/pricing"], ["methodology", "/methodology"],
  ["legal-terms", "/legal/terms"], ["legal-privacy", "/legal/privacy"], ["legal-refunds", "/legal/refunds"],
  ["legal-ai", "/legal/ai-financial-disclaimer"], ["legal-cookies", "/legal/cookies"],
  ["legal-merchant", "/legal/merchant"], ["signup", "/signup"], ["checkout", "/checkout"],
];
const browser = await chromium.launch({ channel: "chrome" });
const lines = [];
for (const locale of ["en", "ar"]) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  for (const [name, path] of PAGES) {
    const url = `${BASE}/${locale}${path}`;
    let status = 0;
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const res = await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
        status = res ? res.status() : 0;
        break;
      } catch (e) {
        if (attempt === 3) throw e;
        await page.waitForTimeout(5000);
      }
    }
    await page.waitForTimeout(1000);
    const text = await page.evaluate(() => document.body.innerText);
    const file = `${name}.${locale}.txt`;
    await writeFile(`${OUT}/${file}`, `${url}\nstatus ${status}, final ${page.url()}\n\n${text}\n`);
    lines.push(`${status}  ${url}  -> ${page.url()}  ${text.length} chars  ${file}`);
  }
  await page.close();
}
await browser.close();
await writeFile(`${OUT}/index.txt`, lines.join("\n") + "\n");
console.log(lines.join("\n"));
