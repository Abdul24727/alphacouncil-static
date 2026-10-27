# Questions for the lawyer — AlphaCouncil, 2026-10-27

Step 7's visit, written to be taken as it is. Each question gives the lawyer the facts first, then
the question, then **what the answer changes in the product** — so an answer can be acted on without a
second visit. Write the answers into `docs/legal-advisors-<date>.md` afterwards (the owner's own summary; no
client names, no personal data, no fee details).

Nothing here is legal advice. These are the five questions the plan says to put, with the facts each needs.

## What the site is, in one paragraph

alphacouncil.tech is a research terminal for listed Gulf equities, operated by **Insight Lane Establishment**,
a Saudi sole establishment, Unified National Number 7050149686, trading as AlphaCouncil. It shows market and
fundamental data for about 714 listed companies across 7 exchanges. Two features use a language model: a
**Copilot** that answers questions about the page's own data with citations, and an **advisors' room** where
six simulated advisors answer a member's question about one company in three rounds and a neutral Chair writes
the room's answer. A **Pro** plan at SAR 79/month is built but **checkout is closed** — nobody has ever been
charged, and the owner's rule is that nothing is charged until the product is fully built. The live site today
is free to use for every account.

Legal texts already published: Terms, Privacy, Cookies, Refunds, Merchant, and an **AI and Financial
Disclaimer** (version 1.0, effective 2026-07-21) whose sections include "Information and education only",
"No advisory, fiduciary or client relationship", "AI limitations and hallucinations" and a multi-advisor
section. The lawyer should read the live texts, not this summary.

## (a) The real names and personas

**The facts.** Six seats sit in the room, each named and pictured as a real, living person, with a one-line
"lens":

| Seat | Name shown | Lens shown | Recuses itself from |
| --- | --- | --- | --- |
| `buffett` | Warren Buffett | Durable advantage at a sensible price | — |
| `lynch` | Peter Lynch | Know the story, check the numbers | — |
| `dalio` | Ray Dalio | Cycles, scenarios and balance | — |
| `marks` | Howard Marks | Risk, cycles and what is priced in | — |
| `alwaleed` | Prince Alwaleed bin Talal | Global brands bought in a crisis | Kingdom Holding (4280 Tadawul) |
| `alrumayyan` | Yasir Al-Rumayyan | Patient capital that builds sectors | **nothing** |

Each seat's prompt file is written in AlphaCouncil's own words from the person's publicly documented
principles. The rules built into every seat, in code: never claim to be the person; never quote them; never
describe their private views, holdings or actions; reason in their manner in its own words; and **never tell
anyone to buy, sell or hold anything, no price targets, no personal investment advice**. The screen labels the
room as simulated and carries the disclaimer on every view.

**Two specifics the lawyer should be told plainly.** Yasir Al-Rumayyan is a **serving public official** —
Governor of the Public Investment Fund and Chairman of Saudi Aramco — so the room can show a seat bearing his
name commenting on companies he chairs, including Aramco (2222 Tadawul), the most-used ticker on the site. His
seat currently has **no recusal list at all**, while Prince Alwaleed's seat sits out Kingdom Holding. That
asymmetry was the owner's decision of 2026-10-26 and is not based on advice.

**The questions.**

1. May the site use these real names and likenesses at all, as simulated personas built from public
   principles, for a paid product sold in Saudi Arabia and advertised there?
2. If yes, what must appear on screen, and in what words — a disclaimer per seat, per session, or per page?
3. If no, or only for some of them: which ones, and does a descriptive persona ("The Value Investor") solve
   it, keeping each seat's method but dropping the name and the portrait?
4. Does Al-Rumayyan's position as a serving official change the answer for his seat specifically — and should
   his seat recuse itself from PIF and Aramco holdings the way Alwaleed's does from Kingdom Holding?
5. Does advertising change any of this, as against merely publishing it?

**What the answer changes.** The seat files, the names in `web/messages/{en,ar}.json`, the portraits, and the
recusal lists. Advisor **ids** stay as they are whatever the names become, so saved sessions keep working. The
plan's recorded default if the advice is "no real names": rename to descriptive personas, keep each method,
and claim no connection to the person anywhere.

## (b) Whether this needs a CMA permit

**The facts.** The owner's own plan of 2026-08-08 said not to "enable Council or Research Assistant for
customers" before a permit — and both are enabled today, free, for every account. The product never gives a
recommendation: the Chair writes an assessment of what the data shows, the no-advice rule is enforced in every
prompt, and an automated check scans the Chair's answer and headline for buy/sell/hold language before any
release. Where a session asks the room to choose between readings, **the engine counts the advisors' leans
arithmetically** — no model decides the outcome, and a tie is reported as a tie. Every figure an advisor cites
is matched against the data pack and marked on screen when it cannot be matched.

