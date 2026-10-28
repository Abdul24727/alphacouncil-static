#!/usr/bin/env bash
# Build the read-only LLM Council verification package for independent review.
#
#   scripts/verification-package.sh [OUTDIR]     # default: the system temp directory
#
# A script rather than a sequence of commands because the first package, built by hand on
# 2026-10-28, shipped a MANIFEST.txt that listed a hash for itself - taken while the file was being
# written, so it could never match. An independent reviewer found it. Here the manifest is built from
# a file list that excludes itself, by construction, and the archive's own hash is printed separately
# rather than put inside the archive.
#
# Never includes: .env files, keys, tokens, database credentials, subscriber or customer data,
# payment configuration, backups. The scan at the end fails the build if anything secret-shaped
# survives, so an accidental inclusion stops the package rather than shipping in it.
set -euo pipefail

# python3 on Linux and macOS, python on a Windows checkout. Each candidate is EXECUTED rather than
# just looked up: on Windows `command -v python3` finds a Microsoft Store app-execution alias that
# exists and then refuses to run, which failed this build half way through with the files staged.
PY=""
for c in python3 python py; do
  if "$c" -c "import sys; sys.exit(0)" >/dev/null 2>&1; then PY="$c"; break; fi
done
[[ -n "$PY" ]] || { echo "no working python found (tried python3, python, py)" >&2; exit 1; }
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
DATE="$(date '+%Y-%m-%d')"
NAME="alphacouncil-council-verification-$DATE"
OUT="${1:-${TMPDIR:-/tmp}}"
PKG="$OUT/$NAME"

rm -rf "$PKG"
mkdir -p "$PKG"/{code/api/app/debate,code/api/app/advisors,code/api/app/copilot,code/api/eval,code/api/tests,code/deploy,data/packs,results,docs}

