// Phase 1 "Done when": every signed-in page renders inside the new shell on staging;
// no teal, purple or Inter anywhere.
//
// Signs up a fresh account, then opens every app page signed in (English and Arabic):
// the shell (sidebar, work area, Copilot) must be there. On every page, app and public,
// it reads every element's computed colours (no teal or purple hue) and asks Chrome which
// fonts it actually drew (no Inter, nor any face but the three brand ones).
//
//   BASE_URL=http://localhost:3100 node scripts/check-phase1.mjs
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;

const APP = [
  "/home", "/portfolio", "/screener", "/markets", "/templates", "/templates/earnings-season",
  "/templates/dividend-hunter", "/templates/sector-vs-sector", "/dashboards", "/settings",
  "/t/2222", "/t/2222/financials", "/t/2222/council", "/t/2222/ownership", "/t/2222/calendar",
];
const SITE = ["/", "/pricing", "/methodology", "/legal", "/legal/privacy", "/login", "/signup", "/forgot-password", "/reset-password"];
const ALLOWED_FONTS = ["Archivo", "Martian Mono", "IBM Plex Sans Arabic"];

const failures = [];
const check = (ok, label, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${!ok && detail ? `\n        ${detail}` : ""}`);
  if (!ok) failures.push(label);
};

function colours() {
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const [r, g, b, a = "1"] = m[1].split(/[ ,/]+/).filter(Boolean);
    return { r: +r / 255, g: +g / 255, b: +b / 255, a: +a };
  };
  const bad = new Set();
  for (const el of document.querySelectorAll("body *")) {
    const s = getComputedStyle(el);
    if (s.display === "none" || s.visibility === "hidden") continue;
    const props = ["color", "backgroundColor", "borderTopColor", "borderBottomColor", "borderLeftColor", "borderRightColor"];
    if (el instanceof SVGElement) props.push("fill", "stroke");
    for (const p of props) {
      const c = parse(s[p] || "");
      if (!c || c.a === 0) continue;
      const max = Math.max(c.r, c.g, c.b), min = Math.min(c.r, c.g, c.b), l = (max + min) / 2, d = max - min;
      if (!d) continue;
      const sat = d / (1 - Math.abs(2 * l - 1));
      let h = max === c.r ? 60 * (((c.g - c.b) / d) % 6) : max === c.g ? 60 * ((c.b - c.r) / d + 2) : 60 * ((c.r - c.g) / d + 4);
      h = (h + 360) % 360;
      if (sat > 0.25 && l > 0.12 && l < 0.9 && ((h >= 160 && h <= 200) || (h >= 255 && h <= 320))) {
        bad.add(`${el.tagName.toLowerCase()} ${p} ${s[p]}`);
      }
    }
  }
  return [...bad].slice(0, 5);
}

async function drawnFonts(page, limit = 500) {
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
  const used = new Set();
  for (const id of [...new Set(parents)].slice(0, limit)) {
    const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId: id }).catch(() => ({ fonts: [] }));
    for (const f of fonts) used.add(f.familyName);
  }
  await cdp.detach();
  return [...used];
}

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, httpCredentials });
const page = await context.newPage();

// A signed-in session for the app pages.
await page.goto(`${BASE_URL}/signup?next=/home`);
await page.getByLabel("Email").fill(`phase1-${Date.now()}@example.com`);
await page.getByLabel("Password").fill("a long test password");
await page.getByRole("checkbox").check();
await page.getByRole("button", { name: "Create account" }).click();
await page.waitForURL((u) => u.pathname === "/home", { timeout: 30000 }); // not /signup?next=/home
check(true, "signed up and signed in");

const settle = async () => {
  await page.waitForFunction(() => !document.querySelector("[aria-busy]"), null, { timeout: 30000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
};

for (const locale of ["en", "ar"]) {
  for (const route of [...APP, ...SITE]) {
    const url = `${BASE_URL}${locale === "ar" ? `/ar${route === "/" ? "" : route}` : route}`;
    const res = await page.goto(url, { waitUntil: "networkidle" });
    await settle();
    const tag = `${locale} ${route}`;
    if (APP.includes(route)) {
      const shell = await page.evaluate(() => ({
        sidebar: !!document.querySelector("aside")?.checkVisibility(),
        copilot: !!document.querySelector("[data-copilot-pane]")?.checkVisibility(),
        work: !!document.querySelector("main")?.checkVisibility(),
        signedIn: !document.querySelector("[data-signin-prompt]"),
      }));
      check(res.status() === 200 && shell.sidebar && shell.copilot && shell.work && shell.signedIn,
        `${tag}: renders signed in, inside the shell (sidebar, work area, Copilot)`, JSON.stringify({ status: res.status(), ...shell }));
    } else {
      check(res.status() === 200, `${tag}: public page renders`, `HTTP ${res.status()}`);
    }
    const bad = await page.evaluate(colours);
    check(bad.length === 0, `${tag}: no teal or purple`, bad.join(" | "));
    const fonts = await drawnFonts(page);
    const off = fonts.filter((f) => !ALLOWED_FONTS.some((ok) => f === ok || f.startsWith(`${ok} `)));
    check(off.length === 0, `${tag}: drawn only in the brand faces (no Inter)`, `also: ${off.join(", ")}`);
  }
}

await browser.close();
console.log(failures.length ? `\nPhase 1 done-when: ${failures.length} check(s) failed` : "\nPhase 1 done-when: all checks passed");
process.exit(failures.length ? 1 : 0);
