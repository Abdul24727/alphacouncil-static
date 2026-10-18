#!/usr/bin/env python3
"""Production monitor for alphacouncil.tech: emails the owner when something breaks, and once more
when it is fixed (docs/production.md, "Monitoring"). Standard library only: it runs on the
server's python3, outside the app's releases, so a broken deploy cannot break the monitor too.

    prod-monitor.py check    # one round of checks; acp-prod-monitor.timer runs it every 5 minutes
    prod-monitor.py status   # the same checks, printed; sends nothing and saves nothing
    prod-monitor.py test     # sends one test alert to ALERT_TO

Each round checks:

- https://alphacouncil.tech/home and /api/v1/health answer 200 (health also says status "ok"),
  and the health answer reports the market data as "ok";
- acp-prod-api and acp-prod-web are active and not restarting in a loop (3 or more automatic
  restarts within 15 minutes);
- acp-prod-billing.service (the hourly Pro renewals): its last run exited 0, its timer is
  active, and its output line (`reminded=… renewed=… failed=… ended=… unreachable=…`) shows no
  unreachable renewals; failed renewals and ended plans are reported as they happen;
- acp-db-backup.service (the nightly database dumps), once its timer is installed: the same
  last-run and timer checks;
- the off-server copy of those dumps (scripts/pull-backups.ps1 on the owner's computer), once it
  has reported in: its last complete copy is at most 3 days old;
- no disk is more than 85% full, and the certificate alphacouncil.tech serves is valid for at
  least 14 more days.

Alerts go out on changes only: a problem after 2 failing rounds in a row (unreachable renewals:
the first run showing them), and again when it clears; nothing is repeated while it lasts. Failed
renewals and ended plans are events, one mail per renewal run that has them. Everything that
changed in a round goes in one mail, and at most MAILS_PER_DAY mails leave in 24 hours and
MAILS_PER_MONTH in 30 days: the mail plan's allowance (about 500 a month) is shared with the old
backend and the app's own emails. A mail that cannot be sent is retried next round.

Mail goes through the API's SMTP settings (SMTP_* in /etc/alphacouncil-platform/prod/api.env),
which are read here and never printed or logged. The recipient is ALERT_TO in
/etc/alphacouncil-platform/prod/monitor.env (several: comma-separated).

The outside check: when monitor.env has PING_URL (a Healthchecks.io check's ping URL), every round
ends with a ping to it, or with a ping to PING_URL/fail when the round had news it could not email
(the mail server refused, or a mail limit was reached). Healthchecks.io emails the owner from
outside when a round fails that way, or when the pings stop: the server, its network or this
monitor is down. The URL is never printed or logged.
"""

from __future__ import annotations

import json
import math
import os
import re
import smtplib
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

SITE = "alphacouncil.tech"
HOME_URL = "https://alphacouncil.tech/home"
HEALTH_URL = "https://alphacouncil.tech/api/v1/health"
SERVICES = ("acp-prod-api", "acp-prod-web")
BILLING = "acp-prod-billing"
BACKUP = "acp-db-backup"  # nightly dumps (docs/production.md, "Backups"); checked once installed
# The owner's computer reports its last complete copy of the dumps here (docs/production.md,
# "Off-server copy"); checked once the file exists.
OFFSITE_PULL = os.environ.get("ACP_OFFSITE_PULL", "/var/lib/acp-offsite-pull/last.json")
OFFSITE_MAX_AGE = 3 * 86400  # seconds

DISK_MAX = 85  # percent used; an alerted disk counts as fixed at DISK_CLEAR or below
DISK_CLEAR = 83
CERT_MIN_DAYS = 14
RESTARTS_MAX = 3  # automatic restarts within RESTART_WINDOW = restarting in a loop
RESTART_WINDOW = 15 * 60
FAILS_BEFORE_ALERT = 2
MAILS_PER_DAY = 8
MAILS_PER_MONTH = 60
TIMEOUT = 20  # seconds, for each HTTP and TLS check
PING_TIMEOUT = 10  # seconds; a missed ping is covered by the next round and the check's grace time

