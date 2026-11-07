# The lawyer pack, checked against the live site (2026-11-07)

**What this is:** review 87's next step. It is a read-only check that `docs/lawyer-review-pack-2026-11-06.md` still
matches the live site, so that the owner can send it.

**The result:** the site answers at every address but one. The pack is corrected in place.
- **What was wrong in the pack:**
  - one wrong address;
  - one feature described too loosely;
  - an outdated release;
  - one question that understated what the site already does;
  - claims stated as confirmed that were not, found by reviews 88 and 89:
    - the room's AI models;
    - where the AI data is processed and how it is routed;
    - what beta shares with production.
- **What was added:** two facts the lawyer should have, and two known issues in the imported legal texts (review
  88).
- **Not done:** nothing was sent, no legal text on the site was changed, and nothing was deployed, pushed or paid
  for.

## The handoff, for the owner

**Give the lawyer exactly two documents:**
1. `docs/lawyer-review-pack-2026-11-06.md`, as updated 2026-11-07. The update note is at its top.
2. `docs/legal-questions-2026-10-27.md`: questions (a)–(e), which the pack refers to and does not repeat.

| | |
|---|---|
| **The live site** | https://alphacouncil.tech (English) and https://alphacouncil.tech/ar (Arabic) |
| **The release it runs** | production `ea51de796c`, since 2026-11-07 19:35 UTC (`docs/release-production-p9-2026-11-07.md`) |
| **The beta copy** | https://beta.alphacouncil.tech answers 401 without its password. The owner gives the lawyer the password privately (pack §3 step 8) |

**Facts still waiting on the owner's confirmation before sending** (the pack marks each one):
1. **The counts in pack §2:** four accounts; one payment, the owner's own, refunded; no paying customer. They are as
   of 2026-11-06 and were not counted again.
2. **The hosting provider and its country** (§5.2), which the pack leaves to the owner.
3. **The AI models the six seats and the Chair use on production** (§5.2). Only the Copilot's was confirmed live.
4. **Where the AI services process the data** (§5.2, (h)), if the owner can find out. Otherwise the pack leaves it
   marked as not verified.

**Kinds of statement in the pack:**
- **Confirmed live on 2026-11-07:** the addresses, page wording, plans, legal versions, the Copilot's model, the
  seats and the universe.
- **Read from the released code:** the renewal reminder, the retries and grace period, the AI services' defaults
  and routing, and what the deploy script is written to copy at setup. These are marked as what the code does, not
  as what production is confirmed to do.
- **For the owner to confirm:** the four facts above.

## How it was checked

Every check is read-only: GET requests to the public site, signed out, with no account, no form and no click. The
code was read at the released commit. Evidence: `docs/screenshots/lawyer-pack-check-2026-11-07/`.
- **`urls.txt`** (`urls.sh`, 20:01 UTC): every address the pack names, in both languages where the pack says both.
  It records the first answer, any redirect, and the final answer.
- **`page-text/`** (`page-text.mjs`): the visible text of 18 pages in English and Arabic, as a signed-out visitor
  sees them at 1440 px. `index.txt` lists the status of each.
- **`api-facts.txt`** (`api-facts.sh`, 20:06 UTC): the public API's health, the company list, the Copilot's model,
  the room's seats, and the address Moyasar was once shown.
- **`contact-check.txt`** (`contact-check.mjs`, 20:19 UTC, after review 88):
  - every site address inside the five legal texts, in both languages;
  - what the contact address answers;
  - what its target, `/legal`, shows. Its text is `page-text/legal-index.{en,ar}.txt`.
- **`plan-diffs.txt`** (after review 88): the plan files' full diff since `5a44457`, the last commit before the
  owner's "Yes, deploy to production".

## Every address in the pack (`urls.txt`)

