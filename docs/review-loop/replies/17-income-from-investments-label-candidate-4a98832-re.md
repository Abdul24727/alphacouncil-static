# Review 17: Income from investments label; candidate 4a98832 (review 16 step)

2026-11-06 01:24 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `17-investment-income-label.md`.

VERDICT: ACCEPT

ISSUES: none.

DRIFT: The change stays within polishing the existing site; tests pass 67/67, typecheck and lint pass, and the lookup comparison confirms six English-only changes. The goal remains a finished, published, polished AlphaCouncil in both languages at 1440 and 390 px, with the master plan’s approval gates intact.

NEXT STEP: Verify the recorded Financials metadata warning against a locally running production build, tracing `web/src/app/[locale]/(app)/t/[ticker]/layout.tsx:14` and `web/src/lib/api/server.ts:42`. Record the result in `docs/release-readiness-2026-11-06.md`. This resolves the remaining recorded rendering uncertainty now; F-16 verification still awaits the 05:00 UTC publish.

DONE WHEN: `npm run build` passes, the existing `check-seo.mjs` passes against the local production server, and direct checks of English and Arabic `/t/2222/financials` confirm correct titles, canonicals and preview metadata. Confirm an unknown ticker retains the owner-approved soft-404/noindex behavior. Record whether the warning represents a production defect or only a development diagnostic.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Give the required release and public-push go-aheads.
3. Address recorded disk pressure and F-14’s rejected pipeline key.
4. Retire or re-register D1/D3/D6 and authorize the $66 pilot; decide on the $393 run afterward.
5. Decide on the explicitly gated `owns` patch.

Response complete
