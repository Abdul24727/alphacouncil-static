# Review 18: Financials metadata verified on a production build (review 17 step)

2026-11-06 01:30 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `18-metadata-verified.md`.

VERDICT: FIX

ISSUES:

1. [Readiness report:152](C:/projects/alphacouncil-platform/docs/release-readiness-2026-11-06.md:152) points to a missing `docs/screenshots/release-candidate-4a98832/seo-production-build/`. The 12 screenshots exist under **untracked `web/docs/`**.
2. [Metadata evidence:2](C:/projects/alphacouncil-platform/docs/screenshots/release-candidate-4a98832/10-metadata-production-build.txt:2) omits descriptions and hreflang for both Financials URLs. The existing SEO checker checks only the English Financials canonical; its 62 passes do not substantiate those additional claims.
3. [Readiness report:143](C:/projects/alphacouncil-platform/docs/release-readiness-2026-11-06.md:143) and `PROJECT.md:253` overstate “every stock page’s metadata” being served in `<head>`. `web/next.config.ts:35` explicitly distinguishes crawler requests from ordinary visitors’ streamed metadata.

DRIFT: The work stayed within verification of the existing site; no app code changed. The goal remains a finished, published, polished AlphaCouncil in both languages at 1440 and 390 px, with the master plan’s approval gates intact.

NEXT STEP: Complete and commit this metadata verification’s evidence under root `docs/` on `rebuild`: place the screenshots at the cited location, capture the missing Financials metadata fields, and qualify the report’s crawler-specific conclusion. This closes the remaining verification gaps now; F-16 still awaits the 05:00 UTC publish.

DONE WHEN: Both Financials URLs have saved production-server results including descriptions and en/ar/x-default alternates; the report accurately identifies the tested user agent; `git ls-files docs/screenshots/release-candidate-4a98832/seo-production-build` lists all 12 screenshots. The recorded 62-pass SEO result remains linked and app code remains unchanged.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Authorize beta/production releases and the public push, separately.
3. Address recorded disk pressure and F-14’s rejected pipeline key.
4. Settle D1/D3/D6 and authorize the $66 pilot; decide on the $393 run afterward.
5. Decide on the explicitly gated `owns` patch.

Response complete
