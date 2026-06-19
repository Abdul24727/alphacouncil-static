# Arabic Marketing Copy — Review Sheet

**Purpose:** every Arabic string below was drafted by the engineering i18n pass and needs a
native-speaker review before launch (marketing copy is brand-facing). Go down the
**Review** column: write **OK** to approve, or write the corrected Arabic. Anything you
change, I'll apply straight back into the code (the keys map 1:1 to `data-i18n` entries in
`js/i18n.js` and the page dictionaries).

**Conventions used in the draft**
- Brand name **AlphaCouncil** is kept in Latin script (not transliterated) — confirm you want that.
- GCC exchange names (تداول/أبوظبي/دبي…) are localised; ticker symbols + numbers stay LTR.
- Tone: concise, modern MSA. Flag anywhere you'd prefer Gulf-colloquial or more formal register.

**Flag legend:** ⚑ = I'm least confident here, please look closely.

---

## 1. Shared marketing nav + CTAs  (`js/i18n.js` → `mnav.*`)
Appears on every marketing page (auto-translated by the engine).

| Key | English | Proposed Arabic | Review |
|---|---|---|---|
| mnav.how_it_works | How it works | كيف يعمل | |
| mnav.features | Features | المزايا | |
| mnav.pricing | Pricing | الأسعار | |
| mnav.methodology | Methodology | المنهجية | |
| mnav.markets | Markets | الأسواق | |
| mnav.about | About | من نحن | |
| mnav.contact | Contact | تواصل معنا | |
| mnav.sign_in | Sign in | تسجيل الدخول | |
| mnav.start_free | Start free | ابدأ مجانًا | |

---

## 2. Landing page — `index.html`  (`idx.*`)

### Hero
| Key | English | Proposed Arabic | Review |
|---|---|---|---|
| idx.hero_badge | Live GCC market coverage | تغطية حيّة لأسواق الخليج | |
| idx.hero_t1 | Understand your GCC portfolio | افهم محفظتك الخليجية | |
| idx.hero_t2 | before the market moves. | قبل أن يتحرّك السوق. | |
| idx.hero_sub | Add your holdings and AlphaCouncil connects your portfolio to GCC news, fundamentals, dividends, risk, and AI Analyst Council reviews — in English or Arabic. | أضِف مراكزك ويربط AlphaCouncil محفظتك بأخبار الخليج والأساسيات والتوزيعات والمخاطر ومراجعات مجلس المحلّلين الذكي — بالعربية أو الإنجليزية. | ⚑ |
| idx.view_sample | View sample dashboard | عرض لوحة تجريبية | |

