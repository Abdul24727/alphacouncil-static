# Output 19: review 18's three issues, fixed

Commit `e1b95f6`. No app code changed (`git diff --stat 4a98832..HEAD -- web/src …` is empty).

1. **Screenshots location.** `check-seo.mjs` resolves `SHOTS_DIR` from `web/scripts/`, so "../docs/…" wrote
   under `web/docs/`. The 12 screenshots were moved to the cited folder and the empty `web/docs/` removed.
   `git ls-files docs/screenshots/release-candidate-4a98832/seo-production-build` lists 12.
2. **Metadata evidence completed.** The local production server (`next start`, against beta's API) was
   re-run, and `10-metadata-production-build.txt` was rewritten from
   `scratchpad/gulf-en/meta-capture.mjs`. For `/t/2222/financials`, `/ar/t/2222/financials`,
   `/t/NO-SUCH-TICKER/financials` and `/ar/t/NO-SUCH-TICKER`, it records:
   - **A. Googlebot, raw HTML:** title, **description**, canonical, robots, `og:title`, `og:url`, `og:image`,
     `og:locale`, and the **en / ar / x-default alternates**. Each field is marked with where it sits, all
     `head`.
   - **B. An ordinary Chrome user agent, raw HTML:** the same fields, all marked **`body`**, streamed.
   - **C. An ordinary Chrome browser after load:** `document.title`, description, canonical, robots, the four
     preview tags and the alternates.

   For 2222's Financials, A and C both carry the full set in both languages: "Saudi Aramco (2222) · Tadawul ·
   AlphaCouncil" and "أرامكو السعودية (2222) · تداول · AlphaCouncil", each with its description, canonical
   `/t/2222` and `/ar/t/2222`, `og:image` `/og/en.png` and `/og/ar.png`, `og:locale` `en_US` and `ar_SA`, and
   alternates en=/t/2222, ar=/ar/t/2222, x-default=/t/2222.
3. **Qualified by user agent.** The readiness report and `PROJECT.md` now say:
   - crawlers on `next.config.ts`'s `HTML_LIMITED_BOTS` (Next's list plus Googlebot) get the metadata in
     `<head>`; only Googlebot was tested;
   - ordinary visitors get it streamed into `<body>`, and the document ends up with the same metadata;
   - `check-seo.mjs`'s 62 passes read as Googlebot and a link-preview bot, and of the Financials URLs check
     only English `/t/2222/financials`'s canonical. The rest comes from file 10.

**One difference found and recorded, not a defect:** the unknown ticker's robots tag is `noindex, nofollow`
for Googlebot and `noindex` for a browser. Both keep the page out of search.

All local servers and the tunnel were stopped. `git status` is clean.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
