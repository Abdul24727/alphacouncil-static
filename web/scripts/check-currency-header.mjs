// The five US-dollar listings on Bahrain Bourse (api/app/data/listing_currencies.json) and the
// stock header while it loads. Screenshots at 1440px and 390px in English and Arabic.
//
//   BASE_URL=http://localhost:3100 node scripts/check-currency-header.mjs
//   BASE_URL=http://localhost:3201 STAGING_AUTH=user:pass SHOTS_DIR=../../docs/screenshots/currency-header-beta node scripts/check-currency-header.mjs
//   BASE_URL=https://alphacouncil.tech SHOTS_DIR=../../docs/screenshots/currency-header-production node scripts/check-currency-header.mjs
//
// SHOTS_DIR is relative to this folder. Uses the local Chrome.
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = (process.env.BASE_URL ?? "http://localhost:3100").replace(/\/$/, "");
const here = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.resolve(here, process.env.SHOTS_DIR ?? "../../docs/screenshots/currency-header-local");
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;
const listed = JSON.parse(await readFile(path.resolve(here, "../../api/app/data/listing_currencies.json"), "utf-8")).listings;
const messages = {
  en: (await import("../messages/en.json", { with: { type: "json" } })).default,
  ar: (await import("../messages/ar.json", { with: { type: "json" } })).default,
};
const LABEL = { en: { USD: "USD" }, ar: { USD: "دولار" } };
const WIDTHS = { 1440: { width: 1440, height: 900 }, 390: { width: 390, height: 844 } };

const failures = [];
const check = (ok, label, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${!ok && detail ? `\n        ${detail}` : ""}`);
  if (!ok) failures.push(label);
};

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ httpCredentials });
const api = async (p) => {
  const r = await context.request.get(`${BASE_URL}/api/v1${p}`);
  if (!r.ok()) throw new Error(`${p}: HTTP ${r.status()}`);
  return r.json();
};
const lp = (locale, p) => (locale === "en" ? p : `/ar${p}`);
const page = await context.newPage();
await mkdir(shotsDir, { recursive: true });
const header = () => page.locator("header:has(h1):visible").first();

async function open(locale, slug) {
  await context.clearCookies(); // next-intl's locale cookie would send English URLs to /ar
  await page.goto(BASE_URL + lp(locale, `/t/${encodeURIComponent(slug)}`), { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => [...document.querySelectorAll("header h1")].some((h) => h.checkVisibility() && h.textContent.trim().length > 1), null, { timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
}

// --- the recorded trading currencies ----------------------------------------------------------
const tickers = await api("/tickers");
for (const [key, cur] of Object.entries(listed)) {
  const t = tickers.find((x) => x.ticker_key === key);
  if (!t) {
    check(false, `${key}: in the universe`);
    continue;
  }
  const d = await api(`/tickers/${encodeURIComponent(t.slug)}`);
  check(d.ticker.currency === cur, `${t.symbol}: API trading currency ${cur}`, `got ${d.ticker.currency}`);
  if (d.quote.last_price == null) continue;
  for (const locale of ["en", "ar"]) {
    for (const w of t.symbol === "ARIG.BH" ? [1440, 390] : [1440]) {
      await page.setViewportSize(WIDTHS[w]);
      await open(locale, t.slug);
      const text = await header().innerText();
      check(text.includes(LABEL[locale][cur]), `${t.symbol} ${locale} ${w}: header in ${LABEL[locale][cur]}`, text.replace(/\s+/g, " "));
      await page.screenshot({ path: path.join(shotsDir, `${t.symbol}-${locale}-${w}.png`) });
    }
  }
}

// --- the header while the quote loads -----------------------------------------------------------
for (const locale of ["en", "ar"]) {
  for (const w of [1440, 390]) {
    await page.setViewportSize(WIDTHS[w]);
    await context.clearCookies();
    // Hold the quote back for a few seconds, as on a slow connection.
    await page.route("**/api/v1/tickers/2222", (r) => setTimeout(() => r.continue().catch(() => {}), 4000));
    await page.goto(BASE_URL + lp(locale, "/t/2222"), { waitUntil: "domcontentloaded" });
    await page.locator("header:has(h1) [aria-busy]:visible").first().waitFor({ timeout: 30000 });
    const loading = await header().innerText();
    check(!loading.includes(messages[locale].stock.noPrice), `2222 ${locale} ${w}: no "${messages[locale].stock.noPrice}" while loading`, loading);
    await page.screenshot({ path: path.join(shotsDir, `loading-2222-${locale}-${w}.png`) });
    await page.unroute("**/api/v1/tickers/2222");
  }
}

// A stock the database has no price for still says so once loaded (412: no briefs price).
{
  const noPrice = [];
  for (const t of tickers.filter((x) => !x.has_prices).slice(0, 40)) {
    const d = await api(`/tickers/${encodeURIComponent(t.slug)}`);
    if (d.quote.last_price == null) noPrice.push(t.slug);
  }
  if (noPrice.length) {
    await page.setViewportSize(WIDTHS[1440]);
    await open("en", noPrice[0]);
    const text = await header().innerText();
    check(text.includes(messages.en.stock.noPrice), `${noPrice[0]}: "${messages.en.stock.noPrice}" once loaded`, text);
    await page.screenshot({ path: path.join(shotsDir, `no-price-${noPrice[0]}-en-1440.png`) });
  } else console.log("      no stock without a price to check");
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failed` : "\nall passed");
process.exit(failures.length ? 1 : 0);
