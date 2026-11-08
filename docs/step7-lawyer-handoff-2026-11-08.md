# Step 7: the lawyer handoff, for the owner (2026-11-08)

Step 7 is the main launch gate still open, and it is the owner's to carry out. Nothing here changes the accepted pack;
it is a checklist pointing to it. The full context is in
`docs/lawyer-pack-check-2026-11-07.md`, section "The handoff, for the owner" (reviews 93 and 94 accepted the pack).

## 1. Confirm three facts first

The pack marks each one. Claude could not settle them read-only; no answer is filled in here.

| # | The fact | Where in the pack | How the owner can confirm it |
|---|---|---|---|
| 1 | The counts as of 2026-11-06: four accounts; one payment, the owner's own, refunded; no paying customer. Still true? | §2 | Payments and refunds: the Moyasar dashboard. Accounts: allow Claude a read-only, counts-only query of production's accounts database (its permission check refused one without the owner's say-so), or count them another way. |
| 2 | The hosting provider and its data centre's country | §5.2 | The Hostinger panel (hPanel), the VPS's location. Public records say Hostinger, with the address registered in France, which does not prove where the server sits. |
| 3 | Where the AI services process the data | §5.2 and question (h) | The OpenRouter account's provider settings, if the owner can find out. If not, leave it as the pack has it: marked not verified. |

If any answer differs from what the pack says, tell Claude before sending, and the pack is corrected first.

## 2. Send exactly two documents

1. **`docs/lawyer-review-pack-2026-11-06.md`**, as updated 2026-11-07; the update note is at its top.
2. **`docs/legal-questions-2026-10-27.md`**: questions (a) to (e), which the pack refers to and does not repeat.

Attach the files, or send these public links. Both files are pinned to commit `7b32e2d`, so the text cannot change
under the lawyer. Checked 2026-11-08: each published copy is hash-equal to the committed file.
- https://github.com/Abdul24727/alphacouncil-static/blob/7b32e2d9b80186814a44294ce57eed3288192739/docs/lawyer-review-pack-2026-11-06.md
- https://github.com/Abdul24727/alphacouncil-static/blob/7b32e2d9b80186814a44294ce57eed3288192739/docs/legal-questions-2026-10-27.md

## 3. Give the lawyer access

- **The live site:** https://alphacouncil.tech (English) and https://alphacouncil.tech/ar (Arabic). It runs
  production `ea51de796c`, released 2026-11-07.
- **The beta copy:** https://beta.alphacouncil.tech answers 401 without its password. Give the lawyer the password
  privately, never in the documents (pack §3, step 8).
- **The test walk-through:** pack §3, about an hour. Claude does not sign up test accounts on the live site
  (decision 2026-10-23), so any account the lawyer uses is the lawyer's or the owner's.

## 4. When the advice comes back

- Save the lawyer's written advice as `docs/legal-advisors-<date>.md`, or send it to Claude to save there.
- Claude then prepares the required changes on `rebuild`. Each release to beta and to production needs its own
  go-ahead from the owner, as always (pack §7 says what the lawyer delivers and how it lands).

## Still open alongside this

- **Step 18, item 4:** verify the first real customer renewal when one happens. A Moyasar connectivity check does
  not prove a renewal, and no renewal is to be simulated.
- **Optional:** the Argaam username form of the exact-value check, only if the username can be had without signing
  in to Argaam. The login email gave three zeros for both pushed ranges on 2026-11-08.
