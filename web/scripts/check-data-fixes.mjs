// Market-data fixes (audit 2026-10-18): each changed page against the API it reads, then
// screenshots at 1440px and 390px in English and Arabic.
//
//   BASE_URL=http://localhost:3100 node scripts/check-data-fixes.mjs
//   BASE_URL=http://localhost:3201 STAGING_AUTH=user:pass SHOTS_DIR=../docs/screenshots/data-fixes-beta node scripts/check-data-fixes.mjs
//   BASE_URL=https://alphacouncil.tech SHOTS_DIR=../docs/screenshots/data-fixes-production SWEEP=1 node scripts/check-data-fixes.mjs
//
// Page checks: the header price keeps the decimals it has (3 for KWD, BHD, OMR); a listing with
// no confirmed currency says so; EPS is the API's (in the price's unit) or its reason; value
// traded shows its reason; the news light is the API's, and the API's news date is the newest
// item's. SWEEP=1 also reads every ticker from the API (one request at a time) and counts what
// the rules now give. No number is written into this file: every expected value is the API's.
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = (process.env.BASE_URL ?? "http://localhost:3100").replace(/\/$/, "");
const here = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.resolve(here, process.env.SHOTS_DIR ?? "../../docs/screenshots/data-fixes-local");
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;
const messages = {
  en: (await import("../messages/en.json", { with: { type: "json" } })).default,
  ar: (await import("../messages/ar.json", { with: { type: "json" } })).default,
};

// NBK (fils EPS), Aramco (no turnover in its file), QCFS (QSE, third decimal), ADNOC Drilling
// (EPS at 10,000x: no unit), National Industries on DFM (pipeline currency KWD on an AED market).
const SAMPLE = ["101", "2222", "QCFS", "ADNOCDRILL", "NIND"];
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

const nf = (v, digits) => new Intl.NumberFormat("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v);
const digitsOf = (cur, v) =>
  ["KWD", "BHD", "OMR"].includes(cur) ? 3 : v != null && Math.abs(Math.round(v * 100) - v * 100) > 1e-6 ? 3 : 2;
const lp = (locale, p) => (locale === "en" ? p : `/ar${p}`);
const visible = (page, sel) => page.locator(`${sel}:visible`).first();

async function openStock(page, locale, slug) {
  // next-intl's locale cookie from an Arabic page would send the next English URL to /ar.
  await context.clearCookies();
  await page.goto(BASE_URL + lp(locale, `/t/${encodeURIComponent(slug)}`), { waitUntil: "domcontentloaded" });
  await visible(page, '[data-panel="overview.metrics"] dl').waitFor({ timeout: 30000 });
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
}

/** The Key metrics value next to a label. */
async function metric(page, label) {
  const panel = visible(page, '[data-panel="overview.metrics"]');
  const dt = panel.locator("dt", { hasText: label }).first();
  await dt.waitFor({ timeout: 60000 });
  return (await dt.locator("xpath=following-sibling::dd[1]").innerText({ timeout: 60000 })).trim();
}

const page = await context.newPage();
await page.setViewportSize(WIDTHS[1440]);
await mkdir(shotsDir, { recursive: true });

for (const slug of SAMPLE) {
  let d;
  try {
    d = await api(`/tickers/${encodeURIComponent(slug)}`);
  } catch (e) {
    check(false, `${slug}: API answers`, String(e));
    continue;
  }
  const { ticker: t, quote: q, valuation: v } = d;
  const news = d.freshness.find((f) => f.category === "news") ?? null;
  const items = await api(`/tickers/${encodeURIComponent(slug)}/news?limit=50`);
  const newest = items.map((i) => i.date).filter(Boolean).sort().at(-1) ?? null;
  if (news) {
    check(
      (news.as_of ?? null)?.slice(0, 10) === (newest ?? null)?.slice(0, 10),
      `${slug}: the news date is the newest item's (${newest?.slice(0, 10) ?? "none"})`,
      `freshness as_of ${news.as_of}`,
    );
  }

  for (const locale of ["en", "ar"]) {
    const m = messages[locale].stock;
    await page.setViewportSize(WIDTHS[1440]);
    await openStock(page, locale, slug);
    const header = await visible(page, "header:has(h1)").innerText();

    if (q.last_price != null) {
      const want = nf(q.last_price, digitsOf(t.currency, q.last_price));
      check(header.includes(want), `${slug} ${locale}: header price ${want}`, header.replace(/\s+/g, " "));
    }
    if (q.last_price != null && !t.currency) {
      check(header.includes(m.currencyUnconfirmed), `${slug} ${locale}: "${m.currencyUnconfirmed}" in the header`);
    }

    const eps = await metric(page, m.metrics.eps_ttm);
    if (v.eps_ttm != null) {
      check(eps.includes(nf(v.eps_ttm, digitsOf(t.currency))), `${slug} ${locale}: EPS ${eps}`, `API ${v.eps_ttm}`);
    } else if (v.eps_ttm_reason) {
      const why = m.metrics.reasons[v.eps_ttm_reason];
      check(eps === why, `${slug} ${locale}: EPS shows "${why}"`, eps);
    }
    if (q.value_traded == null && q.value_traded_reason) {
      const vt = await metric(page, m.metrics.value_traded);
      const why = m.metrics.reasons[q.value_traded_reason];
      check(vt === why, `${slug} ${locale}: value traded shows "${why}"`, vt);
    }

    const light = await visible(page, '[data-panel="overview.news"] [data-freshness]').getAttribute("data-freshness");
    const want = news?.stale == null ? "unknown" : news.stale ? "stale" : "fresh";
    check(light === want, `${slug} ${locale}: news light ${want}`, `page shows ${light}`);

    await page.screenshot({ path: path.join(shotsDir, `${slug}-${locale}-1440.png`) });
    await page.setViewportSize(WIDTHS[390]);
    await openStock(page, locale, slug);
    // The phone layout stacks panels: the header, then Key metrics in view.
    await page.screenshot({ path: path.join(shotsDir, `${slug}-${locale}-390.png`) });
    await visible(page, '[data-panel="overview.metrics"]').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(shotsDir, `${slug}-${locale}-390-metrics.png`) });
  }
}

