#!/usr/bin/env bash
# Step 10's signed-out checks on production after the sector-standing release (026699b906), 2026-11-07.
# The same scripts and settings as docs/launch-check-2026-11-06.md. GETs only: no account, no session, no form.
set -u
D=/c/projects/alphacouncil-platform/docs/screenshots/launch-2026-11-07
B=https://alphacouncil.tech
cd /c/projects/alphacouncil-platform/web
run() { local n="$1"; shift; "$@" > "$D/$n.txt" 2>&1; local e=$?; echo "[exit $e]" >> "$D/$n.txt"; echo "$n exit $e | $(grep -v '^\[exit' "$D/$n.txt" | grep -v '^\s*$' | tail -1 | cut -c1-160)"; }
echo "run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC') against $B"
run check-seo env BASE_URL=$B SHOTS_DIR=../../docs/screenshots/launch-2026-11-07/seo node scripts/check-seo.mjs
run check-advisors-visitor env BASE_URL=$B VISITOR=1 OUT=../docs/screenshots/launch-2026-11-07/advisors-visitor node scripts/check-advisors.mjs
run check-data-fixes env BASE_URL=$B SHOTS_DIR=../../docs/screenshots/launch-2026-11-07/data-fixes SWEEP=1 node scripts/check-data-fixes.mjs
run pages env BASE=$B OUT=$D/pages node $D/page-shots.mjs
echo "done $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"
