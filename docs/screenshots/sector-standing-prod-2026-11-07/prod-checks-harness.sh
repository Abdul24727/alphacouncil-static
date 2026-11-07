#!/usr/bin/env bash
# Read-only checks of production after the sector-standing release (026699b906), 2026-11-07.
# The live site is public, so its pages are read at https://alphacouncil.tech (GET only); the server is read over
# read-only ssh. Nothing here uploads, builds, switches, restarts or deletes.
set -u
C=026699b906ea3a513b4f2dbfc37672fa68ee9d42
WT=/c/AlphaCouncil-Staging/deploy-026699b
REPO=/c/projects/alphacouncil-platform
OUT="$REPO/docs/screenshots/sector-standing-prod-2026-11-07"
TREE="$REPO/docs/screenshots/sector-standing-beta-2026-11-07/tree-sha256.txt"
H=root@alphacouncil.tech
REL=/opt/alphacouncil-platform/prod/releases/026699b906
UA="AlphaCouncil release check"
step() { echo; echo "### $1"; echo "\$ $2"; }
ex() { echo "[exit $1]"; }

echo "production checks for $C, run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"

step "1. what production and beta run (read-only ssh)" "readlink, ls releases, systemctl is-active"
ssh -o ConnectTimeout=15 $H "echo prod: \$(readlink -f /opt/alphacouncil-platform/prod/current); echo prod releases: \$(ls -1t /opt/alphacouncil-platform/prod/releases); echo prod services: \$(systemctl is-active acp-prod-api acp-prod-web); echo beta: \$(readlink -f /opt/alphacouncil-platform/current); echo beta releases: \$(ls -1t /opt/alphacouncil-platform/releases); echo beta services: \$(systemctl is-active acp-api acp-web)"; ex $?

step "2. the eight changed files on production equal the commit (sha256)" "git cat-file -p \$C:<f> | sha256sum  vs  sha256sum on the server"
FILES=$(git -C $WT diff --name-only b5655a5 $C)
for f in $FILES; do echo "$(git -C $WT cat-file -p $C:$f | sha256sum | cut -c1-64)  $f"; done > "$OUT/.local8"
ssh -o ConnectTimeout=15 $H "cd $REL && sha256sum $(echo $FILES)" > "$OUT/.server8"
cat "$OUT/.server8"; diff "$OUT/.local8" "$OUT/.server8"; ex $?; rm -f "$OUT/.local8" "$OUT/.server8"

step "3. every committed file on production equals the commit" "the 3,566 paths of beta's tree-sha256.txt (made from the commit), hashed on the server, then diff"
cut -c67- "$TREE" > "$OUT/.paths"
echo "paths: $(wc -l < "$OUT/.paths")"
ssh -o ConnectTimeout=15 $H "cd $REL && xargs -d '\n' sha256sum" < "$OUT/.paths" > "$OUT/.server-tree"
echo "commit hashes: $(wc -l < "$TREE"), server hashes: $(wc -l < "$OUT/.server-tree")"
diff -q "$TREE" "$OUT/.server-tree"; ex $?
rm -f "$OUT/.paths" "$OUT/.server-tree"

step "4. none of the prototype on production" "test -e presenter.py; grep debate_engine settings.py"
ssh -o ConnectTimeout=15 $H "test -e $REL/api/app/debate/presenter.py && echo presenter.py PRESENT || echo presenter.py absent; echo debate_engine in settings.py: \$(grep -c debate_engine $REL/api/app/settings.py)"; ex $?

step "5. the live site answers" "curl -sL https://alphacouncil.tech/<page>"
for p in "" home ar methodology pricing t/2222/financials ar/t/2222/financials; do
  curl -sL -A "$UA" -o /dev/null --max-time 60 -w "%{http_code}  https://alphacouncil.tech/$p\n" "https://alphacouncil.tech/$p"
done

step "6. the live financials pages carry the new wording and not the old" "count phrases in the served HTML (before: before-labels.txt)"
for p in t/2222/financials ar/t/2222/financials; do
  echo "https://alphacouncil.tech/$p"
  curl -sL -A "$UA" --max-time 60 "https://alphacouncil.tech/$p" | python -X utf8 -c "
import sys
t = sys.stdin.read()
for k in ['Sector percentile', 'Sector standing', 'المئين', 'الترتيب داخل القطاع']:
    print(f'  {k}: {t.count(k)}')
"
done
