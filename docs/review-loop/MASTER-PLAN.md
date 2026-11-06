# The master plan, for every review (do not drift from it)

The owner's instruction (2026-11-06): every output Claude produces is reviewed by ChatGPT. ChatGPT takes
it toward the final plan and gives the next step. Every review restates this plan so the direction cannot
drift.

## The final goal

**alphacouncil.tech is finished, published and polished:** the launch plan in `PROJECT.md` is complete.

The Objective (`PROJECT.md` §1, verbatim): alphacouncil.tech is fully built — everything already on the
site works and is right, the market data is right at its source, the named advisors, portraits and `www`
address are settled, checkout is proven, and the code is safe off this computer — and only then does Pro
billing open and advertising start.

**Out of scope** (verbatim): new features or panels ("fully built" means what is already on the site,
finished and right); the advertising itself (campaigns, budgets, copy); retiring the old backend that still
serves `api.alphacouncil.tech`; a cloud bucket for backups.

"Polished" means what is already on the site reads and works right in both languages, at 1440 and 390 px.
It does not mean new things.

## The four goals (`PROJECT.md` §7) and where they stand

| Goal | Weight | State |
|---|---|---|
| 1 — Safe footing | ~15 % | DONE 2026-10-22 |
| 2 — Market data correct at the source | ~25 % | DONE 2026-10-24; later data fixes F-13, F-15 and F-16 all live (F-16 verified 2026-11-06) |
| 3 — Every known defect fixed, checkout proven | ~30 % | DONE 2026-10-22 |
| 4 — Launch: settled, checked, then paid | ~30 % | Steps 8, 9, 22, 23, 10 DONE (10's signed-out half re-run on production `b5655a5064` 2026-11-06, all PASS); **Step 7 (lawyer) NOT STARTED**, pack ready (`docs/lawyer-review-pack-2026-11-06.md`); Step 18 (billing) open, item 4 needs a real renewal |

Goal 4's Done-when (verbatim, short):
1. The owner's written legal advice is in `docs/legal-advisors-<date>.md`, and every change it asks for is live.
2. Six real portraits in English and Arabic at 1440 and 390 px.
3. `www` answers 301 to the apex, and the certificate covers both.
4. `docs/launch-check-<date>.md` records every check script passing on production, and the monitor at 14 of 14.
5. `checkout_open:true`, and the owner's own first real payment gave Pro.

## What is left (`PROJECT.md` §9, "What is left, by who"), as of 2026-11-06

**The site is published and live** at alphacouncil.tech, running release `b5655a5064` on beta and production.
Billing has been open since 2026-11-02.

**Done on 2026-11-06, on the owner's go-aheads:**
- the release;
- two pushes (`origin/rebuild` at `eeb9a9d`);
- the disk, now at 41 %, with a nightly keep-14;
- F-14, the pipeline's key;
- the test accounts, now removed;
- the `owns` fix, confirmed;
- the $66 pilot, which cost $5.64, with its audit (`docs/council-pilot-2026-11-06.md`);
- the OpenRouter top-up: $37.83, owner-reported and read from OpenRouter.

**Still open:**
- **The owner's** (Claude cannot do these):
  - Step 7, the lawyer. The owner sends `docs/lawyer-review-pack-2026-11-06.md` and the lawyer evaluates the
    live site; the reply comes later, into `docs/legal-advisors-<date>.md`;
  - F-12's duplicate webhook, optional and harmless, in Moyasar's dashboard;
  - optional server hardening;
  - Step 18 item 4, which waits on a real customer's renewal;
  - any paid run: the owner's go-ahead per run.
- **Claude's** (pre-approved, on branch `rebuild`):
  - apply the lawyer's advice when it comes;
  - the owner's direction of 2026-11-06 on the room's cost, below;
  - the open small items in `PROJECT.md` §6 and §9.

**Since then (2026-11-06 evening to 2026-11-07), on the owner's direction below:**
- **Option 2 is built as a prototype** (`api/app/debate/presenter.py`, harness arm P), behind a setting and off by
  default. Nothing is released. Reviews 62 to 65 fixed its accounting, its fallbacks and, in review 65, the planted
  claim: the analyst now sees it exactly as today's room's Chair does (`2e948d9`).
- **The paid comparison of today's room against option 2** (60 sessions, about $10.64 expected, $167 cap) has the
  owner's go-ahead: "Yes, run it", in answer to "Once ChatGPT accepts the fixes, run the paid comparison (about $11,
  ceiling $167)?". It runs once the reviewer accepts the latest fixes. Every answer is audited by hand before any
  result is reported. Adoption, any beta showing and any release stay the owner's, separately.
