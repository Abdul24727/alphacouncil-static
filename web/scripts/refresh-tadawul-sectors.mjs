// Refresh api/app/data/tadawul_sectors.json from the Saudi Exchange's Main Market Watch: the
// companies under each sector (industry group), in English and Arabic.
//
// The exchange refuses automated (headless) browsers, so its two pages are read in an ordinary
// browser:
//   1. Open https://www.saudiexchange.sa/wps/portal/saudiexchange/ourmarkets/main-market-watch?locale=en
//      and, once the table shows, run READ_PAGE (below) in the browser's console. Save what it
//      prints as en.json. Do the same with ?locale=ar and save ar.json.
//   2. node scripts/refresh-tadawul-sectors.mjs en.json ar.json [--dry-run]
//      prints what changed (added, removed, moved, renamed) and, without --dry-run, writes the file.
// The two pages must list the same companies under the same sectors, or nothing is written.
// Then commit the file and release as usual; the API reads it when it starts (api/app/universe.py).
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const READ_PAGE = `copy(JSON.stringify({ url: location.href, groups: [...document.getElementById("marketWatchTable1").tBodies[0].rows].reduce((out, r) => { if (r.classList.contains("dtrg-group")) out.push({ name: r.textContent.trim(), symbols: [] }); else { const m = (r.cells[0]?.innerText.trim() ?? "").match(/(\\d{4})\\s*$/); if (m && out.length) out.at(-1).symbols.push(m[1]); } return out; }, []) }))`;

const here = path.dirname(fileURLToPath(import.meta.url));
const FILE = path.resolve(here, "../../api/app/data/tadawul_sectors.json");
const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const [enFile, arFile] = args.filter((a) => !a.startsWith("--"));
if (!enFile || !arFile) {
  console.error("usage: node scripts/refresh-tadawul-sectors.mjs en.json ar.json [--dry-run]\n\nREAD_PAGE:\n" + READ_PAGE);
  process.exit(2);
}
const en = JSON.parse(await readFile(enFile, "utf-8"));
const ar = JSON.parse(await readFile(arFile, "utf-8"));

const problems = [];
if (!/[?&]locale=en/.test(en.url) || !/[?&]locale=ar/.test(ar.url)) problems.push("en.json must come from ?locale=en and ar.json from ?locale=ar");
if (en.groups.length !== ar.groups.length) problems.push(`${en.groups.length} English sectors, ${ar.groups.length} Arabic`);
en.groups.forEach((g, i) => {
  if (ar.groups[i] && g.symbols.join() !== ar.groups[i].symbols.join()) problems.push(`${g.name} / ${ar.groups[i].name}: members differ`);
});
const all = en.groups.flatMap((g) => g.symbols);
if (new Set(all).size !== all.length) problems.push("a company is listed twice");
if (all.length < 200) problems.push(`only ${all.length} companies read`);
if (problems.length) {
  console.error(`not written:\n  ${problems.join("\n  ")}`);
  process.exit(1);
}

const doc = {
  source: "Saudi Exchange, Main Market Watch, companies grouped by sector (industry group), English and Arabic pages",
  source_urls: { en: en.url, ar: ar.url },
  retrieved: new Date().toISOString().slice(0, 10),
  companies: all.length,
  sectors: en.groups.map((g, i) => ({ en: g.name, ar: ar.groups[i].name, symbols: g.symbols })),
};

const old = JSON.parse(await readFile(FILE, "utf-8"));
const before = new Map(old.sectors.flatMap((s) => s.symbols.map((x) => [x, s.en])));
const after = new Map(doc.sectors.flatMap((s) => s.symbols.map((x) => [x, s.en])));
const added = [...after.keys()].filter((x) => !before.has(x));
const removed = [...before.keys()].filter((x) => !after.has(x));
const moved = [...after.keys()].filter((x) => before.has(x) && before.get(x) !== after.get(x));
const renamed = doc.sectors.filter((s) => !old.sectors.some((o) => o.en === s.en && o.ar === s.ar)).map((s) => `${s.en} / ${s.ar}`);
console.log(`${doc.sectors.length} sectors, ${doc.companies} companies (was ${old.sectors.length}, ${old.companies}; list of ${old.retrieved})`);
console.log(`added: ${added.join(" ") || "none"}`);
console.log(`removed: ${removed.join(" ") || "none"}`);
console.log(`moved: ${moved.map((x) => `${x} ${before.get(x)} -> ${after.get(x)}`).join(", ") || "none"}`);
console.log(`sector names new or changed: ${renamed.join(", ") || "none"}`);
if (!dryRun) {
  await writeFile(FILE, JSON.stringify(doc, null, 1) + "\n", "utf-8");
  console.log(`wrote ${path.relative(process.cwd(), FILE)}`);
}
