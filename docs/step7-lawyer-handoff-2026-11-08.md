# Step 7: the lawyer handoff, for the owner (2026-11-08)

Step 7 is the main launch gate still open, and it is the owner's to carry out. This is a checklist pointing to the
pack, which was corrected on 2026-11-08 with the facts below. The full context is in
`docs/lawyer-pack-check-2026-11-07.md`, section "The handoff, for the owner" (reviews 93 and 94 accepted the pack).

## 1. The three facts, as they stand (2026-11-08)

Claude read them in the owner's own accounts, with the owner signed in (`docs/lawyer-pack-facts-2026-11-08.md`), and
the pack is corrected. One item is left for the owner.

| # | The fact | Where in the pack | Status |
|---|---|---|---|
| 1a | Payments | §2 | **Done.** Moyasar's live account shows two payments ever, both the owner's own tests and both refunded. No paying customer. |
| 1b | The number of accounts (four as of 2026-11-06) | §2 | **The owner's.** Run the counts-only query in the facts file in your own terminal; Claude's permission check refuses it. If the count is not four, tell Claude, and §2 is corrected before sending. |
| 2 | Hosting | §5.2 | **Done.** Hostinger, with the server in Paris, France, from hPanel. |
| 3 | The AI services | §5.2, (h) | **Recorded; location not verified.** The pack lists the providers observed on the shared OpenRouter account for the site's models, including two companies based in China. No site request was traced, and where requests were processed is not shown. The pack says so. |

If the account count differs from the pack, tell Claude before sending, and the pack is corrected first.

## 2. Send exactly two documents

1. **`docs/lawyer-review-pack-2026-11-06.md`**, as updated 2026-11-08; the update notes are at its top.
2. **`docs/legal-questions-2026-10-27.md`**: questions (a) to (e), which the pack refers to and does not repeat.

**Attach the files.** The pack was corrected on 2026-11-08, after the commit `7b32e2d` that the public links
pointed to. Those links show the old text, so they are removed here: never send them. If you want links, they come
from the next push you approve, pinned to that commit and checked. The same holds after any later correction: send
the files as they stand, never a link to an older commit.

## 3. Give the lawyer access

- **The live site:** https://alphacouncil.tech (English) and https://alphacouncil.tech/ar (Arabic). It runs
  production `ea51de796c`, released 2026-11-07.
- **The beta copy:** https://beta.alphacouncil.tech answers 401 without its password. Give the lawyer the password
  privately, never in the documents (pack §3, step 8).
- **The test walk-through:** pack §3, about an hour. Claude does not sign up test accounts on the live site
  (decision 2026-10-23), so any account the lawyer uses is the lawyer's or the owner's.

## 4. When the advice comes back

- **The owner writes a summary** into `docs/legal-advisors-<date>.md`, as the pack's §7 and the questions' "After the
  visit" say. It holds the points of advice, each with the change it requires, and no client names, personal data
  or fees. The repository is public: never commit the lawyer's own letters, emails or documents, and do not hand
  them to Claude to save. Claude works from the summary.
- Claude then prepares the required changes on `rebuild`. Each release to beta and to production needs its own
  go-ahead from the owner, as always (pack §7 says what the lawyer delivers and how it lands).

## Still open alongside this

- **Step 18, item 4:** verify the first real customer renewal when one happens. A Moyasar connectivity check does
  not prove a renewal, and no renewal is to be simulated.
- **Optional:** the Argaam username form of the exact-value check, only if the username can be had without signing
  in to Argaam. The login email gave three zeros for both pushed ranges on 2026-11-08.