API_ENV = os.environ.get("ACP_API_ENV", "/etc/alphacouncil-platform/prod/api.env")
MONITOR_ENV = os.environ.get("ACP_MONITOR_ENV", "/etc/alphacouncil-platform/prod/monitor.env")
STATE_FILE = os.path.join(os.environ.get("STATE_DIRECTORY", "/var/lib/acp-monitor"), "state.json")

UNCHANGED = "unchanged"  # gather(): the billing check did not run, keep the journal position
RIYADH = timezone(timedelta(hours=3))
COUNTS = re.compile(r"\breminded=(\d+) renewed=(\d+) failed=(\d+) ended=(\d+) unreachable=(\d+)\b")
COUNT_NAMES = ("reminded", "renewed", "failed", "ended", "unreachable")
# Settings whose values never go into a mail, even inside a log line.
SECRET_KEY = re.compile(r"PASS|SECRET|KEY|TOKEN|DATABASE_URL|SMTP_USER")
LINE_BREAK = re.compile(r"[\r\n\x00]")


class Result:
    """One check's outcome. ok=None: no new information this round (the state stays as it is)."""

    def __init__(self, name: str, ok: bool | None, detail: str, need: int = FAILS_BEFORE_ALERT, logs: str | None = None):
        self.name, self.ok, self.detail, self.need, self.logs = name, ok, detail, need, logs


# --- settings ------------------------------------------------------------------------------------


def read_env(path: str) -> dict[str, str]:
    """KEY=VALUE lines, as systemd's EnvironmentFile reads them (comments, optional quotes)."""
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            values[key.strip()] = value
    return values


def load_config() -> dict:
    """The recipient, the SMTP settings and the optional ping URL. Fails naming what is missing,
    never a value."""
    try:
        api = read_env(API_ENV)
        monitor = read_env(MONITOR_ENV)
    except OSError as exc:
        raise SystemExit(f"cannot read the settings: {exc.filename}: {exc.strerror}")
    to = [a.strip() for a in monitor.get("ALERT_TO", "").split(",") if a.strip()]
    if not to:
        raise SystemExit(f"ALERT_TO is not set in {MONITOR_ENV}")
    if not api.get("SMTP_HOST"):
        raise SystemExit(f"SMTP_HOST is not set in {API_ENV}")
    secrets = {v for k, v in api.items() if SECRET_KEY.search(k) and len(v) >= 6}
    url = re.match(r"[^:]+://[^:/@]+:([^@]+)@", api.get("DATABASE_URL", ""))
    if url:
        secrets.add(url.group(1))
    ping = monitor.get("PING_URL", "")
    if ping and not re.fullmatch(r"https://[^\s/]+/\S+", ping):
        # Not fatal: the alerts by mail still work, and the missing pings make the outside check email.
        print(f"PING_URL in {MONITOR_ENV} is not an https:// URL: not pinging", file=sys.stderr)
        ping = ""
    return {"to": to, "smtp": {k: v for k, v in api.items() if k.startswith("SMTP_")}, "secrets": secrets,
            "ping": ping}


def redact(text: str, secrets: set[str]) -> str:
    for s in sorted(secrets, key=len, reverse=True):
        text = text.replace(s, "[redacted]")
    return text


# --- system helpers ------------------------------------------------------------------------------


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=60).stdout


def unit_props(unit: str, *props: str) -> dict[str, str]:
    out = run("systemctl", "show", unit, "--no-pager", *(f"--property={p}" for p in props))
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def recent_logs(unit: str, lines: int = 15) -> str:
    try:
        out = run("journalctl", "-u", unit, "-n", str(lines), "-o", "short-iso", "--no-pager")
    except (OSError, subprocess.SubprocessError) as exc:
        return f"(journal not readable: {type(exc).__name__})"
    return "\n".join(line[:400] for line in out.strip().splitlines())


def when(ts: float) -> str:
    utc = datetime.fromtimestamp(ts, timezone.utc)
    return f"{utc:%Y-%m-%d %H:%M} UTC ({utc.astimezone(RIYADH):%H:%M} Riyadh)"


# --- checks --------------------------------------------------------------------------------------


