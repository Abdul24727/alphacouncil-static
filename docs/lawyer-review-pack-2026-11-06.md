# AlphaCouncil: the lawyer's review pack, 2026-11-06

**What the owner asks of the lawyer:** test the live site, then draft or revise every legal document it
needs. This pack has what that takes:
- the facts;
- a walk-through to test with;
- the documents as they stand;
- the open questions.

It brings `docs/legal-questions-2026-10-27.md` up to date. That file's five questions (a)–(e) still
stand and are not repeated in full; where a fact in it has changed, this pack says so. Four questions
are added, (f)–(i).

Nothing here is legal advice. It is the operator's own account of the product, written so that advice
can be given and acted on in one visit.

## 1. The site and who runs it

- **Operator:** Insight Lane Establishment, a Saudi sole establishment, Unified National Number
  7050149686, trading as AlphaCouncil.
- **Address:** `https://alphacouncil.tech` (English) and `https://alphacouncil.tech/ar` (Arabic). Every
  page exists in both languages.
- **What it shows:** market and fundamental data for about 714 listed companies on seven Gulf exchanges:
  - prices;
  - financial statements;
  - ownership;
  - corporate actions;
  - news.
- **Two features use a language model:**
  - the **Copilot**, which answers questions about the page's own data with citations;
  - the **advisors' room**, where six simulated advisors answer a member's question about one company in
    three rounds and a neutral Chair writes the room's answer. The company page's **council** tab shows
    each seat's view of the company.
- **Plans:**

| | Free | Pro, SAR 79 a month |
|---|---|---|
| Copilot | 10 questions a day | 60 an hour |
| Holdings / price alerts | 20 / 5 | 200 / 100 |
| Advisors' room | — | 20 sessions a month |
| Council, Financials, Ownership, Calendar, indicators | locked | included |

Pro renews monthly on the saved card until it is cancelled. A failed renewal is retried for 3 days, and
Pro stays on in the meantime.

## 2. Where things stand on 2026-11-06

- **Live** at `alphacouncil.tech`; the latest release went out on 2026-11-06.
- **Billing has been open since 2026-11-02.** The owner opened it before this review, waiving the plan's
  order; Step 7 comes after the launch check.
- **One payment has ever been taken.** It was the owner's own, on 2026-11-02, and was refunded the same
  evening. There is **no paying customer**.
- **Four accounts.** Every test account the site's automated checks had made was deleted on 2026-11-06.

## 3. How to test the site (about an hour)

**Signed out:**
1. Open the home page, Markets and the Screener, then one company: `/t/2222` (Saudi Aramco). Try its
   tabs. Financials, Ownership, Calendar and Council show as locked, because they are Pro-only.
2. In the footer, open the six legal texts in English, then switch to Arabic (`/ar/legal/...`).
3. Read `/pricing`, in both languages: what Pro is sold as.

**Signed in, Free:**

4. Sign up at `/signup` with an email and password, or with Google. Note the tick-box wording, which is
   §4's "registration" consent, and the verification email.
5. Ask the Copilot a question on a company page. Note the citations and the disclaimer.
6. Add a holding and a price alert. Then, in **Settings**:
   - change the language;
   - sign out;
   - finally, **Delete account**. It removes the account and the records tied to it. Three things outlive it
     (§5.1):
     - payment records;
     - the day's rate-limit rows, which hold the IP address and email;
     - backup copies.

**Pro, the advisors' room**, in either of two ways:

7. *On the live site:* pay SAR 79 at `/checkout`, with the tick box naming four documents, and the owner
   refunds it, as the owner did on 2026-11-02. This tests the real checkout, the acceptance wording,
   **Settings → Billing → cancel** and the refund.
8. *On the beta copy* (`beta.alphacouncil.tech`; the owner gives the password). It runs the same code
   with billing closed, so every visitor has Pro without paying. Nothing is charged there.

**In the room** (`/t/2222/advisors`), run one session and read:
- the names and portraits;
- the "simulated" labels;
- each seat's three rounds;
- the Chair's answer and the disclaimer.

Then open `/t/2222/council`.

## 4. The documents as they stand

All six are published in English and Arabic. They were written for the earlier version of the site
(effective 2026-07-21) and **imported unchanged** by a script from one source; they are never edited in
place.

