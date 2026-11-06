# Output 49: review 50's step. Production's monitor read after today's changes, and recorded.

**Read-only:** `python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status`, at 2026-11-06 12:33:51 UTC, with
production on `b5655a5064`.

**Result: 15 checks: 13 ok, 1 failing, 1 pending.** *(Corrected after review 51: this said 14 ok.)*
- **ok:**
  - home 200, `/api/v1/health` 200, market data;
  - both services;
  - the renewals job and timer;
  - the backup job and timer;
  - the off-server copy (76 files, 0.3 days old);
  - disk `/` at **41 %** (122.4 GB free, from 83 % before the retention);
  - `/boot` at 15 %;
  - the TLS certificate (76 days).
- **FAILING:** model account credit, **$7.83**, below the $10 alert line, with the alert emailed. This is the
  owner's top-up.
- **Pending, not a failure:** "Moyasar for renewals" (–). The hourly job has logged no new run since the monitor's
  previous round. *(Corrected after review 51: this said no renewal has run.)*
  - **What the line cannot show:** it turns ok on any new run summary with no unreachable renewal, including an
    empty run, so neither state proves a real renewal.
  - **What Step 18's item 4 needs:** a `renewal` payment row on production.
- **Alerts:** 3 in 24 hours and 10 in 30 days, within limits.

**Recorded in:**
- `docs/launch-check-2026-10-27.md`, as a new section with the full table;
- the same file, as a dated note that the test accounts its checks left were removed today (24 on production);
- `PROJECT.md` §9: the balance line now notes the failing credit check.

`git diff --check` is clean. Documentation only.

**The question for the review:** is this sound, and what is the single next pre-approved step?

*Review 52's corrections:*
- **The capture.** The complete status output is saved verbatim as
  `docs/screenshots/release-b5655a5064/monitor-status.txt`, captured fresh at 2026-11-06 12:40:01 UTC. It shows 15
  check lines: 13 `ok`, 1 `FAILING` (credit, $7.83) and 1 `-` (renewals). It holds no secret: the outside-check URL
  is reported only as "set".
- **The two older claims** that the renewals line "cannot turn ok before a real renewal" now carry dated correction
  notes: `PROJECT.md` Step 18's status, and `docs/launch-check-2026-10-27.md`'s Step 10 note.
- **Step 18's item 4 stays open.** It closes on a `renewal` payment row on production, with the monitor all ok beside
  it.
