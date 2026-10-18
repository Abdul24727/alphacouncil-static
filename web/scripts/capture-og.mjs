// Link-preview cards (Open Graph / Twitter) for every page: public/og/en.png and ar.png, 1200×630.
//
//   node scripts/capture-og.mjs        # web dev server running (BASE_URL, default :3100); no API needed
//
// The card is drawn over a real page of the app, so it uses the app's own fonts (next/font)
// and BRAND.md tokens (globals.css): graphite, one orange, Archivo condensed, Martian Mono.
// No numbers on it, so it never goes stale. Words come from messages/<locale>.json.
// Uses the local Chrome.
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outDir = path.join(root, "public/og");
const SIZE = { width: 1200, height: 630 };
const EXCHANGES = ["TADAWUL", "ADX", "DFM", "QSE", "KSE", "BSE", "MSM"];

function card(m, locale) {
  const ar = locale === "ar";
  // site.hero.title marks the orange words with <em>…</em>.
  const title = m.site.hero.title.replace(/<em>(.*?)<\/em>/, '<span style="color:var(--color-signal)">$1</span>');
  const exchanges = EXCHANGES.map((e) => m.exchanges[e]).join(" · ");
  return `
  <div data-og style="position:fixed;inset:0;z-index:2147483647;background:var(--color-bg);color:var(--color-text);
       display:flex;flex-direction:column;padding:60px 64px 0;font-family:var(--font-sans)">
    <div style="display:flex;align-items:center;gap:16px">
      <span style="display:block;width:24px;height:24px;border-radius:3px;background:var(--color-signal)"></span>
      <span dir="ltr" style="font-size:34px;font-weight:700;font-stretch:112%;line-height:1">AlphaCouncil</span>
    </div>
    <h1 style="margin:auto 0;font-weight:${ar ? 700 : 800};font-stretch:80%;letter-spacing:-0.01em;
        ${ar ? "font-size:124px;line-height:1.2" : "font-size:112px;line-height:0.92;text-transform:uppercase"}">${title}</h1>
    <div style="display:flex;align-items:center;justify-content:space-between;gap:24px;height:96px;
         border-top:1px solid var(--color-line);color:var(--color-muted)">
      <span style="${ar ? "font-size:22px" : "font-family:var(--font-mono);font-size:17px;text-transform:uppercase;letter-spacing:0.08em"}">${exchanges}</span>
      <span dir="ltr" style="font-family:var(--font-mono);font-size:17px;letter-spacing:0.08em;color:var(--color-text)">alphacouncil.tech</span>
    </div>
  </div>`;
}

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });
for (const locale of ["en", "ar"]) {
  const messages = JSON.parse(await readFile(path.join(root, `messages/${locale}.json`), "utf-8"));
  const page = await browser.newPage({ viewport: SIZE, deviceScaleFactor: 1 });
  // A static page (no API call) in the card's language: lang, dir and font faces come with it.
  await page.goto(`${BASE_URL}${locale === "ar" ? "/ar" : ""}/legal`, { waitUntil: "networkidle" });
  await page.evaluate((html) => document.body.insertAdjacentHTML("beforeend", html), card(messages, locale));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
  const file = path.join(outDir, `${locale}.png`);
  await page.screenshot({ path: file, clip: { x: 0, y: 0, ...SIZE } });
  console.log("saved", path.relative(root, file));
  await page.close();
}
await browser.close();