echo "== code"
cp api/app/debate/*.py        "$PKG/code/api/app/debate/"
cp api/eval/*.py              "$PKG/code/api/eval/"
cp api/app/advisors/*.md      "$PKG/code/api/app/advisors/"
cp api/app/settings.py        "$PKG/code/api/app/"
# The whole Copilot package, not just openai_compat: tests/test_copilot.py imports
# app.copilot.context, and the first package shipped the test without it.
cp api/app/copilot/*.py       "$PKG/code/api/app/copilot/"
cp api/pyproject.toml api/uv.lock "$PKG/code/api/"
cp api/tests/test_debate.py api/tests/test_copilot.py api/tests/test_eval_score.py \
   api/tests/test_eval_budget.py "$PKG/code/api/tests/"
cp deploy/api.env.example     "$PKG/code/deploy/"

echo "== data and results"
cp docs/eval/packs/*.json     "$PKG/data/packs/"
cp docs/eval/results.jsonl docs/eval/planted-partial.jsonl "$PKG/results/"
for extra in docs/eval/exploratory-2026-10-27.jsonl docs/eval/rescore.py; do
  [[ -f "$extra" ]] && cp "$extra" "$PKG/results/"
done

echo "== docs"
for d in council-test-design-2026-10-27.md council-test-run-2026-10-27.md \
         council-test-design-2026-10-28.md council-review-response-2026-10-28.md \
         council-review-response-2026-10-28-round2.md council-review-response-2026-10-28-round3.md \n         beta-advisors-2026-10-27.md; do
  [[ -f "docs/$d" ]] && cp "docs/$d" "$PKG/docs/"
done
[[ -f docs/eval/README.md ]] && cp docs/eval/README.md "$PKG/docs/eval-README.md"

# The package's own front matter is versioned in the repo, not written by hand each time.
cp docs/verification/README.md docs/verification/PROVENANCE.md "$PKG/"

find "$PKG" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

# The one login target that appears in the fault record. Redacted, not dropped: the record is the
# honest disclosure of known defects and a reviewer should have it.
if [[ -f "$PKG/docs/beta-advisors-2026-10-27.md" ]]; then
  "$PY" - "$PKG/docs/beta-advisors-2026-10-27.md" <<'PY'
import re, sys
from pathlib import Path
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = re.sub(r"\b[a-z_][a-z0-9_.-]*@alphacouncil\.tech\b",
           lambda m: "<user>@<host>  [login target redacted for this package]"
           if not m.group(0).startswith("no-reply@") else m.group(0), s)
p.write_text(s, encoding="utf-8", newline="\n")
PY
fi

echo "== commit manifest"
# Asked for by the second review round: the exact commits, path by path, with anything that went in
# unintentionally marked rather than buried.
{ echo "Commits behind this package, newest first. Branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "HEAD: $(git rev-parse HEAD)"
  echo
  git log --format='%h  %ad  %s' --date=short -12
  echo
  echo "Files changed per commit (A added, M modified):"
  for c in $(git log --format=%h -8); do
    echo
    echo "  $c  $(git log -1 --format=%s "$c")"
    git show --stat --format="" --name-status "$c" | sed 's/^/    /'
  done
  echo
  echo "UNINTENTIONAL INCLUSION, identified separately:"
  echo "  718eca0  scripts/set-backup-bucket.sh"
  echo "    Not part of the benchmark change. Staged by a 'git add -A scripts' while adding"
  echo "    scripts/verification-package.sh; it had been untracked in the working tree beforehand."
  echo "    Holds no secret values: every credential is read at runtime and unset after use."
  echo "    Committing on this branch is pre-approved by PROJECT.md section 4. Pushing is NOT, and"
  echo "    this commit has not been pushed, so the inclusion is fully reversible."
  echo "    See docs/council-review-response-2026-10-28-round2.md section 5."
} > "$PKG/MANIFEST-COMMITS.txt"

echo "== manifest"
# Built from a list that EXCLUDES the manifest: a file cannot hash itself.
( cd "$PKG"
  SHA="$(cd "$ROOT" && git rev-parse HEAD)"
  { echo "AlphaCouncil LLM Council verification package"
    echo "Prepared $DATE. Repository HEAD at packaging time: $SHA"
    echo "Benchmark engine commit: d5c28fb (release d5c28fb48b). See PROVENANCE.md."
    echo
    echo "This manifest lists every other file. It deliberately does NOT list itself: the first"
    echo "package included a self-entry whose hash was taken mid-write and could never match."
    echo "The archive's own SHA-256 is printed by this script and travels outside the archive."
    echo
    echo "SHA-256                                                           bytes  file"
    find . -type f ! -name MANIFEST.txt | sort | while read -r f; do
      printf "%s  %8d  %s\n" "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c%s "$f")" "${f#./}"
    done
    echo
    printf "files: %d (excluding this manifest)   total bytes: %d\n" \
      "$(find . -type f ! -name MANIFEST.txt | wc -l)" \
      "$(find . -type f ! -name MANIFEST.txt -printf '%s\n' | awk '{s+=$1} END {print s+0}')"
  } > MANIFEST.txt )

echo "== secret scan (fails the build on a hit)"
"$PY" - "$PKG" <<'PY'
import re, sys
from pathlib import Path
PAT = {
 "model key": re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
 "bearer token": re.compile(r"[Bb]earer\s+[A-Za-z0-9_\-.]{16,}"),
 "aws key id": re.compile(r"AKIA[0-9A-Z]{16}"),
 "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
 "db url with password": re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^\s:]+:[^\s@]{4,}@"),
 "assigned secret": re.compile(r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
 "jwt": re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\."),
 "login target": re.compile(r"\b[a-z_][a-z0-9_\-]*@(?!example)[a-z0-9.\-]+\.[a-z]{2,}\b"),
}
ALLOW = {"no-reply@alphacouncil.tech", "noreply@anthropic.com"}
root = Path(sys.argv[1])
hits = 0
for f in sorted(root.rglob("*")):
    if not f.is_file():
        continue
    text = f.read_text(encoding="utf-8", errors="replace")
    for name, pat in PAT.items():
        for m in pat.finditer(text):
            s = m.group(0)
            if s in ALLOW:
                continue
            if name == "assigned secret" and f.name in ("MANIFEST.txt", "uv.lock"):
                continue
            hits += 1
            print(f"  HIT {f.relative_to(root)}:{text[:m.start()].count(chr(10)) + 1} [{name}] {s[:70]}")
if hits:
    sys.exit(f"\n{hits} secret-shaped strings found: NOT packaging")
print(f"  clean: {sum(1 for f in root.rglob('*') if f.is_file())} files scanned")
PY

echo "== archive"
tar -czf "$OUT/$NAME.tar.gz" -C "$OUT" "$NAME"
rm -rf "$OUT/verify-$NAME"; mkdir -p "$OUT/verify-$NAME"
tar -xzf "$OUT/$NAME.tar.gz" -C "$OUT/verify-$NAME"
diff -rq "$PKG" "$OUT/verify-$NAME/$NAME" >/dev/null && echo "  archive matches the staged package"
rm -rf "$OUT/verify-$NAME"

echo
echo "$OUT/$NAME.tar.gz"
echo "sha256: $(sha256sum "$OUT/$NAME.tar.gz" | cut -d' ' -f1)"
