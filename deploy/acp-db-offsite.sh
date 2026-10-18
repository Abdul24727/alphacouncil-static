#!/usr/bin/env bash
# Off-server copy of the database backups (docs/production.md, "Backups"). Each dump in
# /var/backups/alphacouncil-platform is encrypted with the owner's passphrase (gpg, AES-256), and the
# ones the bucket lacks are uploaded to the S3-compatible bucket in
# /etc/alphacouncil-platform/backup-offsite.env. Installed as /usr/local/sbin/acp-db-offsite;
# acp-db-backup runs it after every backup once that file exists.
#
#   acp-db-offsite           # upload what is missing, then delete bucket copies past their keep time
#   acp-db-offsite --check   # fetch the newest acp_prod copy back, decrypt it, compare with the local dump
#
# The bucket keeps daily copies 15 days and weekly copies 60 days, counted from upload, so an
# emptied local directory does not empty the bucket. Prints file names only, never keys or contents.
set -euo pipefail

DIR="${ACP_BACKUP_DIR:-/var/backups/alphacouncil-platform}"
CONF="${ACP_OFFSITE_CONF:-/etc/alphacouncil-platform/backup-offsite.env}"
PREFIX=alphacouncil-platform
KEEP_DAILY=15d
KEEP_WEEKLY=60d

[[ -f "$CONF" ]] || { echo "off-server copy not configured: no $CONF" >&2; exit 1; }
[[ "$(stat -c %U:%a "$CONF")" == root:600 ]] || { echo "$CONF must be owned by root with mode 0600" >&2; exit 1; }
# KEY=value lines, read (never executed); trailing spaces, a Windows line end and surrounding quotes
# are dropped. Comments go on lines of their own.
conf() { sed -n "s/^$1=//p" "$CONF" | tail -1 | sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"; }
for v in S3_ENDPOINT S3_REGION S3_BUCKET S3_ACCESS_KEY_ID S3_SECRET_ACCESS_KEY BACKUP_PASSPHRASE; do
  [[ -n "$(conf "$v")" ]] || { echo "$CONF: $v is missing or empty" >&2; exit 1; }
done

# rclone takes the bucket's settings from the environment (no rclone.conf, nothing on a command line).
export RCLONE_CONFIG_OFFSITE_TYPE=s3 RCLONE_CONFIG_OFFSITE_PROVIDER=Other
export RCLONE_CONFIG_OFFSITE_ENDPOINT="$(conf S3_ENDPOINT)" RCLONE_CONFIG_OFFSITE_REGION="$(conf S3_REGION)"
export RCLONE_CONFIG_OFFSITE_ACCESS_KEY_ID="$(conf S3_ACCESS_KEY_ID)"
export RCLONE_CONFIG_OFFSITE_SECRET_ACCESS_KEY="$(conf S3_SECRET_ACCESS_KEY)"
# A key limited to one bucket may not create buckets: never try.
export RCLONE_CONFIG_OFFSITE_NO_CHECK_BUCKET=true
remote="${ACP_OFFSITE_REMOTE:-offsite:$(conf S3_BUCKET)/$PREFIX}"   # ACP_OFFSITE_REMOTE: a local directory, for tests
rc() { rclone --config /dev/null --stats 0 "$@" < /dev/null; }

umask 077
export GNUPGHOME="$(mktemp -d)"
work="$(mktemp -d)"
trap 'rm -rf -- "$GNUPGHOME" "$work"' EXIT
# The passphrase reaches gpg through a pipe on fd 3, not through a command line.
gpg_() { gpg --batch --quiet --yes --pinentry-mode loopback --no-symkey-cache --passphrase-fd 3 "$@" 3< <(conf BACKUP_PASSPHRASE) < /dev/null; }

if [[ "${1:-}" == "--check" ]]; then
  local_dump="$(ls -1t "$DIR"/daily/acp_prod-*.dump | head -1)"
  rel="daily/$(basename "$local_dump").gpg"
  rc copyto "$remote/$rel" "$work/check.gpg"
  gpg_ --decrypt -o "$work/check.dump" "$work/check.gpg"
  cmp -s "$local_dump" "$work/check.dump" || { echo "$rel does not decrypt to the local dump" >&2; exit 1; }
  tables="$(docker exec -i acp-postgres pg_restore --list < "$work/check.dump" | grep -c ' TABLE DATA ')"
  echo "check ok: $rel came back, decrypted with the passphrase, matches the local dump byte for byte ($tables tables of data)"
  exit 0
fi

have="$(rc lsf -R --files-only "$remote" 2>/dev/null || true)"
uploaded=0
# Only files younger than the bucket's keep time, or a copy deleted there would be sent again.
while IFS= read -r f; do
  rel="${f#"$DIR"/}.gpg"
  grep -qxF "$rel" <<<"$have" && continue
  gpg_ --symmetric --cipher-algo AES256 -o "$work/upload.gpg" "$f"
  rc copyto "$work/upload.gpg" "$remote/$rel"
  rm -f "$work/upload.gpg"
  echo "uploaded $rel"
  uploaded=$((uploaded + 1))
done < <(find "$DIR/daily" -type f \( -name '*.dump' -o -name '*.sql' \) -mtime -14 | sort
         find "$DIR/weekly" -type f -name '*.dump' -mtime -59 | sort)

rc delete --min-age "$KEEP_DAILY" "$remote/daily"
rc delete --min-age "$KEEP_WEEKLY" "$remote/weekly"
total="$(rc lsf -R --files-only "$remote" | wc -l)"
printf '%s\n' "$(date -u +%FT%TZ)" "$uploaded uploaded, $total in the bucket" > "$DIR/LAST_OFFSITE_OK"
echo "off-server ok: $uploaded uploaded, $total in the bucket"
