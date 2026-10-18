// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import { autoPriceDigits, fmtDate, fmtNumber, fmtStamp } from "./format.ts";

test("dates: English month names, or Arabic ones with Latin digits in a right-to-left isolate", () => {
  assert.equal(fmtDate("2026-10-13"), "13 Oct 2026");
  assert.equal(fmtDate("2026-10-13", "ar"), "\u206713 أكتوبر 2026\u2069");
  assert.equal(fmtDate(null, "ar"), null);
});

test("stamps: time only today, date and time otherwise", () => {
  const now = new Date("2026-10-15T12:00:00");
  assert.equal(fmtStamp("2026-10-15T09:05:00", "en", now), "09:05");
  assert.equal(fmtStamp("2026-10-13T09:05:00", "en", now), "13 Oct 09:05");
  assert.equal(fmtStamp("2026-10-13T09:05:00", "ar", now), "\u206713 أكتوبر 09:05\u2069");
});

test("price decimals: always 3 for fils and baisa, otherwise the third only when the price has one", () => {
  // The stock header used to round these to 2 (NBK 0.815 -> "0.82", QCFS 2.345 -> "2.35").
  assert.equal(fmtNumber(0.815, autoPriceDigits("KWD", 0.815)), "0.815");
  assert.equal(fmtNumber(0.031, autoPriceDigits("KWD", 0.031)), "0.031");
  assert.equal(fmtNumber(0.5, autoPriceDigits("BHD", 0.5)), "0.500");
  assert.equal(fmtNumber(2.345, autoPriceDigits("QAR", 2.345)), "2.345");
  assert.equal(fmtNumber(0.905, autoPriceDigits("AED", 0.905)), "0.905");
  // A price stored with 2 decimals is not padded to look more precise than it is.
  assert.equal(fmtNumber(0.24, autoPriceDigits("AED", 0.24)), "0.24");
  assert.equal(fmtNumber(26.5, autoPriceDigits("SAR", 26.5)), "26.50");
  assert.equal(autoPriceDigits(null, 3.37), 2);
  assert.equal(autoPriceDigits("SAR"), 2);
});
