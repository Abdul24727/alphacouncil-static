// No English on Arabic pages (QA audit rows 8a, 8b): opens every Arabic page of check-phase7.mjs and
// lists each visible Latin word that is not on the allow-list below, with the pages it is on.
// Text and tooltips are scanned; aria-* labels, code and user content (Copilot messages, pinned
// tables) are not. Exits 0 only when there is none.
//
//   BASE_URL=http://localhost:3110 node scripts/check-arabic.mjs              # signed out
//   BASE_URL=http://localhost:3110 SIGNED_IN=1 node scripts/check-arabic.mjs  # a new account (audit-ar-<time>@example.com)
//   WIDTHS=1440,390 adds the phone width (default 1440). STAGING_AUTH=user:pass for beta's public address.
import { readFile } from "node:fs/promises";
import { chromium } from "playwright-core";

// The only Latin words an Arabic page may show (PROJECT.md, Step 14 Defaults), by class.
const ALLOW = {
  keys: ["Ctrl", "K", "B", "L", "Esc"], // shortcut hints (Kbd)
  currencies: ["SAR", "AED", "QAR", "KWD", "BHD", "OMR", "USD"],
  brand: ["AlphaCouncil"],
  // Names a licence or branding rule makes us show: TradingView's chart attribution, "Google" on its sign-in button.
  licence: ["TradingView", "Google"],
  // The switch to the English site ("EN", and the language's own name in Settings).
  languageSwitch: ["EN", "English"],
};
// Also allowed, by shape rather than by word:
//  - tickers: every symbol and slug in /api/v1/tickers;
//  - URLs and email addresses (legal contact lines; the signed-in member's own address);
//  - numbers with a unit letter, as the app formats them everywhere (305.9M, 0.69x);
//  - in the legal merchant block, the Saudi national short address (4 Latin letters, 4 digits);
//  - Arabic data shown as stored (lang="ar": news, event names) that names a company in Latin letters;
//  - data the database holds only in English, shown as stored next to the "بالإنجليزية" tag
//    (components/stock/common.tsx LangTag), or a tooltip that starts with that tag.

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3110";
const SIGNED_IN = process.env.SIGNED_IN === "1";
const WIDTHS = (process.env.WIDTHS ?? "1440").split(",").map(Number);
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

// check-phase7.mjs's pages; signed in, the app pages (the site pages do not change with an account).
const SITE = ["/", "/pricing", "/methodology", "/legal", "/legal/terms", "/login", "/signup", "/forgot-password", "/reset-password"];
const APP = [
  "/home", "/portfolio", "/screener", "/markets", "/templates", "/templates/earnings-season",
  "/templates/dividend-hunter", "/templates/sector-vs-sector", "/dashboards", "/settings",
  "/t/2222", "/t/2222/financials", "/t/2222/council", "/t/2222/ownership", "/t/2222/calendar",
];
const ROUTES = SIGNED_IN ? APP : [...SITE, ...APP];

const ar = JSON.parse(await readFile(new URL("../messages/ar.json", import.meta.url), "utf8"));
const TAGS = Object.values(ar.stock.news.in);
const universe = await (await fetch(`${BASE_URL}/api/v1/tickers`, { headers: httpCredentials ? { authorization: `Basic ${Buffer.from(`${httpCredentials.username}:${httpCredentials.password}`).toString("base64")}` } : {} })).json();
const tickers = new Set(universe.flatMap((t) => [t.symbol, t.slug, ...t.symbol.split(/\s+/)]));
const words = new Set(Object.values(ALLOW).flat());

