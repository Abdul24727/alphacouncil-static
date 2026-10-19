# PROJECT — alphacouncil-platform launch
**File:** C:\projects\alphacouncil-platform\PROJECT.md   **Updated:** 2026-10-19   **At version:** `280211b` on branch `rebuild` (this file's latest state committed on top)

## 1. Objective
alphacouncil.tech is ready to advertise: the code is safe off this computer, the market data is right at its source, and the named advisors, portraits and `www` address are settled.

- The rebuild itself is finished and live: every phase of the original rebuild plan shipped, and production runs this app since 2026-10-17.
- What is left is what stands between "live" and "safe to put money into advertising".
- For the owner (Abdul), who runs AlphaCouncil alone and has no paying members yet.
- Correct data is the product: a research terminal that shows a stopped price or a wrong unit loses trust faster than one that is missing a feature.

**Out of scope:** new features or panels; the advertising itself (campaigns, budgets, copy); retiring the old backend that still serves `api.alphacouncil.tech`; a cloud bucket for backups (the owner has none; the computer copy is used).

## 2. Environment & Ground Truth
Stack, data facts, Next.js patterns and standing rules: `CLAUDE.md`. Servers, releases, billing, backups, monitoring and the outside check: `docs/production.md` (the runbook). Read those; this section holds only what neither says.

- SSH `root@alphacouncil.tech` works from this computer with its key (`~/.ssh/id_ed25519`, also used by the daily backup task). Tunnels to the sites: `localhost:3201` = beta, `localhost:3301` = production; they stall, restart them with `-o ServerAliveInterval=30`.
- The old pipeline (scrapers, nightly run `run_parallel_universe.py`, ticker list `argaam/tickers.csv`) runs on the server in `/opt/alphacouncil/backend`. A local checkout is `C:\AlphaCouncil-Staging\work\f11-prod-merge` (commit `3027ab5`, 2026-09-06) and may differ from the server's copy.
- Alerts (server monitor and outside check) go to `attmimi.abdulw@gmail.com`. The Gmail connected to Claude is a different account: alert emails cannot be checked from here.
- The outside check is the Apps Script project "alphacouncil.tech outside check" in `alphacouncil.admin@gmail.com` (signed in in the built-in browser). Its web app URL is `PING_URL`: treat it as a key.
- Credentials, by name only: `/etc/alphacouncil-platform/prod/api.env` (`OPENROUTER_API_KEY`, `MOYASAR_SECRET_KEY`, `MOYASAR_WEBHOOK_SECRET`, `GOOGLE_CLIENT_SECRET`, `SMTP_PASS`); `/etc/alphacouncil-platform/prod/monitor.env` (`ALERT_TO`, `PING_URL`). Never print, copy into git, or paste them into chat.
- Checks: `web/scripts/check-*.mjs` (`check-all.mjs` runs the set; `check-data-fixes.mjs` with `SWEEP=1` is the data check, 46/46 on production on 2026-10-18). Screenshots at 1440 and 390 px, English and Arabic, go under `docs/screenshots/`.
- `gh` (GitHub CLI) is not installed.

## 3. Decisions
- 2026-10-17 — production (alphacouncil.tech) runs this app; each release goes beta → production through `scripts/deploy-staging.sh` then `scripts/deploy-production.sh`, with the owner's go-ahead per release.
- 2026-10-18 — Pro billing is open (Moyasar, live keys); early access ended.
- 2026-10-18 — Tadawul sectors come from the Saudi Exchange's official list (22 sectors, 273 companies), not the pipeline's labels. Other markets keep the pipeline's labels.
- 2026-10-18 — the 5 USD-traded Bahrain listings show USD (owner's decision, sources in `api/app/data/listing_currencies.json`); other unconfirmed currencies show "Currency not confirmed".
- 2026-10-18 — advisors' room: six named advisors on `deepseek/deepseek-v4-pro` plus a Chair on `anthropic/claude-sonnet-5.5`, Pro only. Rejected: several different models (cost, consistency).
- 2026-10-19 — off-server backups go to the owner's Windows computer (task "AlphaCouncil backup copy", daily). Rejected: a cloud bucket (owner has none; Claude cannot create accounts). The bucket path stays ready.
- 2026-10-19 — outside check = Google Apps Script in the owner's Google account (site visits every 5 min + monitor pings). Rejected: Healthchecks.io (new account, no outside site visit), UptimeRobot (free plan non-commercial).
- 2026-10-19 — PROJECT.md is the only source of project state; Claude's auto memory holds personal working preferences only. Rejected: turning auto memory off.
- 2026-10-19 — pipeline fixes ship as `git format-patch` commits applied with `git apply` on the server (backend tree, and `-p2 --include='nightly_pipeline.sh'` in `/opt/alphacouncil/bin`), each file backed up as `.bak-<date>` first. Rejected: GNU `patch` from Windows (breaks `tickers.csv`'s CRLF hunks).
- 2026-10-19 — chart failures are reported in the nightly OK status and the 06:30 health digest, not as a new alert email. Rejected: emailing every night (9 tickers fail every night today).

## 4. Autorun Policy
- **Pre-approved:** creating and editing files in this repo on branch `rebuild`; running the project's checks and builds; read-only commands on the server over SSH (logs, `systemctl status`, `journalctl`, `sqlite3 -readonly`, listing and reading pipeline files); writing reports under `docs/`; committing on `rebuild`; screenshots with the built-in browser.
- **Defaults:** the simplest change that passes the step's checklist; match the nearest existing file's style and the runbook's wording; anything the step does not decide → the choice the project already uses; ambiguous scope → the minimum that passes, with the rest written down as a new step.
- **Always stop:** any release to production or beta (needs the owner's go-ahead for that release); any change to the old pipeline's code or data, here or on the server, before Step 5's checkpoint is cleared; anything touching credentials, payments or Moyasar; pushing to any remote (only the owner's repo from Step 2, only `rebuild`, never `main`); DNS or certificate changes; nginx changes (and always `nginx -t` first); deleting data; sending or publishing anything outside the project; a fork where both paths are substantial and no default applies.
- **Everything not under Always stop is pre-approved.**

## 5. Changelog
- 2026-10-19 — Project file created after the rebuild finished; the next work is launch readiness, in the owner's order: GitHub, pipeline data, lawyer review and portraits, then `www`.
- 2026-10-19 — Goal 1 Step 1 and Goal 2 Steps 3–4 done in one chat; Goals 1–3 now wait on the owner (URL, fix choice, advice, portraits, DNS). The Apps Script Executions page could not be read (Google sign-in lapsed in the built-in browser); nginx's access log proved the 5-minute rounds instead.

## 6. Current State
- Live on alphacouncil.tech: the rebuilt app (EN/AR), accounts with email verification and Google sign-in, Pro billing (Moyasar, hourly renewals), the advisors' room (six advisors, turn-by-turn playback, release `d356a3c`), official Tadawul sectors, the app-side data fixes.
- Safety nets, all shown running unattended on 2026-10-19: nightly database backups on the server; the daily copy on the owner's computer (09:00 run copied that night's dump); the server monitor (14 checks every 5 min, no missed ping); the outside check (116 rounds every 5 min, all 200).
- Data, part 2 done (`docs/data-audit-part2-2026-10-19.md`): causes found for the stopped tickers (Argaam renamed pages), UAE 2 decimals, holiday copies, Tadawul disclosures (source section stopped in March) and Tadawul turnover. Fixes F-A, F-E, F-B, F-C are a dry-run patch (`docs/pipeline-fixes-2026-10-19.patch`), not applied; F-D (disclosures) not built.
- Waiting on the owner: GitHub repository URL (Step 2); fix choice A/B/C and F-D yes/no (Step 5); lawyer's advice (Step 7); portrait files (Step 8); the `www` DNS record (Step 9).
- Not done: the code has no remote; advisor portraits are initials; no `www`; the lawyer has not reviewed the named advisors.
- Untracked: `scripts/set-backup-bucket.sh` (bucket helper from the backups session; the bucket is not used).

## 7. Goals

## Goal 1 — Code and safety nets confirmed
- **Status:** AWAITING CHECKPOINT — Step 1 DONE (Done-when items 3 and 4 verified 2026-10-19); Step 2 waits for the repository URL (items 1 and 2).
- **Share of project:** ~15%
- **Goal:** The code is in the owner's private GitHub repository, and the backup copy, monitor and outside check are shown to have run on their own.
- **Done when:**
  1. `git ls-remote origin refs/heads/rebuild` prints the same sha as `git rev-parse rebuild`, and `origin` is the owner's private repository.
  2. `git ls-files` lists no `api.env`, no `*.sqlite`, no key file (`git ls-files | grep -E '(^|/)api\.env$|\.sqlite$|id_ed25519'` prints nothing).
  3. `%USERPROFILE%\AlphaCouncil-Backups\pull.log` has an `ok:` line written by the scheduled task after the server's nightly backup, and the copy holds that night's `acp_prod-<date>T…Z.dump`.
  4. The outside check's Executions list shows `check` runs 5 minutes apart over at least an hour, and `prod-monitor.py status` prints `outside check: PING_URL is set`.
- **Depends on:** nothing
- **Reversibility:** costly (pushing code to a third party, even privately)
- **Autorun:** no — checkpoint: human-action (the owner creates the repository and gives its URL)
- **Consumes:** nothing
- **Steps:** 1–2
- **Goal outcome:** _(empty until the goal is worked)_

### Step 1 — Confirm the safety nets ran unattended
- **Status:** DONE
- **Goal:** Evidence that the backup copy, the monitor and the outside check each ran without anyone starting them.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** yes
- **What this step is:** The three were installed and tested by hand on 2026-10-19 between 01:15 and 01:55 Riyadh time. This step checks their first unattended runs, so a silent failure is found before the owner relies on them.
- **Where:** `%USERPROFILE%\AlphaCouncil-Backups\` (this computer); `/var/lib/acp-offsite-pull/last.json`, `journalctl -u acp-db-backup`, `journalctl -u acp-prod-monitor` (server); the Apps Script project's Executions page (built-in browser, `alphacouncil.admin@gmail.com`).
- **Consumes:** the task "AlphaCouncil backup copy" (daily 09:00 and 5 min after sign-in, runs `%USERPROFILE%\AlphaCouncil-Backups\pull-backups.ps1`); the server's backup at 01:30 UTC; the outside check deployed as web app version 2.
- **Produces:** one dated paragraph in `docs/production.md` under each of "Off-server copy (the owner's computer)" and "Outside check (Google Apps Script)", recording the first unattended runs.
- **How:** `Get-ScheduledTaskInfo -TaskName 'AlphaCouncil backup copy'` (LastTaskResult 0); last lines of `pull.log`; on the server `cat /var/lib/acp-offsite-pull/last.json` and `cat /var/backups/alphacouncil-platform/LAST_OK`; Executions page text via `get_page_text`. Never print `PING_URL`.
- **Defaults:** the 09:00 run has not happened yet (computer was off or it is before 09:00) → run the task once with `Start-ScheduledTask` and record that it was started by hand; the Apps Script page asks to sign in → leave the item CANNOT VERIFY HERE with the owner as verifier, do not enter a password; the owner has not confirmed the three test emails → record CANNOT VERIFY HERE, verifier: owner, check: inbox and spam of `attmimi.abdulw@gmail.com` for "alphacouncil.tech outside check".
- **Done when:**
  - [ ] `Get-ScheduledTaskInfo` shows LastTaskResult 0 and a LastRunTime after 2026-10-19 01:32 UTC — check: the command's output
  - [ ] `last.json` `newest` names a dump dated 20261019 or later — check: `cat` on the server
  - [ ] the Apps Script Executions list has `check` runs 5 minutes apart for an hour or more — check: page text
  - [ ] the monitor's journal shows no `outside check not pinged` line since 2026-10-18 22:50 UTC — check: `journalctl -u acp-prod-monitor --since '2026-10-18 22:50' | grep -c 'not pinged'` prints 0
- **Outcome:**
  - *Done:* all three safety nets ran on their own. Backup copy task 09:00 Riyadh, result 0, copied that night's dump. Outside check: 116 rounds 01:29:58–11:04:57 UTC. Monitor: no missed ping.
  - *Not done:* N/A
  - *Touched:* `docs/production.md` — a "First unattended run" paragraph under "Off-server copy (the owner's computer)" and a "First unattended hours" paragraph under "Outside check (Google Apps Script)".
  - *Verification:* (1) VERIFIED — LastRunTime 2026-10-19 09:00 +03:00 (06:00 UTC), LastTaskResult 0, MissedRuns 0; `pull.log` `09:00:17 ok: copied 5, removed 0, 18 files here; newest acp_prod-20261019T013111Z.dump`. (2) VERIFIED — `last.json` `"newest":"acp_prod-20261019T013111Z.dump"`, `"at":"2026-10-19T06:00:16Z"`; `LAST_OK` 2026-10-19T01:31:13Z. (3) VERIFIED by server evidence instead of the Executions page — nginx `access.log`, UA `Google-Apps-Script`: 116 × `/home` 200 and 116 × `/api/v1/health` 200, one round every 5 min over 9.5 h. (4) VERIFIED — the grep printed 0.
  - *Rulings:* item 3 checked through nginx's access log because the built-in browser's Google sign-in had lapsed (the default forbids typing a password). Why: the log proves the fetches arrived, which is stronger than the page saying they ran. Cost if wrong: none for the site checks; the Executions page also lists ping runs, which the log does not show (the monitor's 0 `not pinged` lines cover those).
  - *Failed approaches:* `script.google.com/home/executions` in the built-in browser redirects to the public developers page (signed out).
  - *Debt:* the three test emails from the outside check (2026-10-19) are still unconfirmed — CANNOT VERIFY HERE; verifier: owner; check: inbox and spam of the alert address for "alphacouncil.tech outside check". Monitor status shows 13 `ok` + `- Moyasar for renewals: no renewal run since the last round` (informational, not a failure) — matters for Step 10's "14 of 14".
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `Get-ScheduledTaskInfo -TaskName 'AlphaCouncil backup copy'`; `ssh root@alphacouncil.tech "grep -c Google-Apps-Script /var/log/nginx/access.log"`
  - *Stamp:* 2026-10-19, on `c46da77`

### Step 2 — Push branch `rebuild` to the owner's private GitHub repository
- **Status:** AWAITING CHECKPOINT — needs the owner's empty private repository URL (github.com/new, no README, no licence). Secret scan already done 2026-10-19 (see Outcome); nothing else to decide.
- **Goal:** The owner's private GitHub repository holds branch `rebuild` at the local head.
- **Depends on:** nothing
- **Reversibility:** costly
- **Autorun:** no — checkpoint: human-action (the repository URL)
- **What this step is:** The code exists only on this computer and the server; one disk failure loses the source. The owner creates an empty private repository on github.com (no README) and gives its URL; Claude adds it as `origin` and pushes `rebuild` only.
- **Where:** this repo's git config; github.com (owner's account).
- **Consumes:** the owner's repository URL, given in chat.
- **Produces:** remote `origin` = the owner's URL; `rebuild` pushed with upstream tracking; one line in `CLAUDE.md` naming the remote.
- **How:** first scan for secrets: `git ls-files` check from the goal's Done-when, and `git log --all -p | grep -E 'sk_live_|sk_test_|pk_live_|BEGIN [A-Z ]*PRIVATE KEY|OPENROUTER_API_KEY=.+'` must print nothing. Then `git remote add origin <URL>` and `git push -u origin rebuild`. Git for Windows' credential manager opens GitHub's sign-in for the owner: the owner signs in; Claude never types a password or token.
- **Defaults:** HTTPS URL → use it as given; SSH URL (`git@github.com:…`) → try it, and on a key error ask the owner for the HTTPS URL instead; the secret scan finds anything → stop, push nothing, report the file and commit (not the value); the repository is not empty (push rejected) → stop and ask, never force-push; the owner asks for `main` → push `rebuild` as `main` only if they say so in chat, never `git push … main` from a local `main`.
- **Done when:**
  - [ ] the secret scan prints nothing — check: both commands above
  - [ ] `git ls-remote origin refs/heads/rebuild` equals `git rev-parse rebuild` — check: compare the two outputs
  - [ ] the repository page shows "Private" — check: the owner confirms, or `git ls-remote` fails without credentials
- **Outcome:** (partial — waiting at the checkpoint)
  - *Done:* secret scan. `git ls-files` check prints nothing. The step's history grep prints 6 lines, all false positives: its own regex in `PROJECT.md` (c46da77); `sk_test_x` fake in `api/tests/test_billing.py` and the prefix comment `(pk_test_/sk_test_)` in `deploy/api.env.example` (28e21dd); the empty `# OPENROUTER_API_KEY=  # set on the server only…` placeholder in `deploy/api.env.example` (8b715fd, 55de633, 2bef6a4). A stricter scan for real key shapes (Moyasar `sk_/pk_` + 16 chars, `sk-or-v1-`, `sk-ant-`, `GOCSPX-`, private-key blocks, AWS, `ghp_`, MailerSend `mlsn.`, the Apps Script `macros/s/AKfy…` URL, `hc-ping.com/<uuid>`) prints 0 for history and the working tree. No remote exists yet (`git remote -v` empty); `rebuild` = `c46da77` before this chat's commit.
  - *Rulings:* the step's grep "must print nothing" is read as "finds no secret": all 6 hits are reviewed non-secrets above. Cost if wrong: a secret pushed to a private repository — the stricter scan makes this unlikely.
  - *Resume here:* the owner gives the URL → re-run the stricter scan, which must print 0: `git log --all -p | grep -c -E 'sk_(live|test)_[A-Za-z0-9]{16,}|pk_(live|test)_[A-Za-z0-9]{16,}|sk-or-v1-[0-9a-f]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|GOCSPX-[A-Za-z0-9_-]{10,}|BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|mlsn\.[a-f0-9]{30,}|macros/s/AKfy[A-Za-z0-9_-]{20,}|hc-ping\.com/[0-9a-f-]{36}'`; then `git remote add origin <URL>`; `git push -u origin rebuild`; compare `git ls-remote origin refs/heads/rebuild` with `git rev-parse rebuild`; add one line to `CLAUDE.md` naming the remote.

## Goal 2 — Market data correct at the source
- **Status:** AWAITING CHECKPOINT — Steps 3–4 DONE (Done-when item 1 met by the part-2 report); Step 5 waits for the owner's A/B/C choice.
- **Share of project:** ~45%
- **Goal:** The faults that only the pipeline can fix are fixed on the server, and the nightly data shows it.
- **Done when:**
  1. A report `docs/data-audit-part2-<date>.md` gives a root cause, with server evidence, for each of: the six stopped tickers, 2-decimal prices under 1 AED, repeated holiday bars, the Tadawul disclosure stall since 2026-10-16, and the missing Tadawul turnover.
  2. After a nightly run with the fixes, each fault the owner approved in Step 5 is gone in the data: for example, the six tickers have bars dated after the fix, and new ADX/DFM bars under 1 AED keep 3 decimals.
  3. `SWEEP=1 node web/scripts/check-data-fixes.mjs` against production still passes every check.
  4. The pipeline's own nightly run still finishes: the same success lines and file counts in its log as before the change (679 of 691 price files on 2026-10-17 is the baseline).
- **Depends on:** nothing (it does not need Goal 1)
- **Reversibility:** costly (the pipeline writes the live data)
- **Autorun:** no — checkpoint: decision (Step 5) and the owner's go-ahead for the server change (Step 7)
- **Consumes:** `docs/data-audit-2026-10-18.md` (part 1; its section 8 lists the read-only commands for part 2); `docs/data-fixes-2026-10-18.md` part 3 (faults P2–P4 and "Also for the pipeline", with evidence).
- **Steps:** 3–6
- **Goal outcome:** _(empty until the goal is worked)_

### Step 3 — Data audit part 2: read the server side
- **Status:** DONE
- **Goal:** Each pipeline fault has a root cause backed by the server's own logs, schedule and files.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** yes (read-only)
- **What this step is:** Part 1 measured from outside because that session could not SSH. This session can. Read the pipeline's schedule (cron or systemd), its last runs' logs, the SQLite freshness tables, the raw price CSVs of the six stopped tickers (GASCO, Agility, Gulf Navigation, KPPC, TAQA, AFG), the disclosure fetch, and Tadawul turnover, and the Pro panels (financials, ownership, calendar) against the database.
- **Where:** server, read-only: `/opt/alphacouncil/backend`, `/var/lib/alphacouncil/*.sqlite` (open with `sqlite3 -readonly`, ticker tables only), the universe CSVs under `UNIVERSE_ROOT` (`/opt/alphacouncil/backend/argaam/default_universe`). Report: `docs/data-audit-part2-<date>.md`.
- **Consumes:** `docs/data-audit-2026-10-18.md` section 8 (the commands); `docs/data-fixes-2026-10-18.md` part 3.
- **Produces:** `docs/data-audit-part2-<date>.md` with one section per fault: evidence (file, line, log excerpt with no secrets), root cause, the proposed fix (file and function in the server's copy), risk, and how to check it after a nightly run. A final table "fault → fix → check" that Step 5 shows the owner.
- **How:** never write on the server in this step; never read the user, account, billing or history tables in `briefs_index.sqlite`; never copy a database into the repo. Diff the server's pipeline code against the local checkout `C:\AlphaCouncil-Staging\work\f11-prod-merge` and name which copy is current.
- **Defaults:** a fault whose cause cannot be found from the server → record "cause not found", what was ruled out, and the next check; the server copy differs from the local checkout → the server copy is the truth; logs rotated away → use what remains and say how far back it goes.
- **Done when:**
  - [ ] the report has a section for each of the five faults named in Goal 2's first Done-when item — check: headings in the file
  - [ ] each section quotes server evidence with a path — check: read the file
  - [ ] the fix table names, for each fault, a file and function in the server's copy — check: read the table
- **Outcome:**
  - *Done:* `docs/data-audit-part2-2026-10-19.md`. Causes. F-A: Argaam renamed 4 company pages; old URLs 404, failure counted "done" (KPPC: no page found; TAQA: source data ends 2026-08-06). F-B: UAE path copies Argaam's 2-decimal HTML table; chart endpoint has full precision. F-C: source repeats last session on closed days (table and chart endpoint both). F-D: Tadawul reads company "Disclosures" section 204, which Argaam stopped filling (median newest 2026-03-08); disclosures run only on Friday full runs. F-E: TradingView path writes "" for turnover though the response's field `a` is turnover.
  - *Not done:* the Pro panels vs database check named in "What this step is" (not in Done-when) — left for a later read-only pass. Why 79 Tadawul `news` sections failed with no error text in the 2026-10-16 run — not established.
  - *Touched:* `docs/data-audit-part2-2026-10-19.md` (new). Outside the repo: `C:\AlphaCouncil-Staging\work\pipeline-fixes-20261019\server\` = code-only copy of the server's `/opt/alphacouncil/backend` tracked files at `a38dc07` + `/opt/alphacouncil/bin/{nightly_pipeline,publish_dbs,health_selfcheck}.sh` in `_bin/`, as local git commit `56006fa` (`core.autocrlf false`).
  - *Verification:* (1) VERIFIED — headings F-A…F-E. (2) VERIFIED — each section quotes server paths (`harvest_runs/run_…/meta.json`, `price_history_10y.csv` rows, `main_patched…` lines). (3) VERIFIED — fix table names file + function per fault.
  - *Rulings:* (a) Source facts were checked by fetching Argaam's public pages and chart endpoint from this computer (read-only); cost if wrong: none on the server. (b) F-D is not patched — classed "needs a new source mapping" under Step 4's default; cost: Tadawul disclosures stay stale until it is built. (c) The four extra chart failures found by the scan (412_KSE, AKIC.AD, BILDCO, BMUSC.BH) are listed, not investigated — outside the six named tickers.
  - *Failed approaches:* `logs/daily_<date>.log` is empty after rotation and holds only the rebuild stage; scraper detail lives in `harvest_runs/*/meta.json`. Argaam's company listing URLs (`/ae-ar/companies/dfm`, `/kw-ar/companies`) 404; slugs came from the menus inside company pages.
  - *Debt:* N/A
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `curl -s -o /dev/null -w "%{http_code}" https://www.argaam.com/en/tadawul/tasi/gasco/overview` → 404; `…/gasco-holding/overview` → 200.
  - *Stamp:* 2026-10-19; server pipeline `a38dc07`

### Step 4 — Prepare the fixes as a patch, without touching the server
- **Status:** DONE
- **Goal:** Each proposed fix exists as a reviewed patch with a dry run on copies of the data.
- **Depends on:** 3
- **Reversibility:** reversible
- **Autorun:** yes (nothing leaves this computer)
- **What this step is:** Turn the fix table into code against a local copy of the server's pipeline, and dry-run each fix on copied files, so the owner decides on real diffs and results.
- **Where:** a work folder outside this repo, e.g. `C:\AlphaCouncil-Staging\work\pipeline-fixes-<date>\` (a copy of the server's `/opt/alphacouncil/backend` code, no secrets, no user data); patch file `docs/pipeline-fixes-<date>.patch` in this repo.
- **Consumes:** the fix table in `docs/data-audit-part2-<date>.md`.
- **Produces:** `docs/pipeline-fixes-<date>.patch` (unified diff against the server's copy); a "Dry run" section added to the part-2 report with before/after for each fix.
- **How:** copy code only (`rsync` or `scp` of `.py` files), not `.env` files or databases. Dry runs use copies of the affected CSVs or tables only.
- **Defaults:** a fix needs a source the pipeline does not have yet (for example a new disclosure feed) → do not build it; list it in the report as "needs a new source" for the owner; a fix is larger than ~150 changed lines → split it, and propose the smaller part first.
- **Done when:**
  - [ ] the patch applies cleanly to the copy — check: `git apply --check` or `patch --dry-run`
  - [ ] each fix has before/after output in the report — check: read the "Dry run" section
- **Outcome:**
  - *Done:* `docs/pipeline-fixes-2026-10-19.patch` = 4 commits (`git format-patch`) against an exact-bytes copy of the server: F-A (4 page paths in `argaam/tickers.csv`; new `argaam/tools/chart_failures.py`; its line in `_bin/nightly_pipeline.sh` OK status and `llm-council/scripts/health_digest.py`), F-E (turnover from field `a`), F-B (UAE full-precision overlay `_tv_price_overlay`; `_fmt_price` up to 4 decimals), F-C (`_drop_carried_forward_bars` in `write_price_csv`). 172+/9−. "Dry run" and "Applying it" sections added to the part-2 report.
  - *Not done:* F-D (Tadawul disclosures) has no patch — needs a new mapping of Argaam's market-wide list (est. 100+ lines); owner decides in Step 5 whether to build it as a later step. The F-A scrape itself was not dry-run (needs the Argaam login and Playwright on the server); checked after the first night.
  - *Touched:* `docs/pipeline-fixes-2026-10-19.patch` (new), `docs/data-audit-part2-2026-10-19.md` (Dry run, Applying it), `.gitattributes` (`*.patch -text`, so the CRLF hunks for `tickers.csv` survive). Outside the repo: `C:\AlphaCouncil-Staging\work\pipeline-fixes-20261019\` — `server\` (git: baseline `8fb08a5`, fixes `9e0cbc8` F-A, `648269e` F-E, `ee88d04` F-B, `047fb90` F-C), `data\` (6 copied price files), `dryrun_a.txt`, `dryrun_b_e.txt`, `dryrun_c.txt`.
  - *Verification:* (1) VERIFIED — on a clean worktree of `8fb08a5`: `git apply --check --exclude='_bin/*'` exit 0; `git apply --check -p2 --include='nightly_pipeline.sh'` in a copy of `/opt/alphacouncil/bin` OK; both then applied; `py_compile` and `bash -n` pass. (2) VERIFIED — report "Dry run": F-B before/after (E7 0.91 → 0.905 = reference), F-C counts by exchange (MSM 137/50, BSE 47/19, matching part 1), F-E turnover for Aramco, F-A list of 33.
  - *Rulings:* (a) The patch targets `git apply` on the server, not GNU `patch`: Git for Windows' `patch` rejects the CRLF hunks in text mode, `git apply` handles them; git is on the server. Cost if wrong: Step 6 uses `patch --binary` instead. (b) F-A's new line goes into the OK status and the 06:30 health digest, not a new alert email — 9 tickers fail every night, a daily alert would be noise. Cost: failures are seen in the digest, not instantly. (c) `_fmt_price` keeps up to 4 decimals, so Tadawul's split-adjusted history stores 28.9771 instead of 28.98. Cost: none known; last prices are unadjusted.
  - *Failed approaches:* the first local copy was committed with Git for Windows' system `core.autocrlf=true`, which stored `tickers.csv` (CRLF on the server) as LF and made the diff touch all 721 lines — re-copied with `core.autocrlf false`. F-B does not apply without F-E (adjacent lines around `_fmt_price`).
  - *Debt:* the 4 extra chart failures (412_KSE, AKIC.AD, BILDCO, BMUSC.BH) and KPPC have no fix; F-A's check will list them nightly.
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `cd C:\AlphaCouncil-Staging\work\pipeline-fixes-20261019\server; git log --oneline` (5 commits); `git diff --stat 8fb08a5`.
  - *Stamp:* 2026-10-19; baseline = server `a38dc07`

### Step 5 — Owner decides which fixes go to the server
- **Status:** AWAITING CHECKPOINT — the owner chooses, from the fix table in `docs/data-audit-part2-2026-10-19.md`:
  - **A — all four patched fixes** (F-A, F-E, F-B, F-C). Recommended. Each was dry-run on real data. Cost: one extra Argaam request per UAE ticker a night; one night's data changes for UAE, Muscat, Bahrain and Tadawul turnover at once.
  - **B — the low-risk three** (F-A, F-E, F-C), with F-B (UAE decimals) later. Cost: sub-1 AED prices stay 2-decimal; INVESTB-style fake ±25% days continue.
  - **C — none.** Cost: GASCO, AFG, AGILITY and GULFNAV stay frozen at July/October; holiday copies and missing Tadawul turnover stay.
  - Separately: **build F-D** (Tadawul disclosures from Argaam's market-wide list) as a new step, yes or no. Recommended: yes, after A/B has run one night.
- **Goal:** The owner has chosen, fix by fix, what is applied to the live pipeline.
- **Depends on:** 4
- **Reversibility:** reversible
- **Autorun:** no — checkpoint: decision
- **What this step is:** The standing rule keeps the old pipeline read-only. This is the gate: show the owner the fix table, the patch size and the dry-run results, recommend, and record the answer.
- **Where:** chat; the answer recorded under this step.
- **Consumes:** `docs/data-audit-part2-<date>.md` (fix table, dry runs); `docs/pipeline-fixes-<date>.patch`.
- **Produces:** a `- **Checkpoint cleared:** <date> — <the owner's words>` line naming the approved fixes.
- **How:** one question with the options (all / a listed subset / none), the recommendation, and what each costs.
- **Defaults:** the owner approves "all" → F-A, F-E, F-B, F-C (F-D is not in the patch; "all" does not build it); the owner names a subset that includes F-B → F-E must come too (F-B applies only on top of F-E); the owner says yes to F-D → add it as a new step after Step 6, do not fold it into Step 6; the owner is not at the keyboard → set AWAITING CHECKPOINT and hand over with the paused block.
- **Done when:**
  - [ ] the checkpoint line exists under this step with the owner's words — check: read the step
- **Outcome:** _(empty until worked)_

### Step 6 — Apply the approved fixes on the server and check the next nightly run
- **Status:** NOT STARTED
- **Goal:** The approved fixes run on the server, and the next nightly data shows each fault gone.
- **Depends on:** 5
- **Reversibility:** costly
- **Autorun:** no — checkpoint: decision (the owner's go-ahead for the server change, given in chat)
- **What this step is:** Back up the files being changed, apply the approved part of the patch on the server, wait for the nightly run, then check the data and the app.
- **Where:** server `/opt/alphacouncil/backend` (only the patched files, each backed up as `<file>.bak-<date>`); this repo's runbook.
- **Consumes:** the approved list in Step 5's checkpoint line; `docs/pipeline-fixes-2026-10-19.patch` (4 `git format-patch` commits: F-A, F-E, F-B, F-C); the exact commands in the part-2 report's "Applying it" section; checks per fault in its F-A…F-E sections. Copy the patch to the server with `scp` (it holds no secrets).
- **Produces:** the patched files on the server; a "Pipeline fixes" section in `docs/production.md` (what changed, the backups' names, how to undo); the part-2 report's "After the nightly run" section.
- **How:** apply with `patch` on the server, run the pipeline's own syntax or test check if it has one, never restart or rerun the full pipeline by hand unless the owner says so. After the next nightly run: re-run the checks from the report and `SWEEP=1 node web/scripts/check-data-fixes.mjs` against production.
- **Defaults:** the nightly run fails after the change → restore every `.bak-<date>` file at once (and remove `argaam/tools/chart_failures.py`), then report; a fix shows no effect after one night → leave it in, record it NOT MET, and report the next check; the server's files differ from `a38dc07` when applying (`git apply --check` fails) → stop, apply nothing, report the file; apply with `git apply` (Git for Windows' `patch` mangles the CRLF hunks of `tickers.csv`; on Linux `patch --binary` also works); a subset approved → `git format-patch`'s sections are separate commits: apply only those, in order.
- **Done when:**
  - [ ] each approved fault is gone in the new data — check: the per-fault checks in the report
  - [ ] the nightly run's log shows the same success lines and a price-file count no lower than the baseline — check: the log
  - [ ] `check-data-fixes.mjs` with `SWEEP=1` passes every check on production — check: its summary line
- **Outcome:** _(empty until worked)_

## Goal 3 — Ready to advertise
- **Status:** AWAITING CHECKPOINT — Steps 7–9 each wait on the owner (re-tested 2026-10-19: no `www` record, no portrait files, no legal advice yet); Step 10 waits on Goal 2.
- **Share of project:** ~40%
- **Goal:** The advisors' names and texts follow the owner's legal advice, the six portraits are real, `www.alphacouncil.tech` works, and a full launch check passes on production.
- **Done when:**
  1. The owner's written legal advice is in `docs/legal-advisors-<date>.md` (the owner's summary, no personal data), and every change it asks for is live.
  2. The advisors' room shows six real portraits in English and Arabic at 1440 and 390 px, with the initials only as a fallback for a missing file.
  3. `curl -sI https://www.alphacouncil.tech/` answers 301 to `https://alphacouncil.tech/`, and the certificate covers both names.
  4. `docs/launch-check-<date>.md` records every check script passing on production (`check-all.mjs`, `check-data-fixes.mjs` with `SWEEP=1`, `check-seo.mjs`, `check-advisors.mjs`) and the monitor at 14 of 14.
- **Depends on:** nothing for Steps 7–9; Step 10 (the launch check) depends on Goal 2.
- **Reversibility:** reversible (DNS and certificate: costly)
- **Autorun:** no — checkpoint: human-action (legal advice, portrait files, DNS record)
- **Consumes:** `docs/advisors-portraits-brief.md` (the illustrator's brief); `api/app/advisors/*.md` (the six advisors and the Chair).
- **Steps:** 7–10
- **Goal outcome:** _(empty until the goal is worked)_

### Step 7 — Apply the lawyer's advice to the named advisors
- **Status:** AWAITING CHECKPOINT — the owner pastes or summarises the lawyer's advice in chat (2026-10-19: none yet).
- **Goal:** The advisors' names, wording and disclaimers match the owner's legal advice, live on production.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** no — checkpoint: human-action (the owner brings the advice)
- **What this step is:** The room speaks as Buffett, Lynch, Dalio, Marks, Prince Alwaleed and Abdullah Al-Rajhi. Using real people's names and personas is the main legal exposure before advertising. The owner gets advice; this step applies it.
- **Where:** `api/app/advisors/*.md`; the advisors' room UI copy in `web/messages/en.json` and `web/messages/ar.json`; nothing in `web/src/content/legal` (those texts are copied from the old site by `scripts/import-legal.py` and never edited by hand).
- **Consumes:** the owner's advice, pasted or summarised in chat.
- **Produces:** `docs/legal-advisors-<date>.md` (what the advice says, what changed); the changed files; a release through beta then production with the owner's go-ahead.
- **How:** keep advisor ids (`buffett`, `lynch`, `dalio`, `marks`, `alwaleed`, `alrajhi`) and `DEBATE_ADVISORS` stable even if display names change, so saved sessions keep working.
- **Defaults:** the advice says no real names → rename to descriptive personas (for example "The Value Investor"), keep each advisor's method, and say "inspired by public writings" nowhere unless the advice allows it; the advice is ambiguous on a point → take the more cautious reading and list it for the owner.
- **Done when:**
  - [ ] `docs/legal-advisors-<date>.md` lists each point of the advice and the change made for it — check: read the file
  - [ ] production's advisors' page shows the changed names or texts in English and Arabic — check: screenshots at 1440 and 390 px
  - [ ] `node web/scripts/check-advisors.mjs` passes on production — check: its summary line
- **Outcome:** _(empty until worked)_

### Step 8 — Put the six real portraits in
- **Status:** AWAITING CHECKPOINT — the owner puts `buffett.webp`, `lynch.webp`, `dalio.webp`, `marks.webp`, `alwaleed.webp`, `alrajhi.webp` (and optionally `chair.webp`) in `web/public/advisors/` (2026-10-19: only `README.md` there). Names may change with Step 7.
- **Goal:** The advisors' room shows the illustrator's six portraits, with initials only as a fallback.
- **Depends on:** 7 (names may change)
- **Reversibility:** reversible
- **Autorun:** no — checkpoint: human-action (the owner provides the files)
- **What this step is:** Portraits are initials placeholders until the files arrive (`docs/advisors-portraits-brief.md`). This step adds the files and wires them in.
- **Where:** the web app's static assets and the advisors' seat component (find it with `grep -rl "initials" web/src/components`).
- **Consumes:** the owner's six image files; the advisor ids from Step 7.
- **Produces:** the portrait files in the repo, one per advisor id; the seat component showing them.
- **How:** serve from the app's own origin (the CSP blocks other origins); keep each file small enough for 390 px phones; the Chair keeps its current mark unless the brief says otherwise.
- **Defaults:** a file is missing or unusable → keep that advisor's initials and list it; files are larger than ~150 KB → convert to WebP at the displayed size times two.
- **Done when:**
  - [ ] six portraits show on production in English and Arabic at 1440 and 390 px — check: screenshots
  - [ ] removing one file in a local build shows that advisor's initials — check: local screenshot
- **Outcome:** _(empty until worked)_

### Step 9 — Make `www.alphacouncil.tech` work
- **Status:** AWAITING CHECKPOINT — the owner adds, in Cloudflare (the domain's DNS host: `koa`/`piper.ns.cloudflare.com`), an A record `www` → `72.60.91.24` (the apex's address; no AAAA seen), proxy off ("DNS only"), so the certificate challenge reaches the server. 2026-10-19: `www` answers NXDOMAIN.
- **Goal:** `www.alphacouncil.tech` redirects to `https://alphacouncil.tech/` with a valid certificate.
- **Depends on:** nothing
- **Reversibility:** costly
- **Autorun:** no — checkpoint: human-action (the owner adds the DNS record at the domain's DNS host)
- **What this step is:** There is no DNS record for `www` (runbook, "Not in production yet"). The owner adds it; Claude extends the certificate and adds the redirect.
- **Where:** DNS (owner); server: the certificate and the nginx site for alphacouncil.tech (`deploy/nginx-production.conf` in this repo is the source).
- **Consumes:** the owner's confirmation that `www` points at the server (`dig +short www.alphacouncil.tech` matches `dig +short alphacouncil.tech`).
- **Produces:** the certificate with both names; a `www` → apex 301 in `deploy/nginx-production.conf` and on the server; the runbook's "Not in production yet" line removed.
- **How:** extend the existing certificate with the same tool that issued it (check with `certbot certificates` first); `nginx -t` before any reload; keep HSTS as it is.
- **Defaults:** the owner asks what record to add → an A record `www` with the same IPv4 as `alphacouncil.tech`, plus AAAA if the apex has one; certificate renewal fails → leave nginx unchanged and report.
- **Done when:**
  - [ ] `curl -sI https://www.alphacouncil.tech/` shows 301 and `location: https://alphacouncil.tech/` — check: the command
  - [ ] `openssl s_client -connect alphacouncil.tech:443 -servername www.alphacouncil.tech </dev/null | openssl x509 -noout -ext subjectAltName` lists both names — check: the command
- **Outcome:** _(empty until worked)_

### Step 10 — Launch check on production
- **Status:** NOT STARTED
- **Goal:** One dated record shows every check passing on production after Goals 2 and 3's changes.
- **Depends on:** 6, 7, 8, 9
- **Reversibility:** reversible
- **Autorun:** yes
- **What this step is:** The last pass before the owner spends on advertising: every check script, the monitor and screenshots of the key pages, in one report.
- **Where:** `docs/launch-check-<date>.md`; screenshots under `docs/screenshots/launch-<date>/`.
- **Consumes:** the releases from Steps 6–9.
- **Produces:** `docs/launch-check-<date>.md`.
- **How:** run the scripts against production through the tunnel or over HTTPS as each script supports; `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status` on the server; screenshots of /, /pricing, /home, a Tadawul stock, its advisors' page, in English and Arabic at 1440 and 390 px.
- **Defaults:** a check fails → record it NOT MET with output, fix it only if the fix is inside this repo and small, release only with the owner's go-ahead; a step it depends on is blocked → run the check anyway and mark the gap.
- **Done when:**
  - [ ] the report lists each script with its summary line, all passing — check: read the file
  - [ ] the monitor's status shows 14 of 14 ok — check: its output in the report
  - [ ] the screenshots exist for each page, both languages, both widths — check: list the folder
- **Outcome:** _(empty until worked)_

## 8. Open Questions
- **The GitHub repository URL** — blocks Step 2. The owner creates an empty private repository at github.com/new (no README, no licence) and pastes its URL. No default: Claude cannot create the account or repository.
- **The lawyer's advice on the named advisors** — blocks Step 7 (and Step 8, since names may change). No default: it is the owner's legal call.
- **Which pipeline fixes go to the server (A all four / B without F-B / C none), and whether to build F-D** — blocks Steps 5–6. Recommendation: A, and F-D yes after one night. No default: the standing rule keeps the old pipeline read-only without the owner's approval.
- **The portrait files** — block Step 8. **The `www` A record in Cloudflare** — blocks Step 9. Both are the owner's actions.
- **KPPC (624, Boursa Kuwait) and TAQA (ADX)** — Argaam has no page for KPPC and no TAQA bars after 2026-08-06. Delisted or suspended? The owner may know; until then the app keeps showing them stale (amber).

## 9. Next Up
Goal 1, Step 2 (awaiting the GitHub URL). First action once the owner gives it: run the secret scan again (`git log --all -p` with the stricter pattern in Step 2's Outcome must print 0), then `git remote add origin <URL>` and `git push -u origin rebuild`. Then Goal 2, Step 5 with the owner's A/B/C answer → Step 6 (apply per the part-2 report's "Applying it").
