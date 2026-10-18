// Search engines and link previews: robots.txt, sitemap.xml, and the <head> of a sample of
// pages in English and Arabic, read as Googlebot and as a link-preview bot. Then screenshots
// of the sampled pages at 1440px and 390px.
//
//   BASE_URL=http://localhost:3100 node scripts/check-seo.mjs
//   BASE_URL=http://localhost:3201 SHOTS_DIR=../docs/screenshots/seo-beta node scripts/check-seo.mjs   # beta tunnel
//   BASE_URL=https://alphacouncil.tech SHOTS_DIR=../docs/screenshots/seo-production node scripts/check-seo.mjs
//
// Canonicals, alternates and the sitemap must name https://alphacouncil.tech whatever host
// answers. No digit may appear in a title or description unless it is the stock's symbol
// as the API returns it. Uses the local Chrome.
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = (process.env.BASE_URL ?? "http://localhost:3100").replace(/\/$/, "");
const SITE = "https://alphacouncil.tech";
const here = path.dirname(fileURLToPath(import.meta.url));
const shotsDir = path.resolve(here, process.env.SHOTS_DIR ?? "../../docs/screenshots/seo-local");
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)";
const PREVIEW_BOT = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)";
const PRIVATE = ["/portfolio", "/settings", "/dashboards", "/checkout", "/billing/", "/verify-email", "/reset-password"];

const failures = [];
const check = (ok, label, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${!ok && detail ? `\n        ${detail}` : ""}`);
  if (!ok) failures.push(label);
};

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ httpCredentials });
// Crawlers keep no cookies: without this, next-intl's locale cookie from an Arabic page would
// redirect the next English request to /ar.
const get = async (p, ua = GOOGLEBOT) => {
  await context.clearCookies();
  return context.request.get(BASE_URL + p, { headers: { "User-Agent": ua }, maxRedirects: 0 });
};
const api = async (p) => (await get(`/api/v1${p}`)).json();
const lp = (locale, p) => (locale === "en" ? p : p === "/" ? "/ar" : `/ar${p}`);
const abs = (locale, p) => SITE + lp(locale, p);
const decode = (s) =>
  s.replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#x27;|&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");

/** Everything search engines and previews read from <head>. */
function head(html) {
  const h = html.split("</head>")[0];
  const meta = (attr, key) => {
    const m = h.match(new RegExp(`<meta ${attr}="${key}" content="([^"]*)"`));
    return m ? decode(m[1]) : null;
  };
  const alternates = {};
  for (const m of h.matchAll(/<link rel="alternate" hrefLang="([^"]+)" href="([^"]+)"/g)) alternates[m[1]] = m[2];
  return {
    lang: html.match(/<html[^>]* lang="([^"]+)"/)?.[1],
    title: decode(h.match(/<title>([^<]*)<\/title>/)?.[1] ?? ""),
    description: meta("name", "description"),
    canonical: h.match(/<link rel="canonical" href="([^"]+)"/)?.[1] ?? null,
    robots: meta("name", "robots"),
    alternates,
    ogTitle: meta("property", "og:title"),
    ogUrl: meta("property", "og:url"),
    ogImage: meta("property", "og:image"),
    ogLocale: meta("property", "og:locale"),
    twitterCard: meta("name", "twitter:card"),
    twitterImage: meta("name", "twitter:image"),
  };
}

/** The digits in a title or description must all come from the API (the stock's symbol). */
const strayDigits = (text, allowed = "") => (text ?? "").replace(allowed, "").match(/[0-9٠-٩]/) !== null;

// --- robots.txt ----------------------------------------------------------------------------
{
  const r = await get("/robots.txt");
  const body = await r.text();
  check(r.status() === 200 && (r.headers()["content-type"] ?? "").startsWith("text/plain"), "robots.txt answers as text");
  check(/^Allow: \/$/m.test(body), "robots.txt allows the site");
  check(body.includes(`Sitemap: ${SITE}/sitemap.xml`), "robots.txt points at the sitemap on alphacouncil.tech");
  const missing = ["/api/", ...PRIVATE, ...PRIVATE.map((p) => `/ar${p}`)].filter((p) => !body.includes(`Disallow: ${p}\n`));
  check(missing.length === 0, "robots.txt disallows the account pages and /api/ in both languages", missing.join(" "));
  const blocked = ["/markets", "/screener", "/templates", "/t/", "/pricing"].filter((p) => body.includes(`Disallow: ${p}`));
  check(blocked.length === 0, "robots.txt leaves markets, screener, templates and stock pages open", blocked.join(" "));
}

