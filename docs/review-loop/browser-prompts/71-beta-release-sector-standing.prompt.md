You are the reviewer and director for the AlphaCouncil launch. Claude (the builder) has just produced the output below.
You cannot open the project's repository from here. The files the output relies on are attached to this message beside
this prompt, each under its file name; the list below gives each one's path in the repository. Read them to check what
the output claims, and run code on them if that helps (a script that opens "../x" means the attached file x).
If a claim depends on a file that is not attached, say so rather than assuming it.

Stay on the master plan below. It is the owner's original plan and it does not change: do not drift from it,
do not add scope (no new features, panels, campaigns or tooling the plan does not ask for), and do not reopen
decisions the plan records as made. If the output itself drifted from the plan, say so.

Answer in exactly this form:

VERDICT: ACCEPT or FIX
ISSUES: numbered, each one concrete (file, line or claim) and checked against the attached files; "none" if none.
DRIFT: whether the output stayed on the master plan, in one or two sentences.
NEXT STEP: the ONE next step that moves the site closest to the plan's final goal and that Claude may do now
  under the plan's rules (pre-approved work only). Say what to do, where, and why it is the most valuable.
DONE WHEN: how Claude proves that step is finished (a command, a check, a screenshot).
OWNER ITEMS: anything only the owner can do or approve that now matters most, ranked; "none" if none.

End with the line: Response complete

=== FILES ATTACHED BESIDE THIS PROMPT (repository paths) ===
- docs/release-beta-sector-standing-2026-11-07.md
- docs/screenshots/sector-standing-beta-2026-11-07/beta-checks.txt
- docs/screenshots/sector-standing-beta-2026-11-07/beta-checks-harness.sh
- docs/screenshots/sector-standing-beta-2026-11-07/deploy-beta.log
- docs/screenshots/sector-standing-beta-2026-11-07/viewports.json
- docs/screenshots/sector-standing-beta-2026-11-07/check-arabic.txt
- docs/screenshots/sector-standing-beta-2026-11-07/capture-standing-beta.mjs
- docs/screenshots/sector-standing-beta-2026-11-07/en-1440-2222.png
- docs/screenshots/sector-standing-beta-2026-11-07/ar-1440-2222.png
- docs/screenshots/sector-standing-beta-2026-11-07/en-390-2222.png
- docs/screenshots/sector-standing-beta-2026-11-07/ar-390-2222.png
- docs/screenshots/sector-standing-beta-2026-11-07/tree-sha256.txt
- docs/release-request-sector-standing-2026-11-07.md
- scripts/deploy-production.sh

=== MASTER PLAN (docs/review-loop/MASTER-PLAN.md) ===
# The master plan, for every review (do not drift from it)

The owner's instruction (2026-11-06): every output Claude produces is reviewed by ChatGPT. ChatGPT takes
it toward the final plan and gives the next step. Every review restates this plan so the direction cannot
drift.