**The questions.**

1. Does the Copilot, and does the advisors' room, stay inside an information or publishing service that needs
   no Capital Market Authority permit — or does either cross into securities advice or arranging?
2. If either crosses the line: is the line about the **wording** (what the Chair may say), the **framing**
   (choosing between readings at all), the **personalisation** (it answers one member's question about one
   company), or the **charging** for it?
3. Does it make a difference that it is free today and would be sold at SAR 79/month from launch?
4. If a permit or an exemption is needed, which one, roughly what does the process involve, and may the
   features stay live in the meantime?

**What the answer changes.** Potentially whether Step 18 (opening billing) may happen at all, or whether a
feature must be switched off, reworded, or made non-personalised. This is the question with the most power to
change the plan, so it is worth the lawyer's time even if the first three are quick.

## (c) Whether Moyasar must be told

**The facts.** The payment processor is **Moyasar**. The merchant account was approved on the representation
that the product is **not robo-advisory**. Since that approval the advisors' room has been built and is live;
the product still gives no recommendations. No payment has ever been taken — checkout is closed and the only
live subscription is not charging a card.

**The questions.**

1. Does the advisors' room, as it now stands, change what Moyasar was told — and if so, must they be informed
   before the first charge, or at all?
2. What is the right form of words if they must be told, and does telling them carry a risk to the merchant
   account that waiting does not?
3. Does the answer to (b) change the answer here?

**What the answer changes.** Whether a disclosure to Moyasar is a prerequisite of Step 18. Anything touching
Moyasar is an "Always stop" in this project — the owner does it, not Claude.

## (d) The portraits

**The facts.** Six portraits of living people, plus a Chair, drawn as stylised busts for this site — not
photographs, and not traced from one. All seven came from one generation chain, anchored on the first Buffett
image. They are shown large, round a table, with the full name beneath each. The brief and the prompts used
are in `docs/advisors-portrait-prompts.md` and `docs/advisors-image-requests.md`.

**The questions.**

1. May a commercial site show drawn likenesses of these living people in this way?
2. Does the answer differ for the public official (Al-Rumayyan) from the private individuals?
3. Does it differ between Saudi Arabia and the other markets the site covers, or for advertising as against
   the site itself?
4. If a portrait must go, is a silhouette, initials or an abstract mark acceptable in its place?

**What the answer changes.** The files in `web/public/advisors/`. The room already falls back to a seat's
initials when a portrait file is missing, so removing one is a small change, not a redesign.

## (e) Which legal papers the site needs, reviewing the live site

**The facts.** Terms, Privacy, Cookies, Refunds, Merchant and the AI and Financial Disclaimer are published in
English and Arabic. They were written for the earlier version of the site and were **imported, not
hand-written** — they come from a single source through a script, and are never edited in place. The site
takes accounts with an email and password, stores saved sessions and watchlists, and will take card payments
through Moyasar from launch. It serves Saudi Arabia primarily and shows data for seven Gulf exchanges.

**The questions.**

1. Reading the live texts: what is missing, wrong, or out of date for what the site now does — above all the
   advisors' room, which did not exist when they were written?
2. Is the AI and Financial Disclaimer adequate for a simulated-advisor feature, or does that need its own
   text and its own consent?
3. Does anything need a recorded consent at sign-up rather than a link in the footer, and does changing the
   texts require re-consent from existing accounts?
4. What is needed for Saudi personal-data rules given what is stored, and for taking card payments?
5. Is anything needed before **advertising** that is not needed before merely being live?

**What the answer changes.** New or revised texts enter the site through their import source, not by hand, and
consent versions live in `api/app/legal.py` — so how new wording lands is decided with the owner once the text
exists. If re-consent is needed, that is its own piece of work.

## Before the visit

- The lawyer should **use the live site**, signed in, and run one session in the advisors' room — question (e)
  is about what is actually there, and (a) and (d) are much easier to answer having seen a room.
- The three documents worth having open: the **AI and Financial Disclaimer**, the **Terms**, and one finished
  advisors' session.
- Checkout is closed, so there is nothing to pay for and nothing to test on the billing side.

## After the visit

Write the answers into `docs/legal-advisors-<date>.md`: each point of the advice, and the change it requires
with the step that makes it. Step 7's first two "Done when" conditions are about that file, not about the
visit — and the plan's recorded default where advice is ambiguous is to **take the more cautious reading and
list the point for the owner**.
