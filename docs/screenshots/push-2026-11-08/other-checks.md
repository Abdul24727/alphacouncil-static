# Other pre-push checks, `eeb9a9d..dcc4189` (2026-11-08)

The checks below go beyond Step 2's two scans (`scan-diff-hits.txt`, `scan-history.txt`). Every hit was read.

- **Email addresses in the added lines:** `root@alphacouncil.tech` (the SSH login, already public),
  `support@` and `privacy@alphacouncil.tech` (the site's public addresses), and `nobody@deploy-guard.invalid` (a test
  fixture). The other matches are `@pytest`, which is not an address.
- **Commit messages and authors:**
  - **The author address:** every one of the 97 commits uses the same author address as the 408 commits that were
    already public.
  - **The co-author line:** `noreply@anthropic.com`.
  - **File names:** no file name contains an address.
- **Already public before this push:** every Gmail-style address in the pushed tree was already in the tree at
  `eeb9a9d`, so this push added none.
- **"password":**
  - **Where it appears:** route and file names (`/forgot-password`, `/reset-password`, the password-reset screenshot
    folders) and the public legal pages' text.
  - **The beta password:** only in notes saying the owner gives it to the lawyer privately.
  - **Values:** none appears.
- **Value-shaped assignments** (password, secret, token, API key, cookie, authorization): one match, the locale cookie
  `NEXT_LOCALE=ar`, which is not a credential.
- **Argaam lines:**
  - **What they are:** the standing rules ("never sign in", "never record the account name"), the lawyer pack's
    account of the data source, and file names under `scripts/argaam_ar_labels/`.
  - **The account:** none of these lines names an account.
- **A local path:** `docs/screenshots/sector-standing-2026-11-07/deploy-preflight.txt` shows a scratch path under
  `C:/Users/Abdul/AppData/...`.
  - **What it reveals:** a Windows user name, which is already public in the GitHub handle `Abdul24727`, and a
    temporary folder.
  - **Verdict:** not a credential. Later records shorten such paths to `<scratch>`.
- **Binary files:** 82 PNGs.
  - **The signed-out launch check:** 74 PNGs, of production as a visitor.
  - **Stock 2222's Financials tab:** 8 PNGs, 4 from the release candidate's check and 4 from beta. I opened one of
    each: neither shows any account detail, and the beta one shows "Sign in".
- **CI:** no CI or deploy configuration in the range, so the push starts nothing.
- **Default branch:** `master`, not `rebuild`.

## Not run: the Argaam account check by its exact value

- **What earlier pushes did** (2026-11-06):
  1. Copy the account name, unprinted, from the nightly run's session-gate log line on the server into a scratch file.
  2. Count matches with `grep -F` over the added lines, commit messages, tracked files and file names.
  3. Delete the scratch file.
- **When it should have run:** the 2026-11-07 pre-push audit left it for push time.
- **This time:**
  - **Before the push:** I did not run it; I missed it. The checks above are what ran before the push.
  - **After the push:** I tried a read-only SSH command that would only show the shape of the gate lines, with every
    value masked. The session's permission check refused it, and it was not tried another way.
- **What still covers it:**
  - **Emails:** this push added no new email address anywhere (above).
  - **Argaam lines:** every added line that mentions Argaam was read, and none names an account.
- **What remains unverified:** if the account name is not an email address and appears in a line that does not mention
  Argaam, these checks would not see it.
- **For the owner:**
  - **Option 1:** run the count yourself, e.g. `git log -p eeb9a9d..dcc4189 | grep -cF '<the account name>'`, plus the
    same over `git ls-files`.
  - **Option 2:** allow the log read, and Claude runs it.
