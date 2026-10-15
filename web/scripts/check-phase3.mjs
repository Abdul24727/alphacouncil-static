// Phase 3 "Done when": every ticker with price history draws a chart, and a
// ticker with no history shows "Data unavailable" instead of an empty chart.
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase3.mjs [--limit N]
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const limitArg = process.argv.indexOf("--limit");
const limit = limitArg > 0 ? Number(process.argv[limitArg + 1]) : Infinity;
const WORKERS = 4;

const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, httpCredentials });
const list = await (await context.request.get(`${BASE_URL}/api/v1/tickers`)).json();
const tickers = list.slice(0, limit);
console.log(`${tickers.length} tickers, ${tickers.filter((t) => t.has_prices).length} with a price file`);

const results = [];
let next = 0;

async function worker() {
  const page = await context.newPage();
  while (next < tickers.length) {
    const t = tickers[next++];
    const res = { slug: t.slug, has_prices: t.has_prices, outcome: "?" };
    try {
      await page.goto(`${BASE_URL}/t/${encodeURIComponent(t.slug)}`, { waitUntil: "domcontentloaded", timeout: 45000 });
      const panel = page.locator('[data-panel="overview.price"]:visible');
      await panel.waitFor({ timeout: 30000 });
      // Wait until the panel settles: a drawn chart or an unavailable label.
      await page.waitForFunction(
        () => {
          const p = [...document.querySelectorAll('[data-panel="overview.price"]')].find((e) => e.checkVisibility());
          if (!p) return false;
          return !!p.querySelector('[data-chart="price"] canvas') || /Data unavailable/i.test(p.textContent ?? "");
        },
        null,
        { timeout: 30000 },
      );
      const drawn = await panel.locator('[data-chart="price"] canvas').count();
      const bars = drawn ? Number(await panel.locator('[data-chart="price"]').getAttribute("data-bars")) : 0;
      const unavailable = /Data unavailable/i.test(await panel.innerText());
      res.outcome = drawn && bars >= 2 ? "chart" : unavailable ? "unavailable" : "empty";
      res.bars = bars;
    } catch (e) {
      res.outcome = `error: ${String(e.message).split("\n")[0].slice(0, 100)}`;
    }
    res.ok = t.has_prices ? res.outcome === "chart" : res.outcome === "unavailable";
    results.push(res);
    if (results.length % 50 === 0) console.log(`… ${results.length}/${tickers.length}`);
  }
  await page.close();
}

await Promise.all(Array.from({ length: WORKERS }, worker));
await browser.close();

const withPrices = results.filter((r) => r.has_prices);
const without = results.filter((r) => !r.has_prices);
const failed = results.filter((r) => !r.ok);
console.log(`charts drawn: ${withPrices.filter((r) => r.ok).length}/${withPrices.length} tickers with price history`);
console.log(`"Data unavailable": ${without.filter((r) => r.ok).length}/${without.length} tickers without history`);
for (const f of failed.slice(0, 30)) console.log(`FAIL ${f.slug}: expected ${f.has_prices ? "chart" : "unavailable"}, got ${f.outcome}`);
if (failed.length) {
  console.log(`\n${failed.length} ticker(s) failed`);
  process.exit(1);
}
console.log("\nPhase 3 done-when: all checks passed");