/** Runs in the page: Latin words outside the allow-list, with where they are. */
function scan({ words, tickers, tags }) {
  words = new Set(words);
  tickers = new Set(tickers);
  const SKIP = "script,style,noscript,code,[data-message],[data-panel^='pinned.']";
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && el.checkVisibility?.() !== false;
  };
  const allowed = (token, legal) => {
    const t = token.replace(/^[^\p{L}\p{N}@]+|[^\p{L}\p{N}]+$/gu, "");
    if (!/[A-Za-z]/.test(t)) return true;
    if (/^[+\-−]?\d[\d.,]*[A-Za-z%]{0,2}$/.test(t)) return true; // 305.9M, 0.69x
    // The Saudi national short address (4 letters, 4 digits) is written in Latin letters.
    if (legal && /^[A-Z]{4}\d{4}$/.test(t)) return true;
    return tickers.has(t) || words.has(t) || words.has(t.replace(/[^A-Za-z]/g, ""));
  };
  const URL_OR_EMAIL = /\b(?:https?:\/\/|www\.)\S+|[^\s@:"<>]+@[^\s@"<>]+\.[a-z]{2,}/gi;
  const bad = (text, legal = false) =>
    text.replace(URL_OR_EMAIL, " ").split(/[\s()[\]{},;:·|«»"“”،؛!?…]+/).filter((tok) => tok && !allowed(tok, legal));
  // Data shown as stored (dataLabel, newsText mark it with its own lang): Arabic data may name a
  // company in Latin letters; English data needs the language tag in the same item.
  const tagged = (el) => {
    const l = el.closest("[lang]");
    if (!l || l === document.documentElement) return false;
    if (l.getAttribute("lang") === "ar") return true;
    if (l.getAttribute("lang") !== "en") return false;
    const item = l.closest("li, tr, td") ?? l.parentElement;
    return !!item?.querySelector("[data-lang-tag]");
  };
  const legalLine = (el) => !!el.closest("#merchant");
  const where = (el) => el.closest("[data-panel]")?.getAttribute("data-panel") ?? el.closest("header,nav,aside,main,footer")?.tagName.toLowerCase() ?? el.tagName.toLowerCase();

  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || el.closest(SKIP) || !visible(el) || tagged(el)) continue;
    const b = bad(n.textContent, legalLine(el));
    if (b.length) out.push({ text: n.textContent.replace(/\s+/g, " ").trim().slice(0, 80), words: b.slice(0, 6), where: where(el) });
  }
  for (const el of document.querySelectorAll("[title]")) {
    const title = el.getAttribute("title");
    if (el.closest(SKIP) || !visible(el) || tags.some((t) => title.startsWith(t))) continue;
    const b = bad(title);
    if (b.length) out.push({ text: `title="${title.slice(0, 70)}"`, words: b.slice(0, 6), where: where(el) });
  }
  return out;
}

const browser = await chromium.launch({ channel: "chrome" });
let storageState;
if (SIGNED_IN) {
  const ctx = await browser.newContext({ httpCredentials });
  const page = await ctx.newPage();
  await page.goto(`${BASE_URL}/signup?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(`audit-ar-${Date.now()}@example.com`);
  await page.locator("input[type=password]:visible").fill("a long test password");
  await page.locator("input[type=checkbox]:visible").check();
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 });
  storageState = await ctx.storageState();
  await ctx.close();
}

const leaks = new Map();
let views = 0;
for (const width of WIDTHS) {
  const ctx = await browser.newContext({
    viewport: { width, height: width < 768 ? 844 : 900 },
    ...(width < 768 ? { isMobile: true, hasTouch: true } : {}),
    httpCredentials,
    storageState,
  });
  for (const route of ROUTES) {
    const page = await ctx.newPage();
    const res = await page.goto(`${BASE_URL}/ar${route === "/" ? "" : route}`, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(600);
    views++;
    if (res?.status() !== 200) console.log(`FAIL  /ar${route} at ${width}px: HTTP ${res?.status()}`);
    for (const l of await page.evaluate(scan, { words: [...words], tickers: [...tickers], tags: TAGS })) {
      const key = `${l.text}  [${l.words.join(", ")}] in ${l.where}`;
      if (!leaks.has(key)) leaks.set(key, new Set());
      leaks.get(key).add(`${route}${WIDTHS.length > 1 ? ` @${width}` : ""}`);
    }
    await page.close();
  }
  await ctx.close();
}
await browser.close();

for (const [k, where] of leaks) console.log(`ENGLISH  ${k}\n         on ${[...where].slice(0, 4).join(", ")}${where.size > 4 ? `, … (${where.size} pages)` : ""}`);
console.log(`\n${views} Arabic page view(s)${SIGNED_IN ? " signed in" : " signed out"}; ${leaks.size} English string(s) outside the allow-list`);
process.exit(leaks.size ? 1 : 0);