**How reviews run (the owner's rule, 2026-11-07):** in ChatGPT on chatgpt.com in the owner's browser, with the
strongest model the menu offers (today GPT-6, thinking effort High). The owner's words: "for chatgpt reviews you
should use the broswer and set chatgpt on max model that part does not use credit and we will still have usage so set
this as a roll". The reviewer there cannot open the repository, so every file an output relies on is attached
(`scripts/review-loop/browser_review.py`). Reviews 1 to 69 ran through the Codex CLI, until its usage limit.

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

**The site is published and live** at alphacouncil.tech, running release `b5655a5064` on production. Beta has run
`026699b906` (the sector-standing fix) since 2026-11-07.
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
- **It ran on 2026-11-07 from `d7c2091`:** 60 sessions, $11.36. All 60 were audited by hand, and the counted claims
  (264 retained; 265 before review 70 took one out) were each checked against the session text (`docs/eval/presenter-comparison/RESULT.md`, `audit.md`).
  - **Option 2 fails the cost criterion clearly:** 62 % of today's room against the 40 % limit. Under the rule written
    before the run, that settles it, and today's room stays.
  - **Option 2's discussion was far more accurate:** 55 wrong claims against 209, none in a final answer against 7,
    and 2 inventions against 47. But it is twice as slow, with about 40 seconds before the first words, and
    one of its sessions failed.
  - **The audit found two issues in today's room:**
    - the "sector percentile" field reads the wrong way for lower-is-better metrics;
    - advisors invent statement figures on packs that have no statements (P9).
  - **What comes next is the owner's choice:** keep today's room and fix those two issues, screen a one-model option 2,
    or stop.
  - **The owner chose (2026-11-07): "Keep it, take the fix".** Today's room stays. The sector-percentile fix (site
    labels in en and ar, the room's pack, the Copilot) is on `rebuild` as `867f944`. Releasing it needs the owner's
    go-ahead.
  - **The release candidate (reviews 73 to 75):**
    - **What it is:** a fix-only branch, `release/sector-standing` at
      `026699b906ea3a513b4f2dbfc37672fa68ee9d42`. It is today's live `b5655a5` plus the fix, eight files, with none
      of the prototype.
    - **Review 74 accepted it.**
    - **The deploy scripts now ship only an exact approved commit** (`DEPLOY_SHA`, review 75's fix).
    - **Beta released 2026-11-07** on the owner's go-ahead ("Yes, deploy to beta"). Beta runs `026699b906`, its
      files equal the commit, and its checks pass (`docs/release-beta-sector-standing-2026-11-07.md`).
    - **What waits:** production, on its own go-ahead. Its `--check` now passes. It still runs `b5655a5064`.

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

=== CLAUDE'S OUTPUT: Beta release of the sector-standing fix (026699b906) ===
# Output 71: the sector-standing fix is on beta (the owner's go-ahead)

**The owner's go-ahead** (in chat, 2026-11-07): "Yes, deploy to beta", to the question "Deploy the sector-standing
fix (026699b906) to beta only?". Review 76's owner item 2 asked for exactly this.

**What was done** (`docs/release-beta-sector-standing-2026-11-07.md`, attached):
1. **The preflight first, as the request said:**
   - `git diff --quiet c3bcff6 -- scripts/deploy-staging.sh` exited 0.
   - The checkout was clean at `026699b906ea3a513b4f2dbfc37672fa68ee9d42`.
   - The staging `--check` exited 0 and matched `deploy-final-check.txt`.
2. **The request's own deploy command:** nothing changed or added (`deploy-beta.log`, attached).
   - **Upload, build and switch:** the commit was uploaded and built (`next build`, 93 of 93 pages).
   - **The restart:** both beta services restarted and answered 200.
   - **The prune:** it removed `2e44ee6fbf`, as the request said.
   - **The exit:** 0.
3. **Production was not touched.** Nothing was pushed or paid for.

**The checks after** (`beta-checks.txt`, made by the attached `beta-checks-harness.sh`; read-only, GET only, through
SSH tunnels):
- **What runs:** beta runs `releases/026699b906`, with releases `026699b906 b5655a5064 5c18a3ae46`. Production runs
  `prod/releases/b5655a5064`, unchanged, and all four services are active.
- **The files:**
  - **The changed files:** the eight are equal by sha256 to the commit.
  - **The whole tree:** all 3,566 committed files (all but symlinks) on beta are equal by sha256 to the commit
    (`tree-sha256.txt`).
  - **The prototype:** `presenter.py` and `debate_engine` are absent.
- **The site:** API health is ok and the pages answer. The en and ar captures at 1440 and 390 carry the new labels
  and tooltip, with no sideways scroll and no old label (`viewports.json`; the four PNGs are attached).
- **The notes:** P9's notes on beta say "sector standing" and never "sector percentile".
- **The Arabic string check** (signed out, 1440 and 390): 48 Arabic page views, 0 English strings outside the
  allow-list, exit 0 (`check-arabic.txt`, attached).
- **Production's `--check` for the commit now exits 0**, with "beta now: 026699b906" and `b5655a5064` kept as its
  rollback. It approves nothing.

**One thing that looked wrong and is explained:**
- **What moved:** three standings differ from the candidate's captures: 28 → 27, 82 → 81 on gross margin, 47 → 45.
- **The timing:** those captures were made at 00:50 UTC. The pipeline's nightly refreshed the fundamentals at 01:48
  UTC (`as_of` in check 7).
- **The code:** the code that serves the numbers is identical in both releases
  (`git diff --quiet b5655a5 026699b -- api/app/routers web/src` exits 0).
- **The page:** it shows exactly what beta's API returns now.
- **So:** the change is the night's data, not the release.

**A harness slip, fixed before the record was kept:**
- **What happened:** the first run of check 3 reported a difference.
- **The cause:** Python on Windows wrote the local hash list with CRLF line endings, and the server's has LF.
- **The fix:** the harness now writes LF and keeps whole paths (none contains a space), and its rerun matches. Only
  the rerun is recorded.

**What was not checked:**
- **The room's and the Copilot's wording with a real model:** that needs a paid session. Their code is on beta byte
  for byte, and its tests passed in review 74.
- **Production's API:** opening its tunnel was refused by the session's permission check, and it was not needed for
  the comparison.

**The question for the review:** is beta's release of `026699b906` verified well enough to put production to the owner,
as described in the attached record?
