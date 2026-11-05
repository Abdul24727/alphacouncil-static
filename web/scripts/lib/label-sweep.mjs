// The English-label sweep of check-data-fixes.mjs (SWEEP=1), kept apart from the browser so it can be
// tested. An Arabic-stored statement line shows in English on an English page when the first dictionary
// pair with that Arabic gives it one (lib/data-labels.ts reads web/src/content/data-labels.json the same
// way). The sweep reads every listed company's statements, and what it could not check counts as much
// as what it found (review 02, 2026-11-06):
//   - a shown line the dictionary leaves in Arabic          -> fail, named;
//   - a request that failed (5xx, 429, 404, a network error) -> fail: that company was not checked;
//   - statements Pro-only from the first company (401/403)   -> "unavailable": not a pass, not a fail;
//   - Pro-only after some companies were read                -> fail (coverage incomplete), and what was
//     already found is still reported.
// The API answers 200 with an empty list for a company that has no statements, so a listed company has
// no other reason to refuse.

/** The two statements the Financials panel shows (components/stock/tabs.tsx). */
export const SHOWN = new Set(["Income Statement", "Balance Sheet"]);

export const normLabel = (s) => s.replace(/\s+/g, " ").trim().toLowerCase();
export const isArabic = (s) => /[؀-ۿ]/.test(s);

/** Arabic -> English, first pair wins (as lib/data-labels.ts). */
export function englishLookup(pairs) {
  const toEn = new Map();
  for (const [en, ar] of pairs) if (!toEn.has(normLabel(ar))) toEn.set(normLabel(ar), en);
  return toEn;
}

/**
 * @param {string[]} slugs every listed company
 * @param {(slug: string) => Promise<{status: number, body?: any}>} fetchStatements
 * @param {Map<string, string>} toEn from englishLookup
 */
export async function sweepLabels(slugs, fetchStatements, toEn) {
  const left = new Map(); // "label (section)" -> slugs
  const errors = [];
  let lines = 0;
  let read = 0;
  let gatedAt = null;
  for (const slug of slugs) {
    let res;
    try {
      res = await fetchStatements(slug);
    } catch (e) {
      errors.push(`${slug}: ${e instanceof Error ? e.message : String(e)}`);
      continue;
    }
    if (res.status === 401 || res.status === 403) {
      gatedAt = slug;
      break;
    }
    if (res.status !== 200) {
      errors.push(`${slug}: HTTP ${res.status}`);
      continue;
    }
    read++;
    for (const s of res.body?.statements ?? []) {
      if (!SHOWN.has(s.section)) continue;
      for (const row of s.rows ?? []) {
        lines++;
        if (isArabic(row.label) && !toEn.has(normLabel(row.label))) {
          const k = `${row.label} (${s.section})`;
          left.set(k, (left.get(k) ?? []).concat(slug));
        }
      }
    }
  }

  const problems = [];
  if (left.size) {
    const worst = [...left].sort((a, b) => b[1].length - a[1].length).slice(0, 12);
    problems.push(`${left.size} label(s) still Arabic: ` +
      worst.map(([k, t]) => `${k} on ${t.length} (e.g. ${t.slice(0, 3).join(", ")})`).join("; "));
  }
  if (errors.length) problems.push(`${errors.length} compan(ies) not checked: ${errors.slice(0, 5).join("; ")}`);
  if (gatedAt && read) problems.push(`statements turned Pro-only at ${gatedAt} after ${read} compan(ies): coverage incomplete`);
  if (!gatedAt && read === 0 && !errors.length) problems.push("no company was checked");

  const verdict = problems.length ? "fail" : gatedAt ? "unavailable" : "pass";
  return { verdict, lines, read, total: slugs.length, left, errors, gatedAt, problems };
}
