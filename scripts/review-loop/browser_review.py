"""The review loop through ChatGPT in the owner's browser (owner's rule, 2026-11-07): chatgpt.com in the
owner's Chrome, with the max model picked in the model menu, in place of the Codex CLI (`ask_chatgpt.py`),
whose usage limit stopped the loop that night. The web plan does not spend the CLI's credits.

Two steps, with the browser in between (Claude drives it through Claude in Chrome):

    python -X utf8 scripts/review-loop/browser_review.py prompt --title "..." --output <file.md> [--attach <file> ...]
        Writes the prompt file - the same reviewer preamble and the whole of MASTER-PLAN.md as before, then the
        output - and prints its path and the list of files to attach. The web reviewer cannot open the
        repository, so every file the output relies on is attached beside the prompt file.

    python -X utf8 scripts/review-loop/browser_review.py save --title "..." --output <file.md> --reply <reply.txt> --model "<as shown>"
        Saves ChatGPT's answer as docs/review-loop/replies/<NN>-<slug>.md and adds one line to
        docs/review-loop/LOG.md, as ask_chatgpt.py did. Exit 2 if the answer does not end "Response complete".
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOOP = ROOT / "docs" / "review-loop"
PROMPTS = LOOP / "browser-prompts"
# The browser can upload only files inside the Claude session's own folders, and the repository is not one of
# them, so the prompt and its attachments are copied here first. It is emptied each time and kept nowhere else.
STAGE = Path(r"C:\AlphaCouncil-Staging\review-upload")

PREAMBLE = """You are the reviewer and director for the AlphaCouncil launch. Claude (the builder) has just produced the output below.
You cannot open the project's repository from here. The files the output relies on are attached to this message beside
this prompt, each under its file name; the list below gives each one's path in the repository. Read them to check what
the output claims, and run code on them if that helps (a script that opens "../x" means the attached file x).
If a claim depends on a file that is not attached, say so rather than assuming it.

Stay on the master plan below. It is the owner's original plan and it does not change: do not drift from it,
do not add scope (no new features, panels, campaigns or tooling the plan does not ask for), and do not reopen
decisions the plan records as made. If the output itself drifted from the plan, say so.

Answer in exactly this form:

VERDICT: ACCEPT or FIX
ISSUES: numbered, each one concrete (file, line or claim) and checked against the attached files; "none" if none.
DRIFT: whether the output stayed on the master plan, in one or two sentences.
NEXT STEP: the ONE next step that moves the site closest to the plan's final goal and that Claude may do now
  under the plan's rules (pre-approved work only). Say what to do, where, and why it is the most valuable.
DONE WHEN: how Claude proves that step is finished (a command, a check, a screenshot).
OWNER ITEMS: anything only the owner can do or approve that now matters most, ranked; "none" if none.

End with the line: Response complete
"""


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]


def prompt(a: argparse.Namespace) -> int:
    plan = (LOOP / "MASTER-PLAN.md").read_text(encoding="utf-8")
    output = a.output.read_text(encoding="utf-8")
    attached = []
    for f in a.attach:
        p = Path(f).resolve()
        if not p.is_file():
            print(f"NOT A FILE: {f}", file=sys.stderr)
            return 2
        attached.append(p.relative_to(ROOT).as_posix())
    extra = []
    for f in a.extra:
        p = Path(f).resolve()
        if not p.is_file():
            print(f"NOT A FILE: {f}", file=sys.stderr)
            return 2
        extra.append(p)
    listing = "\n".join(f"- {x}" for x in attached) or "- (none)"
    if extra:
        listing += "\n" + "\n".join(f"- {p.name} (made for this review, not in the repository: a diff or a"
                                    " command transcript)" for p in extra)
    text = (f"{PREAMBLE}\n=== FILES ATTACHED BESIDE THIS PROMPT (repository paths) ===\n{listing}\n\n"
            f"=== MASTER PLAN (docs/review-loop/MASTER-PLAN.md) ===\n{plan}\n"
            f"=== CLAUDE'S OUTPUT: {a.title} ===\n{output}\n")
    PROMPTS.mkdir(parents=True, exist_ok=True)
    path = PROMPTS / f"{a.output.stem}.prompt.md"
    path.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    names = [Path(x).name for x in attached] + [p.name for p in extra]
    if len(set(names)) != len(names):
        print("TWO ATTACHMENTS SHARE A FILE NAME; rename one", file=sys.stderr)
        return 2
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    shutil.copy2(path, STAGE / path.name)
    for x in attached:
        shutil.copy2(ROOT / x, STAGE / Path(x).name)
    for p in extra:
        shutil.copy2(p, STAGE / p.name)
    print(f"prompt {path.relative_to(ROOT)}; staged for upload in {STAGE}:")
    for f in sorted(STAGE.iterdir()):
        print(f)
    return 0


def save(a: argparse.Namespace) -> int:
    answer = a.reply.read_text(encoding="utf-8").strip()
    if "Response complete" not in answer:
        print("NO USABLE ANSWER: it does not end 'Response complete'", file=sys.stderr)
        return 2
    answer = answer[: answer.rindex("Response complete") + len("Response complete")]
    replies = LOOP / "replies"
    replies.mkdir(parents=True, exist_ok=True)
    n = len(list(replies.glob("*.md"))) + 1
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    path = replies / f"{n:02d}-{_slug(a.title)}.md"
    path.write_text(f"# Review {n:02d}: {a.title}\n\n{when}. Reviewer: ChatGPT on chatgpt.com in the owner's browser,"
                    f" model {a.model}, with the attached files.\nOutput reviewed: `{a.output.name}`.\n\n{answer}\n",
                    encoding="utf-8", newline="\n")
    verdict = (re.search(r"VERDICT:\s*(\w+)", answer) or [None, "?"])[1]
    with (LOOP / "LOG.md").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"- {when} — **{a.title}** — {verdict} — [{path.name}](replies/{path.name})\n")
    print(f"saved {path.relative_to(ROOT)} — VERDICT {verdict}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--title", required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--attach", nargs="*", default=[], help="repository files the output relies on")
    p.add_argument("--extra", nargs="*", default=[], help="files made for this review outside the repository")
    s = sub.add_parser("save")
    s.add_argument("--title", required=True)
    s.add_argument("--output", required=True, type=Path)
    s.add_argument("--reply", required=True, type=Path)
    s.add_argument("--model", required=True)
    a = ap.parse_args()
    return prompt(a) if a.cmd == "prompt" else save(a)


if __name__ == "__main__":
    sys.exit(main())