// /methodology states the news window the lights use.
{
  const m = await api("/methodology");
  const rule = m.freshness.find((f) => f.category === "news");
  check(rule && rule.trading_days === false, "methodology: news ages in calendar days", JSON.stringify(rule));
  for (const locale of ["en", "ar"]) {
    for (const w of [1440, 390]) {
      await page.setViewportSize(WIDTHS[w]);
      await context.clearCookies();
      await page.goto(BASE_URL + lp(locale, "/methodology"), { waitUntil: "networkidle" });
      const table = page.locator("[data-freshness-table]");
      await table.scrollIntoViewIfNeeded();
      const text = await table.innerText();
      check(text.includes(messages[locale].site.methodology.fresh.categories.news) && text.includes(String(rule?.max_age_days)),
        `methodology ${locale} ${w}: news row shows ${rule?.max_age_days}`);
      await page.screenshot({ path: path.join(shotsDir, `methodology-${locale}-${w}.png`) });
    }
  }
}

if (process.env.SWEEP) {
  const all = await api("/tickers");
  const n = { tickers: 0, eps_shown: 0, eps_unconfirmed: 0, eps_bad: 0, news_green_old: 0, news_green: 0, no_currency: 0, vt_reason: 0 };
  const now = Date.now();
  for (const e of all) {
    const d = await api(`/tickers/${encodeURIComponent(e.slug)}`);
    n.tickers++;
    const { quote: q, valuation: v } = d;
    if (v.eps_ttm != null) {
      n.eps_shown++;
      const f = (v.eps_ttm * v.pe) / q.last_price;
      if (!(Math.abs(f - 1) <= 0.2)) n.eps_bad++;
    }
    if (v.eps_ttm_reason) n.eps_unconfirmed++;
    if (q.value_traded_reason) n.vt_reason++;
    if (!d.ticker.currency) n.no_currency++;
    const news = d.freshness.find((f) => f.category === "news");
    if (news && news.stale === false) {
      n.news_green++;
      if (!news.as_of || now - Date.parse(news.as_of) > 30.5 * 86400e3) n.news_green_old++;
    }
  }
  console.log("sweep", JSON.stringify(n));
  check(n.eps_bad === 0, "sweep: every EPS shown times its P/E gives the price (within 20%)");
  check(n.news_green_old === 0, "sweep: no green news light on an item older than 30 days");
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failed` : "\nall passed");
process.exit(failures.length ? 1 : 0);
