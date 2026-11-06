"""SUPERSEDED - do not run. Kept as the record of what was tried (2026-11-03).

The server harvest it performs was blocked: Argaam answers the Arabic statement pages with a "Human
Verification" bot challenge, which is not to be got around. The owner then ruled out signing in to
Argaam anywhere else, because a second sign-in signs the nightly's single session out. Argaam's Arabic
for the Saudi lines comes instead from the Gulf statement pages the nightly already saves in Arabic,
with no request to Argaam: see pair_from_gulf.py and docs/arabic-statement-labels-2026-11-03.md.

As first written:

One-off: save Argaam's ARABIC financial-statement page for every Tadawul ticker, so that
pair_labels.py can read Argaam's own Arabic name for each statement line.

Why one-off and not the nightly: the nightly harvest reads Argaam's /en/ pages for Saudi companies
(main_patched2026_with_sectors.py, scrape_financial_statements), so Argaam's Arabic wording for the
Saudi lines is nowhere on the server. The wording is Argaam's fixed template, so it is harvested once
(and again only if Argaam adds lines), into a folder of its own. Nothing the nightly reads or writes
is touched: the harvest runs, the databases and the session file are only read.

It uses the nightly's signed-in Argaam session READ-ONLY (the storage_state JSON that the session
gate `_export_auth_state.py` refreshes each night): it loads it into a fresh browser context and never
writes it back. One page at a time with a pause between pages.

Runs on the server with the pipeline's Python (Playwright is installed there):

  PY=/opt/alphacouncil/pipeline-venv/bin/python
  $PY harvest_ar_statements.py --dry-run                       # the URLs it would open; no browser
  $PY harvest_ar_statements.py --tickers 2222,1120,8010        # the pilot: three templates
  $PY harvest_ar_statements.py                                 # all Tadawul tickers (~269)

Refuses to start while the nightly scrape or rebuild is running, or between 23:30 and 03:00 UTC.
Stops after three pages in a row come back without a statement grid (a lapsed session or a block).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_URL = "https://www.argaam.com"
UNIVERSE = Path("/opt/alphacouncil/backend/argaam/default_universe")
SESSION = UNIVERSE / "_auth_state.json"
ROW = re.compile(r'<tr[^>]+id="tr\d+"')
KSA_PATH = re.compile(r"^/en/tadawul/tasi/([^/]+)/overview/?$")


def slug_of(ticker_dir: Path) -> str | None:
    """The company's Argaam slug, from the newest harvest run that recorded its company path."""
    for run in sorted((ticker_dir / "harvest_runs").glob("run_*"), reverse=True):
        f = run / "discovery_links.json"
        if not f.exists():
            continue
        try:
            path = json.loads(f.read_text(encoding="utf-8")).get("company_path") or ""
        except (OSError, ValueError):
            continue
        m = KSA_PATH.match(path)
        if m:
            return m.group(1)
    return None


def nightly_busy() -> str | None:
    now = dt.datetime.now(dt.timezone.utc)
    if now.hour >= 23 and now.minute >= 30 or now.hour < 3:
        return f"inside the nightly window (now {now:%H:%M} UTC; allowed 03:00-23:30)"
    r = subprocess.run(["pgrep", "-af", "nightly_pipeline|run_parallel_universe|run_rebuild_pipeline"],
                       capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if "harvest_ar_statements" not in ln and "pgrep" not in ln]
    return f"the nightly is running: {lines[0][:120]}" if lines else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Save Argaam's Arabic statement page per Tadawul ticker.")
    ap.add_argument("--out", type=Path, default=Path("/root/argaam-ar-statements"))
    ap.add_argument("--tickers", default="", help="comma list of codes (2222,1120) for a pilot; empty = all")
    ap.add_argument("--delay", type=float, default=4.0, help="seconds between pages")
    ap.add_argument("--dry-run", action="store_true", help="print the URLs; open no browser")
    ap.add_argument("--redo", action="store_true", help="fetch again even if a page is already saved")
    a = ap.parse_args()

    want = {t.strip() for t in a.tickers.split(",") if t.strip()}
    todo = []
    for d in sorted(p for p in UNIVERSE.iterdir() if p.is_dir() and p.name.endswith("_TADAWUL")):
        code = d.name[: -len("_TADAWUL")]
        if want and code not in want:
            continue
        slug = slug_of(d)
        todo.append((d.name, f"{BASE_URL}/ar/tadawul/tasi/{slug}/financial-statement" if slug else None))
    no_slug = [t for t, u in todo if u is None]
    todo = [(t, u) for t, u in todo if u]
    print(f"tickers: {len(todo)} with a URL, {len(no_slug)} without a recorded company path {no_slug[:10]}")

    if a.dry_run:
        for t, u in todo[:400]:
            print(t, u)
        return 0
    busy = nightly_busy()
    if busy:
        print(f"REFUSING: {busy}")
        return 2
    if not SESSION.exists():
        print(f"REFUSING: no session file at {SESSION}")
        return 2

    from playwright.sync_api import sync_playwright  # only on a real run

    a.out.mkdir(parents=True, exist_ok=True)
    saved, failed, skipped, in_a_row = [], [], [], 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(SESSION), locale="ar-SA")  # read, never written back
        page = ctx.new_page()
        for i, (t, url) in enumerate(todo, 1):
            target = a.out / f"{t}.html"
            if target.exists() and not a.redo and ROW.search(target.read_text(encoding="utf-8", errors="replace")):
                skipped.append(t)
                continue
            html, err = "", ""
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_selector('tr[id^="tr"] td[data-fieldname]', timeout=30_000)
                page.wait_for_timeout(1500)
                html = page.content()
            except Exception as e:  # noqa: BLE001 - recorded and counted, then the next ticker
                err = f"{type(e).__name__}: {str(e)[:160]}"
                try:
                    html = page.content()
                except Exception:  # noqa: BLE001
                    html = ""
            n = len(ROW.findall(html))
            if n:
                target.write_text(html, encoding="utf-8")
                saved.append((t, n))
                in_a_row = 0
                print(f"[{i}/{len(todo)}] {t}: {n} rows  {page.url[:110]}", flush=True)
            else:
                failed.append((t, err or "no statement rows (signed out, blocked or not loaded)"))
                in_a_row += 1
                print(f"[{i}/{len(todo)}] {t}: NO ROWS  {err[:120]}", flush=True)
                if in_a_row >= 3:
                    print("STOPPING: three pages in a row without a statement grid")
                    break
            time.sleep(a.delay)
        browser.close()

    summary = {"saved": len(saved), "skipped_already_saved": len(skipped), "failed": failed, "no_slug": no_slug,
               "out": str(a.out), "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    (a.out / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
