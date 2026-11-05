"""Send Claude's latest output to ChatGPT (the Codex CLI, signed in with the owner's ChatGPT plan) for
review against the master plan, and save its answer.

    python -X utf8 scripts/review-loop/ask_chatgpt.py --title "what this output is" --output <file.md> [--timeout 1200]

Every call sends the same preamble and the whole of docs/review-loop/MASTER-PLAN.md, so the reviewer starts
from the original plan each time (a `codex exec` call keeps no memory of the last one). Codex runs in this
repo in a read-only sandbox, so it can open PROJECT.md, docs/ and the code to check the output against them,
and can change nothing. The prompt goes on stdin: as an argument, Windows cut it at the first newline.

The answer is saved as docs/review-loop/replies/<NN>-<slug>.md and one line is added to
docs/review-loop/LOG.md. Exit 0 = an answer ending "Response complete"; 2 = no usable answer.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOOP = ROOT / "docs" / "review-loop"

PREAMBLE = """You are the reviewer and director for the AlphaCouncil launch. Claude (the builder) has just produced the output below.
You run read-only inside the project's repository: open PROJECT.md, docs/ and the code to check what the output claims.

Stay on the master plan below. It is the owner's original plan and it does not change: do not drift from it,
do not add scope (no new features, panels, campaigns or tooling the plan does not ask for), and do not reopen
decisions the plan records as made. If the output itself drifted from the plan, say so.

Answer in exactly this form:

VERDICT: ACCEPT or FIX
ISSUES: numbered, each one concrete (file, line or claim) and checked against the repository; "none" if none.
DRIFT: whether the output stayed on the master plan, in one or two sentences.
NEXT STEP: the ONE next step that moves the site closest to the plan's final goal and that Claude may do now
  under the plan's rules (pre-approved work only). Say what to do, where, and why it is the most valuable.
DONE WHEN: how Claude proves that step is finished (a command, a check, a screenshot).
OWNER ITEMS: anything only the owner can do or approve that now matters most, ranked; "none" if none.

End with the line: Response complete
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--output", required=True, type=Path, help="Claude's output to review (markdown)")
    ap.add_argument("--timeout", type=int, default=1200)
    a = ap.parse_args()

    codex = shutil.which("codex")
    if not codex:
        print("NO REVIEWER: codex CLI not found", file=sys.stderr)
        return 2
    plan = (LOOP / "MASTER-PLAN.md").read_text(encoding="utf-8")
    output = a.output.read_text(encoding="utf-8")
    prompt = (f"{PREAMBLE}\n=== MASTER PLAN (docs/review-loop/MASTER-PLAN.md) ===\n{plan}\n"
              f"=== CLAUDE'S OUTPUT: {a.title} ===\n{output}\n")
    p = subprocess.run([codex, "exec", "--skip-git-repo-check", "-s", "read-only"], input=prompt,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=a.timeout, cwd=str(ROOT))
    out = p.stdout
    # codex exec prints progress, then "codex" and the final message, then "tokens used"; the final
    # message is repeated after it. Keep the last block that ends "Response complete".
    blocks = re.split(r"(?m)^codex\s*$", out)
    answer = blocks[-1] if len(blocks) > 1 else out
    answer = re.split(r"(?m)^tokens used\s*$", answer)[0].strip()
    if p.returncode != 0 or "Response complete" not in answer:
        print(f"NO USABLE ANSWER (exit {p.returncode})\n--- stdout tail ---\n{out[-3000:]}\n--- stderr tail ---\n{p.stderr[-2000:]}",
              file=sys.stderr)
        return 2

    replies = LOOP / "replies"
    replies.mkdir(parents=True, exist_ok=True)
    n = len(list(replies.glob("*.md"))) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:50]
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    path = replies / f"{n:02d}-{slug}.md"
    path.write_text(f"# Review {n:02d}: {a.title}\n\n{when}. Reviewer: ChatGPT via the Codex CLI, read-only in the repo.\n"
                    f"Output reviewed: `{a.output.name}`.\n\n{answer}\n", encoding="utf-8")
    verdict = (re.search(r"VERDICT:\s*(\w+)", answer) or [None, "?"])[1]
    log = LOOP / "LOG.md"
    if not log.exists():
        log.write_text("# Review loop log\n\nEach line: when, the output reviewed, ChatGPT's verdict, its reply.\n\n",
                       encoding="utf-8")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"- {when} — **{a.title}** — {verdict} — [{path.name}](replies/{path.name})\n")
    print(answer)
    print(f"\nsaved {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
