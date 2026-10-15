// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import { fmtDate, fmtStamp } from "./format.ts";

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