- **It ran on 2026-11-07 from `d7c2091`:** 60 sessions, $11.36. All 60 were audited by hand, and the 265 counted
  claims were each checked against the session text (`docs/eval/presenter-comparison/RESULT.md`, `audit.md`).
  - **Option 2 fails the cost criterion clearly:** 62 % of today's room against the 40 % limit. Under the rule written
    before the run, that settles it, and today's room stays.
  - **Option 2's discussion was far more accurate:** 55 wrong claims against 210, none in a final answer against 7,
    and 2 inventions against 48. But it is twice as slow, with about 40 seconds before the first words, and
    one of its sessions failed.
  - **The audit found two issues in today's room:**
    - the "sector percentile" field reads the wrong way for lower-is-better metrics;
    - advisors invent statement figures on packs that have no statements (P9).
  - **What comes next is the owner's choice:** keep today's room and fix those two issues, screen a one-model option 2,
    or stop.

## The owner's direction of 2026-11-06 on the advisors' room (in chat, verbatim)

"The idea from the LLM council is not only for performance. If performance is similar or very clearly similar and
we are spending way too much on the presentation, we can find another way to keep the presentation as is but
running it on one model. Two maximum, one for keeping the presentation and one is doing the heavy lifting in the
real work. This presentation of multiple financial images and them discussing is a major selling factor in our
website. The open router has been topped up. If you think it's necessary and the reviewer sees it necessary to run
extra tests, then the account is topped up. Other than that, we need to continue on the progress and publish the
site. Because the lawyer needs published, running site to evaluate what's need to be written."

**How this sits with the plan:**
- **It is the owner's own instruction, so it is not drift.** It changes how an existing feature is built, not
  what the site shows: the room's presentation (the portraits, the rounds, the Chair) stays as it is.
- **Paid tests need the reviewer to judge them necessary, and the owner's go-ahead per run still applies.**
- **The lawyer will evaluate the live site as it is.** The site is ready; Step 7 has not started, and the owner
  sends the pack. If the room's build changes, the site's own words about how
  the room works must stay true. The How-it-works copy says "Each advisor writes their own full answer at the
  same time", so any change in how it is built is shown to the lawyer before release.

## Rules no review can change (`PROJECT.md` §4)

- **Pre-approved:**
  - editing files in this repo on branch `rebuild`;
  - running checks and builds;
  - read-only SSH;
  - reports under `docs/`;
  - commits on `rebuild`;
  - screenshots.
- **Always the owner's go-ahead in chat, per action:**
  - any release to beta or production;
  - any change to the pipeline's code or data on the server;
  - pushing (the repository is PUBLIC);
  - paid model calls;
  - credentials, payments, Moyasar;
  - DNS, certificates, nginx;
  - deleting data;
  - publishing or sending anything outside the project.
- Never show a number that is not from the database. Missing data is a labelled placeholder.
- Claude makes no accounts on the live site.
- Never sign in to Argaam; never get around a bot check.

A review may recommend an action that needs the owner's go-ahead. Claude then asks the owner and does not
act on the review's word alone.

**Owner instructions given in chat stand, even where the repository's general rules would allow more.**
They are recorded in `PROJECT.md` when known. Standing ones:
- The `check-advisors.mjs` `owns` case fix: applied, and CONFIRMED by the owner 2026-11-06 ("Yes, push" to the
  question naming it).
- Never sign in to Argaam anywhere; it signs the nightly's single session out.
- Never record the Argaam account name in committed files; the repository is public.
