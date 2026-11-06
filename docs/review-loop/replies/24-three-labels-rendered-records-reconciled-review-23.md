# Review 24: Three labels rendered; records reconciled (review 23 fixes)

2026-11-06 05:32 UTC. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.
Output reviewed: `24-three-labels-rendered.md`.

VERDICT: FIX

ISSUES:

1. `docs/release-readiness-2026-11-06.md:122` and `PROJECT.md:257` say seven listings lack currency. The cited `11-sweep-on-the-2026-11-06-publish.txt:43` records `"no_currency":8`. Correct the claim.
2. The acknowledged caption defect is confirmed: `research-panels.tsx:208` passes an empty `currencyLabel()` into “Millions of {currency}”. KFH’s screenshots show the incomplete caption in both languages. The three label fixes and F-16 record corrections themselves are supported.

DRIFT: The output stayed within evidence gathering and polishing existing Financials. The goal remains a finished, published, polished alphacouncil.tech under PROJECT.md, with the owner’s decisions and approval gates preserved.

NEXT STEP: On `rebuild`, finish the existing missing-currency unit captions in `web/src/components/stock/research-panels.tsx` and `web/messages/{en,ar}.json`: retain the millions scale and explicitly state that currency is unconfirmed. Update the evidence and correct the count during closeout. This removes a visible ambiguity about financial figures without guessing a currency or adding scope.

DONE WHEN: KFH screenshots in English and Arabic at 1440 and 390 px show complete, unclipped captions; a confirmed-currency control retains its correct caption; displayed figures remain unchanged and match API formatting. From `web/`, `npm test` and `npm run build` pass, and the readiness report records the new candidate and accurate sweep count.

OWNER ITEMS:

1. Obtain Step 7’s written legal advice.
2. Address disk pressure and F-14’s rejected pipeline key.
3. Separately authorize beta release, production release and public push after the candidate passes.
4. Settle D1/D3/D6 and authorize/fund the $66 pilot before deciding on the $393 run.
5. Decide on the explicitly gated `owns` patch.

Response complete
