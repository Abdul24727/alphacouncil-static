# Output 18: review 17's step, the Financials metadata notice verified on a production build

Commit `9f51428`. No app code changed (`git diff --stat 4a98832..HEAD -- web/src …` is empty).

**Setup:**
- `npm run build` of the candidate's app code passes (93/93), with `API_ORIGIN` pointed at a keep-alive
  tunnel to beta's API.
- Then `next start -p 3100`, a real production server, not dev.

**The code:**
- `web/src/app/[locale]/(app)/t/[ticker]/layout.tsx` `generateMetadata()` awaits
  `getTickerRef(slug)`.
- `web/src/lib/api/server.ts:42` `getTickerRef()` calls `connection()` and fetches `/v1/tickers/{ref}`
  with `no-store`, on purpose: a stock page's title is the API's company name and symbol, read at request
  time.
- With Cache Components, that makes the metadata dynamic while the rest of the route can prerender. That is
  what the dev notice describes.

**Results (production server):**
- **The server's log has no "uncached" or `generateMetadata` line.** The notice is a development diagnostic.
- **Metadata as served, read as Googlebot** (`10-metadata-production-build.txt`):
  - `/t/2222/financials`: 200. `<title>` "Saudi Aramco (2222) · Tadawul · AlphaCouncil", with its
    description. Canonical `https://alphacouncil.tech/t/2222`, and `og:url` the same. `og:title` equals the
    title. `og:image` `/og/en.png`, `og:locale` `en_US`. hreflang en, ar and x-default.
  - `/ar/t/2222/financials`: 200. "أرامكو السعودية (2222) · تداول · AlphaCouncil", with the Arabic
    description. Canonical `/ar/t/2222`, `og:image` `/og/ar.png`, `og:locale` `ar_SA`.
  - `/t/NO-SUCH-TICKER/financials` and `/ar/t/NO-SUCH-TICKER`: "Unknown ticker" / "رمز غير معروف" with
    `robots: noindex, nofollow`, the existing soft not-found.
- **`check-seo.mjs` against the production server: 62 PASS, 0 FAIL, "ALL PASS"**
  (`9-check-seo-production-build.txt`, screenshots in `seo-production-build/`). It includes:
  - `/t/2222/financials` canonical is `/t/2222`;
  - the link-preview card in `<head>` on `/t/2222` and `/ar/t/2222`;
  - `/t/NO-SUCH-TICKER` is noindex;
  - robots.txt and sitemap.

**Verdict, recorded in the readiness report and `PROJECT.md`:** not a production defect; nothing to change.

All local servers and the tunnel were stopped afterwards.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
