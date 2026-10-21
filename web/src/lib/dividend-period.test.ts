// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { dividendPeriod } from "./dividend-period.ts";

test("dividend period: the pipeline's period spellings in both languages", () => {
  assert.deepEqual(dividendPeriod("Q 3 _ 2025", "ar"), { label: "الربع الثالث 2025", rest: null });
  assert.deepEqual(dividendPeriod("Q 3 _ 2025", "en"), { label: "Q3 2025", rest: null });
  assert.deepEqual(dividendPeriod("H1-2026", "ar"), { label: "النصف الأول 2026", rest: null });
  assert.deepEqual(dividendPeriod("H 2 _ 2025", "en"), { label: "H2 2025", rest: null });
  assert.deepEqual(dividendPeriod("F Y _ 2024", "ar"), { label: "السنة المالية 2024", rest: null });
  assert.deepEqual(dividendPeriod("FY-2023", "en"), { label: "FY 2023", rest: null });
});

test("dividend period: a trailing note and whole sentences stay as stored", () => {
  assert.deepEqual(dividendPeriod("Q 3 _ 2025 (including performance-linked dividends SAR 820 million)", "ar"), {
    label: "الربع الثالث 2025",
    rest: "including performance-linked dividends SAR 820 million",
  });
  const sentence = "The General Assembly approved 10% cash dividend for FY2025";
  assert.deepEqual(dividendPeriod(sentence, "ar"), { label: null, rest: sentence });
  assert.deepEqual(dividendPeriod(null, "en"), { label: null, rest: null });
});
