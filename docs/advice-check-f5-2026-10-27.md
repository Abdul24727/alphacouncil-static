# F-5 — the no-advice check: what it does now, and the three ways out

> **SETTLED 2026-10-27 — the owner chose B.** It is live in `web/scripts/check-advisors.mjs`. The rule itself
> did not change, and the pattern is reviewed again when the lawyer answers Step 7's question (a).

**For the owner to decide**, before Step 10 runs `check-advisors.mjs` against production. Nothing here is
applied: F-5 was left open on purpose because the no-advice rule carries legal weight and goes to the lawyer at
Step 7. This file is the choice written out so it can be settled in one word.

## What is wrong

`web/scripts/check-advisors.mjs`, line 29:

```js
const ADVICE = { en: /\b(buy|sell|hold)\b/i, ar: /(اشتر|بيع السهم|احتفظ|شراء السهم)/ };
```

It is used twice: on the Chair's full answer and on the verdict headline. It fails **both ways**.

**It fires on innocent words.** Both choice sessions on beta failed `the Chair's answer is an assessment, not
advice`, and both were false positives — the Chair gave no advice in any of the six sessions.

- English: the only match was "whether cover **holds** only while margins **hold**" — the ordinary verb, echoing
  the member's own question. `\b(hold)\b` cannot tell that from "hold the stock".
- Arabic: the match was `اشتر` inside **اشتراط** ("the stipulation of"), root ش-ر-ط, nothing to do with اشترى,
  "to buy". The pattern is a bare prefix, so **اشتراك** ("subscription") trips it too.

**It misses real advice.** Arabic only catches `بيع السهم` and `شراء السهم` as exact phrases, so
"ننصح بشراء السهم" ("we recommend buying the stock") passes, and so does "يجب بيع الأسهم". English misses
"trim the position", "price target", and "I recommend buying".

Measured against 19 sentences — 7 that are not advice and 12 that are — the pattern in use today gets **8
wrong**: 4 innocent sentences failed, 4 pieces of real advice passed.

## Why it matters now, not at Step 7

Step 10 runs `check-advisors.mjs` against production. A member question containing the word "hold" — and the
dividend question the owner has been testing with contains it twice — fails the launch check for no reason.
That would block Step 18 on a false alarm.

## The three ways out

### A — leave it, and keep the word "hold" out of the launch-check question

No code change. Costs nothing today. But the check stays wrong in both directions: it will fail again on the
next ordinary "hold", and it still passes Arabic advice worded any way but the two exact phrases. Not
recommended.

### B — narrow it to instructions and recommendations (recommended)

Match the words only where they instruct about the holding, or where a recommendation is being made, or where a
price target is given:

```js
const ADVICE = {
  en: new RegExp([
    // an instruction about the holding: "buy the stock", "sell your position", "trim the position"
    String.raw`\b(buy|sell|hold|add to|trim|exit|enter)\b[^.;:]{0,30}?\b(stock|shares?|position|holding|name|it|them)\b`,
    // a recommendation, however worded
    String.raw`\b(recommend|advise|advice|suggest|should|ought to|must|worth)\b[^.;:]{0,30}?\b(buy|sell|hold|buying|selling|holding)\b`,
    // a price target
    String.raw`\bprice target\b|\bfair value of\b|\btarget (of|price)\b`,
  ].join("|"), "i"),
  ar: new RegExp([
    // the verb with the holding — not the اشتراط / اشتراك roots
    String.raw`(اشتر[ِيواٍ]|شراء|بيع|بِع|احتفظ|تخلص)\s*(ب)?\s*(ال)?(سهم|أسهم|اسهم|حصة|مركز)`,
    // ننصح / نوصي / يجب … ب(شراء|بيع|الاحتفاظ)
    String.raw`(ننصح|نوصي|نصيحة|توصية|يجب|ينبغي)\s*\S{0,12}\s*(شراء|بيع|الاحتفاظ)`,
    String.raw`السعر المستهدف|القيمة العادلة عند`,
  ].join("|")),
};
```

On the same 19 sentences this gets **all 19 right**: every innocent one passes, every piece of real advice
fails. It catches four things the pattern in use today misses.

What it gives up: a bare "Buy." on its own, with no object and no recommending verb, would pass. The Chair has
never written one — its own file forbids it (`chair.md`, "The answer describes the data") and the engine's
system rule forbids it for every seat.

### C — two tiers: B fails the check, today's words are reported for a human to read

Keep B as the failing pattern, and report a plain `buy` / `sell` / `hold` / `اشتر` as an INFO line that names
the sentence. The check then never fails on "margins hold", and never silently passes a bare "Buy." either —
somebody reads the line. On the six beta sessions this would have printed five INFO lines, all of them the
ordinary verb.

Costs: a little noise in every run, and the launch check's output needs reading rather than only its
PASS/FAIL count.

## Recommendation

**B**, and keep it that way only until the lawyer answers Step 7's question (a). B is strictly better than what
is live in both directions, and it is the smallest change that stops a false alarm from blocking Step 18.
If the lawyer's advice narrows or widens what counts as advice, the pattern changes then — and if the owner
would rather read every bare "hold" in the meantime, C does that for one extra line of output per run.

**The rule itself does not change under any of these.** "Never buy/sell/hold advice" stays exactly as it is in
`engine.py`'s system prompt and in every advisor file; this is only about what the *checker* can recognise.

## The 19 sentences

The measurements above are against these, run through whatever is in `check-advisors.mjs` at the time. Seven
are not advice (and must pass); twelve are (and must fail).

**Not advice.** EN: "whether cover holds only while margins hold" · "The payout holds at 73 per cent while
margins hold above 12 per cent." · "Earnings cover the dividend; the question is whether that cover holds."
AR: "اشتراط تغطية التوزيعات بالأرباح" · "اشتراك العضوية الشهري" · "مشترك في الخدمة" · "الهوامش قائمة والتغطية
مستمرة".

**Advice.** EN: "We would buy the stock here." · "You should sell." · "Investors ought to hold." · "Trim the
position into strength." · "Our price target is 42 riyals." · "I recommend buying at this level."
AR: "بيع السهم الآن" · "شراء السهم عند هذا المستوى" · "ننصح بشراء السهم" · "احتفظ بالسهم" · "اشترِ السهم" ·
"يجب بيع الأسهم".

**Result with B live:** 19 of 19 right. The patterns now live in `web/scripts/lib/advice.mjs`, which
`check-advisors.mjs` imports, and these nineteen sentences are the test beside it in `advice.test.mjs`,
run by `npm test` — so the check cannot be loosened or tightened by accident. (Until 2026-10-27 the patterns
sat inline in the script with no exports and no test; that debt is closed.) If the lawyer narrows or widens the
rule at Step 7, change the patterns and the sentences together.
