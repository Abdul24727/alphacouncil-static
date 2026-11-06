# Output 29: review 28's two corrections, made

Both corrections are made in `docs/release-readiness-2026-11-06.md`, "Pre-push audit", and in output 28, each
with a correction note. `PROJECT.md` §5 notes them too.

**1. File categories, reconciled with git** over `ccfe063..9712418`:
- 1,289 files: 1,136 PNG, 68 txt, 60 md, 22 code (8 py, 6 ts, 4 mjs, 3 json, 1 tsx) and 3 patch.
  1,136 + 68 + 60 + 22 + 3 = 1,289.
- `git diff --numstat`: 153 text files, **5,520 lines added and 122 removed**. 1,136 binary.
- `--diff-filter=D`: **0 files deleted**.
- The record now says "0 files deleted" in place of "nothing deleted", and gives the line counts.

**2. Both tracked env templates.** `git ls-files '*env*'` gives two files. `git diff --name-only ccfe063..9712418
-- '*env*'` gives 0, so neither changed in the range. Both were read in full.
- `api/.env.example`: paths left empty, plus `MARKET_DB_IMMUTABLE=true`, a non-secret default.
- `deploy/api.env.example`: server paths (`/var/lib/alphacouncil/…`, `/opt/alphacouncil/…`) and non-secret
  defaults. Every key, secret and password line is commented out with nothing after the `=`:
  - `OPENROUTER_API_KEY`;
  - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`;
  - `MOYASAR_PUBLISHABLE_KEY`, `MOYASAR_SECRET_KEY` and `MOYASAR_WEBHOOK_SECRET`;
  - `ANTHROPIC_API_KEY`;
  - `SMTP_USER` and `SMTP_PASS`.
- **Why it was missed:** my file-name pattern matched `.env` but not `api.env`.

**Unchanged:**
- **Re-scan at push time:** the same scans run again over the exact range at push time. Commits after
  `9712418` are outside the audited range by construction.
- **The push:** it is the owner's go-ahead.

**The question for the review:** is this sound, and what is the single next pre-approved step?
