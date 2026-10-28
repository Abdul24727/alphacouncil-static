#!/usr/bin/env bash
# Connect the nightly backups to the owner's bucket (docs/production.md, "Off-server copy").
# Asks for the bucket's four details, writes /etc/alphacouncil-platform/backup-offsite.env on the
# server (root-only), makes the encryption passphrase there on first use and shows it once, then
# uploads the backups and checks that one comes back. The details travel over ssh's input, never
# on a command line, and nothing here stores them on this computer.
#
#   bash scripts/set-backup-bucket.sh                     # run again to correct a detail; the passphrase stays
#   bash scripts/set-backup-bucket.sh --show-passphrase   # show the passphrase again
set -euo pipefail

HOST="${PROD_HOST:-root@alphacouncil.tech}"
CONF="${ACP_OFFSITE_CONF:-/etc/alphacouncil-platform/backup-offsite.env}"
ssh_() { ssh -o BatchMode=yes "$HOST" "$@"; }

if [[ "${1:-}" == "--show-passphrase" ]]; then
  ssh_ "sed -n 's/^BACKUP_PASSPHRASE=//p' $CONF"
  exit 0
fi

echo
echo "Connect the AlphaCouncil backups to your bucket."
echo "Copy each value from the Backblaze website, paste it here (right-click pastes) and press Enter."
echo
read -r -p "1/4  Endpoint, shown on the bucket (like s3.us-west-004.backblazeb2.com): " endpoint
read -r -p "2/4  Bucket name: " bucket
read -r -p "3/4  keyID: " keyid
read -r -s -p "4/4  applicationKey (it stays hidden while you paste it): " appkey
echo
# None of these values contains spaces: drop any that came with the paste.
endpoint="${endpoint//[[:space:]]/}" bucket="${bucket//[[:space:]]/}"
keyid="${keyid//[[:space:]]/}" appkey="${appkey//[[:space:]]/}"
host="${endpoint#https://}"; host="${host#http://}"; host="${host%%/*}"
case "$host" in
  s3.*.backblazeb2.com | s3.*.amazonaws.com) region="$(cut -d. -f2 <<<"$host")" ;;
  *.r2.cloudflarestorage.com) region=auto ;;
  *) read -r -p "     Region of the bucket: " region; region="${region//[[:space:]]/}" ;;
esac
for v in host bucket keyid appkey region; do
  [[ -n "${!v}" ]] || { echo "One of the values was empty. Nothing was changed; run this again." >&2; exit 1; }
done

# On the server: keep an existing passphrase (older uploads need it), or make one.
remote='set -euo pipefail
F="$1"; umask 077
new="$(mktemp "$(dirname "$F")/.backup-offsite.XXXXXX")"
cat > "$new"
pass="$({ sed -n "s/^BACKUP_PASSPHRASE=//p" "$F" 2>/dev/null || true; } | tail -1)"
if [[ -z "$pass" ]]; then
  pass="$(openssl rand -hex 16 | sed "s/..../&-/g; s/-$//")"
  echo "NEW $pass"
fi
echo "BACKUP_PASSPHRASE=$pass" >> "$new"
chown root:root "$new" && chmod 600 "$new" && mv "$new" "$F"'
out="$(printf 'S3_ENDPOINT=https://%s\nS3_REGION=%s\nS3_BUCKET=%s\nS3_ACCESS_KEY_ID=%s\nS3_SECRET_ACCESS_KEY=%s\n' \
         "$host" "$region" "$bucket" "$keyid" "$appkey" | ssh_ "bash -c $(printf %q "$remote") _ $CONF")"
unset appkey
echo "Saved on the server."

if [[ "$out" == NEW* ]]; then
  cat <<EOF

Your backup passphrase, made just now:

      ${out#NEW }

Save it now where you keep important passwords (a password manager, or written down and kept
somewhere safe). The backups in the bucket can only be opened with it, and if the server is ever
lost, its copy of the passphrase is lost too.
EOF
  read -r -p "Press Enter once it is saved... " _
fi

echo
echo "Uploading the backups to the bucket and checking that one comes back..."
if ssh_ "ACP_OFFSITE_CONF=$CONF acp-db-offsite && ACP_OFFSITE_CONF=$CONF acp-db-offsite --check"; then
  echo
  echo "Done. Every night's backup now also goes to your bucket, encrypted."
else
  echo
  echo "That did not work: a value is probably wrong (the message above says what the bucket answered)."
  echo "Run this again and paste the four values once more; the passphrase stays the same."
  exit 1
fi
