// Run with: npm test
// Checks the dictionary's content under the rule lib/data-labels.ts applies: whitespace collapsed,
// case ignored, and the FIRST pair for a label wins in each direction. (data-labels.ts itself imports
// through the "@/" alias, which node --test does not resolve, so the file is read here directly.)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const data = JSON.parse(readFileSync(new URL("../content/data-labels.json", import.meta.url), "utf8")) as {
  pairs: [string, string][];
};
const norm = (s: string) => s.replace(/\s+/g, " ").trim().toLowerCase();
const toAr = new Map<string, string>();
const toEn = new Map<string, string>();
for (const [en, ar] of data.pairs) {
  if (!toAr.has(norm(en))) toAr.set(norm(en), ar);
  if (!toEn.has(norm(ar))) toEn.set(norm(ar), en);
}

test("Arabic pages: a sub-line keeps the word its English label carries", () => {
  // Argaam's Arabic for these leans on the heading above ("مرابحة" under the financing-income
  // heading); the panel shows lines without headings, so the word is part of the label.
  const cases: [string, string][] = [
    ["Income from Murabahat", "دخل المرابحة"],
    ["Income from Mutajara", "دخل المتاجرة"],
    ["Income from Istisnaa", "دخل الاستصناع"],
    ["Income from Installment sale", "دخل البيع بالتقسيط"],
    ["Other Investment Income", "دخل إستثمارات أخرى"],
    ["Others-Fee and commission income", "دخل اتعاب و عمولات اخرى"],
    ["Others-Special Commission Expenses", "مصاريف عمولات خاصة اخرى"],
    ["Others-Total Operating Expenses", "مصاريف عمليات اخرى"],
    ["Return On Customers’ Time Investments", "العائد على استثمارات العملاء لأجل"],
    ["Return on due to banks and financial institutions’ time investments", "العائد على المطلوبات للبنوك واستثمارات المؤسسات المالية لأجل"],
    ["Selling and distribution expenses", "مصاريف بيع و توزيع"],
    ["General & Administrative Expenses", "مصاريف عمومية وإدارية"],
    ["Property under development", "استثمارات عقارية تحت التطوير"],
  ];
  for (const [en, ar] of cases) assert.equal(toAr.get(norm(en)), ar, en);
});

test("English pages: Argaam's short Gulf Arabic still reads back to the same Argaam line", () => {
  // Each is one Argaam row id on the Gulf pages and on the Saudi pages (2026-11-04 scan).
  const cases: [string, string][] = [
    ["مرابحة", "Income from Murabahat"],
    ["متاجرة", "Income from Mutajara"],
    ["استصناع", "Income from Istisnaa"],
    ["استثمارات العملاء", "Return On Customers’ Time Investments"],
    ["المطلوبات للبنوك واستثمارات المؤسسات المالية", "Return on due to banks and financial institutions’ time investments"],
    ["استثمارات تحت التطوير", "Property under development"],
    // Argaam's own misspellings, corrected for Arabic pages but stored that way for Gulf companies.
    ["بيع بالتقسط", "Income from Installment sale"],
    ["ايرادا تمويل غير مكتسب", "Unearned finance income"],
    ["هبوط في قيم استثمارت عقارية", "Impairment of real estate investments"],
    ["استثمارات وآخرى", "Investment and Others"],
    ["إجمالي الأستثمارات العقارية", "Total Real estate Investments"],
  ];
  for (const [ar, en] of cases) assert.equal(toEn.get(norm(ar)), en, ar);
});

test("Arabic pages: a corrected misspelling is what Arabic pages show", () => {
  assert.equal(toAr.get(norm("Income from Installment sale")), "دخل البيع بالتقسيط");
  assert.equal(toAr.get(norm("Unearned finance income")), "إيرادات تمويل غير مكتسبة");
  assert.equal(toAr.get(norm("Total Real estate Investments")), "إجمالي الاستثمارات العقارية");
});

test("English pages: an Arabic label Argaam uses for two different lines is not given one English", () => {
  // "إستثمارات أخرى" is both Other Investment Income (tr1255) and Other Investments (tr1289).
  assert.equal(toEn.get(norm("إستثمارات أخرى")), undefined);
});
