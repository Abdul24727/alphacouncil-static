// Phase 6 "Done when": the landing page passes the BRAND.md banned list line by line.
// Checked in English and Arabic at 1440px and 390px. Also: every link on the public pages
// resolves, no page scrolls sideways at 390px, and the legal pages carry their full text.
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase6.mjs
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;
const here = path.dirname(fileURLToPath(import.meta.url));

const failures = [];
const check = (ok, label, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${!ok && detail ? `\n        ${detail}` : ""}`);
  if (!ok) failures.push(label);
};

// BRAND.md colours; anything else on the page is reported.
const BRAND = {
  bg: "#0c0d10", panel: "#14161b", "panel-raised": "#1d2028", line: "#272b34", text: "#eceef2",
  "text-soft": "#b8beca", muted: "#9299a8", signal: "#ff6a1a", "signal-ink": "#170800",
  gain: "#3fd98a", loss: "#ff4d5e", stale: "#f2b134", "neutral-seat": "#4a505c",
};
const ALLOWED_FONTS = ["Archivo", "Martian Mono", "IBM Plex Sans Arabic"];

const browser = await chromium.launch({ channel: "chrome" });
const context0 = await browser.newContext({ httpCredentials });
const api = async (p) => (await context0.request.get(`${BASE_URL}/api/v1${p}`)).json();
const exchanges = await api("/market/exchanges");
const plans = await api("/plans");
const expected = {
  exchanges: String(exchanges.length),
  equities: String(exchanges.reduce((n, e) => n + e.equities, 0)),
  perExchange: exchanges.map((e) => String(e.equities)),
  pro: String(plans.plans.find((p) => p.id === "pro").price_sar),
};

/** Runs in the page: everything the banned list needs, measured from computed styles. */
function audit(brand) {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none" && Number(s.opacity) > 0;
  };
  const all = [...document.querySelectorAll("body *")].filter(visible);
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const [r, g, b, a = "1"] = m[1].split(/[ ,/]+/).filter(Boolean);
    return { r: +r, g: +g, b: +b, a: +a };
  };
  const hex = ({ r, g, b }) => "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const hsl = ({ r, g, b }) => {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2, d = max - min;
    if (!d) return { h: 0, s: 0, l };
    const s = d / (1 - Math.abs(2 * l - 1));
    const h = max === r ? 60 * (((g - b) / d) % 6) : max === g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
    return { h: (h + 360) % 360, s, l };
  };
  const brandHex = new Set(Object.values(brand));
  const describe = (el) => `${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}.${[...el.classList].slice(0, 3).join(".")} "${(el.textContent || "").trim().slice(0, 30)}"`;

  const offBrand = new Map(), tealPurple = [], gradients = [], glows = [];
  for (const el of all) {
    const s = getComputedStyle(el);
    const props = ["color", "backgroundColor", "borderTopColor", "borderBottomColor", "borderLeftColor", "borderRightColor", "outlineColor", "fill", "stroke"];
    for (const p of props) {
      if ((p === "fill" || p === "stroke") && !(el instanceof SVGElement)) continue; // HTML elements report a default black
      if (p.startsWith("border") && parseFloat(s[p.replace("Color", "Width")]) === 0) continue;
      if (p === "outlineColor" && s.outlineStyle === "none") continue;
      const c = parse(s[p] || "");
      if (!c || c.a === 0) continue;
      const { h, s: sat, l } = hsl(c);
      if (sat > 0.25 && l > 0.12 && l < 0.9 && ((h >= 160 && h <= 200) || (h >= 255 && h <= 320))) tealPurple.push(`${describe(el)} ${p} ${hex(c)}`);
      if (!brandHex.has(hex(c))) offBrand.set(hex(c), `${describe(el)} ${p}`);
    }
    if (/gradient/.test(s.backgroundImage)) gradients.push(describe(el));
    if (s.webkitBackgroundClip === "text" || s.backgroundClip === "text") gradients.push(`text clip: ${describe(el)}`);
    if (s.boxShadow !== "none" || s.textShadow !== "none" || /drop-shadow|blur/.test(s.filter)) glows.push(describe(el));
  }

  // Emoji: default-emoji code points, any pictograph forced to emoji (U+FE0F), and flags.
  const text = document.body.innerText + " " + [...document.querySelectorAll("[alt],[aria-label],[title]")].map((e) => [e.getAttribute("alt"), e.getAttribute("aria-label"), e.getAttribute("title")].join(" ")).join(" ");
  const emoji = text.match(/\p{Emoji_Presentation}|\p{Extended_Pictographic}️|\p{Regional_Indicator}/gu) ?? [];

  // Icon in a rounded box: a filled or outlined rounded element whose only content is an icon.
  const iconBoxes = all.filter((el) => {
    const s = getComputedStyle(el);
    const boxed = parseFloat(s.borderTopLeftRadius) > 0 && ((parse(s.backgroundColor)?.a ?? 0) > 0 || parseFloat(s.borderTopWidth) > 0);
    const kids = [...el.children];
    return boxed && kids.length === 1 && /^(svg|img)$/i.test(kids[0].tagName) && !(el.textContent || "").trim() && el.getBoundingClientRect().width < 96;
  }).map(describe);

  // Grids of identical cards: 3+ siblings that are each a filled or fully outlined rounded box.
  const isCard = (el) => {
    const s = getComputedStyle(el);
    const fill = (parse(s.backgroundColor)?.a ?? 0) > 0;
    const ring = ["Top", "Right", "Bottom", "Left"].every((d) => parseFloat(s[`border${d}Width`]) > 0);
    return (fill || ring) && parseFloat(s.borderTopLeftRadius) > 0 && el.getBoundingClientRect().height > 80;
  };
  const cardGrids = all.filter((el) => {
    const kids = [...el.children].filter(visible);
    return kids.length >= 3 && kids.filter(isCard).length >= 3;
  }).map(describe);

  // Eyebrows: a small all-caps line directly above a heading.
  const eyebrows = [...document.querySelectorAll("h1,h2,h3")].filter(visible).flatMap((h) => {
    let prev = h.previousElementSibling;
    if (!prev && h.parentElement) prev = h.parentElement.previousElementSibling;
    if (!prev || !visible(prev)) return [];
    const s = getComputedStyle(prev);
    const t = (prev.textContent || "").trim();
    const caps = s.textTransform === "uppercase" || (t.length > 2 && t === t.toUpperCase() && /[A-Z]/.test(t));
    return caps && parseFloat(s.fontSize) < 14 && t.length < 48 ? [`"${t}" above ${h.tagName} "${h.textContent.trim().slice(0, 30)}"`] : [];
  });

  // Fake browser dots: 3+ small round siblings in a row. Stat-chip rows: 3+ chips holding numbers.
  const round = (el) => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width <= 16 && Math.abs(r.width - r.height) < 1 && parseFloat(s.borderTopLeftRadius) >= r.width / 2 - 0.5;
  };
  const dots = all.filter((el) => [...el.children].filter((k) => visible(k) && round(k)).length >= 3).map(describe);
  const chip = (el) => {
    const s = getComputedStyle(el);
    return parseFloat(s.borderTopLeftRadius) > 0 && ((parse(s.backgroundColor)?.a ?? 0) > 0 || parseFloat(s.borderTopWidth) > 0) && /\d/.test(el.textContent || "");
  };
  const statChips = all.filter((el) => [...el.children].filter((k) => visible(k) && chip(k)).length >= 3).map(describe);

  // Numbers: every visible digit must sit inside a [data-db] element.
  const loose = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || !/\d/.test(n.textContent) || !visible(el) || el.closest("script,style,noscript")) continue;
    if (!el.closest("[data-db]")) loose.push(`"${n.textContent.trim().slice(0, 40)}" in ${describe(el)}`);
  }
  const db = [...document.querySelectorAll("[data-db]")].filter(visible).map((e) => e.textContent.trim());

  return {
    offBrand: [...offBrand].map(([c, where]) => `${c} at ${where}`),
    tealPurple, gradients, glows, emoji, iconBoxes, cardGrids, eyebrows, dots, statChips, loose, db,
    coverage: [...document.querySelectorAll("[data-coverage] [data-db]")].map((e) => e.textContent.trim()),
    exchangeCounts: [...document.querySelectorAll("[data-exchanges] [data-db]")].filter(visible).map((e) => e.textContent.trim()),
    plan: document.querySelector("[data-plans] [data-db]")?.textContent.trim(),
    sideways: document.scrollingElement.scrollWidth - window.innerWidth,
  };
}

/** Fonts actually used to draw each text node (Chrome DevTools protocol), not the CSS stacks. */
async function renderedFonts(page) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const { root } = await cdp.send("DOM.getDocument", { depth: -1 });
  const used = new Map();
  const walk = async (node) => {
    if (node.nodeType === 3 && node.nodeValue.trim()) {
      const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: node.parentId ?? node.nodeId }).catch(() => ({ fonts: [] }));
      for (const f of fonts) used.set(f.familyName, (used.get(f.familyName) ?? 0) + f.glyphCount);
    }
    if (node.nodeName === "SCRIPT" || node.nodeName === "STYLE" || node.nodeName === "NOSCRIPT") return;
    for (const child of node.children ?? []) {
      child.parentId = node.nodeId;
      await walk(child);
    }
  };
  await walk(root);
  return used;
}

for (const locale of ["en", "ar"]) {
  for (const [label, viewport] of [["1440", { width: 1440, height: 900 }], ["390", { width: 390, height: 844 }]]) {
    const context = await browser.newContext({ viewport, httpCredentials, isMobile: label === "390", hasTouch: label === "390" });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message.slice(0, 160)));
    await page.goto(`${BASE_URL}${locale === "ar" ? "/ar" : "/"}`, { waitUntil: "networkidle" });
    await page.locator("[data-coverage]").waitFor({ timeout: 30000 });
    await page.locator("[data-exchanges] [data-db]").first().waitFor({ timeout: 30000 });
    await page.evaluate(() => document.fonts.ready);
    const a = await page.evaluate(audit, BRAND);
    const fonts = await renderedFonts(page);
    const tag = `landing ${locale} ${label}px`;
    const list = (xs) => xs.slice(0, 6).join(" | ");

    check(a.tealPurple.length === 0, `${tag}: no teal or purple`, list(a.tealPurple));
    check(a.offBrand.length === 0, `${tag}: only BRAND.md colours`, list(a.offBrand));
    check(a.gradients.length === 0, `${tag}: no gradient text or background`, list(a.gradients));
    check(a.glows.length === 0, `${tag}: no glow effects (shadows, blurs)`, list(a.glows));
    check(a.emoji.length === 0, `${tag}: no emoji or flag emoji`, a.emoji.join(" "));
    check(a.iconBoxes.length === 0, `${tag}: no icon-in-a-rounded-box`, list(a.iconBoxes));
    check(a.cardGrids.length === 0, `${tag}: no grid of identical feature cards`, list(a.cardGrids));
    check(a.eyebrows.length === 0, `${tag}: no small uppercase eyebrow above a heading`, list(a.eyebrows));
    check(a.dots.length === 0, `${tag}: no fake browser dots`, list(a.dots));
    check(a.statChips.length === 0, `${tag}: no repeated stat-chip rows`, list(a.statChips));
    // Platform names carry the style ("Archivo SemiBold", "Martian Mono SemiExpanded").
    const banned = [...fonts.keys()].filter((f) => !ALLOWED_FONTS.some((ok) => f === ok || f.startsWith(`${ok} `)));
    check(banned.length === 0, `${tag}: rendered fonts are ${[...fonts.keys()].join(", ")}`, `not allowed: ${banned.join(", ")}`);
    check(a.loose.length === 0, `${tag}: every number on screen sits in a database value (${a.db.length} found)`, list(a.loose));
    const dbOk =
      a.coverage.join(",") === `${expected.exchanges},${expected.equities}` &&
      a.exchangeCounts.join(",") === expected.perExchange.join(",") &&
      a.plan === expected.pro;
    check(dbOk, `${tag}: those values equal the API (${expected.exchanges} exchanges, ${expected.equities} equities, Pro ${expected.pro})`,
      `coverage ${a.coverage} · exchanges ${a.exchangeCounts} · pro ${a.plan}`);
    check(a.sideways <= 0, `${tag}: no sideways scroll`, `${a.sideways}px wider than the screen`);
    check(errors.length === 0, `${tag}: no page errors`, errors.join(" | "));
    await context.close();
  }
}

// Every link on the public pages resolves (both languages).
const pages = ["/", "/pricing", "/methodology", "/legal", "/legal/terms", "/legal/privacy", "/legal/refunds", "/legal/cookies", "/legal/ai-financial-disclaimer"];
const seen = new Map();
const ctx = await browser.newContext({ httpCredentials });
const page = await ctx.newPage();
for (const p of [...pages, ...pages.map((p) => `/ar${p === "/" ? "" : p}`)]) {
  await ctx.clearCookies();
  const res = await page.goto(BASE_URL + p, { waitUntil: "domcontentloaded" });
  check(res.status() === 200, `page ${p} → ${res.status()}`);
  const hrefs = await page.locator("a[href]").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  for (const h of hrefs) if (h.startsWith("/") && !seen.has(h.split("#")[0])) seen.set(h.split("#")[0], p);
}
const broken = [];
for (const [href, from] of seen) {
  await ctx.clearCookies();
  const res = await ctx.request.get(BASE_URL + href, { maxRedirects: 5 });
  if (res.status() !== 200) broken.push(`${href} (${res.status()}, linked from ${from})`);
}
check(broken.length === 0, `all ${seen.size} internal links on the public pages resolve`, broken.join(" | "));

// Legal pages carry the full signed-off text, and the English ones their content hash.
for (const doc of ["terms", "privacy", "refunds", "cookies", "ai-financial-disclaimer"]) {
  for (const locale of ["en", "ar"]) {
    const src = JSON.parse(await readFile(path.join(here, `../src/content/legal/${doc}.${locale}.json`), "utf8"));
    await ctx.clearCookies(); // next-intl's locale cookie would send an unprefixed URL to /ar
    await page.goto(`${BASE_URL}${locale === "ar" ? "/ar" : ""}/legal/${doc}`);
    // The rendered document has exactly the imported text (compared as text: nesting differs).
    const { same, hash, words } = await page.evaluate((html) => {
      const norm = (t) => t.replace(/\s+/g, " ").trim();
      const body = document.querySelector("#legal-body");
      const tpl = document.createElement("template");
      tpl.innerHTML = html;
      const want = norm(tpl.content.textContent);
      return { same: norm(body.textContent) === want, hash: body.getAttribute("data-canonical-hash"), words: want.split(" ").length };
    }, src.html);
    check(same && hash === (src.canonicalHash ?? null), `legal ${locale} ${doc}: full text (${words} words)${hash ? `, hash ${hash.slice(0, 12)}…` : ""}`);
  }
}
await ctx.close();
await context0.close();
await browser.close();

console.log(failures.length ? `\nPhase 6 done-when: ${failures.length} check(s) failed` : "\nPhase 6 done-when: all checks passed");
process.exit(failures.length ? 1 : 0);
