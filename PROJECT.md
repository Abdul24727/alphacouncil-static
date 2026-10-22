# PROJECT — alphacouncil-platform launch
**File:** C:\projects\alphacouncil-platform\PROJECT.md   **Updated:** 2026-10-22   **At version:** `859edaf` on branch `rebuild` (beta `859edafff3`, production `56476948f5`; this file's latest state committed on top)

## 1. Objective
alphacouncil.tech is fully built — everything already on the site works and is right, the market data is right at its source, the named advisors, portraits and `www` address are settled, checkout is proven, and the code is safe off this computer — and only then does Pro billing open and advertising start.

- The rebuild itself is finished and live: every phase of the original rebuild plan shipped, and production runs this app since 2026-10-17.
- What is left is what stands between "live" and "fully built": the independent beta audit's open defects (`docs/qa-beta-2026-10/report.md`), the pipeline's data faults, the legal and portrait work, `www`, a checkout proven in test mode, and a full launch check.
- **No one is charged until it is fully built** (owner, 2026-10-21: "I'm not gonna charge people when my product is half-baked. We'll lose customers forever."). Billing closes now (Step 11); opening it is the last step (Step 18).
- For the owner (Abdul), who runs AlphaCouncil alone and has no paying members yet.
- Correct data is the product: a research terminal that shows a stopped price or a wrong unit loses trust faster than one that is missing a feature.

**Out of scope:** new features or panels ("fully built" means what is already on the site, finished and right); the advertising itself (campaigns, budgets, copy); retiring the old backend that still serves `api.alphacouncil.tech`; a cloud bucket for backups (the owner has none; the computer copy is used).

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
- 2026-10-18 — Pro billing is open (Moyasar, live keys); early access ended. — **superseded 2026-10-21**: the owner will not charge anyone until the product is fully built (see below).
- 2026-10-18 — Tadawul sectors come from the Saudi Exchange's official list (22 sectors, 273 companies), not the pipeline's labels. Other markets keep the pipeline's labels.
- 2026-10-18 — the 5 USD-traded Bahrain listings show USD (owner's decision, sources in `api/app/data/listing_currencies.json`); other unconfirmed currencies show "Currency not confirmed".
- 2026-10-18 — advisors' room: six named advisors on `deepseek/deepseek-v4-pro` plus a Chair on `anthropic/claude-sonnet-5.5`, Pro only. Rejected: several different models (cost, consistency).
- 2026-10-19 — off-server backups go to the owner's Windows computer (task "AlphaCouncil backup copy", daily). Rejected: a cloud bucket (owner has none; Claude cannot create accounts). The bucket path stays ready.
- 2026-10-19 — outside check = Google Apps Script in the owner's Google account (site visits every 5 min + monitor pings). Rejected: Healthchecks.io (new account, no outside site visit), UptimeRobot (free plan non-commercial).
- 2026-10-19 — PROJECT.md is the only source of project state; Claude's auto memory holds personal working preferences only. Rejected: turning auto memory off.
- 2026-10-19 — pipeline fixes ship as `git format-patch` commits applied with `git apply` on the server (backend tree, and `-p2 --include='nightly_pipeline.sh'` in `/opt/alphacouncil/bin`), each file backed up as `.bak-<date>` first. Rejected: GNU `patch` from Windows (breaks `tickers.csv`'s CRLF hunks).
- 2026-10-19 — chart failures are reported in the nightly OK status and the 06:30 health digest, not as a new alert email. Rejected: emailing every night (9 tickers fail every night today).
- 2026-10-21 — No charging until fully built: production's checkout closes (Step 11) and reopens only as the last step, after the launch check passes (Step 18). Why: a customer who pays for a half-finished product is lost for good. Rejected: keeping billing open while the fixes land.
- 2026-10-21 — "Fully built" includes the independent beta audit (`docs/qa-beta-2026-10/report.md`, runs 1–3): every FAIL row is fixed, or the owner accepts it in writing as by design (follows from the rule above). Rejected: launching with the audit's minor rows open.
- 2026-10-22 — "Not signed in" answers 401; a request carrying an HTTP Basic login (beta's staging gate) answers 403, because any 401 makes the browser drop the gate's login (audit 9c). Rejected: 401 everywhere (re-breaks 9c on beta); an nginx change on beta (Always stop, and not needed).
- 2026-10-22 — The owner accepts the audit's BY DESIGN items 1–4: phones get a tab bar, not a sidebar; signed-out `/portfolio`, `/dashboards`, `/settings` answer 200 with a prompt; "Google" and "EN"/"English" may appear on Arabic pages; behind beta's gate "not signed in" stays 403.
- 2026-10-22 — Copilot answers are short and quote the data's own figures (at most five, under about 120 words, no ratios of its own); a refused instruction gets one sentence. Owner's option (b), after the model service turned wordier. Rejected for now: changing the model or pinning a host (owner's call).

## 4. Autorun Policy
- **Pre-approved:** creating and editing files in this repo on branch `rebuild`; running the project's checks and builds; read-only commands on the server over SSH (logs, `systemctl status`, `journalctl`, `sqlite3 -readonly`, listing and reading pipeline files); writing reports under `docs/`; committing on `rebuild`; screenshots with the built-in browser.
- **Defaults:** the simplest change that passes the step's checklist; match the nearest existing file's style and the runbook's wording; anything the step does not decide → the choice the project already uses; ambiguous scope → the minimum that passes, with the rest written down as a new step.
- **Always stop:** any release to production or beta (needs the owner's go-ahead for that release); any change to the old pipeline's code or data, here or on the server, before Step 5's checkpoint is cleared; anything touching credentials, payments or Moyasar; pushing to any remote (only the owner's repo from Step 2, only `rebuild`, never `main`); DNS or certificate changes; nginx changes (and always `nginx -t` first); deleting data; sending or publishing anything outside the project; a fork where both paths are substantial and no default applies.
- **Everything not under Always stop is pre-approved.**

## 5. Changelog
- 2026-10-19 — Project file created after the rebuild finished; the next work is launch readiness, in the owner's order: GitHub, pipeline data, lawyer review and portraits, then `www`.
- 2026-10-19 — Goal 1 Step 1 and Goal 2 Steps 3–4 done in one chat; Goals 1–3 now wait on the owner (URL, fix choice, advice, portraits, DNS). The Apps Script Executions page could not be read (Google sign-in lapsed in the built-in browser); nginx's access log proved the 5-minute rounds instead.
- 2026-10-21 — Owner's rule: no charging until fully built. Plan grown to four goals: Goal 1 adds closing billing (Step 11); new Goal 3 fixes the independent beta audit's defects and proves checkout in Moyasar test mode (Steps 12–17; audit copied to `docs/qa-beta-2026-10/`); the old Goal 3 is now Goal 4 and ends with opening billing (Step 18). The GitHub URL the owner gave (`alphacouncil-static`) is public and holds the old site, so it is not used (Step 2).
- 2026-10-22 — Goal 3 Steps 12–15 done in one chat. The beta audit's run 2 had predated four releases: 8 of 15 items were already fixed. 403 → 401 kept 403 for requests carrying beta's gate login, since the audit's own 9c fix needed it. Copilot obeyed a prompt injection once (C4) on the same release that passed it on 10-21; a prompt rule is on `rebuild`, proven only after Step 17's beta release.
- 2026-10-22 — Owner's go-ahead: production checkout closed (Step 11; 0 renewing payers, 0 payments ever) and checkout proven on beta in Moyasar test mode, 13 of 13 (Step 16). Beta's password gate stands between Moyasar and beta (its return and its webhooks); the test scripts route around it and say so.
- 2026-10-22 — Beta released (`ae72d6a05b`) and re-audited: all audit items pass except Copilot speed; C4 3/3; check-all 9/9. Measured the cause of the slowdown on production (old prompt): the model service, not the release.
- 2026-10-22 — Production released twice (`53c3c54aa0`, `56476948f5`), check-all 9/9 each time; BY DESIGN 1–4 accepted; option (b) cut Copilot's full answers to 13.4 s but not first words (8.6 s). Goal 1 item 5 met (Step 11).
- 2026-10-22 — Option (c) tried on beta: OpenRouter hosts timed with the Copilot's real input; Phala and SiliconFlow pinned in the app in turn. SiliconFlow halves first words (3.8 s) but writes slowly (median 23.8 s, one 150 s); no host meets both targets, so production was not released.

## 6. Current State
- Live on alphacouncil.tech since 2026-10-22: release `56476948f5` (the QA audit fixes and the short-answer Copilot prompt; beta runs the same). The rebuilt app (EN/AR), accounts with email verification and Google sign-in, Pro checkout **closed since 2026-10-22** (Step 11: early access, everyone has Pro; it reopens at Step 18; no one had paid), the advisors' room (six advisors, turn-by-turn playback, release `d356a3c`), official Tadawul sectors, the app-side data fixes.
- Safety nets, all shown running unattended on 2026-10-19: nightly database backups on the server; the daily copy on the owner's computer (09:00 run copied that night's dump); the server monitor (14 checks every 5 min, no missed ping); the outside check (116 rounds every 5 min, all 200).
- Data, part 2 done (`docs/data-audit-part2-2026-10-19.md`): causes found for the stopped tickers (Argaam renamed pages), UAE 2 decimals, holiday copies, Tadawul disclosures (source section stopped in March) and Tadawul turnover. Fixes F-A, F-E, F-B, F-C are a dry-run patch (`docs/pipeline-fixes-2026-10-19.patch`), not applied; F-D (disclosures) not built.
- Independent beta audit (`docs/qa-beta-2026-10/report.md`), re-checked 2026-10-22 (`defects-2026-10-22.md`): 8 of its 15 open items were already fixed by the 10-17/18 releases; Arabic pages (8a/8b, `b548bbe`), 401/404 (9b/9f, `b551630`) and a Copilot prompt rule (C4, failed once today) are fixed on `rebuild` but **not released**; Copilot speed meets the target on the median. Checkout proven in Moyasar test mode on beta, 13 of 13 (Step 16). Re-audit done and released (`reaudit-2026-10-22.md`): every item PASS or BY DESIGN (accepted by the owner) except 7f's first words; `check-all` 9/9 on production.
- Copilot's model service (`deepseek/deepseek-v3.2` on OpenRouter) turned 2–3× wordier and slower on 2026-10-22 ~00:00 UTC; the short-answer prompt brought full answers back to a 13.4 s median, but first words take 8.6 s (target 5 s). Pinning a host (option (c)) did not fix both. Beta runs `859edafff3` (host setting available, unused); production `56476948f5`.
- No ticker has ownership or analyst data today (0 of 716 on beta's API); the audit saw 2222's ownership on 2026-10-16.
- Waiting on the owner (re-tested 2026-10-22: `www` NXDOMAIN, no portrait files): Copilot's first-words choice (Step 17); a new empty private GitHub repository's URL (Step 2); fix choice A/B/C and F-D yes/no (Step 5); lawyer's advice (Step 7); portrait files (Step 8); the `www` DNS record (Step 9).
- Not done: the code has no remote; advisor portraits are initials; no `www`; the lawyer has not reviewed the named advisors.
- Untracked: `scripts/set-backup-bucket.sh` (bucket helper from the backups session; the bucket is not used).

## 7. Goals

## Goal 1 — Safe footing: code backed up, safety nets proven, nobody charged
- **Status:** AWAITING CHECKPOINT — Steps 1 and 11 DONE (Done-when items 3 and 4 verified 2026-10-19, item 5 on 2026-10-22); Step 2 waits for an empty private repository's URL (items 1 and 2).
- **Share of project:** ~15%
- **Goal:** The code is in the owner's private GitHub repository, the backup copy, monitor and outside check are shown to have run on their own, and production takes no payments until the launch.
- **Done when:**
  1. `git ls-remote origin refs/heads/rebuild` prints the same sha as `git rev-parse rebuild`, and `origin` is the owner's private repository.
  2. `git ls-files` lists no `api.env`, no `*.sqlite`, no key file (`git ls-files | grep -E '(^|/)api\.env$|\.sqlite$|id_ed25519'` prints nothing).
  3. `%USERPROFILE%\AlphaCouncil-Backups\pull.log` has an `ok:` line written by the scheduled task after the server's nightly backup, and the copy holds that night's `acp_prod-<date>T…Z.dump`.
  4. The outside check's Executions list shows `check` runs 5 minutes apart over at least an hour, and `prod-monitor.py status` prints `outside check: PING_URL is set`.
  5. `curl -s https://alphacouncil.tech/api/v1/plans` prints `"checkout_open":false`, and `/pricing` shows the early-access note in English and Arabic.
- **Depends on:** nothing
- **Reversibility:** costly (pushing code to a third party, even privately)
- **Autorun:** no — checkpoint: human-action (the owner creates the repository and gives its URL) and decision (closing billing, Step 11)
- **Consumes:** nothing
- **Steps:** 1–2, 11
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
- **Status:** AWAITING CHECKPOINT — needs the owner's **empty, private** repository URL (github.com/new, Private, no README, no licence). Secret scan already done 2026-10-19 (see Outcome). 2026-10-21: the owner gave `https://github.com/Abdul24727/alphacouncil-static`, which cannot be used — see Outcome *Rulings* (b).
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
  - *Rulings:* the step's grep "must print nothing" is read as "finds no secret": all 6 hits are reviewed non-secrets above. Cost if wrong: a secret pushed to a private repository — the stricter scan makes this unlikely. (b) 2026-10-21: the URL the owner gave, `https://github.com/Abdul24727/alphacouncil-static`, is not used. It is **public** (`git -c credential.helper= ls-remote` lists it with no sign-in) and not empty: it holds the old static site (`master` 2026-07-03; also `staging-option-a`, `vps-production-sync-20260714`, `feat/settings-market-multiselect`, and `claude/affectionate-visvesvaraya-15c98d`, the newest at 2026-08-29). Pushing `rebuild` there would publish this code. The old backend repository `Argaam-council-before-testing-cluade-project-` is private but holds the old backend. So: ask for a new empty private repository (suggested name `alphacouncil-platform`). Cost if wrong: one more round-trip with the owner.
  - *Resume here:* the owner gives the URL → re-run the stricter scan, which must print 0: `git log --all -p | grep -c -E 'sk_(live|test)_[A-Za-z0-9]{16,}|pk_(live|test)_[A-Za-z0-9]{16,}|sk-or-v1-[0-9a-f]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|GOCSPX-[A-Za-z0-9_-]{10,}|BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|mlsn\.[a-f0-9]{30,}|macros/s/AKfy[A-Za-z0-9_-]{20,}|hc-ping\.com/[0-9a-f-]{36}'`; then `git remote add origin <URL>`; `git push -u origin rebuild`; compare `git ls-remote origin refs/heads/rebuild` with `git rev-parse rebuild`; add one line to `CLAUDE.md` naming the remote.

### Step 11 — Close Pro checkout on production until the launch
- **Status:** DONE
- **Checkpoint cleared:** 2026-10-22 — owner in chat: "Go-ahead: close Pro checkout on production now (Step 11)"
- **Goal:** Production's checkout is closed and every account has Pro free (early access) until Step 18 opens billing.
- **Depends on:** nothing
- **Reversibility:** reversible (put the line back)
- **Autorun:** no — checkpoint: decision
- **What this step is:** Billing opened on 2026-10-18 (`BILLING_OPEN=true`). On 2026-10-21 the owner ruled that no one is charged until the product is fully built. There are no paying members, so closing it costs nobody anything, and visitors see the whole product while it is finished. The runbook already holds the procedure.
- **Where:** server `/etc/alphacouncil-platform/prod/api.env`; service `acp-prod-api`; `docs/production.md` section "Pro billing (Moyasar)".
- **Consumes:** the runbook's lines "To close billing again (everyone back to Pro, checkout closed): delete the `BILLING_OPEN` line, then `systemctl restart acp-prod-api`."
- **Produces:** `api.env.bak-<YYYYMMDDHHMMSS>` beside production's `api.env` (Step 18 names it); the `BILLING_OPEN` line removed; a dated paragraph "Billing closed again (<date>)" under "Billing is open (since 2026-10-18)" in `docs/production.md`, with the checks below.
- **How:** first count renewing payers without reading any row: subscriptions with status `active` or `past_due` and a saved card (`token_id` set), count only. Then `cp -p api.env api.env.bak-<timestamp>`, `sed -i '/^BILLING_OPEN=/d' api.env`, `systemctl restart acp-prod-api`, then the checks. Never print `api.env`. Leave `acp-prod-billing.timer` enabled: with no renewing payers it charges nobody, and the monitor expects it.
- **Defaults:** the count is above 0 → stop, change nothing, tell the owner the count (whether to refund or keep that member is the owner's call); a count-only query cannot be run → the owner checks Moyasar's live dashboard for payments since 2026-10-18, and that answer is recorded; the restart fails → restore the backup file, restart, report.
- **Done when:**
  - [x] `curl -s https://alphacouncil.tech/api/v1/plans` prints `"checkout_open":false` — check: the command
  - [x] `/pricing` shows "Checkout is not open yet. During early access every account has the Pro features free." (English) and its Arabic text (Arabic) — check: screenshots at 1440 and 390 px
  - [x] a signed-out visitor sees the Ownership and Financials panels of `/t/2222` unlocked — check: screenshot
  - [x] the monitor's ok count is the same as before the change — check: `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status` before and after
- **Outcome:**
  - *Done:* production's checkout is closed; every account has Pro free again. Counts first: 0 subscriptions renewing on a saved card, 1 subscription in all, 0 payments in `billing_payments`.
  - *Not done:* N/A
  - *Touched:* server `/etc/alphacouncil-platform/prod/api.env` (`BILLING_OPEN` line removed; backup `api.env.bak-20261021231429`, UTC — Step 18 restores from it or re-adds the line), `acp-prod-api` restarted; `docs/production.md` paragraph "Billing closed again (2026-10-22)"; screenshots `docs/screenshots/billing-closed-2026-10-22/`.
  - *Verification:* (1) VERIFIED — `"checkout_open":false` over HTTPS. (2) VERIFIED — `/pricing` shows no buy button and the note "Early access: every account gets the Pro features free until paid plans open. We will tell you before anything changes, and subscribing will be your choice." and in Arabic "وصول مبكر: كل حساب يحصل على مزايا برو مجانًا حتى تُفتح الخطط المدفوعة…", at 1440 and 390 px (`pricing-*.png`, `*-full.png`). The item's quoted sentence is the signed-in checkout message; signed out, the page shows this note instead, which says the same. (3) VERIFIED — signed out, `/t/2222/ownership` and `/financials` (EN, AR) show their panels with no Pro lock (`t2222-*.png`). (4) VERIFIED — 13 `ok` before and after (plus the informational "Moyasar for renewals: no renewal run since the last round").
  - *Rulings:* (a) The one existing subscription is not renewing on a card (the count was 0), so it was left as it is. Cost if wrong: none charged — the renewals job only charges a saved card.
  - *Failed approaches:* N/A
  - *Debt:* N/A
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `curl -s https://alphacouncil.tech/api/v1/plans | grep -o '"checkout_open":[a-z]*'`
  - *Stamp:* 2026-10-22, on `7b2437a` (server change; no code change)


## Goal 2 — Market data correct at the source
- **Status:** AWAITING CHECKPOINT — Steps 3–4 DONE (Done-when item 1 met by the part-2 report); Step 5 waits for the owner's A/B/C choice.
- **Share of project:** ~25%
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

## Goal 3 — Every known defect fixed, checkout proven
- **Status:** AWAITING CHECKPOINT — Steps 12–16 DONE 2026-10-22 (checkout proven on beta); Step 17 live: beta and production on `56476948f5`, `check-all` 9/9 on production, BY DESIGN 1–4 accepted; one decision left — Copilot speed (7f); option (c) tried, no host meets both targets.
- **Share of project:** ~30%
- **Goal:** Every defect the independent beta audit found is fixed or accepted by the owner as by design, the fixes are live on production, and checkout has been proven end to end in Moyasar test mode on beta.
- **Done when:**
  1. `docs/qa-beta-2026-10/reaudit-<date>.md` lists every item of Step 12's list (the audit's FAIL rows 1b, 1e, 2b, 5f, 7d, 7e, 7f, 8a, 8b, 8c, 9b, 10b, 10c, the 9f nit, and Copilot at 390 px) as PASS with evidence, or BY DESIGN with the owner's acceptance quoted.
  2. `node web/scripts/check-arabic.mjs` passes on production: no English text on Arabic pages outside its allow-list.
  3. `docs/checkout-test-<date>.md` shows every case passing in Moyasar test mode on beta, and beta's `api.env` has no `BILLING_OPEN` line afterwards.
  4. Production runs the same release that was re-audited on beta (release ids recorded in `docs/production.md` match), and `node web/scripts/check-all.mjs` passes on it.
- **Depends on:** nothing (Step 17's releases need the owner's go-ahead)
- **Reversibility:** reversible
- **Autorun:** yes for Steps 12–15 (read-only checks; code on `rebuild` checked on the local build); no for Step 16 (Moyasar and beta's billing setting) and Step 17 (releases)
- **Consumes:** `docs/qa-beta-2026-10/report.md` (FAIL rows with exact repro steps; "Not tested" list); `docs/qa-beta-2026-10/moyasar-checkout-interview-prompt.md`; `docs/qa-beta-2026-10/copilot-adversarial-plan.md`; `BRAND.md`.
- **Steps:** 12–17
- **Goal outcome:** _(empty until the goal is worked)_

### Step 12 — Re-check the audit's open rows on today's beta
- **Status:** DONE
- **Goal:** A dated list says, for each open item of the beta audit, whether it still fails today, with evidence, and which step fixes it.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** yes (read-only)
- **What this step is:** The audit ran 2026-10-15 → 21 while releases were still landing, so some rows may already be fixed. For example, the pricing placeholder "[Pro features: to be decided before the paid launch]" (row 10c) no longer appears in `web/messages`. Re-check before fixing, so no work goes into what is already right.
- **Where:** beta through the tunnel `localhost:3201` (built-in browser and the check scripts); `docs/qa-beta-2026-10/`; screenshots under `docs/screenshots/qa-recheck-<date>/`.
- **Consumes:** `docs/qa-beta-2026-10/report.md`: the FAIL rows 1b, 1e, 2b, 5f, 7d, 7e, 7f, 8a, 8b, 8c, 9b, 10b, 10c with their "Exact repro steps"; the 9f nit (DELETE answers 200 for an id the caller does not own); "Not tested" item 5 (Copilot at 390 px).
- **Produces:** `docs/qa-beta-2026-10/defects-<date>.md` — one row per item (15 rows) with columns `row | finding | today (STILL FAILS / FIXED / BY DESIGN?) | evidence | fixed by (Step 13, 14, 15 or 16)`, then a section "Proposed BY DESIGN" listing what the owner is asked to accept in Step 17, each with one line of why.
- **How:** follow each row's repro steps exactly, at the widths and languages it names. Row 2b: compare computed colours and fonts on `/home`, `/t/2222` and `/pricing` with the tokens in `BRAND.md` (the audit could not; the file is not served). Pages that need an account: use the accounts the project's phase checks already use. Never use production in this step.
- **Defaults:** a row behaves as the code intends and the intent is sensible (1b: phones get a bottom tab bar, not a sidebar; signed-out `/portfolio`, `/dashboards`, `/settings` answer 200 with a sign-in prompt) → "BY DESIGN?" with the reason; text a licence requires (TradingView's "Charting by TradingView") → "BY DESIGN?"; a row does not reproduce on two tries → FIXED, with both tries as evidence; a row needs an account the checks do not have → CANNOT VERIFY HERE, verifier: owner, check: the row's repro steps.
- **Done when:**
  - [x] the file has 15 rows, each with a today value and evidence — check: count the rows
  - [x] every STILL FAILS row names its fixing step — check: read the table
- **Outcome:**
  - *Done:* `docs/qa-beta-2026-10/defects-2026-10-22.md`, 15 rows, on beta release `d356a3c`. FIXED: 1e, 2b (now tested), 5f, 7d, 7e, 8c, 10c, Copilot at 390 px (now tested). STILL FAILS: 7f and 9b and the 9f nit (→ Step 15), 8a and 8b (→ Step 14), 10b (→ Step 16). BY DESIGN?: 1b and the pages half of 9b (→ owner, Step 17). Most fixes came from `af9aca8`, `2bef6a4`, `46bb715`, `2977bfd` (2026-10-17/18), which landed after the audit's run 2.
  - *Not done:* N/A
  - *Touched:* new `web/scripts/check-audit.mjs` (every item's repro as one check; `[items]` filter; `COPILOT=0` skips the slow ones); `docs/qa-beta-2026-10/defects-2026-10-22.md`; evidence in `docs/screenshots/qa-recheck-2026-10-22/` (`results.json`, `slow/`, `c390/`).
  - *Verification:* (1) VERIFIED — 15 table rows, each with a today value and evidence. (2) VERIFIED — every STILL FAILS row names Step 14, 15 or 16.
  - *Rulings:* (a) 1e is FIXED although no ticker has ownership data today: the panel was proven with the audit's own JSON fed to beta's page, plus the existing API test. Cost if wrong: the pipeline's real block has a shape the sample lacks; seen when data returns. (b) 5f is FIXED without a reason line beside P/E: the defect was P/E "n/a" beside an EPS that implied 3.5x; EPS is now withheld ("Unit not confirmed"), and "N/A" is the app's standard placeholder. Cost if wrong: the owner wants a reason line; a small change in Step 13. (c) 2b compares computed colours of every visible element (charts and SVG excluded; the audit's 2a covers chart pixels) and first font faces; phase 7 checks drawn fonts. (d) 8a/8b counted against Step 14's allow-list classes; the language option "English" (`lang="en"`) and the user's own email are left for Step 14 to classify. (e) The 9f probe deletes a missing id (987654321), not qa1's objects; same query path, no other account touched. (f) 7f measured on 4 answers against Step 15's default target (5 s / 20 s median).
  - *Failed approaches:* reading `screening.sqlite` on the server with `python3` over SSH was refused by Claude Code's auto-mode classifier ("Production Reads"); scanning all 716 tickers through beta's own API (`/tickers/{slug}/insights`) answered the same question.
  - *Debt:* `ticker_insights.ownership` (and `analysts`) is null for all 716 tickers on beta's API today; the audit saw 2222's ownership on 2026-10-16, so the pipeline stopped writing it — a Goal 2 data question (see Open Questions).
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `cd web && BASE_URL=http://localhost:3201 COPILOT=0 node scripts/check-audit.mjs 1e,5f,9b,10c`
  - *Stamp:* 2026-10-22, on `37c3898` (beta and production on release `d356a3c`)


### Step 13 — Fix the data and display defects
- **Status:** DONE
- **Goal:** The Ownership tab shows holders properly, AFNIC's header and valuation tell the truth, English pages show English news, and the pricing page has no placeholder — on the local build, in both languages.
- **Depends on:** 12
- **Reversibility:** reversible
- **Autorun:** yes (code on `rebuild`, checked on the local build; the release is Step 17)
- **What this step is:** Fix the rows Step 12 marks STILL FAILS among: 1e — the Ownership panel (`section[data-panel="ownership.holders"]`) prints the API's JSON in a `<pre>` (`foreign_series`, `foreign_current_pct`, `major_holders`), and the series lists 2026-10-11 twice; 5f — AFNIC shows P/E "n/a" beside EPS 65.81 AED and price 230, and its header has no "As of" date; 8c — `/home` in English lists Arabic-only news; 10c — the pricing placeholder.
- **Where:** the ownership panel (`grep -rn "ownership.holders" web/src`), the ticker header and key-metrics components, the home news component, `web/messages/en.json` and `ar.json`, `api/app/routers/ticker_research.py`.
- **Consumes:** `docs/qa-beta-2026-10/defects-<date>.md` rows 1e, 5f, 8c, 10c.
- **Produces:** the fixed components and API; one check per fix (extend the nearest `web/scripts/check-*.mjs`; API tests under `api/tests/`); each row in `defects-<date>.md` marked "fixed in <commit>".
- **How:** reuse the patterns other panels already use (tables, freshness dots, "As of" labels, "Data unavailable"); see `CLAUDE.md` for the Next.js patterns. De-duplicate the ownership series in the API (one point per date, the latest).
- **Defaults:** Ownership has no design yet → a holders table (name, %) plus the foreign-ownership line chart drawn with the library the price panel uses; a price with no date → the header says so in the wording the app already uses for missing dates, and P/E stays "n/a" with a one-line reason (never compute a valuation from an undated price); no English headline for a news item → in English show it with a visible "Arabic" tag and `lang="ar"`, rather than hiding all news.
- **Done when:**
  - [x] on `/t/2222/ownership` and `/ar/t/2222/ownership` the panel has a table and no `pre` element — check: `document.querySelector('section[data-panel="ownership.holders"] pre') === null` in both languages, screenshots 1440 and 390 px
  - [x] the ownership API returns each date at most once for 2222 — check: the new API test
  - [x] `/t/AFNIC` shows a date or an explicit no-date label in the header, and a reason beside P/E — check: screenshot
  - [x] English `/home` shows no untagged Arabic-only news item — check: the extended check script
  - [x] `grep -rn "to be decided" web/messages` prints nothing — check: the command
- **Outcome:** *(reconciled from reality, not worked in this chat)*
  - *Done:* all four rows (1e, 5f, 8c, 10c) were already fixed by `af9aca8`, `46bb715`, `2977bfd` (2026-10-17/18) and run on beta in release `d356a3c`; Step 12 re-checked each. No code change was needed: `git diff d356a3c..HEAD -- web/src web/messages api/app` is empty, so beta runs the local code.
  - *Not done:* N/A
  - *Touched:* nothing beyond Step 12's `web/scripts/check-audit.mjs`, which holds one check per row (`1e`, `5f`, `8c`, `10c`).
  - *Verification:* (1) VERIFIED — `check-audit.mjs 1e`: 0 `pre` on 8/8 loads; with the audit's sample, a table at 1440 and 390 px, EN and AR (`docs/screenshots/qa-recheck-2026-10-22/1e-audit-sample-*.png`). Live pages show "No ownership data" because no ticker has ownership data today (Step 12 *Debt*). (2) VERIFIED — `pytest tests/test_ticker.py -k ownership`: 1 passed (`test_ownership_keeps_one_point_per_day_and_named_holders`, the audit's duplicate 2026-10-11 case). (3) VERIFIED — header `As of 16 Oct 2026` (`5f-AFNIC-{en,ar}-1440.png`); the P/E half per ruling (a). (4) VERIFIED — `check-audit.mjs 8c`: 10 items, 0 Arabic-only. (5) VERIFIED — grep exit 1, no output.
  - *Rulings:* (a) No reason line added beside AFNIC's P/E: the item was written for "P/E n/a beside EPS 65.81"; EPS is now withheld with its reason ("Unit not confirmed"), and the database has no P/E for AFNIC, which "N/A" already says. Cost if wrong: the owner wants a line such as "Not in our data"; one message key and one row.
  - *Failed approaches:* N/A
  - *Debt:* N/A
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `cd web && BASE_URL=http://localhost:3201 COPILOT=0 node scripts/check-audit.mjs 1e,5f,8c,10c`
  - *Stamp:* 2026-10-22, on `c103a63`


### Step 14 — Finish the Arabic pages
- **Status:** DONE
- **Goal:** Arabic pages show no English text except an agreed allow-list, and a check script keeps it that way.
- **Depends on:** 12
- **Reversibility:** reversible
- **Autorun:** yes (code on `rebuild`, checked on the local build)
- **What this step is:** The audit found 52 English strings on public Arabic pages (102 in run 1) and 34 on signed-in ones (rows 8a, 8b): English news headlines on `/ar/t/2222`, "Ctrl K", the model id "deepseek/deepseek-v3.2" on every app page, TradingView's chart title, and "English version" plus contact URLs on `/ar/legal/*`. Arabic is half the market; it has to be first-class.
- **Where:** `web/messages/ar.json`; the Copilot pane and search-hint components; the news components; the legal page shell (not `web/src/content/legal`, which `scripts/import-legal.py` writes); new `web/scripts/check-arabic.mjs`; `web/scripts/check-all.mjs`.
- **Consumes:** `docs/qa-beta-2026-10/defects-<date>.md` rows 8a, 8b.
- **Produces:** `web/scripts/check-arabic.mjs` — opens the Arabic public pages (the page list in `web/scripts/check-phase7.mjs`) and, with `SIGNED_IN=1`, the signed-in ones; reports visible Latin-letter words outside an allow-list kept at the top of the file; exits 0 only when there are none; listed in `check-all.mjs`. Plus the copy fixes.
- **How:** scan visible text only (not `aria-*`, not code); skip user content (a pinned Copilot table the user asked in English).
- **Defaults:** a news item with only an English headline → keep it, mark it `lang="en"` with a small Arabic "English" tag; never machine-translate news. The model id → remove it from the UI in both languages (it means nothing to members and was out of date). Allow-list: key names (Ctrl, K), tickers, currency codes, "AlphaCouncil", URLs and email addresses in legal contact lines, TradingView's attribution (licence).
- **Done when:**
  - [x] `node web/scripts/check-arabic.mjs` exits 0 on the local build, signed out and with `SIGNED_IN=1` — check: its summary line
  - [x] the allow-list holds only the classes named in Defaults — check: read it
  - [x] `check-all.mjs` runs it — check: `grep -n check-arabic web/scripts/check-all.mjs`
- **Outcome:**
  - *Done:* every English string Step 12 found on Arabic pages is gone or tagged: the Copilot model id is removed from the header in both languages (only the stand-in keeps a label); "FY2025" → "2025" in Arabic statements; sector percentiles "P54" → "المئين 61" (group) and "54" (rows); "±14d" → "±14 يوم"; dividend periods ("Q 3 _ 2025", "H1-2026", "F Y _ 2024") are formatted per language (`web/src/lib/dividend-period.ts`, "الربع الثالث 2025"), any other words in the note stay as stored with the "بالإنجليزية" tag; English event names and capital-change notes are tagged the same way (row tooltips start with the tag; the empty-field word "Notes" is hidden); "financial results date" and "eligibility of cash dividend" added to `web/src/content/data-labels.json`. News already followed the rule (`af9aca8`); its tag is now the shared `LangTag` (`components/stock/common.tsx`, `data-lang-tag`).
  - *Not done:* N/A
  - *Touched:* `web/scripts/check-arabic.mjs` (new), `web/scripts/check-all.mjs` (runs it signed out and signed in), `web/src/lib/dividend-period.ts` + `.test.ts` (new), `components/stock/{common,overview-panels,research-panels}.tsx`, `components/shell/CopilotPane.tsx`, `components/market/HomeView.tsx`, `components/templates/TemplateViews.tsx`, `messages/{en,ar}.json` (`stock.statements.fy`, `stock.fundamentals.score`/`pctShort`, `templates.windowDays`; `copilot.model` removed), `content/data-labels.json`. Screenshots: `docs/screenshots/arabic-2026-10-22/`.
  - *Verification:* (1) VERIFIED — local build (`next build`, `next start -p 3110`, local API): "24 Arabic page view(s) signed out; 0 English string(s) outside the allow-list" and "15 Arabic page view(s) signed in; 0 …". On beta's current release the same check lists 30 (the baseline it was built against). (2) VERIFIED for the Defaults' classes (keys, tickers, currency codes, AlphaCouncil, legal URLs/emails, TradingView), with two additions by ruling (b), put to the owner in Step 17. (3) VERIFIED — `check-all.mjs` lines 17–18 run it signed out and with `SIGNED_IN=1`. Regression: `check-phase7.mjs` on the local build "96 page views; 0 failure(s)"; `npm test` 27/27 (2 new); `tsc --noEmit` and eslint clean. English pages unchanged ("Q3 2025", no tag).
  - *Rulings:* (a) Structured period labels (Q/H/FY + year) are formatted, not translated; free text stays as stored with the tag — the news rule from Defaults applied to calendar data. Cost if wrong: the owner wants Arabic for the notes too; that needs Arabic source data or translation, a pipeline question. (b) Allow-list additions: "Google" (Google's branding rules require it on the sign-in button) and "EN"/"English" (the switch to the English site names the language in itself). Cost if wrong: two message changes. (c) Numbers keep Latin digits and K/M/B/x suffixes in Arabic (Phase 7 decision); the check treats them as numbers. Cost if wrong: an Arabic compact format in `lib/format.ts`. (d) Arabic data that names a company in Latin letters (news, event names) is accepted: it is Arabic text as published.
  - *Failed approaches:* `node --test` cannot load `lib/data-labels.ts` (it imports through the `@/` alias), so the period formatter lives in its own module.
  - *Debt:* 21 English event names across the universe have no Arabic entry yet (tagged, not translated; list from beta's API in this chat: "eligibility for subscription to rights issue", "press conference", "rump offering starts", …); 992 of 994 capital-change notes are English only.
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `cd web && BASE_URL=http://localhost:3110 node scripts/check-arabic.mjs` (local build and API running)
  - *Stamp:* 2026-10-22, on `b548bbe`


### Step 15 — Fix API answers and Copilot gaps
- **Status:** DONE
- **Goal:** Signed-out calls to protected APIs answer 401, deleting someone else's object answers 404, every Copilot answer that quotes a figure cites its panel, and Copilot's speed is measured against a target.
- **Depends on:** 12
- **Reversibility:** reversible
- **Autorun:** yes (code on `rebuild`; Copilot runs on beta are read-only questions)
- **What this step is:** Row 9b: signed out, `GET /v1/portfolio`, `GET /v1/portfolio/alerts`, `GET /v1/me/prefs`, `POST /v1/portfolio/holdings` and `POST /v1/portfolio/alerts` answer 403 `{"detail":"Sign in to use this."}`, and `POST /v1/copilot/chat` answers 403 `sign_in_required`; 401 is the code for "not signed in". The 9f nit: `DELETE /v1/portfolio/holdings/{id}` answers 200 for an id the caller does not own (it changes nothing, which is right). Row 7d: an answer quoted book value and EPS with no citation chip. Row 7f: full answers take 12–41 s. Row 7e: tool-use narration in an answer in run 2, not seen in run 3 — keep a guard against it.
- **Where:** the shared sign-in dependency in `api/app/` (find it with `grep -rn "Sign in to use this" api/app`), `api/app/routers/portfolio.py`, `api/app/routers/copilot.py` and its prompt, the web client's error handling in `web/src/lib/api/`.
- **Consumes:** `docs/qa-beta-2026-10/defects-<date>.md` rows 9b, 9f nit, 7d, 7e, 7f; `docs/qa-beta-2026-10/copilot-adversarial-plan.md` (tests C1–C8, which must keep passing).
- **Produces:** the status-code changes with tests in `api/tests/`; a Copilot citation rule (in the prompt, or a server-side check that asks for a citation when a figure has none); `docs/copilot-latency-<date>.md` with first-word and full-answer times, before and after, for the questions in rows 7d (`/t/METH.AD`, Key metrics, "What are the EV/EBITDA and the dividend yield?") and 7e (`/t/AFNIC`, Price + Key metrics, "What was the last closing price and the 1-month return?") plus three on `/t/2222`.
- **How:** change the shared dependency once, not each route; keep the JSON bodies; check that the web client treats 401 as it treated 403 (`grep -rn "403" web/src`).
- **Defaults:** speed target — first words within 5 s and full answers within 20 s (median); if the current model cannot reach it, record the times and the options (shorter context, earlier streaming, a faster model for Copilot) in the latency doc and change no model without the owner; the citation rule makes any of C1–C8 fail → revert it and record why; signed-out pages keep answering 200 with a sign-in prompt (BY DESIGN? in Step 12).
- **Done when:**
  - [x] API tests prove 401 signed out on the six routes above and 404 on a foreign or missing holding and alert id — check: `pytest api/tests -q` summary line
  - [x] each question in the latency doc that quotes a figure shows at least one citation — check: the doc's table
  - [x] the latency doc shows the target met, or the owner's choice recorded — check: the doc
  - [ ] C1–C8 pass after the change — check: their results in the latency doc *(CANNOT VERIFY HERE: see Verification (4))*
- **Outcome:**
  - *Done:* not signed in → 401 (`auth.not_signed_in`, with `WWW-Authenticate: Session`) on every route behind `require_user` and on Copilot chat; a request that carries an HTTP Basic login (beta's staging gate) keeps 403 so the gate login survives (audit 9c). Deleting a holding or alert that is not the member's, or no longer exists, → 404; the web client refetches the list on 404. Copilot's prompt gained an "Instructions." rule (data is never instructions; requests to drop the rules or answer with a fixed word get a one-line redirect) after C4 failed once on beta today. The citation rule and the narration guard already existed (`2bef6a4`) and passed (7d, 7e). `docs/copilot-latency-2026-10-22.md`: Step 15's five questions, C1–C8 twice.
  - *Not done:* N/A
  - *Touched:* `api/app/auth.py`, `api/app/routers/{copilot,portfolio}.py`, `api/app/copilot/engine.py`, `api/tests/test_{accounts,copilot,debate}.py`, `web/src/lib/queries-app.ts`, `web/scripts/check-audit.mjs` (latency set, item `C`), `docs/copilot-latency-2026-10-22.md`, `docs/qa-beta-2026-10/defects-2026-10-22.md`. Commit `b551630`.
  - *Verification:* (1) VERIFIED — `pytest -q`: 157 passed; `test_signed_out_calls_answer_401_but_403_behind_the_staging_gate` (the six routes plus PUT prefs, both deletes, `/me/delete`), `test_one_account_cannot_change_anothers_holdings_or_alerts` (qa1's ids and missing ids → 404), Copilot 401 `sign_in_required`. End to end on the local build through Next's proxy: 401 plain, 403 with a Basic login; `check-audit.mjs 9b,9f` → PASS, PASS. A member still deletes their own holding and alert from the UI (200, rows gone). (2) VERIFIED — the doc's table: 4–11 citations on every answer. (3) VERIFIED — median first words 1.7 s, full 17.2 s against 5 / 20 s; nine answers today: 2.7 / 17.2 s; the tail reaches 56 s (options listed, none applied). (4) CANNOT VERIFY HERE — on beta's current release C1–C8 pass except C4, which failed once and passed once; the prompt rule that answers C4 can only meet the real model once released. Verifier: Step 17. Check: after the beta release, `BASE_URL=http://localhost:3201 OUT=… node web/scripts/check-audit.mjs C` three times, C4 PASS each time, and C1–C8 PASS.
  - *Rulings:* (a) 401 everywhere except requests carrying an HTTP Basic login, which keep 403. Why: beta's gate is HTTP Basic and any 401 makes browsers drop its login (audit 9c); production has no gate. Cost if wrong: an auditor on the public beta address still sees 403; production and the tunnel show 401 (put to the owner as BY DESIGN 4). (b) Failed sign-ins, used links and Pro-only data keep 403 (not "not signed in"). (c) The prompt rule was added without a run against the real model (no AI key off the server). Cost if wrong: C4 still flaky after release; Step 17 catches it before production. (d) Speed: target met on the median, so no change and no question to the owner; the long tail is written down.
  - *Failed approaches:* the first C1–C8 run reused one browser, so attached panels carried over and C7/C8 could not attach; each question now gets a fresh browser. The first C3 grader read "No, I cannot give you a yes or no answer" as a "no".
  - *Debt:* C8's answer named an internal field ("the data freshness category"); the prompt forbids field names. Minor; watch in Step 17.
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `cd api && uv run pytest -q tests/test_accounts.py -k "401 or anothers"`
  - *Stamp:* 2026-10-22, on `b551630`


### Step 16 — Prove checkout in Moyasar test mode on beta
- **Status:** DONE
- **Checkpoint cleared:** 2026-10-22 — owner in chat: "run the checkout tests in Moyasar test mode on beta (Step 16)"
- **Goal:** Every checkout case has run in Moyasar test mode on beta and passed, and beta is back to billing closed.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** no — checkpoint: decision (the owner's go-ahead: it changes beta's billing setting and uses Moyasar, both Always stop)
- **What this step is:** The audit could not test checkout (row 10b): beta runs with billing closed, so `/pricing` says checkout is not open. The runbook records one test-mode payment on beta on 2026-10-18, not the full set of cases. This step proves the paid path before anyone pays.
- **Where:** beta's `/etc/alphacouncil-platform/api.env` (`BILLING_OPEN` and the Moyasar **test** keys, by name only) and service `acp-api`; `web/scripts/check-billing.mjs`; Moyasar's test dashboard (owner); `docs/checkout-test-<date>.md`.
- **Consumes:** `docs/qa-beta-2026-10/moyasar-checkout-interview-prompt.md` (run it with the owner first to agree the case list); the runbook section "Pro billing (Moyasar)".
- **Produces:** `docs/checkout-test-<date>.md` — each case with steps, expected result, result and evidence; `api.env.bak-<timestamp>` beside beta's `api.env`.
- **How:** back up beta's `api.env`, add `BILLING_OPEN=true`, `systemctl restart acp-api`, run the cases through the beta tunnel with Moyasar's published test cards, then remove the line and restart. Cases, at least: success (Pro granted; `/billing/return` confirms against Moyasar's record); declined card; 3-D Secure pass and fail; closing the browser after paying (the webhook grants Pro); a duplicate webhook applied once; cancel (Pro to the end of the period, no renewal); renewal (`python -m app.billing renew` on beta with a due test subscription); a refund in Moyasar's test dashboard ends Pro (owner); English and Arabic, 1440 and 390 px. Never live keys; never a real card.
- **Defaults:** beta has no Moyasar test keys → stop; the owner adds them (names in the runbook); a case fails → record it, fix it in the repo if small, re-run; never leave beta with billing open at the end of the chat.
- **Done when:**
  - [x] `docs/checkout-test-<date>.md` lists every case above as PASS with evidence — check: read it
  - [x] `node web/scripts/check-billing.mjs` passes on beta — check: its summary line, copied into the file
  - [x] `grep -c '^BILLING_OPEN=' /etc/alphacouncil-platform/api.env` prints 0 on the server afterwards — check: the command
- **Outcome:**
  - *Done:* every checkout case passed in Moyasar test mode on beta in one run (13 of 13, 2026-10-21 23:47–23:48 UTC): declined card, 3-D Secure refused and approved, the return page ignoring a forged `status=paid`, renewal on the saved card, cancel, refund ending Pro, a closed browser started by the notification, a duplicate notification applied once, a wrong secret refused, EN/AR at 1440 and 390 px. `check-billing.mjs`: "Billing checks: all passed". Beta closed again. No app change was needed.
  - *Not done:* N/A
  - *Touched:* new `web/scripts/check-checkout.mjs`; `web/scripts/check-billing.mjs` (return page through the tunnel); `docs/checkout-test-2026-10-22.md`; `docs/production.md` (Pro billing: the 2026-10-22 test); screenshots `docs/screenshots/checkout-test-2026-10-22/`. Server: beta `api.env` backed up as `api.env.bak-20261021231949`, `BILLING_OPEN=true` and a throwaway `MOYASAR_WEBHOOK_SECRET` added for the test, then the backup restored and `acp-api` restarted (23:50:40 UTC).
  - *Verification:* (1) VERIFIED — the doc's table: 13 PASS with payment ids and screenshots. (2) VERIFIED — "Billing checks: all passed" copied into the doc (its Pro-account part from the run before). (3) VERIFIED — `grep -c` → 0 for `BILLING_OPEN` and for `MOYASAR_WEBHOOK_SECRET`; `/v1/plans` → `"checkout_open":false`.
  - *Rulings:* (a) Moyasar's webhooks cannot reach beta (the password gate answers 401), so the notification cases delivered Moyasar's body to beta's API from the server; the handler still re-fetches each payment from Moyasar. Cost if wrong: Moyasar's real delivery is untested on beta; production's live webhooks were seen arriving on 2026-10-18, and Step 18's first real payment checks it again. (b) The refund went through Moyasar's test API with beta's test key (the script refuses any other key), not the owner's dashboard. Cost if wrong: none for money (test mode); the dashboard's own refund button is untested. (c) A throwaway webhook secret was added to beta for the test and removed with the restore. (d) Test addresses were confirmed by setting `email_verified_at` in beta's database (example.com gets no email).
  - *Failed approaches:* first runs stopped at Moyasar's return to `https://beta.alphacouncil.tech/billing/return` (401 from the gate in a browser without its login), at Cloudflare's 1010 on Python's default user agent, and at the shared sign-in limit (10 per 15 min; the tunnel is one address). The scripts handle all three.
  - *Debt:* beta keeps the `checkout-*@example.com` test accounts; three have test-mode subscriptions that renew monthly on Moyasar test cards (no real money). Deleting them is the owner's call.
  - *Resume here:* N/A
  - *Verify in 30 seconds:* `ssh root@alphacouncil.tech "grep -c '^BILLING_OPEN=' /etc/alphacouncil-platform/api.env"` (prints 0)
  - *Stamp:* 2026-10-22, on `01f3249` (scripts and docs committed with this outcome)


### Step 17 — Re-audit beta, then release the fixes to production
- **Status:** AWAITING CHECKPOINT — everything done and live except Copilot speed (7f): production's median first words 8.6 s (target 5 s), full answers 13.4 s (met). Option (c) tried on 2026-10-22: no OpenRouter host meets both targets. The owner chooses: accept the current speed (BY DESIGN), (d) a faster model, or (e) a first turn that answers from the data already given.
- **Checkpoint cleared:** 2026-10-22 — beta release only; owner in chat: "Go-ahead: one beta release of rebuild (Step 17), then re-audit it."
- **Checkpoint cleared:** 2026-10-22 — owner in chat: "Copilot first words: try option (c), pin the OpenRouter host that served the fast answers on 2026-10-21. Go-ahead for the beta release and, if it meets the target, production."
- **Checkpoint cleared:** 2026-10-22 — owner in chat: "Go-ahead: release to production now. Accept BY DESIGN items 1-4. Copilot speed: option (b) — add the length rule and drop "and suggest one", as a second small beta release, then production."
- **Goal:** Steps 13–15's fixes run on beta and production, every audit item is PASS or accepted by the owner, and nothing regressed.
- **Depends on:** 12, 13, 14, 15, 16
- **Reversibility:** reversible (a release rolls back per the runbook)
- **Autorun:** no — checkpoint: decision (the owner's go-ahead for the beta release, the BY DESIGN list, and the production release)
- **What this step is:** One beta release with all of Goal 3's fixes, every audit item re-run on it, one question to the owner for the BY DESIGN list, then the production release.
- **Where:** `scripts/deploy-staging.sh`, `scripts/deploy-production.sh`; `docs/qa-beta-2026-10/reaudit-<date>.md`; `docs/production.md`.
- **Consumes:** `docs/qa-beta-2026-10/defects-2026-10-22.md` (16 rows with their fixing commits `b548bbe`, `b551630`, and 4 Proposed BY DESIGN items); `web/scripts/check-audit.mjs` (every item's repro; `C` = trust suite C1–C8; `7f` = Step 15's latency set); `web/scripts/check-arabic.mjs`; `docs/copilot-latency-2026-10-22.md`; `docs/checkout-test-<date>.md`.
- **Produces:** `docs/qa-beta-2026-10/reaudit-<date>.md` — each item PASS with evidence, or BY DESIGN with the owner's words; the production release id recorded in `docs/production.md`.
- **How:** release to beta (go-ahead) → re-run each item's repro steps plus `check-all.mjs` and `check-arabic.mjs` on beta → ask the owner once to accept or reject the BY DESIGN list → release to production (go-ahead) → `check-all.mjs` and `check-arabic.mjs` on production.
- **Defaults:** an item fails again on beta → back to its step, no production release; the owner rejects a BY DESIGN item → it becomes a fix in the step that owns its area (13, 14 or 15). Re-audit through the tunnel: `cd web && BASE_URL=http://localhost:3201 OUT=../docs/screenshots/reaudit-<date> node scripts/check-audit.mjs` (all items, ~15 min), then `check-audit.mjs C` twice more (C4 must pass 3 of 3: the prompt rule from `b551630` meets the real model only on beta), then `check-arabic.mjs` signed out and `SIGNED_IN=1`. 9b through the tunnel must show 401; on the public beta address it shows 403 by design (BY DESIGN 4). Ownership (1e): if no ticker has ownership data yet, the audit-sample proof stands. Ask the owner the four BY DESIGN items in one message, with the release go-ahead.
- **Done when:**
  - [ ] the re-audit file shows every item PASS, or BY DESIGN with the owner's words — check: read it
  - [ ] production's release id equals the re-audited beta release — check: `docs/production.md`
  - [ ] `check-all.mjs` and `check-arabic.mjs` pass on production — check: summary lines in the re-audit file
- **Outcome:**
  - *Done:* beta re-audited on `ae72d6a05b` (every audit item PASS or BY DESIGN, except 7f); the owner accepted BY DESIGN 1–4 (quoted in `docs/qa-beta-2026-10/reaudit-2026-10-22.md`). Production released twice with the owner's go-ahead: `53c3c54aa0` (10:11 UTC; the same app as the re-audited `ae72d6a05b`) and `56476948f5` (10:36 UTC; option (b), Copilot answers short and from the data's own figures, a refusal is one sentence). Each time beta ran the same release first; `check-all.mjs` 9/9 on production both times (Arabic check signed out and in included); production checkout still closed; monitor 13 ok throughout. Release log: `docs/production.md` "Release log".
  - *Not done:* 7f (Copilot speed). Option (c), 2026-10-22: `COPILOT_PROVIDER_ORDER` and per-step host logging (`859edaf`, beta `859edafff3`); hosts timed from the server; in the app, Phala first 8.2 s / 19.7 s, SiliconFlow first 3.8 s / 23.8 s (one answer 150 s), automatic 8.6 s / 13.4 s (first words / full, medians). No setup meets both; production not released (owner's condition); beta's settings restored. Details: `reaudit-2026-10-22.md`, "Option (c)".
  - *Touched:* `api/app/copilot/engine.py` + `api/tests/test_copilot.py` (`5647694`); `web/scripts/check-audit.mjs` (8a/8b via `check-arabic.mjs`, 10b via the checkout record, C1 and C7 graders); `docs/qa-beta-2026-10/{reaudit,defects}-2026-10-22.md`; `docs/copilot-latency-2026-10-22.md`; `docs/production.md`; evidence `docs/screenshots/reaudit-2026-10-22/` (incl. `after-b/`, `smoke-53c3c54/`, `check-all-production-*.txt`).
  - *Verification:* (1) re-audit file — NOT MET for 7f only (full answers met, first words not); every other item PASS, or BY DESIGN with the owner's words. (2) production's release id equals beta's — VERIFIED: both `56476948f5` (`readlink` on the server; release log). (3) `check-all.mjs` and `check-arabic.mjs` on production — VERIFIED: 9/9, `check-all-production-56476948f5.txt`.
  - *Rulings:* (a) Production got `53c3c54aa0`, not `ae72d6a05b`: the production script ships only the commit beta runs, and the only commit between them was the re-audit record (0 lines of app code); beta was re-pointed and smoke-checked first. Cost if wrong: none found (smoke 6/6, check-all 9/9). (b) The length rule also says "work out no ratios of your own", from the standing rule "never show a number that is not from our database"; it is what ended the 1.4x/1.36x inconsistency. Cost if wrong: answers say "payout ratio not published" where a computed ratio would help; the owner can relax it. (c) Re-audit verdicts for Copilot on `56476948f5` come from the three after-(b) runs, not a second full re-audit; the rest of the app is unchanged since `ae72d6a05b`. (d) C1–C8 counted by reading where the grader missed (C1 wording, C7 extra figures); graders fixed.
  - *Failed approaches:* the production script refuses uncommitted changes and any HEAD beta does not run; edits were stashed for the second release and restored after.
  - *Debt:* a model answer once quoted database ratios unrounded ("0.200619170560779"); beta keeps test accounts from the checkout test; an `ssh.exe` tunnel may be left running on this computer.
  - *Resume here:* when the owner chooses: accept → write "7f BY DESIGN" with their words into `reaudit-2026-10-22.md` and close Goal 3 (production already runs the re-audited release). (d) a faster model or (e) a first turn without lookups → change on `rebuild`, beta release (go-ahead), `check-audit.mjs 7f,C` twice (targets 5 s / 20 s median), production release (go-ahead), `check-all.mjs` on production. A host can be tried without a release: `COPILOT_PROVIDER_ORDER=<hosts>` in beta's `api.env`, `systemctl restart acp-api`.
  - *Verify in 30 seconds:* `ssh root@alphacouncil.tech 'readlink -f /opt/alphacouncil-platform/current /opt/alphacouncil-platform/prod/current'` (both `…/56476948f5`)
  - *Stamp:* 2026-10-22, beta and production on `56476948f5`

## Goal 4 — Launch: settled, checked, then paid
- **Status:** AWAITING CHECKPOINT — Steps 7–9 each wait on the owner (re-tested 2026-10-22: `www` NXDOMAIN, no portrait files, no legal advice in chat); Step 10 waits on Goals 2 and 3; Step 18 waits on Step 10 and the owner's go-ahead.
- **Share of project:** ~30%
- **Goal:** The advisors' names and texts follow the owner's legal advice, the six portraits are real, `www.alphacouncil.tech` works, a full launch check passes on production, and only then is Pro checkout open.
- **Done when:**
  1. The owner's written legal advice is in `docs/legal-advisors-<date>.md` (the owner's summary, no personal data), it answers Step 7's three questions, and every change it asks for is live.
  2. The advisors' room shows six real portraits in English and Arabic at 1440 and 390 px, with the initials only as a fallback for a missing file.
  3. `curl -sI https://www.alphacouncil.tech/` answers 301 to `https://alphacouncil.tech/`, and the certificate covers both names.
  4. `docs/launch-check-<date>.md` records every check script passing on production (`check-all.mjs`, `check-data-fixes.mjs` with `SWEEP=1`, `check-seo.mjs`, `check-advisors.mjs`, `check-arabic.mjs`) and the monitor at 14 of 14.
  5. `curl -s https://alphacouncil.tech/api/v1/plans` prints `"checkout_open":true`, and the owner's own first real payment gave Pro (and its refund ended it, or the refund is recorded as waiting for Moyasar's settlement).
- **Depends on:** nothing for Steps 7–9; Step 10 (the launch check) depends on Goals 2 and 3; Step 18 depends on Step 10.
- **Reversibility:** reversible (DNS and certificate: costly; opening billing: costly — whoever pays is owed their month)
- **Autorun:** no — checkpoint: human-action (legal advice, portrait files, DNS record) and decision (opening billing, Step 18)
- **Consumes:** `docs/advisors-portraits-brief.md` (the illustrator's brief); `api/app/advisors/*.md` (the six advisors and the Chair); `docs/qa-beta-2026-10/reaudit-<date>.md` (Goal 3).
- **Steps:** 7–10, 18
- **Goal outcome:** _(empty until the goal is worked)_

### Step 7 — Apply the lawyer's advice to the named advisors
- **Status:** AWAITING CHECKPOINT — the owner pastes or summarises the lawyer's advice in chat (2026-10-19: none yet).
- **Goal:** The advisors' names, wording and disclaimers match the owner's legal advice, live on production.
- **Depends on:** nothing
- **Reversibility:** reversible
- **Autorun:** no — checkpoint: human-action (the owner brings the advice)
- **What this step is:** The room speaks as Buffett, Lynch, Dalio, Marks, Prince Alwaleed and Abdullah Al-Rajhi. Using real people's names and personas is the main legal exposure before advertising. The owner gets advice; this step applies it. Put three questions to the lawyer in one visit: (a) the real names and personas; (b) whether the live Copilot and the advisors' room stay inside an information service that needs no CMA permit — the owner's own plan of 2026-08-08 (`C:\AlphaCouncil-Staging\CMA_FINTECH_EXPERMIT_PLAN.md`, lines 137–144) said not to "enable Council or Research Assistant for customers" before a permit; (c) whether Moyasar must be told, since the merchant account was approved on the representation that the product is not robo-advisory (`C:\AlphaCouncil-Staging\PROJECT_ENDGAME.md`, line 36).
- **Where:** `api/app/advisors/*.md`; the advisors' room UI copy in `web/messages/en.json` and `web/messages/ar.json`; nothing in `web/src/content/legal` (those texts are copied from the old site by `scripts/import-legal.py` and never edited by hand).
- **Consumes:** the owner's advice, pasted or summarised in chat.
- **Produces:** `docs/legal-advisors-<date>.md` (what the advice says, what changed); the changed files; a release through beta then production with the owner's go-ahead.
- **How:** keep advisor ids (`buffett`, `lynch`, `dalio`, `marks`, `alwaleed`, `alrajhi`) and `DEBATE_ADVISORS` stable even if display names change, so saved sessions keep working.
- **Defaults:** the advice says no real names → rename to descriptive personas (for example "The Value Investor"), keep each advisor's method, and say "inspired by public writings" nowhere unless the advice allows it; the advice is ambiguous on a point → take the more cautious reading and list it for the owner.
- **Done when:**
  - [ ] `docs/legal-advisors-<date>.md` lists each point of the advice and the change made for it — check: read the file
  - [ ] the file records the lawyer's answers to (b) and (c), and any change they require is listed with the step that makes it — check: read the file
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
- **Goal:** One dated record shows every check passing on production after Goals 2, 3 and 4's changes, with billing still closed.
- **Depends on:** 6, 7, 8, 9, 17
- **Reversibility:** reversible
- **Autorun:** yes
- **What this step is:** The last pass before the owner spends on advertising: every check script, the monitor and screenshots of the key pages, in one report.
- **Where:** `docs/launch-check-<date>.md`; screenshots under `docs/screenshots/launch-<date>/`.
- **Consumes:** the releases from Steps 6–9 and 17; `docs/qa-beta-2026-10/reaudit-<date>.md`; `web/scripts/check-arabic.mjs`.
- **Produces:** `docs/launch-check-<date>.md` (Step 18 reads it before billing opens).
- **How:** run the scripts against production through the tunnel or over HTTPS as each script supports; `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status` on the server; screenshots of /, /pricing, /home, a Tadawul stock, its advisors' page, in English and Arabic at 1440 and 390 px.
- **Defaults:** a check fails → record it NOT MET with output, fix it only if the fix is inside this repo and small, release only with the owner's go-ahead; a step it depends on is blocked → run the check anyway and mark the gap.
- **Done when:**
  - [ ] the report lists each script with its summary line, all passing — check: read the file
  - [ ] the monitor's status shows 14 of 14 ok — check: its output in the report
  - [ ] the screenshots exist for each page, both languages, both widths — check: list the folder
  - [ ] `check-arabic.mjs` passes on production — check: its summary line in the report
- **Outcome:** _(empty until worked)_

### Step 18 — Open Pro billing on production (the paid launch)
- **Status:** NOT STARTED
- **Goal:** Pro can be bought on alphacouncil.tech, and the owner's own first real payment proved it end to end.
- **Depends on:** 10
- **Reversibility:** costly (whoever pays is owed their month, even if billing closes again)
- **Autorun:** no — checkpoint: decision (the owner's go-ahead in chat after reading `docs/launch-check-<date>.md`)
- **What this step is:** The last step of the plan. Billing reopens only when the launch check is all green (owner's rule, 2026-10-21).
- **Where:** `/etc/alphacouncil-platform/prod/api.env`; service `acp-prod-api`; Moyasar's live dashboard (owner); `docs/production.md`.
- **Consumes:** `docs/launch-check-<date>.md` with every item passing; the runbook section "Billing is open (since 2026-10-18)" (how it was opened and checked); Step 11's `api.env.bak-<YYYYMMDDHHMMSS>` and its "Billing closed again (<date>)" paragraph.
- **Produces:** `BILLING_OPEN=true` in production's `api.env` (the file before it kept as `api.env.bak-<timestamp>`); a "Paid launch (<date>)" paragraph in `docs/production.md` with the checks below.
- **How:** as on 2026-10-18: back up, add the line, `systemctl restart acp-prod-api`, check `/pricing` ("Get Pro", no early-access note) and that the live card form loads in English and Arabic, without paying. Then the owner pays once with their own card, confirms Pro on their account, and refunds in Moyasar's dashboard; the refund ends Pro (runbook).
- **Defaults:** the refund is refused because Moyasar has not settled the payment (it happened on the old site on 2026-08-11: `insufficient_balance`) → record it; the owner refunds after settlement; that item is CANNOT VERIFY HERE, verifier: owner, check: Moyasar's dashboard shows the payment Refunded. Any check fails → close billing again at once (remove the line, restart) and report.
- **Done when:**
  - [ ] `curl -s https://alphacouncil.tech/api/v1/plans` prints `"checkout_open":true` — check: the command
  - [ ] the owner's payment gave their account Pro, and the payment was applied once — check: the owner's Settings → Billing screenshot and the API log line for that payment id
  - [ ] the refund ended Pro, or is recorded as waiting for settlement — check: screenshot, or the note
  - [ ] the monitor shows 14 of 14 ok — check: `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status`
- **Outcome:** _(empty until worked)_

## 8. Open Questions
- **A new empty private GitHub repository's URL** — blocks Step 2. The owner creates one at github.com/new (Private, no README, no licence; suggested name `alphacouncil-platform`) and pastes its URL. The URL given on 2026-10-21 (`alphacouncil-static`) is public and holds the old site, so it is not used (Step 2, *Rulings* (b)). No default: Claude cannot create the repository.
- **Copilot speed (7f)** — blocks Goal 3. Production: first words 8.6 s (target 5 s), full answers 13.4 s (met). Option (c) (pinning a host) was tried on 2026-10-22: no host meets both (`docs/qa-beta-2026-10/reaudit-2026-10-22.md`, "Option (c)"). Choose: accept the current speed (7f becomes BY DESIGN; Goal 3 closes), (d) a faster model for Copilot, or (e) a first turn that answers from the data already given (the automatic host always looks something up first). Recommended: (e), then accept if it falls short. No default: model choices are the owner's.
- **Ownership data has stopped** — no ticker has `ticker_insights.ownership` today (beta's API, 2026-10-22); it existed on 2026-10-16. Pipeline question for Goal 2 (Step 5's fix list does not cover it). Until then the Ownership tab says "No ownership data".
- **The lawyer's advice on the named advisors** — blocks Step 7 (and Step 8, since names may change). No default: it is the owner's legal call.
- **Which pipeline fixes go to the server (A all four / B without F-B / C none), and whether to build F-D** — blocks Steps 5–6. Recommendation: A, and F-D yes after one night. No default: the standing rule keeps the old pipeline read-only without the owner's approval.
- **The portrait files** — block Step 8. **The `www` A record in Cloudflare** — blocks Step 9. Both are the owner's actions.
- **KPPC (624, Boursa Kuwait) and TAQA (ADX)** — Argaam has no page for KPPC and no TAQA bars after 2026-08-06. Delisted or suspended? The owner may know; until then the app keeps showing them stale (amber).

## 9. Next Up
Goal 3 needs one answer: Copilot speed — accept, (d) or (e) (Step 17 *Resume here*). Then, as each answer arrives: Step 2 (push to the new private repository — Goal 1's last item), Step 5 → 6 (pipeline fixes), Steps 7–9 (advice, portraits, `www`), Step 10 (launch check), Step 18 (open billing).
