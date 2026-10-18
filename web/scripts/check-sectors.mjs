// Tadawul sectors from the Saudi Exchange's classification (api/app/data/tadawul_sectors.json):
// every Tadawul company in the API against the list, peers within one sector, then the peers
// panel and the Sector vs Sector page in English and Arabic at 1440px and 390px.
//
//   BASE_URL=http://localhost:3100 node scripts/check-sectors.mjs
//   BASE_URL=http://localhost:3201 STAGING_AUTH=user:pass SHOTS_DIR=../../docs/screenshots/sectors-beta node scripts/check-sectors.mjs
//   BASE_URL=https://alphacouncil.tech SHOTS_DIR=../../docs/screenshots/sectors-production node scripts/check-sectors.mjs
//
// SHOTS_DIR is relative to this folder. Uses the local Chrome.
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = (process.env.BASE_URL ?? "http://localhost:3100").replace(/\/$/, "");
const here = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.resolve(here, process.env.SHOTS_DIR ?? "../../docs/screenshots/sectors-local");
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;
const list = JSON.parse(await readFile(path.resolve(here, "../../api/app/data/tadawul_sectors.json"), "utf-8"));
const official = new Map(list.sectors.flatMap((s) => s.symbols.map((sym) => [sym, s])));
const messages = {
  en: (await import("../messages/en.json", { with: { type: "json" } })).default,
  ar: (await import("../messages/ar.json", { with: { type: "json" } })).default,
};

// Almarai (was "Transportation"), Maaden (was "Hotels & Restaurants"), Mouwasat (was "Tobacco"),
// Bahri (Energy on the exchange's list), Saudi Tadawul Group (was the catch-all).
const SAMPLE = ["2280", "1211", "4002", "4030", "1111"];
const PAIR = ["Food & Beverages", "Materials"];
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

// --- every Tadawul company against the list -------------------------------------------------
{
  const tadawul = (await api("/tickers")).filter((t) => t.exchange === "TADAWUL");
  const wrong = tadawul.filter((t) => {
    const s = official.get(t.symbol);
    return s ? t.sector_en !== s.en || t.sector_ar !== s.ar : t.sector_en !== null;
  });
  check(wrong.length === 0, `${tadawul.length} Tadawul companies carry the exchange's sector, or none`,
    wrong.slice(0, 5).map((t) => `${t.symbol}: ${t.sector_en}`).join(", "));
  const unknown = tadawul.filter((t) => !official.has(t.symbol)).map((t) => t.symbol);
  console.log(`      not on the exchange's list (sector unknown): ${unknown.length ? unknown.join(" ") : "none"}`);
  const names = new Set((await api("/templates/sectors")).map((s) => s.sector_en));
  check(list.sectors.every((s) => names.has(s.en)), `all ${list.sectors.length} official sectors are offered in the templates`);
}

// --- peers ----------------------------------------------------------------------------------
for (const sym of SAMPLE) {
  const p = await api(`/tickers/${sym}/peers`);
  const s = official.get(sym);
  check(p.sector_en === s.en && p.peers.every((x) => x.ticker.sector_en === s.en),
    `${sym}: peers are all ${s.en} (${p.peers.length}, ${p.basis})`, p.peers.map((x) => `${x.ticker.symbol}:${x.ticker.sector_en}`).join(" "));
}

// --- pages ----------------------------------------------------------------------------------
const lp = (locale, p) => (locale === "en" ? p : `/ar${p}`);
const page = await context.newPage();
await mkdir(shotsDir, { recursive: true });

async function open(locale, p, ready) {
  await context.clearCookies(); // next-intl's locale cookie would send English URLs to /ar
  await page.goto(BASE_URL + lp(locale, p), { waitUntil: "domcontentloaded" });
  await page.locator(`${ready}:visible`).first().waitFor({ timeout: 60000 });
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
}

for (const locale of ["en", "ar"]) {
  const m = messages[locale];
  for (const w of [1440, 390]) {
    await page.setViewportSize(WIDTHS[w]);
    for (const sym of ["2280", "1211"]) {
      await open(locale, `/t/${sym}`, '[data-panel="overview.peers"] table');
      const panel = page.locator('[data-panel="overview.peers"]:visible').first();
      const text = (await panel.innerText()).toLowerCase(); // the basis label is set in caps
      check([m.stock.peers.basis_sector_exchange, m.stock.peers.basis_sector_gcc].some((b) => text.includes(b.toLowerCase())),
        `${sym} ${locale} ${w}: peers panel lists same-sector peers`);
      await panel.scrollIntoViewIfNeeded();
      await page.screenshot({ path: path.join(shotsDir, `peers-${sym}-${locale}-${w}.png`) });
    }

    await open(locale, "/templates/sector-vs-sector", "select");
    const [a, b] = [page.locator("select:visible").nth(0), page.locator("select:visible").nth(1)];
    await a.selectOption(PAIR[0]);
    await b.selectOption(PAIR[1]);
    await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(1500);
    const body = await page.locator("main:visible").first().innerText();
    const names = PAIR.map((en) => (locale === "ar" ? list.sectors.find((s) => s.en === en).ar : en));
    check(names.every((n) => body.includes(n)), `sector vs sector ${locale} ${w}: ${names.join(" / ")}`);
    await page.screenshot({ path: path.join(shotsDir, `sector-vs-sector-${locale}-${w}.png`) });
  }
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failed` : "\nall passed");
process.exit(failures.length ? 1 : 0);
