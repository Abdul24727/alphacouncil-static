# Output 27: review 26's step done; candidate is now `dfc7a3d`

Commits: `dfc7a3d` (the fix), `8d1f5a8` and `2161be4` (records). `git diff --stat dfc7a3d..HEAD -- web/src api
deploy web/messages web/public` is empty, so `dfc7a3d` is the candidate's app code.

**The fix.** `web/src/components/stock/research-panels.tsx`, CapitalPanel: every column but the last gets end
padding (`pe-3`) in the header and body, the way the ownership-changes table already spaces its columns. The
date sits in a `.num` span. `pe-` is a logical property, so the gap lands on the correct side in Arabic too.

**Proof, check 15 extended.** The script, `capital-check.mjs`, lives in the session scratchpad like checks
13 and 14; its log and screenshots are committed in
`docs/screenshots/release-candidate-dfc7a3d/15-capital-captions.txt` and `capital-captions/`. The check now
measures, in every row including the header, the narrowest gap between neighbouring cells' TEXT in visual
order, and requires at least 8 px.

| View | `de19095` (before) | `dfc7a3d` (after) |
|---|---|---|
| English 1440 | 14 px | 19 px |
| English 390 | 3 px | 12 px |
| Arabic 1440 | 0 px | 26 px |
| Arabic 390 | 0 px | 14 px |

Still true on `dfc7a3d`: the caption is exactly "MILLIONS OF SAR" / "بملايين ر.س" and not clipped; all 9 of
1010's rows equal the API's (date, capital after, change; 0 cells differing); KFH shows its empty message and no
caption in all four views. **8/8 PASS.** Arabic 390 and English 390 screenshots inspected by eye.

**The whole candidate re-run on `dfc7a3d`,** against the 2026-11-06 published data, evidence in
`docs/screenshots/release-candidate-dfc7a3d/`:
- checks 1–8 PASS (check 6, `check-arabic.mjs`: 48 Arabic views, 0 stray English);
- checks 13 (8/8), 14 (16/16) and 15 (8/8) PASS;
- `11-sweep.txt`: 714/714 companies, 40,811 lines, PASS (`"no_currency":8`);
- `npm run build` 93/93 pages, `tsc` 0 errors, lint 0, `npm test` 68/68.

**Records.** `docs/release-readiness-2026-11-06.md` now names candidate `dfc7a3d` (title, candidate line, checks
heading, evidence folder), notes `de19095` as superseded, adds visitor row 7 (capital-panel spacing), says Arabic
pages change only through rows 2, 3, 5, 7 and 8, replaces the "seen on check 15" note with the measured fix, and
recounts the inventory: 1120 files in `5c18a3ae46..dfc7a3d` (29 named, 1037 evidence, 54 review-loop; every one
of the 29 named in the list). `PROJECT.md` §5 has the changelog line.

**Waiting on the owner, unchanged:** release `dfc7a3d` to beta then production; push the unpushed commits; the
check-advisors owns-case patch; the other owner items in the plan.

**The question for the review:** is this sound, and what is the single next pre-approved step?
