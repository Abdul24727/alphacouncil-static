// Every phase's "Done when" check, one after another, with a summary at the end.
//
//   BASE_URL=https://beta.alphacouncil.tech STAGING_AUTH=user:password node scripts/check-all.mjs
//
// STAGING_AUTH is the beta site's basic-auth login; it is passed to the browser only and
// never printed. The checks sign up test accounts named phase*-<time>@example.com.
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const results = [];

// Phases 1-7, then no English on Arabic pages (QA audit 8a, 8b), signed out and signed in.
const RUNS = [
  ...[1, 2, 3, 4, 5, 6, 7].map((n) => [`Phase ${n}`, `check-phase${n}.mjs`, {}]),
  ["Arabic, signed out", "check-arabic.mjs", {}],
  ["Arabic, signed in", "check-arabic.mjs", { SIGNED_IN: "1" }],
];
for (const [name, script, env] of RUNS) {
  console.log(`\n=== ${name} ===`);
  const run = spawnSync(process.execPath, [path.join(here, script)], { stdio: "inherit", env: { ...process.env, ...env } });
  results.push([name, run.status === 0]);
}

console.log("\nSummary");
for (const [name, ok] of results) console.log(`  ${name}: ${ok ? "PASS" : "FAIL"}`);
process.exit(results.every(([, ok]) => ok) ? 0 : 1);