// --- sitemap.xml ---------------------------------------------------------------------------
const tickers = await api("/tickers");
{
  const r = await get("/sitemap.xml");
  const xml = await r.text();
  check(r.status() === 200 && (r.headers()["content-type"] ?? "").includes("xml"), "sitemap.xml answers as XML");
  const urls = [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((m) => ({
    loc: m[1].match(/<loc>([^<]+)<\/loc>/)?.[1],
    lastmod: m[1].match(/<lastmod>([^<]+)<\/lastmod>/)?.[1] ?? null,
    alt: Object.fromEntries([...m[1].matchAll(/hreflang="([^"]+)" href="([^"]+)"/g)].map((a) => [a[1], a[2]])),
  }));
  console.log(`      sitemap: ${urls.length} URLs, API universe: ${tickers.length} tickers`);
  const offsite = urls.filter((u) => !u.loc?.startsWith(SITE + "/") && u.loc !== SITE + "/" && !u.loc?.startsWith(SITE));
  check(offsite.length === 0, "every sitemap URL is on https://alphacouncil.tech", offsite.slice(0, 3).map((u) => u.loc).join(" "));
  const altsOff = urls.filter((u) => !u.alt.en?.startsWith(SITE) || !u.alt.ar?.startsWith(SITE) || !u.alt["x-default"]?.startsWith(SITE));
  check(altsOff.length === 0, "every sitemap URL lists en, ar and x-default alternates on alphacouncil.tech", altsOff.slice(0, 3).map((u) => u.loc).join(" "));
  const locs = new Set(urls.map((u) => u.loc));
  const pages = ["/", "/pricing", "/methodology", "/legal", "/legal/terms", "/markets", "/screener", "/templates",
    "/templates/earnings-season", "/templates/dividend-hunter", "/templates/sector-vs-sector"];
  const absent = pages.flatMap((p) => ["en", "ar"].map((l) => abs(l, p))).filter((u) => !locs.has(u) && !locs.has(u + "/"));
  check(absent.length === 0, "sitemap lists the public pages in English and Arabic", absent.join(" "));
  const priv = urls.filter((u) => PRIVATE.some((p) => u.loc.includes(p.replace(/\/$/, ""))));
  check(priv.length === 0, "sitemap lists no account page", priv.map((u) => u.loc).join(" "));
  const byLoc = new Map(urls.map((u) => [u.loc, u]));
  const noStock = [];
  const badDate = [];
  for (const t of tickers) {
    for (const l of ["en", "ar"]) {
      const u = byLoc.get(abs(l, `/t/${encodeURIComponent(t.slug)}`));
      if (!u) noStock.push(`${l}:${t.slug}`);
      else if (u.lastmod !== (t.prices_as_of ?? null)) badDate.push(`${l}:${t.slug} ${u.lastmod} vs ${t.prices_as_of}`);
    }
  }
  check(tickers.length > 0 && noStock.length === 0, `sitemap lists every stock page in both languages (${tickers.length} × 2)`, noStock.slice(0, 5).join(" "));
  check(badDate.length === 0, "stock lastmod is the date of the last price bar, and absent without one", badDate.slice(0, 5).join(" "));
}

// --- <head> of a sample of pages -----------------------------------------------------------
const sample = ["2222", "1120"];
const other = tickers.find((t) => t.exchange !== "TADAWUL" && t.name_en && t.name_ar);
if (other) sample.push(other.slug);
const stockRefs = Object.fromEntries(await Promise.all(sample.map(async (s) => [s, (await api(`/tickers/${encodeURIComponent(s)}`)).ticker])));
const exchangeNames = {
  en: { TADAWUL: "Tadawul", ADX: "ADX", DFM: "DFM", QSE: "QSE", KSE: "Boursa Kuwait", BSE: "BHB", MSM: "MSX" },
  ar: { TADAWUL: "تداول", ADX: "سوق أبوظبي", DFM: "سوق دبي", QSE: "بورصة قطر", KSE: "بورصة الكويت", BSE: "بورصة البحرين", MSM: "بورصة مسقط" },
};

const PUBLIC = ["/", "/pricing", "/methodology", "/legal/terms", "/markets", "/screener", "/templates", "/templates/dividend-hunter", "/login"];
for (const locale of ["en", "ar"]) {
  for (const p of [...PUBLIC, ...sample.map((s) => `/t/${encodeURIComponent(s)}`)]) {
    const url = lp(locale, p);
    const r = await get(url);
    const m = head(await r.text());
    const want = abs(locale, p);
    const slug = p.startsWith("/t/") ? decodeURIComponent(p.slice(3)) : null;
    const ref = slug ? stockRefs[slug] : null;
    const problems = [];
    if (r.status() !== 200) problems.push(`status ${r.status()}`);
    if (m.lang !== locale) problems.push(`lang ${m.lang}`);
    if (!m.title.endsWith("AlphaCouncil") && !m.title.startsWith("AlphaCouncil")) problems.push(`title "${m.title}"`);
    if (!m.description) problems.push("no description");
    if (m.canonical !== want && m.canonical + "/" !== want && m.canonical !== want + "/") problems.push(`canonical ${m.canonical}`);
    for (const l of ["en", "ar"]) if (m.alternates[l]?.replace(/\/$/, "") !== abs(l, p).replace(/\/$/, "")) problems.push(`hreflang ${l} ${m.alternates[l]}`);
    if (m.alternates["x-default"]?.replace(/\/$/, "") !== abs("en", p).replace(/\/$/, "")) problems.push("x-default");
    if (m.robots?.includes("noindex")) problems.push(`robots ${m.robots}`);
    if (m.ogTitle !== m.title) problems.push("og:title");
    if (m.ogUrl !== m.canonical) problems.push(`og:url ${m.ogUrl}`);
    if (m.ogImage !== `${SITE}/og/${locale}.png` || m.twitterImage !== m.ogImage) problems.push(`og:image ${m.ogImage}`);
    if (m.ogLocale !== (locale === "ar" ? "ar_SA" : "en_US")) problems.push(`og:locale ${m.ogLocale}`);
    if (m.twitterCard !== "summary_large_image") problems.push(`twitter:card ${m.twitterCard}`);
    if (strayDigits(m.title, ref?.symbol) || strayDigits(m.description, ref?.symbol)) problems.push("a digit that is not the symbol");
    if (ref) {
      const name = locale === "ar" ? (ref.name_ar ?? ref.name_en) : (ref.name_en ?? ref.name_ar);
      const company = name ? `${name} (${ref.symbol})` : ref.symbol;
      if (!m.title.startsWith(`${company} · ${exchangeNames[locale][ref.exchange]}`)) problems.push(`stock title "${m.title}"`);
    }
    check(problems.length === 0, `${url.padEnd(28)} ${m.title}`, problems.join("; "));
  }
}

// Link previews (facebookexternalhit, WhatsApp, Slack…) get the card in <head> too.
for (const url of ["/t/2222", "/ar/t/2222"]) {
  const m = head(await (await get(url, PREVIEW_BOT)).text());
  check(Boolean(m.ogTitle && m.ogImage && m.canonical), `link-preview bot reads the card in <head> on ${url}`, JSON.stringify(m));
}

// Another address of the same stock, and its other tabs, consolidate on /t/<slug>.
for (const [url, want] of [["/t/2222_TADAWUL", "/t/2222"], ["/t/2222/financials", "/t/2222"], ["/ar/t/2222/council", "/ar/t/2222"]]) {
  const m = head(await (await get(url)).text());
  check(m.canonical === SITE + want, `${url} canonical is ${want}`, String(m.canonical));
}

// Unknown tickers and account pages stay out of the index.
for (const url of ["/t/NO-SUCH-TICKER", "/portfolio", "/ar/settings", "/checkout", "/verify-email", "/ar/reset-password", "/billing/return"]) {
  const m = head(await (await get(url)).text());
  check(Boolean(m.robots?.includes("noindex")), `${url} is noindex`, `robots=${m.robots} title=${m.title}`);
}

// The preview cards themselves: PNG, 1200×630.
for (const locale of ["en", "ar"]) {
  const r = await get(`/og/${locale}.png`);
  const b = await r.body();
  const size = b.length > 24 ? [b.readUInt32BE(16), b.readUInt32BE(20)] : [];
  check(r.status() === 200 && r.headers()["content-type"] === "image/png" && size.join("x") === "1200x630",
    `/og/${locale}.png is a 1200x630 PNG`, `${r.status()} ${r.headers()["content-type"]} ${size.join("x")}`);
}

// --- In a browser: the tab title an ordinary visitor sees, and screenshots -----------------
await mkdir(shotsDir, { recursive: true });
const SHOTS = [
  ["/", "landing"], ["/ar", "landing"], ["/t/2222", "stock-2222"], ["/ar/t/2222", "stock-2222"],
  ["/markets", "markets"], ["/ar/templates/dividend-hunter", "dividend-hunter"],
];
for (const [url, stem] of SHOTS) {
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    await context.clearCookies();
    const page = await context.newPage();
    await page.setViewportSize({ width: w, height: h });
    await page.goto(BASE_URL + url, { waitUntil: "networkidle" });
    await page.waitForTimeout(800);
    const title = await page.title();
    const m = head(await (await get(url)).text());
    check(title === m.title, `browser tab title on ${url} at ${w}px: ${title}`, `expected ${m.title}`);
    const locale = url.startsWith("/ar") ? "ar" : "en";
    await page.screenshot({ path: path.join(shotsDir, `${stem}.${locale}.${w}.png`) });
    await page.close();
  }
}
console.log(`      screenshots in ${path.relative(process.cwd(), shotsDir)}`);

await browser.close();
console.log(failures.length ? `\n${failures.length} FAILED` : "\nALL PASS");
process.exit(failures.length ? 1 : 0);
