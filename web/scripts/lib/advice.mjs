// What counts as investment advice on screen, for check-advisors.mjs to look for in the Chair's answer
// and in the verdict headline.
//
// The rule itself lives in the product, not here: api/app/debate/engine.py's system prompt and every file in
// api/app/advisors/ forbid telling anyone to buy, sell or hold, forbid price targets and forbid personal
// advice, for every seat. These patterns are only what the checker can recognise.
//
// They replace `\b(buy|sell|hold)\b` and a bare `اشتر`, which failed in both directions (F-5 of
// docs/beta-advisors-2026-10-27.md, settled by the owner on 2026-10-27 as option B of
// docs/advice-check-f5-2026-10-27.md): the old pair fired on "while margins hold" and on `اشتر` inside
// اشتراط ("the stipulation of"), and let "we recommend buying", "Trim the position", a price target and
// "يجب بيع الأسهم" through. These match the words only where they instruct about the holding, where
// something is recommended, or where a price target is given.
//
// Reviewed again when the lawyer answers Step 7's question (a). advice.test.mjs holds the sentences.
export const ADVICE = {
  en: new RegExp(
    [
      // an instruction about the holding: "buy the stock", "sell your position", "trim the position"
      String.raw`\b(buy|sell|hold|add to|trim|exit|enter)\b[^.;:]{0,30}?\b(stock|shares?|position|holding|name|it|them)\b`,
      // a recommendation, however worded
      String.raw`\b(recommend|advise|advice|suggest|should|ought to|must|worth)\b[^.;:]{0,30}?\b(buy|sell|hold|buying|selling|holding)\b`,
      // a price target
      String.raw`\bprice target\b|\bfair value of\b|\btarget (of|price)\b`,
    ].join("|"),
    "i",
  ),
  ar: new RegExp(
    [
      // the verb with the holding — not the اشتراط / اشتراك roots
      String.raw`(اشتر[ِيواٍ]|شراء|بيع|بِع|احتفظ|تخلص)\s*(ب)?\s*(ال)?(سهم|أسهم|اسهم|حصة|مركز)`,
      // ننصح / نوصي / يجب … ب(شراء|بيع|الاحتفاظ)
      String.raw`(ننصح|نوصي|نصيحة|توصية|يجب|ينبغي)\s*\S{0,12}\s*(شراء|بيع|الاحتفاظ)`,
      String.raw`السعر المستهدف|القيمة العادلة عند`,
    ].join("|"),
  ),
};

/** True when `text` reads as advice in `locale`, by the patterns above. */
export const isAdvice = (locale, text) => ADVICE[locale].test(text);
