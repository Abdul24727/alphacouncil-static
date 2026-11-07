// The legal texts' "Contact page" address, and what a visitor lands on. Signed out, GET only, no click.
import { createRequire } from "node:module";
import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
const require = createRequire("C:/projects/alphacouncil-platform/web/package.json");
const { chromium } = require("playwright-core");
const OUT = process.env.OUT;
const BASE = "https://alphacouncil.tech";
const UA = "AlphaCouncil lawyer-pack check";
const lines = [`the legal texts' contact address, ${new Date().toISOString().replace("T", " ").slice(0, 19)} UTC`, ""];

lines.push("Where the legal texts give it (page-text/, lines after the two-line header):");
for (const doc of ["terms", "privacy", "refunds", "ai", "cookies"]) {
  for (const loc of ["en", "ar"]) {
    const t = (await readFile(`${OUT}/page-text/legal-${doc}.${loc}.txt`, "utf8")).split("\n").slice(2);
    const hits = t.map((l, i) => [i + 3, l]).filter(([, l]) => l.includes("contact.html"));
    for (const [n, l] of hits) lines.push(`  legal-${doc}.${loc}.txt:${n}: ${l.trim().slice(0, 120)}`);
  }
}
lines.push("", "What the addresses answer (curl, first answer, then after redirects):");
for (const path of ["/contact.html", "/ar/contact.html", "/contact"]) {
  const first = execFileSync("curl", ["-s", "-o", "/dev/null", "-A", UA, "--max-time", "30", "-w", "%{http_code} %{redirect_url}", BASE + path]).toString();
  const final = execFileSync("curl", ["-s", "-o", "/dev/null", "-L", "-A", UA, "--max-time", "30", "-w", "%{http_code} %{url_effective}", BASE + path]).toString();
  lines.push(`  ${path}  first ${first.trim() || "-"}  final ${final.trim()}`);
}
lines.push("", "What /legal shows a visitor (the redirect's target), lines naming a contact detail:");
const browser = await chromium.launch({ channel: "chrome" });
for (const loc of ["", "/ar"]) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const res = await page.goto(`${BASE}${loc}/legal`, { waitUntil: "networkidle", timeout: 60000 });
  const text = await page.evaluate(() => document.body.innerText);
  await writeFile(`${OUT}/page-text/legal-index.${loc ? "ar" : "en"}.txt`, `${BASE}${loc}/legal\nstatus ${res.status()}, final ${page.url()}\n\n${text}\n`);
  const contact = text.split("\n").filter((l) => /@|contact|تواصل|اتصل|Building|مبنى/i.test(l));
  lines.push(`  ${loc || "/en"}/legal: status ${res.status()}, ${text.length} chars; email addresses on the page: ${(text.match(/[\w.+-]+@[\w.-]+\.\w+/g) || []).length}`);
  for (const l of contact) lines.push(`    ${l.trim().slice(0, 160)}`);
  await page.close();
}
await browser.close();
await writeFile(`${OUT}/contact-check.txt`, lines.join("\n") + "\n");
console.log(lines.join("\n"));
