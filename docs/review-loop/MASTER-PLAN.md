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
| 2 — Market data correct at the source | ~25 % | DONE 2026-10-24; later data fixes F-13, F-15 live, F-16 applied 2026-11-05 (lands with the 2026-11-06 publish) |
| 3 — Every known defect fixed, checkout proven | ~30 % | DONE 2026-10-22 |
| 4 — Launch: settled, checked, then paid | ~30 % | Steps 8, 9, 22, 23, 10 DONE; **Step 7 (lawyer) NOT STARTED**; Step 18 (billing) open, item 4 needs a real renewal |

Goal 4's Done-when (verbatim, short):
1. The owner's written legal advice is in `docs/legal-advisors-<date>.md`, and every change it asks for is live.
2. Six real portraits in English and Arabic at 1440 and 390 px.
3. `www` answers 301 to the apex, and the certificate covers both.
4. `docs/launch-check-<date>.md` records every check script passing on production, and the monitor at 14 of 14.
5. `checkout_open:true`, and the owner's own first real payment gave Pro.

## What is left (`PROJECT.md` §9, "What is left, by who")

- **The owner's** (Claude cannot do these):
  - Step 7, the lawyer: the questions are in `docs/legal-questions-2026-10-27.md`;
  - the go-ahead for the $66 pilot, then the $393 run (paid model calls);
  - F-14, the pipeline's OpenRouter key;
  - the disk at 83 %;
  - F-12's duplicate webhook;
  - six test accounts;
  - optional server hardening;
  - Step 18 item 4, which waits on a real customer's renewal.
- **Claude's** (pre-approved, on branch `rebuild`):
  - apply the lawyer's advice when it comes;
  - run and read the pilot once the owner funds it;
  - check F-16 after the 2026-11-06 05:00 UTC publish;
  - polish: about 8,100 Gulf statement rows still show in Arabic on English pages (7.6 %), and nothing checks
    that direction yet;
  - the open small items in `PROJECT.md` §6 and §9.

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