### Section headings (eyebrow / title / subtitle)
| Key | English | Proposed Arabic | Review |
|---|---|---|---|
| idx.eye_problem | The Problem | المشكلة | |
| idx.t_problem | GCC investors don't need more data. They need context. | لا يحتاج مستثمرو الخليج إلى مزيد من البيانات، بل إلى السياق. | |
| idx.s_problem | Traditional tools show charts and numbers. AlphaCouncil explains what matters for your portfolio. | تعرض الأدوات التقليدية الرسوم والأرقام. أمّا AlphaCouncil فيشرح ما يهمّ محفظتك. | |
| idx.eye_features | Features | المزايا | |
| idx.t_features | AlphaCouncil connects your portfolio to the market. | يربط AlphaCouncil محفظتك بالسوق. | |
| idx.eye_council | AI Analyst Council | مجلس المحلّلين الذكي | ⚑ |
| idx.t_council | Meet your AI Analyst Council. | تعرّف على مجلس محلّليك الذكي. | |
| idx.s_council | Different questions need different perspectives. AlphaCouncil reviews your portfolio through specialized AI analyst members before giving you a clear, source-aware synthesis. | تحتاج الأسئلة المختلفة إلى وجهات نظر مختلفة. يراجع AlphaCouncil محفظتك عبر محلّلين ذكيين متخصّصين قبل أن يقدّم لك خلاصة واضحة مدعومة بالمصادر. | |
| idx.eye_coverage | Coverage | التغطية | |
| idx.t_coverage | Built for GCC investors. | مصمَّم لمستثمري الخليج. | |
| idx.s_coverage | Local market structure, dividends, Arabic context, and regional news flow — not US data adapted for the Gulf. | بنية السوق المحلّية والتوزيعات والسياق العربي وتدفّق الأخبار الإقليمية — لا بيانات أمريكية مُكيَّفة للخليج. | |
| idx.eye_live | Live Intelligence | ذكاء حيّ | ⚑ |
| idx.t_live | Your portfolio, always monitored. | محفظتك تحت المراقبة دائمًا. | |
| idx.s_live | Real-time alerts explain what's happening and why it matters to your holdings. | تشرح التنبيهات ما يحدث ولماذا يهمّ مراكزك. | |
| idx.eye_current | Always Current | محدَّث دائمًا | |
| idx.t_current | Intelligence that works while you don't. | ذكاء يعمل بينما ترتاح. | ⚑ |
| idx.eye_how | How It Works | كيف يعمل | |
| idx.t_how | From "what's happening?" to "what should I do?" | من «ماذا يحدث؟» إلى «ماذا أفعل؟» | |
| idx.s_how | Four steps to portfolio clarity. | أربع خطوات نحو وضوح المحفظة. | |
| idx.eye_adviser | AI Adviser | المستشار الذكي | |
| idx.t_adviser | Ask anything about your portfolio. | اسأل أي شيء عن محفظتك. | |

---

## 3. Remaining marketing pages — NOW DRAFTED + LIVE (review by toggling AR)
All of these are translated, committed, and deployed. **Quickest review:** open each page,
click **AR** in the nav, and read it top-to-bottom; mark anything to change and I'll fix the
key. (Each page's Arabic lives in its own `AC_I18N.add({…})` block at the bottom of the file.)

| Page | Status | Scope translated |
|---|---|---|
| about.html | ✅ live (c46638d) | hero, mission, 3 value cards, 4 section headers |
| contact.html | ✅ live (c107b0b) | hero, form labels + placeholders, channels, regional, FAQ teaser |
| how-it-works.html | ✅ live (90c7416) | hero, 5 steps, 3 sections, 2 add-methods |
| features.html | ✅ live (a26724a) | hero, 9 section headers, 4 feature headlines + leads (demo mockups left as illustrative) |
| pricing.html | ✅ live (cc77cb1) | hero, billing toggle, 3 section headers, 6 FAQ questions (plan matrix is numeric) |
| markets.html | ✅ live (51dcc68) | hero, 4 stat labels, 2 sections, 6 country names, per-card stat labels |
| methodology.html | ✅ live (fully translated) | hero, framework, **all 12 scoring dimensions** (9 fundamental + Momentum/Technicals/Sentiment), Understanding-Scores section + 3 cards, **AI Analyst Council** + all 7 analyst roles, News Classification, Source-Linked Analysis, **Limitations & Boundaries** + "What AlphaCouncil Is Not", final note |

**One honest gap to confirm:**
- **legal.html** — **intentionally left English.** It's template Terms/Privacy/Disclaimer
  already pending legal counsel; an unreviewed machine-translated Arabic *legal agreement* is a
  liability. Translate the lawyer-finalised version with a **certified** translator, not here.

---

### Glossary decisions to confirm (apply across all pages)
| English term | Proposed Arabic | Review |
|---|---|---|
| AI Analyst Council | مجلس المحلّلين الذكي | |
| Portfolio | المحفظة | |
| Holdings | المراكز | |
| Dividends | التوزيعات | |
| Thesis | الأطروحة | |
| Watchlist | قائمة المتابعة | |
| Adviser | المستشار | |
| Council review | مراجعة المجلس | |

> Once you mark this sheet up, reply with it (or just the corrections) and I'll update
> `js/i18n.js` + the page dictionaries and re-run the i18n tests.
