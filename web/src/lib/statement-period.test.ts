// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { monthYear, statementColumns } from "./statement-period.ts";

// Aramco (2222) as /v1/tickers/2222/statements answered on beta after the 2026-11-03 publish.
const YEARS = [2025, 2026];
const INCOME = {
  periods: { "2026": { period: "TTM", period_end: "2026-06", aggregation: "sum_quarters", source_columns: ["2025-09", "2025-12", "2026-03", "2026-06"] } },
  rows: [{ values: { "2026": 1823483 } }, { values: { "2026": -887177 } }],
};
const BALANCE = {
  periods: {
    "2025": { period: "FY", period_end: "2025-12", aggregation: "year_end_snapshot", source_columns: ["2025-12"] },
    "2026": { period: "Q", period_end: "2026-06", aggregation: "quarter_end_snapshot", source_columns: ["2026-06"] },
  },
  rows: [{ values: { "2025": 243099, "2026": 167387 } }],
};

test("statement period: a month and year in both languages", () => {
  assert.equal(monthYear("2026-06", "en"), "Jun 2026");
  assert.equal(monthYear("2026-06", "ar"), "يونيو 2026");
  assert.equal(monthYear("2025-12-31", "en"), "Dec 2025");
  assert.equal(monthYear("2026-13", "en"), null);
  assert.equal(monthYear(null, "ar"), null);
});

test("statement period: a trailing income statement is not headed FY, and its empty year is dropped", () => {
  const en = statementColumns(YEARS, INCOME.periods, INCOME.rows, "en");
  assert.deepEqual(en.map((c) => [c.year, c.heading]), [[2026, "TTM Jun 2026"]]);
  assert.match(en[0].note ?? "", /four quarters to Jun 2026 added together/);
  const ar = statementColumns(YEARS, INCOME.periods, INCOME.rows, "ar");
  assert.deepEqual(ar.map((c) => c.heading), ["12 شهرًا حتى يونيو 2026"]);
  assert.match(ar[0].note ?? "", /مجموع الأرباع الأربعة/);
});

test("statement period: a quarter-end balance sheet beside a fiscal year-end", () => {
  const en = statementColumns(YEARS, BALANCE.periods, BALANCE.rows, "en");
  assert.deepEqual(en.map((c) => [c.heading, c.note]), [
    ["Jun 2026", "Jun 2026: the position at that quarter-end, not a fiscal year-end."],
    ["FY2025", null],
  ]);
  const ar = statementColumns(YEARS, BALANCE.periods, BALANCE.rows, "ar");
  assert.deepEqual(ar.map((c) => c.heading), ["يونيو 2026", "2025"]);
});

test("statement period: annual statements read as before", () => {
  const years = [2021, 2022, 2023, 2024, 2025];
  const periods = Object.fromEntries(years.map((y) => [String(y), { period: "FY", period_end: `${y}-12`, aggregation: null }]));
  const rows = [{ values: Object.fromEntries(years.map((y) => [String(y), 1])) }];
  const cols = statementColumns(years, periods, rows, "en");
  assert.deepEqual(cols.map((c) => c.heading), ["FY2025", "FY2024", "FY2023", "FY2022", "FY2021"]);
  assert.ok(cols.every((c) => c.note === null));
});

test("statement period: the old response shape keeps its fiscal-year headings", () => {
  const cols = statementColumns(YEARS, {}, [{ values: { "2025": 1, "2026": 2 } }], "en");
  assert.deepEqual(cols.map((c) => c.heading), ["FY2026", "FY2025"]);
  assert.deepEqual(statementColumns(YEARS, undefined, [{ values: { "2025": 1 } }], "ar").map((c) => c.heading), ["2025"]);
});

test("statement period: an undated or unknown column claims no period", () => {
  const cols = statementColumns([2026], { "2026": { period: null, period_end: null } }, [{ values: { "2026": 5 } }], "en");
  assert.deepEqual(cols.map((c) => c.heading), ["2026"]);
  assert.match(cols[0].note ?? "", /does not say which period/);
  const q = statementColumns([2026], { "2026": { period: "Q", period_end: "2026-03", aggregation: "single_quarter" } }, [{ values: { "2026": 5 } }], "en");
  assert.deepEqual(q.map((c) => c.heading), ["3M Mar 2026"]);
});

test("statement period: a statement with no figures at all keeps every year rather than none", () => {
  assert.deepEqual(statementColumns(YEARS, {}, [{ values: {} }], "en").map((c) => c.year), [2026, 2025]);
});

test("statement period: newest first, so a phone opens on the newest period beside the labels", () => {
  // The response lists years oldest first; the order shown must not depend on it.
  const years = [2023, 2021, 2025, 2022, 2024];
  const rows = [{ values: Object.fromEntries(years.map((y) => [String(y), 1])) }];
  assert.deepEqual(statementColumns(years, {}, rows, "en").map((c) => c.year), [2025, 2024, 2023, 2022, 2021]);
  assert.deepEqual(statementColumns(years, {}, rows, "ar").map((c) => c.year), [2025, 2024, 2023, 2022, 2021]);
  assert.deepEqual(years, [2023, 2021, 2025, 2022, 2024]); // the caller's array is not reordered
});
