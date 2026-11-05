// The English-label sweep must not certify what it did not check (review 02, 2026-11-06): a failed
// request fails, a gate after some reading keeps what was found, a fully gated run is "unavailable",
// and only a complete, clean run passes.
import assert from "node:assert/strict";
import test from "node:test";

import { englishLookup, sweepLabels } from "./label-sweep.mjs";

const toEn = englishLookup([
  ["Total Assets", "مجموع الموجودات"],
  ["Total Assets", "إجمالي الموجودات"],
]);
const ok = (rows, section = "Balance Sheet") => ({ status: 200, body: { statements: [{ section, rows }] } });
const english = ok([{ label: "إجمالي الموجودات" }, { label: "Cash" }]);
const untranslated = ok([{ label: "بند غير معروف" }]);
const run = (answers) => sweepLabels(Object.keys(answers), async (s) => {
  const a = answers[s];
  if (a instanceof Error) throw a;
  return a;
}, toEn);

test("every line has English: pass", async () => {
  const r = await run({ A: english, B: ok([{ label: "Revenue" }], "Income Statement") });
  assert.equal(r.verdict, "pass");
  assert.equal(r.read, 2);
  assert.equal(r.lines, 3);
});

test("a line left in Arabic fails, named", async () => {
  const r = await run({ A: english, B: untranslated });
  assert.equal(r.verdict, "fail");
  assert.deepEqual([...r.left.keys()], ["بند غير معروف (Balance Sheet)"]);
});

test("a statement the panel does not show is not counted", async () => {
  const r = await run({ A: english, B: ok([{ label: "بند غير معروف" }], "Cash Flow Statement") });
  assert.equal(r.verdict, "pass");
});

for (const status of [500, 503, 429, 404]) {
  test(`HTTP ${status} fails: that company was not checked`, async () => {
    const r = await run({ A: english, B: { status } });
    assert.equal(r.verdict, "fail");
    assert.equal(r.errors.length, 1);
  });
}

test("a network error fails", async () => {
  const r = await run({ A: english, B: new Error("socket hang up") });
  assert.equal(r.verdict, "fail");
});

test("Pro-only from the first company: unavailable, not a pass", async () => {
  const r = await run({ A: { status: 403 }, B: english });
  assert.equal(r.verdict, "unavailable");
  assert.equal(r.read, 0);
});

test("Pro-only after some reading: fail, and what was found is kept", async () => {
  const r = await run({ A: untranslated, B: { status: 401 }, C: english });
  assert.equal(r.verdict, "fail");
  assert.equal(r.left.size, 1);
  assert.match(r.problems.join(" "), /coverage incomplete/);
});

test("no company checked at all fails", async () => {
  const r = await run({});
  assert.equal(r.verdict, "fail");
});
