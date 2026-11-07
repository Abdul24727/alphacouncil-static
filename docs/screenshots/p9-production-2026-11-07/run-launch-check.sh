#!/usr/bin/env bash
# Step 10's signed-out checks on production after the P9 release (ea51de796c), 2026-11-07.
# The same scripts and settings as docs/screenshots/launch-2026-11-07/run-launch-check.sh. GETs only: no account, no
# session, no form. web/ is byte-identical to the last release, so only the text outputs are kept here; the
# screenshots go to a scratch folder outside the repository.
set -u
D=/c/projects/alphacouncil-platform/docs/screenshots/p9-production-2026-11-07/launch-check
S=${SHOTS:?set SHOTS to a scratch folder outside the repository}
B=https://alphacouncil.tech
mkdir -p "$D" "$S"
cd /c/projects/alphacouncil-platform/web
run() { local n="$1"; shift; "$@" > "$D/$n.txt" 2>&1; local e=$?; echo "[exit $e]" >> "$D/$n.txt"; echo "$n exit $e | $(grep -v '^\[exit' "$D/$n.txt" | grep -v '^\s*$' | tail -1 | cut -c1-160)"; }
echo "run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC') against $B"
run check-seo env BASE_URL=$B SHOTS_DIR="$S/seo" node scripts/check-seo.mjs
run check-arabic env BASE_URL=$B WIDTHS=1440,390 node scripts/check-arabic.mjs
run check-advisors-visitor env BASE_URL=$B VISITOR=1 OUT="$S/advisors-visitor" node scripts/check-advisors.mjs
run check-data-fixes env BASE_URL=$B SHOTS_DIR="$S/data-fixes" SWEEP=1 node scripts/check-data-fixes.mjs
run pages env BASE=$B OUT="$S/pages" node ../docs/screenshots/launch-2026-11-07/page-shots.mjs
echo "done $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"