| Address | Answer |
|---|---|
| `/` and `/ar` | 200 |
| `/home`, `/markets`, `/screener` (en and ar) | 200 |
| `/t/2222` and its tabs `financials`, `ownership`, `calendar`, `council`, `advisors` (en and ar) | 200 |
| `/legal` and `/legal/terms`, `privacy`, `refunds`, `ai-financial-disclaimer`, `cookies` (en and ar) | 200 |
| **`/legal/merchant` (en and ar)** | **404**. See discrepancy 1 |
| `/pricing`, `/methodology`, `/signup`, `/login`, `/checkout`, `/settings` (en and ar) | 200 |
| `beta.alphacouncil.tech` | 401 without the password, as expected |
| `www.alphacouncil.tech` | 301 to `/`, then 200 |

**A note on `/legal/merchant`:**
- **What it answered:** the first request answered 200, and every request after it 404. The page-text read got 404
  in both languages. Three more rounds at 20:08 UTC got 404 each time, while `/legal` answered 200
  (`merchant-recheck.txt`).
- **Why 404 is right:** the address is not one of the site's legal documents (`LEGAL_DOCS`).
- **The first 200:** not explained here.

**The repository files the pack links to:** all exist, locally and on the public branch `origin/rebuild`:
`launch-check-2026-11-06.md`, the two contact sheets, `screenshots/release-b5655a5064/beta-checks.txt` and
`legal-questions-2026-10-27.md`.

## The pack's descriptions, against the site's own words

**The advisors' room (pack §1, §3 and §5.5):** it matches.
- **Seats:** six named advisors and a Chair, each with a portrait (`/api/v1/debate/status`).
- **Rounds:** `/t/2222/advisors` shows the rounds Brief, Answers, Fault lines, Challenges, Final word and The
  answer. The advisors speak in three of them, and the Chair in the other three.
- **The answer:** the Chair "writes the room's complete answer … Never buy, sell or hold."
- **The label:** "Simulated advisors built from each person's publicly documented principles and drawn as
  caricatures. They are not the people and do not speak for them. The room assesses AlphaCouncil data; it does not
  give investment advice." The Arabic page carries the same label.
- **Signed out:** the room asks the visitor to sign in to convene the advisors.
- **Pricing:** `/pricing` sells it as "20 sessions a month in which simulated advisors debate your question about a
  stock and score the options against our data". The API's `pro_limit` is 20.

**The plans (pack §1):** they match `/pricing` and `api/app/plans.py`.
- **Price:** Free is 0 and Pro is 79 SAR a month.
- **Copilot:** 10 questions a day on Free, and 60 an hour on Pro.
- **Holdings and price alerts:** 20 and 5 on Free, 200 and 100 on Pro.
- **The room:** 20 sessions a month, on Pro only.
- **Pro-only tabs:** Financials, Ownership, Calendar and Council each show the Pro lock to a signed-out visitor, in
  both languages.
- **Renewal:** a failed renewal is retried daily up to 3 times, with Pro kept on for 3 days (`billing.py`; `plans.GRACE`).

**The legal documents (pack §4):** they match.
- **Versions:** Terms 1.2, Privacy 1.2, Refunds 1.2, AI and Financial Disclaimer 1.0, Cookies 1.0. Each is
  effective 2026-07-21, in both languages.
- **The sign-up tick box:** it reads exactly "I agree to the Terms of Service and acknowledge the Privacy Policy."
- **The checkout wording:** the pack quotes `api/app/legal.py` word for word. Checkout itself asks a signed-out
  visitor to sign in first, so its tick box was not seen.
- **The footer:** it carries all six links.

**Other facts (pack §1, §5.2, and question (c)):**
- **The universe:** 714 companies on seven exchanges.
- **The Copilot's model:** `deepseek/deepseek-v3.2`, read from the live `/api/v1/copilot/status`.
- **The room's models:** not confirmed. The code's defaults are DeepSeek for the six seats and Anthropic's Claude
  for the Chair. Production's own setting is in a file that also holds credentials, so it was not read. See
  discrepancy 5.
- **`/api/capabilities`** still answers 404, as question (c) says.

