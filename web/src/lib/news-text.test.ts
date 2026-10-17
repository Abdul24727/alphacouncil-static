// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { newsText } from "./news-text.ts";

const english = { title: "Aramco signs deal", lang: "en", summary_ar: "وقعت أرامكو صفقة" };
const arabic = { title: "أرامكو توقع صفقة", lang: "ar", summary_en: "Aramco signed a deal" };

test("news: an item in the page's language shows its own headline and summary", () => {
  assert.deepEqual(newsText(english, "en"), { title: "Aramco signs deal", lang: "en", summary: null, long: false, foreign: null });
  assert.equal(newsText(arabic, "ar").title, "أرامكو توقع صفقة");
});

test("news: another language shows the page-language headline or summary the database has", () => {
  assert.equal(newsText({ ...arabic, title_en: "Aramco deal" }, "en").title, "Aramco deal");
  assert.deepEqual(newsText(arabic, "en"), { title: "Aramco signed a deal", lang: "en", summary: null, long: true, foreign: null });
  assert.deepEqual(newsText(english, "ar"), { title: "وقعت أرامكو صفقة", lang: "ar", summary: null, long: true, foreign: null });
});

test("news: with nothing in the page's language, the original headline is marked as foreign", () => {
  assert.equal(newsText({ title: "Aramco signs deal", lang: "en" }, "ar").foreign, "en");
  assert.equal(newsText({ title: "أرامكو توقع صفقة", lang: "ar" }, "en").foreign, "ar");
});
