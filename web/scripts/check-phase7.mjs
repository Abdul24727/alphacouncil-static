// Phase 7 sweep: every page in Arabic and English at 1440px and 390px.
//   - html lang/dir, and in Arabic the shell mirrored (sidebar right, Copilot left)
//   - fonts actually drawn (DevTools): Archivo, Martian Mono, IBM Plex Sans Arabic only
//   - numbers left-to-right; no page wider than the screen; no page errors
//   - Arabic pages: English words left in the interface (reported with where they are)
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase7.mjs [route-filter]
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const filter = process.argv[2];
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const ROUTES = [
  "/", "/pricing", "/methodology", "/legal", "/legal/terms", "/login", "/signup", "/forgot-password", "/reset-password",
  "/home", "/portfolio", "/screener", "/markets", "/templates", "/templates/earnings-season",
  "/templates/dividend-hunter", "/templates/sector-vs-sector", "/dashboards", "/settings",
  "/t/2222", "/t/2222/financials", "/t/2222/council", "/t/2222/ownership", "/t/2222/calendar",
].filter((r) => !filter || r.includes(filter));
const SITE = new Set(["/", "/pricing", "/methodology", "/legal", "/legal/terms", "/login", "/signup", "/forgot-password", "/reset-password"]);
const ALLOWED_FONTS = ["Archivo", "Martian Mono", "IBM Plex Sans Arabic"];
// Latin that belongs in an Arabic page: the brand, currency and exchange codes, keys, the EN switch.
const LATIN_OK = new Set(["AlphaCouncil", "Google", "EN", "SAR", "AED", "QAR", "KWD", "BHD", "OMR", "TASI", "ADX", "DFM", "QSE", "MSX", "BHB", "Ctrl", "DB", "EV/EBITDA", "Moyasar"]);

const failures = [];
const leaks = new Map();
const check = (ok, label, detail = "") => {
  if (!ok) {
    console.log(`FAIL  ${label}${detail ? `\n        ${detail}` : ""}`);
    failures.push(label);
  }
  return ok;
};

async function renderedFonts(page, limit = 600) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const { root } = await cdp.send("DOM.getDocument", { depth: -1 });
  const parents = [];
  const walk = (node, parent) => {
    if (["SCRIPT", "STYLE", "NOSCRIPT", "svg"].includes(node.nodeName)) return;
    if (node.nodeType === 3 && node.nodeValue.trim() && parent) parents.push(parent.nodeId);
    for (const c of node.children ?? []) walk(c, node);
  };
  walk(root, null);
  const used = new Map();
  for (const id of [...new Set(parents)].slice(0, limit)) {
    const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: id }).catch(() => ({ fonts: [] }));
    for (const f of fonts) used.set(f.familyName, (used.get(f.familyName) ?? 0) + f.glyphCount);
  }
  await cdp.detach();
  return used;
}

function inspect({ ar, allowed }) {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && el.checkVisibility?.() !== false;
  };
  const describe = (el) => `${el.tagName.toLowerCase()}${el.closest("[data-panel]") ? ` in panel ${el.closest("[data-panel]").getAttribute("data-panel")}` : ""}`;

  // Elements poking out of the screen sideways, unless a scrolling box clips them.
  const W = window.innerWidth;
  const out = [];
  for (const el of document.querySelectorAll("body *")) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right <= W + 1 && r.left >= -1) continue;
    let p = el.parentElement, clipped = false;
    while (p && p !== document.body) {
      const s = getComputedStyle(p);
      if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) {
        const pr = p.getBoundingClientRect();
        if (pr.right <= W + 1 && pr.left >= -1) { clipped = true; break; }
      }
      p = p.parentElement;
    }
    if (!clipped) out.push(`${describe(el)} "${(el.textContent || "").trim().slice(0, 30)}" [${Math.round(r.left)}..${Math.round(r.right)}]`);
  }

  // Numbers drawn right-to-left: a .num that is not direction:ltr.
  const rtlNums = [...document.querySelectorAll(".num")].filter((el) => visible(el) && getComputedStyle(el).direction !== "ltr").length;

  // English left in an Arabic interface.
  const latin = [];
  if (ar) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement;
      if (!el || !visible(el) || el.closest("script,style,.num,kbd,code,[lang=en],[data-latin-ok],#legal-body,a[href^='mailto'],[data-message='user']")) continue;
      // News headlines and company names keep their own language.
      if (el.closest("[dir=auto],[data-names]")) continue;
      const words = (n.textContent.match(/[A-Za-z][A-Za-z.\/'-]*[A-Za-z]|[A-Za-z]/g) ?? []).filter((w) => !allowed.includes(w) && w.length > 1);
      if (words.length) latin.push({ text: n.textContent.trim().slice(0, 60), where: describe(el) });
    }
  }

  const aside = document.querySelector("aside");
  const copilot = document.querySelector("[data-copilot-pane]");
  const mid = (el) => (el && visible(el) ? el.getBoundingClientRect().left + el.getBoundingClientRect().width / 2 : null);
  return {
    lang: document.documentElement.lang,
    dir: document.documentElement.dir,
    sideways: document.scrollingElement.scrollWidth - W,
    out: out.slice(0, 8),
    outCount: out.length,
    rtlNums,
    latin,
    asideMid: mid(aside),
    copilotMid: mid(copilot),
    W,
  };
}

