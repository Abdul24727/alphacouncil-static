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

for (const n of [1, 2, 3, 4, 5, 6, 7]) {
  console.log(`\n=== Phase ${n} ===`);
  const run = spawnSync(process.execPath, [path.join(here, `check-phase${n}.mjs`)], { stdio: "inherit", env: process.env });
  results.push([n, run.status === 0]);
}

console.log("\nSummary");
for (const [n, ok] of results) console.log(`  Phase ${n}: ${ok ? "PASS" : "FAIL"}`);
process.exit(results.every(([, ok]) => ok) ? 0 : 1);
