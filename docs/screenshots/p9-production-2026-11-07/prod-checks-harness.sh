#!/usr/bin/env bash
# Read-only checks of production after the P9 release (ea51de796c), 2026-11-07.
# The live site is public, so its pages are read at https://alphacouncil.tech (GET only); the server is read over
# read-only ssh. Nothing here uploads, builds, switches, restarts or deletes. No model is called.
set -u
C=ea51de796cf3bbdbea21a45f35682335eab5a2f8
BASE=026699b906ea3a513b4f2dbfc37672fa68ee9d42
WT=/c/AlphaCouncil-Staging/deploy-p9
REPO=/c/projects/alphacouncil-platform
OUT="$REPO/docs/screenshots/p9-production-2026-11-07"
TREE="$REPO/docs/screenshots/p9-beta-2026-11-07/tree-sha256.txt"
H=root@alphacouncil.tech
REL=/opt/alphacouncil-platform/prod/releases/ea51de796c
UA="AlphaCouncil release check"
step() { echo; echo "### $1"; echo "\$ $2"; }
ex() { echo "[exit $1]"; }

echo "production checks for $C, run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"

step "1. what production and beta run (read-only ssh)" "readlink, ls releases, systemctl is-active"
ssh -o ConnectTimeout=15 $H "echo prod: \$(readlink -f /opt/alphacouncil-platform/prod/current); echo prod releases: \$(ls -1t /opt/alphacouncil-platform/prod/releases); echo prod services: \$(systemctl is-active acp-prod-api acp-prod-web); echo beta: \$(readlink -f /opt/alphacouncil-platform/current); echo beta releases: \$(ls -1t /opt/alphacouncil-platform/releases); echo beta services: \$(systemctl is-active acp-api acp-web)"; ex $?

step "2. the running production processes started after the switch, from the new release" "systemctl show -p MainPID,ActiveEnterTimestamp; readlink /proc/<pid>/cwd"
ssh -o ConnectTimeout=15 $H "for s in acp-prod-api acp-prod-web; do pid=\$(systemctl show -p MainPID --value \$s); echo \"\$s: pid \$pid, active since \$(systemctl show -p ActiveEnterTimestamp --value \$s), cwd \$(readlink -f /proc/\$pid/cwd)\"; done"; ex $?

step "3. what the release changes from production's previous commit" "git diff --name-status \$BASE \$C; git diff --quiet \$BASE \$C -- web api/app/routers"
git -C $WT diff --name-status $BASE $C; ex $?
git -C $WT diff --quiet $BASE $C -- web api/app/routers; ex $?

step "4. the four changed files on production equal the commit (sha256)" "git cat-file -p \$C:<f> | sha256sum  vs  sha256sum on the server"
FILES=$(git -C $WT diff --name-only $BASE $C)
for f in $FILES; do echo "$(git -C $WT cat-file -p $C:$f | sha256sum | cut -c1-64)  $f"; done > "$OUT/.local4"
ssh -o ConnectTimeout=15 $H "cd $REL && sha256sum $(echo $FILES)" > "$OUT/.server4"
cat "$OUT/.server4"; diff "$OUT/.local4" "$OUT/.server4"; ex $?; rm -f "$OUT/.local4" "$OUT/.server4"

step "5. every committed file on production equals the commit" "the 3,566 paths of beta's tree-sha256.txt (made from the commit), hashed on the server, then diff"
cut -c67- "$TREE" > "$OUT/.paths"
echo "paths: $(wc -l < "$OUT/.paths")"
ssh -o ConnectTimeout=15 $H "cd $REL && xargs -d '\n' sha256sum" < "$OUT/.paths" > "$OUT/.server-tree"
echo "commit hashes: $(wc -l < "$TREE"), server hashes: $(wc -l < "$OUT/.server-tree")"
diff -q "$TREE" "$OUT/.server-tree"; ex $?
rm -f "$OUT/.paths" "$OUT/.server-tree"

step "6. none of the prototype on production" "test -e presenter.py; grep debate_engine settings.py"
ssh -o ConnectTimeout=15 $H "test -e $REL/api/app/debate/presenter.py && echo presenter.py PRESENT || echo presenter.py absent; echo debate_engine in settings.py: \$(grep -c debate_engine $REL/api/app/settings.py)"

step "7. the live site answers" "curl -sL https://alphacouncil.tech/<page>"
for p in "" home ar t/4330 t/2222/financials ar/t/2222/financials methodology pricing api/v1/health; do
  curl -sL -A "$UA" -o /dev/null --max-time 60 -w "%{http_code}  https://alphacouncil.tech/$p\n" "https://alphacouncil.tech/$p"
done
echo "health: $(curl -sS -A "$UA" --max-time 30 https://alphacouncil.tech/api/v1/health)"

step "8. the evidence endpoint stays Pro-only for an anonymous reader" "curl https://alphacouncil.tech/api/v1/tickers/4330/evidence"
curl -sS -A "$UA" --max-time 30 -w "  [%{http_code}]\n" https://alphacouncil.tech/api/v1/tickers/4330/evidence

step "9. the monitor (status: works on a copy of its state; saves, mails and pings nothing)" "ssh root@alphacouncil.tech python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status"
ssh -o ConnectTimeout=15 $H "python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status"; ex $?