| Document | Version | Address | Accepted where |
|---|---|---|---|
| Terms of Service | 1.2 | `/legal/terms` | at sign-up and at checkout |
| Privacy Policy | 1.2 | `/legal/privacy` | acknowledged at sign-up and at checkout |
| Refund and Cancellation Policy | 1.2 | `/legal/refunds` | at checkout |
| AI and Financial Disclaimer | 1.0 | `/legal/ai-financial-disclaimer` | at checkout |
| Cookie Policy | 1.0 | `/legal/cookies` | linked, not accepted |
| Merchant information | — | `/legal/merchant` | linked, not accepted |

**What is recorded:** each acceptance is stored with the account, as its kind, wording version, document
versions and time:
- **at sign-up:** "I agree to the Terms of Service and acknowledge the Privacy Policy." Terms 1.2, Privacy
  1.2;
- **at checkout:** "I agree to the Terms of Service and acknowledge the Privacy Policy, Refund and
  Cancellation Policy, and AI and Financial Disclaimer." It adds Refunds 1.2 and the Disclaimer 1.0.

A new version of a document can require existing members to accept again. Whether it must is the
lawyer's call.

## 5. Facts for drafting

### 5.1 Personal data the site stores

Two things are kept apart below: how long a token or link **works**, and when its **record is deleted**. The code
is cited for each, so the drafting can follow what the site does.

| What | Why | Works for | Record deleted |
|---|---|---|---|
| Email, display name, language, sign-up time, time the email was verified | the account | — | when the account is deleted |
| Password, as a bcrypt hash only; never the password | sign-in | — | when the account is deleted, or replaced on a reset |
| Google account link, if the member signs in with Google | sign-in | — | when the account is deleted |
| Sign-in sessions: a hash of the cookie's token, never the token | staying signed in | 30 days (`auth.py`, `SESSION_DAYS`); an expired one is refused | at sign-out, at a password reset (all of the account's sessions), or when the account is deleted. An expired session that is never signed out stays until then. |
| Password-reset links: a hash only | the reset email | one hour, once (`RESET_MINUTES`) | expired ones, anyone's, are deleted the next time any reset is requested (`forgot_password`); the account's unused ones on a successful reset |
| Email-verification links: a hash only | the confirmation email | 48 hours, once (`VERIFY_HOURS`) | an unused one is replaced when a new link is sent (`issue_verification`); a used one stays until the account is deleted |
| IP address and email of sign-in, sign-up, reset and verification attempts | stopping abuse | counted over a window of minutes | rows older than a day are deleted the next time anyone's attempt is counted (`DbRateLimit.hit` in `auth.py`). They are **not** tied to the account (`rate_hits` has no user link), so deleting the account does not remove them early. |
| Holdings (company, quantity, average cost), price alerts, preferences | portfolio features | — | when the account is deleted |
| Advisors' room sessions: the member's question, the company, every seat's answer, the Chair's answer, cost | the session record the member can reopen | — | when the account is deleted |
| Acceptances (§4) | proof of consent | — | when the account is deleted |
| Payments: Moyasar's payment id, amount, status, period paid | billing records | — | **never**: kept after the account is deleted, without the link to it |
| Subscription: status, period end, renewal attempts | Pro | — | when the account is deleted |
| Saved card at Moyasar: its token | monthly renewal | until the plan ends | see below |
| Card brand and last four digits; never the card number | billing emails and Settings | — | when the account is deleted. They stay after the plan ends. |

**The saved card, step by step** (`api/app/billing.py`). Four steps decide what happens to the token:
- **Cancelling renewal** (`cancel_renewal`) keeps the token, so the member can resume before the paid period ends
  (`resume_renewal`). A cancelled plan is never charged again: renewals charge only plans not cancelled.
- **The end of a plan is applied by the hourly billing job** (`run_renewals`, the `acp-prod-billing` timer), not at
  the exact end time. The job clears the token and asks Moyasar to delete it (`_end`) on its first run after a
  cancelled plan's period ends. It does the same after the third failed renewal, which is retried once a day.
- **A refund** (`_refunded`) ends Pro and clears the token **only when the refunded payment is the one that paid
  the current period**. A refund of an older payment marks that payment refunded and leaves the plan and the
  token as they are.
- **When the account is deleted** (`forget_card`), the site asks Moyasar to delete the card first. A failure is
  logged, and the account is deleted either way.

`_end` and `_refunded` do not check Moyasar's answer. So the site's records show when it stopped holding a
token, but not that Moyasar deleted its copy.

**Backups** keep their own schedule, whatever is deleted from the live database (`docs/production.md`, "Backups"):
- **On the server:** the account database is dumped every night. `daily/` keeps the newest 14 dumps and `weekly/` the
  newest 8.
