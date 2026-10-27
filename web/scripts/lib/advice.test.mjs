// The sentences F-5 was measured on (docs/advice-check-f5-2026-10-27.md): seven that are not advice and
// twelve that are. The no-advice rule carries legal weight and goes to the lawyer at Step 7, so it should
// not be possible to loosen or tighten these patterns by accident.
import assert from "node:assert/strict";
import test from "node:test";

import { ADVICE, isAdvice } from "./advice.mjs";

const NOT_ADVICE = [
  // The ordinary verb "hold", which the old pattern failed on — the member's own question contains it.
  ["en", "whether cover holds only while margins hold"],
  ["en", "The payout holds at 73 per cent while margins hold above 12 per cent."],
  ["en", "Earnings cover the dividend; the question is whether that cover holds."],
  // اشتراط ("the stipulation of") and اشتراك ("subscription"), both root ش-ر-ط / ش-ر-ك, not اشترى "to buy".
  ["ar", "اشتراط تغطية التوزيعات بالأرباح"],
  ["ar", "اشتراك العضوية الشهري"],
  ["ar", "مشترك في الخدمة"],
  ["ar", "الهوامش قائمة والتغطية مستمرة"],
];

const ADVICE_SENTENCES = [
  ["en", "We would buy the stock here."],
  ["en", "You should sell."],
  ["en", "Investors ought to hold."],
  ["en", "Trim the position into strength."],
  ["en", "Our price target is 42 riyals."],
  ["en", "I recommend buying at this level."],
  ["ar", "بيع السهم الآن"],
  ["ar", "شراء السهم عند هذا المستوى"],
  ["ar", "ننصح بشراء السهم"],
  ["ar", "احتفظ بالسهم"],
  ["ar", "اشترِ السهم"],
  ["ar", "يجب بيع الأسهم"],
];

test("advice: an assessment is not advice, however often it says hold", () => {
  for (const [locale, text] of NOT_ADVICE) {
    assert.equal(isAdvice(locale, text), false, `should pass: ${locale} ${text}`);
  }
});

test("advice: an instruction, a recommendation or a price target is advice", () => {
  for (const [locale, text] of ADVICE_SENTENCES) {
    assert.equal(isAdvice(locale, text), true, `should fail the check: ${locale} ${text}`);
  }
});

test("advice: the patterns are not sticky, so one call cannot affect the next", () => {
  // A /g or /y regex would carry lastIndex between tests and start passing real advice.
  for (const re of Object.values(ADVICE)) assert.equal(re.global || re.sticky, false);
  const advice = "We would buy the stock here.";
  assert.equal(isAdvice("en", advice), true);
  assert.equal(isAdvice("en", advice), true);
});

test("advice: both locales are covered", () => {
  assert.deepEqual(Object.keys(ADVICE).sort(), ["ar", "en"]);
});
