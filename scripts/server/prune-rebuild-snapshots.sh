#!/usr/bin/env bash
# Keep the newest KEEP rebuild snapshots that hold screening.sqlite; remove every older one.
#
# Why this is safe: the nightly pipeline (run_rebuild_pipeline.py) writes one snapshot per run
# and reads back only the NEWEST one that holds screening.sqlite (_latest_prev_snapshot_screening),
# as the baseline for its row-count checks. Older snapshots are history nothing reads.
# Owner's decision 2026-11-06: keep 14, once now and nightly after (docs/release-readiness-2026-11-06.md, "Disk").
#
#   prune-rebuild-snapshots.sh --dry-run   # list what would go, change nothing
#   prune-rebuild-snapshots.sh             # remove it
#
# Installed on the server as /opt/alphacouncil/bin/prune-rebuild-snapshots.sh, run from root's crontab
# after the nightly pipeline and the morning publish window.
set -euo pipefail

DIR=/var/backups/alphacouncil/rebuild-snapshots
KEEP=14
NAME_RE='^rebuild-snapshot-[0-9]{8}-[0-9]{6}$'

dry=0
case "${1:-}" in
  --dry-run) dry=1 ;;
  "") ;;
  *) echo "usage: $0 [--dry-run]" >&2; exit 2 ;;
esac

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { echo "$(stamp) $*"; }

exec 9>/run/lock/prune-rebuild-snapshots.lock
flock -n 9 || { say "another prune is running; nothing done"; exit 0; }

[[ -d "$DIR" && ! -L "$DIR" ]] || { say "ERROR: $DIR is missing or a link; nothing done"; exit 1; }

# Every snapshot folder, oldest first (the name's timestamp sorts as time).
mapfile -t all < <(find "$DIR" -mindepth 1 -maxdepth 1 -type d -name 'rebuild-snapshot-*' -printf '%f\n' \
  | grep -E "$NAME_RE" | LC_ALL=C sort)
# The ones the pipeline could read: they hold screening.sqlite.
eligible=()
for d in "${all[@]}"; do
  if [[ -f "$DIR/$d/screening.sqlite" ]]; then eligible+=("$d"); fi
done

n=${#eligible[@]}
if (( n <= KEEP )); then
  say "$n snapshots hold screening.sqlite (keep $KEEP); nothing to remove"
  exit 0
fi

oldest_kept=${eligible[$((n - KEEP))]}
remove=()
for d in "${all[@]}"; do
  if [[ "$d" < "$oldest_kept" ]]; then remove+=("$d"); fi
done

tag=""; verb="freed"
if ((dry)); then tag="DRY RUN: "; verb="would free"; fi

say "${tag}${#all[@]} snapshots, $n hold screening.sqlite; keeping the newest $KEEP" \
    "(oldest kept $oldest_kept, newest ${eligible[$((n - 1))]}); removing ${#remove[@]}"
say "disk before: $(df -h --output=used,avail,pcent / | tail -1 | tr -s ' ')"

freed=0
for d in "${remove[@]}"; do
  [[ "$d" =~ $NAME_RE && "$d" < "$oldest_kept" ]] || { say "ERROR: refusing '$d'"; exit 1; }
  bytes=$(du -sb -- "$DIR/$d" | cut -f1)
  if ((dry)); then
    say "would remove $d ($bytes bytes)"
  else
    rm -rf --one-file-system -- "${DIR:?}/$d"
    say "removed $d ($bytes bytes)"
  fi
  freed=$((freed + bytes))
done

say "$verb $freed bytes; disk after: $(df -h --output=used,avail,pcent / | tail -1 | tr -s ' ')"