- **Off the server:** a copy is pulled to the owner's own computer each day and kept 60 days (daily) and 400 days
  (weekly). The owner's computer therefore holds personal data, unencrypted, behind its sign-in.

The dumps include the card-token ids.

### 5.2 Who else receives data

- **Moyasar** (Saudi payment processor): the member types the card into Moyasar's form, and the site
  never sees the card number.
- **MailerSend:** sends the site's emails (verification, password reset, billing).
- **Google:** only for a member who chooses "Sign in with Google".
- **OpenRouter, and the AI model providers it routes to:** the member's Copilot and room questions,
  together with the company's data, go to language models outside the Kingdom:
  - DeepSeek models for the Copilot and the six seats;
  - Anthropic's Claude for the Chair.
- **The hosting provider:** a rented virtual server. *The owner to state which provider and in which
  country.*

### 5.3 Cookies

Only what the site needs to work:
- **the sign-in session cookie**: 30 days, sent only over HTTPS, unreadable by page scripts;
- **a short-lived cookie** that protects "Sign in with Google" while it is under way;
- **browser storage** (not cookies), which keeps:
  - the layout, such as the sidebar's width;
  - the open Copilot conversation, until the tab is closed. The server does not keep Copilot
    conversations in its database; they pass through it to the model (§5.2).

The language comes from the address (`/ar`), not a cookie. **No analytics or advertising tracker** was
found in the site's code. Moyasar's payment form and Google's sign-in set their own cookies on their own
domains.

### 5.4 Where the data shown comes from

Market data, financial statements and news are collected each night by the operator's own pipeline:
- **mainly from Argaam**, a Saudi financial-data publisher, through an Argaam account;
- **and from the exchanges.**

For news written in Arabic, **an AI model writes**:
- an English headline;
- a summary in both languages;
- an "impact" read: positive, negative or neutral, with a one-line reason.

### 5.5 What keeps the AI features from giving advice

These are built into the product (`docs/legal-questions-2026-10-27.md` (a) and (b) give the detail):
- no seat claims to be the person it is named after, quotes them, or describes their private views;
- no buy, sell or hold, no price target, no personal investment advice. The rule is in every prompt, and
  a check scans the Chair's answer for that language before each release;
- every figure a seat cites is matched against the company's data and marked on screen when it cannot
  be matched;
- where the room is asked to choose between readings, the engine counts the seats' leans arithmetically,
  and a tie is reported as a tie.

## 6. The questions

**(a)–(e)** are as written in `docs/legal-questions-2026-10-27.md`:
- (a) the real names and personas;
- (b) whether a CMA permit is needed;
- (c) whether Moyasar must be told;
- (d) the portraits;
- (e) which legal papers the site needs.

Updates since that file:
- **(b) and (c):** "no customer has paid" is still true on 2026-11-06. The only payment was the owner's
  own, refunded.
- **(e):** the "imported, not hand-written" texts are unchanged. Self-service account deletion exists
  (§3 step 6).

**(f) The data's source.** The site republishes, for a fee, data and news its pipeline collects from
Argaam (through an Argaam account) and from the exchanges.
1. Does Argaam's agreement for that account, and do the exchanges' terms, allow commercial
   republication?
2. If not, what licence is needed, and from whom?
3. What attribution must the pages carry?

**(g) AI-written news text.**
1. What labelling do the AI-written headlines, summaries and "impact" reads need (§5.4)?
2. Does an "impact" read on a listed company's news come closer to advice than the rest of the site
   (see (b))?

**(h) Sending data outside the Kingdom.** Questions go to AI providers abroad, and emails through
MailerSend (§5.2). Under the Personal Data Protection Law, what do the Privacy Policy, the sign-up flow
or the contracts with those providers need for that?

**(i) Monthly renewal.** Pro renews automatically on the saved card. What must checkout say about it,
and must a reminder go out before each renewal? The site can already send one.

## 7. What the lawyer delivers, and how it lands

**From the lawyer:**
- every document the site needs, new or revised, in Arabic and English, each with a version number and an
  effective date;
- the answers to (a)–(i).

**The owner** writes those answers into `docs/legal-advisors-<date>.md`: points of advice only, with no
client names, personal data or fees.

**Then, on the `rebuild` branch:**
- the texts go in through the import script;
- the versions go into `api/app/legal.py`;
- any product change is made: names, portraits, recusals, wording, a feature moved or switched off,
  re-acceptance;
- the checks run, and the result is released to beta and then production, each on the owner's go-ahead.

Expected effort: half a day to two days, depending on what changes. Where the advice is ambiguous, the
plan's rule is to take the more cautious reading and list the point for the owner.
