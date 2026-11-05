// Run with: npm test
// The real lookup (lib/data-labels-core.ts) on the real dictionary: a bank's income-statement sub-line
// says what it is inside the income statement, and nothing else moves (review 04, 2026-11-06).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { makeDataLabel, type LabelData } from "./data-labels-core.ts";

const data = JSON.parse(readFileSync(new URL("../content/data-labels.json", import.meta.url), "utf8")) as LabelData;
const dataLabel = makeDataLabel(data);
const IS = "Income Statement";
const BS = "Balance Sheet";

// Stored text on Gulf pages (Arabic) and Saudi pages (English) for the same Argaam row ids, every one a
// child of "Special commission income/expense" in all 39 income statements harvested (2026-11-06).
const SUBLINES: [string, string, string, string][] = [
  ["الاستثمارات", "Investments", "Special commission income from investments", "دخل العمولات الخاصة من الاستثمارات"],
  ["أرصدة لدى البنوك والمؤسسات المالية", "Due from Banks & Other FI's", "Special commission income from banks & other FIs", "دخل العمولات الخاصة من الأرصدة لدى البنوك والمؤسسات المالية"],
  ["قروض و سلف", "Loans and Advances", "Special commission income from loans and advances", "دخل العمولات الخاصة من القروض والسلف"],
  ["ارصدة للبنوك و المؤسسات المالية", "Due to Banks", "Special commission expense on due to banks & other FIs", "مصاريف العمولات الخاصة على الأرصدة للبنوك والمؤسسات المالية"],
  ["ودائع العملاء", "Customer Deposits", "Special commission expense on customer deposits", "مصاريف العمولات الخاصة على ودائع العملاء"],
];

test("income statement: a bank sub-line says it is commission income or expense, in both languages", () => {
  for (const [storedAr, storedEn, en, ar] of SUBLINES) {
    for (const stored of [storedAr, storedEn]) {
      assert.deepEqual(dataLabel(stored, "en", IS), { text: en, lang: "en" }, stored);
      assert.deepEqual(dataLabel(stored, "ar", IS), { text: ar, lang: "ar" }, stored);
    }
  }
});

test("balance sheet: the same words keep their balance-sheet meaning", () => {
  assert.deepEqual(dataLabel("الاستثمارات", "en", BS), { text: "Investments", lang: "en" });
  assert.deepEqual(dataLabel("ودائع العملاء", "en", BS), { text: "Customer Deposits", lang: "en" });
  assert.deepEqual(dataLabel("Investments", "ar", BS), { text: "استثمارات", lang: "ar" });
  assert.deepEqual(dataLabel("Due to Banks", "ar", BS), { text: "مستحق للبنوك", lang: "ar" });
  assert.deepEqual(dataLabel("الاستثمارات", "ar", BS), { text: "الاستثمارات", lang: "ar" });
});

test("no statement given: the lookup is the one every other caller had before", () => {
  assert.deepEqual(dataLabel("Investments", "en"), { text: "Investments", lang: "en" });
  assert.deepEqual(dataLabel("الاستثمارات", "en"), { text: "Investments", lang: "en" });
  assert.deepEqual(dataLabel("Bonus SharesCancelled", "en"), { text: "Bonus shares (cancelled)", lang: "en" });
  assert.deepEqual(dataLabel("بند غير معروف", "en"), { text: "بند غير معروف", lang: "ar" });
  assert.deepEqual(dataLabel("Unknown line", "ar"), { text: "Unknown line", lang: "en" });
  assert.deepEqual(dataLabel(null, "en"), { text: "", lang: "en" });
});

test("income statement: other lines are untouched by the statement", () => {
  assert.deepEqual(dataLabel("صافي الربح", "en", IS), dataLabel("صافي الربح", "en"));
  assert.deepEqual(dataLabel("Total Assets", "ar", IS), dataLabel("Total Assets", "ar"));
});

test("real-estate investments read cleanly, from Argaam's garbled English as from the Arabic", () => {
  // Argaam's English for row tr432 is "property Real estate Investment" (210 Saudi pages); the same
  // Arabic, "استثمارات عقارية", is "Real Estate Investments" in its English for row tr73 (review 05).
  for (const stored of ["property Real estate Investment", "استثمارات عقارية"]) {
    assert.deepEqual(dataLabel(stored, "en", BS), { text: "Real Estate Investments", lang: "en" }, stored);
  }
  // Arabic pages keep what they showed: the stored Saudi spelling still finds its Arabic.
  assert.deepEqual(dataLabel("property Real estate Investment", "ar", BS), { text: "استثمارات عقارية", lang: "ar" });
});