def fetch(url: str) -> tuple[bool, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "alphacouncil-monitor/1"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body, status = r.read(500_000), r.status
    except urllib.error.HTTPError as exc:
        return False, f"{url} answered HTTP {exc.code}", b""
    except urllib.error.URLError as exc:
        return False, f"{url}: {exc.reason}", b""
    except (OSError, ValueError) as exc:  # timeouts while reading, broken connections
        return False, f"{url}: {type(exc).__name__}: {exc}", b""
    ms = round((time.monotonic() - start) * 1000)
    if status != 200:
        return False, f"{url} answered HTTP {status}", body
    return True, f"{url} answered 200 in {ms} ms", body


def check_site() -> list[tuple[str, Result]]:
    ok, detail, _ = fetch(HOME_URL)
    out = [("site:home", Result("alphacouncil.tech/home", ok, detail, logs=None if ok else "acp-prod-web"))]
    ok, detail, body = fetch(HEALTH_URL)
    market = Result("market data", None, "unknown: the health check did not answer")
    if ok:
        try:
            health = json.loads(body)
        except ValueError:
            health = {}
        if not isinstance(health, dict) or health.get("status") != "ok":
            ok, detail = False, f"{HEALTH_URL} answered 200 without status \"ok\""
        else:
            md = str(health.get("market_data", ""))
            market = Result("market data", md == "ok", f"the health check reports market data: {md}")
    out.append(("site:health", Result("alphacouncil.tech/api/v1/health", ok, detail, logs=None if ok else "acp-prod-api")))
    out.append(("market-data", market))
    return out


def check_service(unit: str, state: dict, now: float) -> Result:
    p = unit_props(f"{unit}.service", "ActiveState", "SubState", "Result", "NRestarts")
    restarts = int(p.get("NRestarts") or 0)
    # NRestarts counts automatic restarts and starts again from 0 when someone restarts the
    # unit (a deploy), so only its growth within the window counts.
    samples = [s for s in state.setdefault("restarts", {}).get(unit, []) if s[0] >= now - RESTART_WINDOW and s[1] <= restarts]
    samples.append([now, restarts])
    state["restarts"][unit] = samples
    looped = restarts - samples[0][1]
    if p.get("ActiveState") != "active":
        detail = f"{unit} is {p.get('ActiveState')} ({p.get('SubState')}), last result {p.get('Result')}"
        return Result(unit, False, detail, logs=unit)
    if looped >= RESTARTS_MAX:
        return Result(unit, False, f"{unit} restarted by itself {looped} times in the last 15 minutes", logs=unit)
    return Result(unit, True, f"{unit} is active")


def billing_runs(state: dict) -> tuple[list[tuple[float, dict[str, int]]], str | None]:
    """The renewal runs logged since the last round, and the journal position after them. The
    first round only notes where the journal ends: past runs are not news."""
    cursor = state.get("billing_cursor")
    first = not cursor
    args = ["journalctl", "-u", f"{BILLING}.service", "-o", "json", "--no-pager"]
    if first:
        args += ["-n", "1"]
    elif cursor:
        args += ["--after-cursor", cursor]
    entries = [json.loads(line) for line in run(*args).splitlines() if line.strip()]
    new_cursor = entries[-1]["__CURSOR"] if entries else cursor
    if first:
        return [], new_cursor
    found = []
    for e in entries:
        msg = e.get("MESSAGE")
        if isinstance(msg, list):  # journald hands non-UTF-8 messages over as bytes
            msg = bytes(msg).decode("utf-8", "replace")
        m = COUNTS.search(msg or "")
        if m:
            ts = int(e.get("__REALTIME_TIMESTAMP", "0")) / 1e6
            found.append((ts, dict(zip(COUNT_NAMES, map(int, m.groups())))))
    return found, new_cursor


def check_job(unit: str, label: str, optional: bool = False) -> list[tuple[str, Result]]:
    """A job a timer starts: its last run exited 0, and the timer is active. An optional job
    is skipped until its timer is installed."""
    timer = unit_props(f"{unit}.timer", "LoadState", "ActiveState")
    if optional and timer.get("LoadState") != "loaded":
        return [(f"job:{unit}", Result(f"{label} job", None, f"{unit}.timer is not installed"))]
    job = unit_props(f"{unit}.service", "ActiveState", "Result", "ExecMainStatus", "ExecMainExitTimestamp")
    if job.get("ActiveState") in ("activating", "deactivating"):
        res = Result(f"{label} job", None, "running now")
    elif job.get("Result") != "success" or job.get("ActiveState") == "failed":
        detail = (f"the last run of {unit}.service ended with result {job.get('Result')} "
                  f"(exit status {job.get('ExecMainStatus')}) at {job.get('ExecMainExitTimestamp') or 'unknown time'}")
        res = Result(f"{label} job", False, detail, logs=f"{unit}.service")
    else:
        res = Result(f"{label} job", True, "the last run exited 0")
    return [(f"job:{unit}", res), (f"timer:{unit}", Result(f"{label} timer", timer.get("ActiveState") == "active",
                                                           f"{unit}.timer is {timer.get('ActiveState')}"))]


def check_billing(state: dict) -> tuple[list[tuple[str, Result]], list[tuple[str, str]], str | None]:
    out = check_job(BILLING, "Pro renewals")
    runs, cursor = billing_runs(state)
    events = []
    for ts, c in runs:
        if c["failed"]:
            events.append(("Pro renewal declined", f"{c['failed']} Pro renewal charge(s) declined in the run at {when(ts)}. "
                           "The customer was emailed and keeps Pro; the charge is retried daily, and the plan ends after 3 tries."))
        if c["ended"]:
            events.append(("Pro plan ended", f"{c['ended']} Pro plan(s) ended in the run at {when(ts)}: cancelled and the "
                           "paid period over, 3 declined renewals, or complimentary Pro ran out. The saved card was deleted."))
    if runs:
        ts, c = runs[-1]
        detail = (f"Moyasar did not answer for {c['unreachable']} due renewal(s) in the run at {when(ts)}; "
                  "they are tried again every hour" if c["unreachable"] else f"the run at {when(ts)} reached Moyasar")
        out.append(("billing:unreachable", Result("Moyasar for renewals", not c["unreachable"], detail, need=1)))
    else:
        out.append(("billing:unreachable", Result("Moyasar for renewals", None, "no renewal run since the last round")))
    return out, events, cursor


def check_disks(state: dict) -> list[tuple[str, Result]]:
    keys = state.get("keys", {})
    seen: dict[int, str] = {}
    with open("/proc/self/mounts", encoding="utf-8") as f:
        for line in f:
            _, mount, fstype = line.split()[:3]
            if fstype not in ("ext2", "ext3", "ext4", "xfs", "btrfs", "zfs", "f2fs"):
                continue
            mount = mount.replace("\\040", " ")
            try:
                dev = os.stat(mount).st_dev
            except OSError:
                continue
            if dev not in seen or len(mount) < len(seen[dev]):  # bind mounts: keep the shortest path
                seen[dev] = mount
    out = []
    for mount in sorted(seen.values()):
        st = os.statvfs(mount)
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        free = st.f_bavail * st.f_frsize
        pct = math.ceil(used * 100 / (used + free)) if used + free else 0  # as df rounds it
        key = f"disk:{mount}"
        limit = DISK_CLEAR if keys.get(key, {}).get("alerted") else DISK_MAX
        out.append((key, Result(f"disk {mount}", pct <= limit, f"{mount} is {pct}% full ({free / 1e9:.1f} GB free)")))
    return out


def check_offsite() -> Result:
    name = "off-server backup copy"
    try:
        with open(OFFSITE_PULL, encoding="utf-8-sig") as f:
            report = json.load(f)
    except FileNotFoundError:
        return Result(name, None, f"no copy reported yet ({OFFSITE_PULL} does not exist)")
    at = datetime.strptime(report["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    age = time.time() - at
    detail = (f"the owner's computer last copied the backups at {when(at)}, {age / 86400:.1f} days ago "
              f"({report.get('files')} files, newest {report.get('newest') or 'unknown'})")
    if age > OFFSITE_MAX_AGE:
        detail += ('; turn that computer on and sign in: its task "AlphaCouncil backup copy" catches up '
                   "by itself, and its pull.log says what went wrong")
    return Result(name, age <= OFFSITE_MAX_AGE, detail)


def check_cert() -> Result:
    try:
        with socket.create_connection((SITE, 443), timeout=TIMEOUT) as sock:
            with ssl.create_default_context().wrap_socket(sock, server_hostname=SITE) as tls:
                cert = tls.getpeercert()
    except ssl.SSLCertVerificationError as exc:
        return Result("TLS certificate", False, f"the certificate {SITE} serves is not valid: {exc.verify_message}")
    except (OSError, ssl.SSLError) as exc:
        return Result("TLS certificate", False, f"TLS connection to {SITE}:443 failed: {type(exc).__name__}: {exc}")
    end = ssl.cert_time_to_seconds(cert["notAfter"])
    days = (end - time.time()) / 86400
    detail = f"the certificate for {SITE} expires on {when(end)}, in {days:.0f} days"
    return Result("TLS certificate", days >= CERT_MIN_DAYS, detail)


def gather(state: dict, now: float) -> tuple[dict[str, Result], list[tuple[str, str]], str | None]:
    """All checks. The journal position comes back as UNCHANGED when the billing check could not run."""
    results: dict[str, Result] = {}
    events: list[tuple[str, str]] = []
    cursor = UNCHANGED

    def guarded(group: str, fn):
        # A check that cannot run is itself a problem (alerted like any other), never a crash.
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            results[f"check:{group}"] = Result(f"{group} check", False, f"the check could not run: {type(exc).__name__}: {exc}")
            return None

    for key, res in guarded("site", check_site) or []:
        results[key] = res
    for unit in SERVICES:
        res = guarded(unit, lambda unit=unit: check_service(unit, state, now))
        if res:
            results[f"service:{unit}"] = res
    billing = guarded("billing", lambda: check_billing(state))
    if billing:
        pairs, events, cursor = billing
        results.update(pairs)
    for key, res in guarded("backup", lambda: check_job(BACKUP, "database backup", optional=True)) or []:
        results[key] = res
    res = guarded("offsite", check_offsite)
    if res:
        results["offsite"] = res
    for key, res in guarded("disk", lambda: check_disks(state)) or []:
        results[key] = res
    res = guarded("certificate", check_cert)
    if res:
        results["cert"] = res
    for group in ("site", *SERVICES, "billing", "backup", "offsite", "disk", "certificate"):
        if f"check:{group}" in state.get("keys", {}):  # it could not run before: now it did
            results.setdefault(f"check:{group}", Result(f"{group} check", True, "the check ran"))
    return results, events, cursor


# --- mail ----------------------------------------------------------------------------------------


def send_mail(config: dict, subject: str, body: str) -> None:
    smtp_cfg = config["smtp"]
    host, port = smtp_cfg["SMTP_HOST"], int(smtp_cfg.get("SMTP_PORT") or 587)
    msg = EmailMessage()
    msg["From"] = LINE_BREAK.sub(" ", smtp_cfg.get("SMTP_FROM") or f"AlphaCouncil <no-reply@{SITE}>")
    msg["To"] = ", ".join(LINE_BREAK.sub(" ", a) for a in config["to"])
    msg["Subject"] = LINE_BREAK.sub(" ", subject)
    msg["Date"] = formatdate()
    msg["Message-ID"] = make_msgid(domain=SITE)
    msg.set_content(redact(body, config["secrets"]))
    smtp = smtplib.SMTP_SSL(host, port, timeout=30) if port == 465 else smtplib.SMTP(host, port, timeout=30)
    with smtp:
        if port != 465:
            smtp.starttls(context=ssl.create_default_context())
        if smtp_cfg.get("SMTP_USER"):
            smtp.login(smtp_cfg["SMTP_USER"], smtp_cfg.get("SMTP_PASS", ""))
        smtp.send_message(msg)


def try_send(config: dict, state: dict, now: float, subject: str, body: str) -> str:
    """"sent", "capped" (the daily or monthly limit is reached) or "error"."""
    sent = [t for t in state.get("sent", []) if t > now - 30 * 86400]
    state["sent"] = sent
    day = sum(t > now - 86400 for t in sent)
    if day >= MAILS_PER_DAY or len(sent) >= MAILS_PER_MONTH:
        print(f"alert not emailed: {day} alerts in 24 hours and {len(sent)} in 30 days already (limits "
              f"{MAILS_PER_DAY} and {MAILS_PER_MONTH}); retried next round: {subject}")
        return "capped"
    try:
        send_mail(config, subject, body)
    except Exception as exc:  # noqa: BLE001
        # Never the message or the settings: an SMTP error can echo the login.
        print(f"alert not emailed: {type(exc).__name__} {getattr(exc, 'smtp_code', '')} (retried next round)", file=sys.stderr)
        return "error"
    sent.append(now)
    print(f"alert emailed: {subject}")
    return "sent"


def ping(config: dict, failed: bool, body: str) -> None:
    """Tells the outside check (PING_URL) that this round ran: PING_URL/fail when it had news that
    could not be emailed. Pings that stop are the outside check's own alarm."""
    if not config["ping"]:
        return
    url = config["ping"].rstrip("/") + ("/fail" if failed else "")
    req = urllib.request.Request(url, data=body.encode()[:10_000], headers={"User-Agent": "alphacouncil-monitor/1"})
    try:
        with urllib.request.urlopen(req, timeout=PING_TIMEOUT) as r:
            r.read(1000)
    except (OSError, ValueError) as exc:  # HTTP errors, timeouts, no network
        # Never the URL: it is the check's key.
        print(f"outside check not pinged: {type(exc).__name__} {getattr(exc, 'code', '')}", file=sys.stderr)


FOOTER = (
    "Checks run every 5 minutes on the server (acp-prod-monitor.timer). A problem is emailed when it\n"
    "starts and once more when it clears, never in between. What each check means, and how to change\n"
    "the recipient: docs/production.md, \"Monitoring\". Current state: prod-monitor.py status.\n"
)


def compose(problems, recovered, events, still, now: float) -> tuple[str, str]:
    titles = [f"Problem: {r.name}" for _, r in problems] + [f"Recovered: {r.name}" for _, r, _ in recovered]
    titles += [title for title, _ in events]
    subject = f"[{SITE}] {titles[0]}" + (f" (+{len(titles) - 1} more)" if len(titles) > 1 else "")
    lines: list[str] = []
    for _, r in problems:
        lines += [f"PROBLEM    {r.name}", f"  {r.detail}", ""]
    for _, r, since in recovered:
        lines += [f"RECOVERED  {r.name}", f"  {r.detail}" + (f" (reported {when(since)})" if since else ""), ""]
    for title, text in events:
        lines += [f"PRO BILLING  {title}", f"  {text}", ""]
    if still:
        lines.append("Still failing (already reported):")
        lines += [f"  {r.name}: {r.detail}" for r in still]
        lines.append("")
    for unit in dict.fromkeys(r.logs for _, r in problems if r.logs):
        lines += [f"Last lines of journalctl -u {unit} (secrets removed):", recent_logs(unit), ""]
    lines += ["--", f"Sent by acp-prod-monitor on {socket.gethostname()} at {when(now)}.", FOOTER]
    return subject, "\n".join(lines)


# --- commands ------------------------------------------------------------------------------------


def load_state() -> dict:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, STATE_FILE)


def check() -> int:
    config = load_config()  # first: a monitor that could not send an alert fails at once
    state, now = load_state(), time.time()
    results, events, cursor = gather(state, now)
    keys = state.setdefault("keys", {})
    problems, recovered = [], []
    for key, res in results.items():
        k = keys.setdefault(key, {"fails": 0, "alerted": False})
        k["name"], k["detail"] = res.name, res.detail
        if res.ok is None:
            continue
        if res.ok:
            k["fails"] = 0
            if k["alerted"]:
                recovered.append((key, res, k.get("alerted_at")))
        else:
            k["fails"] += 1
            if k["fails"] >= res.need and not k["alerted"]:
                problems.append((key, res))
    news = {key for key, _ in problems} | {key for key, _, _ in recovered}
    still = [results[key] for key, k in keys.items() if k["alerted"] and key not in news and key in results]

    failing = [r.name for r in results.values() if r.ok is False]
    summary = f"{len(results) - len(failing)} of {len(results)} checks ok" + (f"; failing: {', '.join(failing)}" if failing else "")
    print(summary)
    outcome = "sent"
    if problems or recovered or events:
        subject, body = compose(problems, recovered, events, still, now)
        outcome = try_send(config, state, now, subject, body)
        if outcome != "sent":
            why = "a mail limit is reached" if outcome == "capped" else "the mail server failed"
            summary += f"\nNot emailed because {why} (tried again every round): {subject}"
    if outcome == "sent":
        for key, _ in problems:
            keys[key].update(alerted=True, alerted_at=now)
        for key, _, _ in recovered:
            keys[key].update(alerted=False, alerted_at=None)
        if cursor is not UNCHANGED:
            state["billing_cursor"] = cursor
    # Not sent: the alert flags and the journal position stay, so the next round tries again.
    for key in [key for key, k in keys.items() if not k["alerted"] and not k["fails"]
                and (key.startswith("check:") or key not in results)]:
        del keys[key]  # a check that runs again, a disk that is gone
    save_state(state)
    ping(config, outcome != "sent", summary + "\n")  # last: a round that crashed before here sends no ping
    return 1 if outcome == "error" else 0


def status() -> int:
    state = load_state()
    results, events, _ = gather(json.loads(json.dumps(state)), time.time())
    for key, res in results.items():
        mark = {True: "ok     ", False: "FAILING", None: "-      "}[res.ok]
        alerted = " (alert sent)" if state.get("keys", {}).get(key, {}).get("alerted") else ""
        print(f"{mark} {res.name}: {res.detail}{alerted}")
    for title, text in events:
        print(f"event   {title}: {text}")
    sent = state.get("sent", [])
    day = sum(t > time.time() - 86400 for t in sent)
    print(f"alerts emailed: {day} in 24 hours (limit {MAILS_PER_DAY}), {len(sent)} in 30 days (limit {MAILS_PER_MONTH})")
    try:
        pinged = bool(read_env(MONITOR_ENV).get("PING_URL"))
    except OSError:
        pinged = False
    print("outside check: " + ("PING_URL is set, pinged at the end of every round" if pinged else f"none (no PING_URL in {MONITOR_ENV})"))
    return 0


def test() -> int:
    config = load_config()
    now = time.time()
    results, _, _ = gather({}, now)
    marks = {True: "ok     ", False: "FAILING", None: "-      "}
    snapshot = "\n".join(f"  {marks[r.ok]} {r.name}: {r.detail}" for r in results.values())
    body = (
        "This is a test of the alphacouncil.tech monitor. Nothing is wrong because of it.\n\n"
        "From now on this address gets an email when:\n"
        "  - alphacouncil.tech/home or /api/v1/health fails 2 checks in a row (5 minutes apart),\n"
        "  - acp-prod-api or acp-prod-web stops or keeps restarting,\n"
        "  - the hourly Pro renewals job fails, Moyasar cannot be reached for a renewal,\n"
        "    a renewal charge is declined, or a Pro plan ends,\n"
        "  - the nightly database backup fails (once its timer is installed),\n"
        "  - the off-server backup copy on the owner's computer is more than 3 days old,\n"
        f"  - a disk is over {DISK_MAX}% full or the certificate expires within {CERT_MIN_DAYS} days,\n"
        "and once more when each problem clears.\n\n"
        f"The checks right now:\n{snapshot}\n\n"
        f"--\nSent by acp-prod-monitor on {socket.gethostname()} at {when(now)}.\n{FOOTER}"
    )
    try:
        send_mail(config, f"[{SITE}] Test alert: monitoring is on", body)
    except Exception as exc:  # noqa: BLE001
        print(f"test alert not sent: {type(exc).__name__} {getattr(exc, 'smtp_code', '')}", file=sys.stderr)
        return 1
    print(f"test alert sent to {len(config['to'])} address(es) in {MONITOR_ENV}")
    return 0


if __name__ == "__main__":
    commands = {"check": check, "status": status, "test": test}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(__doc__.split("\n\n")[1])
        sys.exit(2)
    sys.exit(commands[sys.argv[1]]())