const browser = await chromium.launch({ channel: "chrome" });
let pages = 0;
for (const locale of ["ar", "en"]) {
  for (const [label, viewport] of [["1440", { width: 1440, height: 900 }], ["390", { width: 390, height: 844 }]]) {
    const context = await browser.newContext({ viewport, httpCredentials, isMobile: label === "390", hasTouch: label === "390" });
    for (const route of ROUTES) {
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.message.slice(0, 140)));
      page.on("console", (m) => m.type() === "error" && !/Failed to load resource/.test(m.text()) && errors.push(m.text().split("\n")[0].slice(0, 140)));
      const url = `${BASE_URL}${locale === "ar" ? `/ar${route === "/" ? "" : route}` : route}`;
      const res = await page.goto(url, { waitUntil: "networkidle" }).catch((e) => ({ status: () => String(e.message).slice(0, 60) }));
      await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(600);
      const tag = `${locale} ${label}px ${route}`;
      pages++;
      check(res.status() === 200, `${tag}: HTTP ${res.status()}`);
      const a = await page.evaluate(inspect, { ar: locale === "ar", allowed: [...LATIN_OK] });
      check(a.lang === locale && a.dir === (locale === "ar" ? "rtl" : "ltr"), `${tag}: lang/dir ${a.lang}/${a.dir}`);
      check(a.sideways <= 0, `${tag}: page ${a.sideways}px wider than the screen`);
      check(a.outCount === 0, `${tag}: ${a.outCount} element(s) outside the screen`, a.out.join(" | "));
      check(a.rtlNums === 0, `${tag}: ${a.rtlNums} number(s) not left-to-right`);
      if (!SITE.has(route) && label === "1440" && a.asideMid != null) {
        const sidebarRight = a.asideMid > a.W / 2;
        check(sidebarRight === (locale === "ar"), `${tag}: sidebar on the ${sidebarRight ? "right" : "left"}`);
        if (a.copilotMid != null) check((a.copilotMid < a.W / 2) === (locale === "ar"), `${tag}: Copilot on the ${a.copilotMid < a.W / 2 ? "left" : "right"}`);
      }
      const fonts = await renderedFonts(page);
      const bad = [...fonts.keys()].filter((f) => !ALLOWED_FONTS.some((ok) => f === ok || f.startsWith(`${ok} `)));
      check(bad.length === 0, `${tag}: drawn in ${bad.join(", ")}`, [...fonts].map(([f, n]) => `${f}:${n}`).join(", "));
      check(errors.length === 0, `${tag}: page errors`, errors.slice(0, 3).join(" | "));
      for (const l of a.latin) {
        const key = `${l.text} — ${l.where}`;
        if (!leaks.has(key)) leaks.set(key, new Set());
        leaks.get(key).add(`${label} ${route}`);
      }
      await page.close();
    }
    await context.close();
  }
}
await browser.close();

if (leaks.size) {
  console.log(`\nEnglish left in Arabic pages (${leaks.size}):`);
  for (const [k, where] of leaks) console.log(`  ${k}   [${[...where].slice(0, 3).join(", ")}${where.size > 3 ? ", …" : ""}]`);
}
console.log(`\n${pages} page views; ${failures.length} failure(s); ${leaks.size} English string(s) in Arabic pages`);
process.exit(failures.length || leaks.size ? 1 : 0);
