# Launch check, signed out, on production `b5655a5064` (2026-11-06)

**Why:** Step 10's signed-out half, run again after the 2026-11-06 release (review 55's step), so the site the lawyer
will test is checked as it stands.

**How it ran:**
- **Where:** from `web/` against `https://alphacouncil.tech`.
- **Signed out:** no account was made and no paid session was run.
- **Output:** the files are in `docs/screenshots/launch-2026-11-06/`, 49 in all.
  - **The SEO screenshots:** `check-seo.mjs` resolves `SHOTS_DIR` from its own folder, so its 12 screenshots were
    first written under an untracked `web/docs/…`. They were moved into `seo/` here (review 56).

| Script | How | Summary line | Result |
| --- | --- | --- | --- |
| `check-seo.mjs` | `SHOTS_DIR=…/seo` | **"ALL PASS"**, 62 PASS, 0 FAIL | PASS (`check-seo.txt`, 12 screenshots in `seo/`) |
| `check-arabic.mjs` | `SIGNED_IN=0 WIDTHS=1440,390` | **"48 Arabic page view(s) signed out; 0 English string(s) outside the allow-list"** | PASS (`check-arabic.txt`) |
| `check-advisors.mjs` | `VISITOR=1` (signed out) | **"all passed"**, 24 PASS, 0 FAIL | PASS (`check-advisors-visitor.txt`, screenshots in `advisors-visitor/`) |
| `check-data-fixes.mjs` | `SWEEP=1` | **"all passed"**, 44 PASS, 0 FAIL, 1 INFO; sweep 714 tickers, `eps_bad` 0, `vt_reason` 0, `news_green_old` 0, `no_currency` 8 | PASS (`check-data-fixes.txt`) |
| five pages × two languages × two widths | `page-shots.mjs` (GETs only) | **20 views, every one 200, no sideways scroll** | PASS (`pages/pages.txt`) |

**What the sweep cannot read here.** The English statement-label sweep prints **UNAVAILABLE** on production:
- **Why:** statements are Pro-only there, and a signed-out visitor cannot read them ("0 of 714 companies … not
  checked").
- **Where it is covered instead:** the same sweep passed 714/714 companies and 40,811 lines against deployed beta,
  which runs the same release on the same data (`docs/screenshots/release-b5655a5064/beta-checks.txt`).
- **What ties production to beta:** production's labels chunk is hash-equal to beta's (`production-check.txt`).

**The five pages, looked at:** `/`, `/pricing`, `/home`, `/t/2222` and `/t/2222/advisors`, in English and Arabic at
1440 and 390. The contact sheets are `pages/contact-sheet-1440.png` and `pages/contact-sheet-390.png`.
- **What they show:** every page renders, the Arabic pages read right to left, nothing is cut off, and the phone
  pages keep their bottom tab bar.
- **Signed out:** the advisors' page shows the room and "Sign in to convene the advisors".
- **The landing page's terminal preview:** it is a fixed product screenshot
  (`web/src/assets/screens/app-desktop.*.jpg`). Its Aramco price is that day's, not today's, by design.

**What this check does not cover, and where it is recorded:**
- **Signed-in and Pro pages:** Claude makes no accounts on the live site. The owner's `check-all.mjs` and signed-in
  advisors runs of 2026-11-02 closed Step 10 (`docs/launch-check-2026-10-27.md`).
- **The monitor:**
  - **At the time of the check:** credit was **FAILING at $7.83**, below the $10 alert. *(Resolved later on
    2026-11-06: the owner topped up to $37.83, read at 15:30 UTC, and the monitor's credit check is ok again.)*
  - **Still open:** renewals show "–", so Step 18's item 4 stays open until a real `renewal` payment.
  - **Where:** `docs/launch-check-2026-10-27.md`, "Production monitor after the 2026-11-06 release", with the
    verbatim capture in `docs/screenshots/release-b5655a5064/monitor-status.txt`.
