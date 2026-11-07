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
- docs/review-loop/replies/75-deploy-preflight-for-candidate-026699b.md
- scripts/deploy-staging.sh
- scripts/deploy-production.sh
- docs/release-request-sector-standing-2026-11-07.md
- docs/screenshots/sector-standing-2026-11-07/deploy-preflight.txt
- docs/screenshots/sector-standing-2026-11-07/deploy-preflight-harness.sh
- 70-scripts-since-review-75.diff (made for this review, not in the repository: a diff or a command transcript)
- 70-docs.diff (made for this review, not in the repository: a diff or a command transcript)
- 70-git-checks.txt (made for this review, not in the repository: a diff or a command transcript)

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
    - **What waits:** the beta release waits for the owner's go-ahead, and production is a separate go-ahead after
      beta is checked (`docs/release-request-sector-standing-2026-11-07.md`).

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

=== CLAUDE'S OUTPUT: Exact-commit deploy guard ===
# Output 70: the deploy scripts ship only the exact approved commit (review 75's step)

**Commits on `rebuild`:** `724e742` (the guard), `8e53826` and `c3bcff6` (two output wordings), `6959e1f` (the request
and the record). Nothing was uploaded, deployed, pushed or paid for.

**What changed in both scripts** (`70-scripts-since-review-75.diff`, both scripts attached):
- **The commit is pinned (issue 1):**
  - **When it is required:** with `DEPLOY_BRANCH` set to anything but `rebuild`, `DEPLOY_SHA` is required.
  - **What it must be:** a full 40-character lowercase commit (`^[0-9a-f]{40}$`), equal to
    `git rev-parse --verify "HEAD^{commit}"`.
  - **What ships:** the script stores that commit in `commit` and archives it (`git archive --format=tar "$commit"`),
    so HEAD is not resolved again.
  - **The release name:** `${commit:0:10}`, the same 10 characters as the old `--short=10`.
- **The default is kept:** with no `DEPLOY_*` set, `rebuild` deploys as before. `DEPLOY_SHA` may also pin a `rebuild`
  deploy.
- **`--check` fails when prerequisites are unmet (issue 2):**
  - **Production:** it exits 1 with "NOT READY: beta runs …" while beta runs another commit.
  - **Both scripts:** they now also report which releases a deploy would prune and the rollback release, and exit 1 if
    the rollback release would be pruned.
  - **A passing check** prints "preconditions met (this check approves nothing; deploying needs the owner's
    go-ahead)". It no longer says "ready", because `rebuild` passes it too and must not ship.
  - **Still read-only:** `--check` reads the server and exits before any upload.
- **The placeholder is gone (issue 3):** `docs/release-request-sector-standing-2026-11-07.md` now gives the tested
  command in full:
  `cd /c/AlphaCouncil-Staging/deploy-026699b && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=026699b906ea3a513b4f2dbfc37672fa68ee9d42 bash /c/projects/alphacouncil-platform/scripts/deploy-staging.sh`.
  It also adds a step before the deploy: confirm the script is unchanged since `c3bcff6`, then rerun with `--check`.
- **Issue 4 (evidence cited, not attached):** noted. Per review 75, review 74's suite is not repeated, since the
  application code did not change. Only the two deploy scripts and documents changed.

**The DONE WHEN of review 75, item by item** (`deploy-preflight.txt`, made by the attached
`deploy-preflight-harness.sh`; each case shows its command, output and exit code):
1. **`bash -n`:** exit 0 for both scripts.
2. **Staging `--check` accepts `release/sector-standing` only with the exact SHA:**
   - **S9, the exact SHA:** exit 0, "commit: 026699b906ea3a513b4f2dbfc37672fa68ee9d42 (equals DEPLOY_SHA)", 3,837
     paths, release `releases/026699b906`.
   - **S3 (no SHA), S4 (short `026699b`) and S5 (`b5655a5…` full):** each refused, exit 1.
3. **Each failure refuses before any upload, build, switch or deletion:**
   - **The cases:** missing SHA (S3), wrong SHA (S5), a different branch (S6: `rebuild`'s checkout with the candidate's
     settings), and an advanced release-branch HEAD (S7). Each is refused with exit 1.
   - **The advanced HEAD:** S7 ran in a throwaway local clone whose `release/sector-standing` is one empty commit past
     `026699b`. The real branch was not touched, and the clone was deleted afterwards.
   - **On the deploy path itself:** S2', S3', S5', S6' and S7' rerun these cases without `--check`, with
     `STAGING_HOST=nobody@deploy-guard.invalid`, so even a broken guard could not have uploaded. Each is refused,
     exit 1, and none prints `== upload`.
4. **The default `rebuild` invocation:** S1 exits 0 with the same fields as before (checkout, branch, the full commit,
   now labelled `commit:` rather than `HEAD:`, archive count, release, beta now, releases), plus the prune and rollback
   lines. S8 shows that `DEPLOY_SHA` also pins
   `rebuild`: a wrong SHA is refused.
5. **Production's preflight fails while beta runs `b5655a5064`:**
   - **P1, the candidate with the exact SHA:** exit 1, "NOT READY: beta runs b5655a5064, not 026699b906".
   - **P2 (no SHA), P3 (advanced HEAD) and P4 (`rebuild`):** exit 1 each.
   - Nothing was deployed.
6. **The final read-only preflight** (S9 and P1, and the server read at the end):
   - **The checkout:** `C:/AlphaCouncil-Staging/deploy-026699b`, branch `release/sector-standing`, clean.
   - **The commit and archive source:** commit `026699b906ea3a513b4f2dbfc37672fa68ee9d42`, which is also the archive
     source.
   - **Beta and production:** both `/…/releases/b5655a5064`, all four services active.
   - **Release lists:** `b5655a5064 5c18a3ae46 2e44ee6fbf` on both tiers.
   - **The prune:** `2e44ee6fbf`.
   - **The rollback:** `releases/b5655a5064 (kept)`.
7. **The updated request** (attached) states:
   - **The candidate:** the exact commit.
   - **The commands:** the check, the deploy and a rollback.
   - **The scope:** beta only.
   - **The prune:** it removes `2e44ee6fbf`, and `b5655a5064` stays as the rollback.
   - **Production:** a separate go-ahead, whose `--check` passes only once beta runs `026699b906`.

**Whitespace:** `git diff --check` is clean for every commit. The record has no trailing spaces, which is why
`c3bcff6` joins the release lists with `paste -sd` rather than `tr`.

**The question for the review:** is the exact-commit guard sound, and may the beta release of
`026699b906ea3a513b4f2dbfc37672fa68ee9d42` now be put to the owner?