## Discrepancies found, and how the pack now reads

1. **The merchant information's address (pack §4).**
   - **The pack said:** `/legal/merchant`, which answers 404.
   - **The site:** the footer's "Merchant information" link goes to `/legal#merchant` (`SiteFooter.tsx`). The same
     notice also appears at the foot of every legal document.
   - **Now:** the table reads `/legal#merchant`, and at the foot of every legal document.
2. **The council tab (pack §1).**
   - **The pack said:** the council tab "shows each seat's view of the company". That reads as the advisors' room.
   - **The site:** the council is a separate feature with no language model. It has six rule-based seats (Value,
     Quality, Income, Momentum, Risk, News), and each votes bullish, neutral or bearish on every equity
     (`/methodology`, "How the council votes"). `/pricing` sells "The council's vote and each seat's reasoning on
     every equity".
   - **Now:** §1 describes it in those terms and points to question (b). Question (b) in `legal-questions` already
     asks whether the word "vote" matters. Neither file had said what the vote is.
3. **The release (pack §2).**
   - **The pack said:** the site runs `b5655a5064`.
   - **The site:** it runs `ea51de796c`, which adds two fixes. One relabels "Sector percentile" as "Sector standing"
     on the Pro Financials panel. The other changes the data notes the room and the Copilot are given; nothing
     visible changes.
   - **Now:** §2 says so, and notes that the signed-out checks were run again on 2026-11-07 with the same results.
4. **Renewal (pack §6 (i)).**
   - **The pack said:** "The site can already send" a reminder.
   - **The site:** it already does. The hourly billing job emails a reminder three days before each renewal
     (`billing.py`, `REMIND_BEFORE`). Checkout already says "Renews automatically every month on the same day, at
     the same price, until you cancel." (`web/messages/en.json`, `checkout.renewal`).
   - **No reminder has gone out yet:** billing opened on 2026-11-02, so the first renewal can fall due no earlier
     than 2026-12-02, and its reminder no earlier than 2026-11-29.
   - **Now:** (i) states both, and adds that `/pricing`, read signed out, does not mention renewal.

**Found by review 88, two claims the pack stated as confirmed that were not:**

5. **The AI models (pack §5.2).**
   - **The pack said:** "DeepSeek models for the Copilot and the six seats; Anthropic's Claude for the Chair", as fact.
   - **What is known:**
     - **The Copilot:** confirmed live: `deepseek/deepseek-v3.2`, `"stand_in": false`.
     - **The room:** confirmed live not on the stand-in (`/api/v1/debate/status`, `"stand_in": false`). In this code
       that means an OpenRouter key is set and `COPILOT_PROVIDER` is not `standin` (`api/app/routers/debate.py`,
       `uses_models`). *(Added after review 90.)*
     - **The seats and the Chair:** only the code's defaults are known.
     - **Routing** (`api/app/settings.py` lines 34–54; `api/app/copilot/openai_compat.py`, `host_routing`):
       - **The service:** OpenRouter by the code's default. `COPILOT_PROVIDER=auto` picks OpenRouter when its key is
         set, otherwise Anthropic when its key is set, otherwise the stand-in. Any OpenAI-compatible endpoint can stand
         in for OpenRouter.
       - **When OpenRouter is used:** it chooses the hosting company per request. The code's default asks it to sort
         hosts by latency, and `COPILOT_PROVIDER_ORDER` can name hosts for the Copilot to try first, with fallbacks.
       - **Not read:** production's values for all of these.
     - **Where the data is processed:** not verified. Neither the serving companies nor their countries are known
       from this check.
   - **Now:** §5.2 and (h) keep the confirmed fact apart from the code's defaults. They mark the seats' and the
     Chair's models for the owner to confirm. They say the data *may* be processed outside the Kingdom, and that the
     companies, the countries and production's routing were not verified (review 89).
6. **What beta shares with production (pack §2).**
   - **The pack said:** beta "runs the same release on the same data".
   - **What is known:**
     - **The release:** the same.
     - **The setup:** the deploy script is written to copy beta's market-data settings when it first creates
       production's settings file, and to leave an existing file alone (`scripts/deploy-production.sh`, lines 79–99).
     - **Not established** (review 89): that the copy ran, since no output of that first setup is on record, and that
       the settings match today.
   - **Now:** §2 says exactly that.
   - **Also corrected:** the same claim in `docs/release-production-p9-2026-11-07.md`, which now says production's
     P9 notes are not established to equal beta's.

**Known issues in the imported legal texts, found by review 88** (now listed under question (e); the texts
themselves are left alone until the lawyer advises):

7. **The contact page** (`contact-check.txt`).
   - **What the texts say:** all five documents, in English and Arabic, say "Contact page:
     https://alphacouncil.tech/contact.html".
   - **Where it leads:** the rebuilt site has no contact page. nginx redirects that address with a 301 to `/legal`
     (`deploy/nginx-production.conf`: `location = /contact.html { return 301 /legal; }`).
   - **What `/legal` shows:** the merchant notice, with the registered address, a telephone number and the emails. It
     has no contact form.
   - **Other addresses:** `/ar/contact.html` and `/contact` answer 404.
   - **The only other site address in the texts** is the bare `https://alphacouncil.tech`.
8. **The merchant notice differs by language.**
   - **English:** "Support: support@alphacouncil.tech · Privacy: privacy@alphacouncil.tech".
   - **Arabic:** gives only the support email.
   - **Where it shows:** the notice shows on `/legal` and at the foot of every legal document, so the Arabic
     documents' foot lacks the privacy email.
   - **Not affected:** the Arabic Privacy Policy's own text does carry it (`page-text/legal-privacy.ar.txt`).

**Added, because the lawyer should have them:**
- **VAT (pack §1):** `/pricing` says "AlphaCouncil is not currently charging VAT; any applicable tax will be shown
  before payment."
- **The data's source (question (f)):** the site's `/methodology` says the pipeline collects "from public market
  sources", and no English page read here names Argaam. The pack's own account is that the data comes mainly from
  Argaam, through an account. That gap is part of what (f) asks.

## What this check did not cover

- **The signed-in walk-through (pack §3, steps 4–8):** Claude makes no accounts on the live site. That includes
  sign-up, the Copilot, holdings, Settings, checkout, and a room session.
- **The legal texts' content:** what the texts say was not reviewed; that is the lawyer's work. Only their
  addresses, versions and dates were compared. After review 88, so were the site addresses and emails inside them.
- **The account and payment counts:** not counted again (above).

## The repository after this check

- **Changed:**
  - this file and its evidence folder;
  - the pack;
  - the plan files (`PROJECT.md`, `docs/review-loop/MASTER-PLAN.md`);
  - a correction in `docs/release-production-p9-2026-11-07.md`, about which data production's notes are made from.
- **Not changed:** anything outside `docs/` and `PROJECT.md`.
- **`git diff --check` is clean,** after two whitespace-only edits:
  - review 88's saved reply lost one trailing space at the end of a line;
  - `plan-diffs.txt` lost the single spaces that mark blank context lines.

  The reply was copied with its length and SHA-256 checked against the page before saving.

**The plan files' changes are status updates only** (`plan-diffs.txt`, from `5a44457` to this commit). Every
removed line was replaced by its updated form. The hunks touch:
- **`PROJECT.md`:**
  - line 2's "Deployed" sentence;
  - new bullets in the P9 history under §5: the go-ahead, the release, its checks, reviews 87 and 88, and this check.
- **`docs/review-loop/MASTER-PLAN.md`:**
  - Goal 4's state cell, adding the evening's launch-check rerun;
  - the "site is published" sentence, naming the release;
  - new P9 bullets.
- **Untouched:** the objective, the out-of-scope list, the four goals' Done-when, §4's rules and approvals, the
  owner's directions and the settled decisions.
