#!/usr/bin/env bash
# Read-only checks of beta after the sector-standing release (026699b906), 2026-11-07.
# Needs the tunnels: ssh -f -N -L 3201:[::1]:3200 -L 8200:127.0.0.1:8200 root@alphacouncil.tech
# Nothing here uploads, builds, switches, restarts or deletes. GET requests only.
set -u
C=026699b906ea3a513b4f2dbfc37672fa68ee9d42
WT=/c/AlphaCouncil-Staging/deploy-026699b
REPO=/c/projects/alphacouncil-platform
OUT="$REPO/docs/screenshots/sector-standing-beta-2026-11-07"
H=root@alphacouncil.tech
step() { echo; echo "### $1"; echo "\$ $2"; }
ex() { echo "[exit $1]"; }

echo "beta checks for $C, run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"

step "1. what beta and production run (read-only ssh)" "readlink, ls releases, systemctl is-active"
ssh -o ConnectTimeout=15 $H "echo beta: \$(readlink -f /opt/alphacouncil-platform/current); echo beta releases: \$(ls -1t /opt/alphacouncil-platform/releases); echo beta services: \$(systemctl is-active acp-api acp-web); echo prod: \$(readlink -f /opt/alphacouncil-platform/prod/current); echo prod releases: \$(ls -1t /opt/alphacouncil-platform/prod/releases); echo prod services: \$(systemctl is-active acp-prod-api acp-prod-web)"; ex $?

step "2. the eight changed files on beta equal the commit (sha256)" "git cat-file -p \$C:<f> | sha256sum  vs  sha256sum on the server"
FILES=$(git -C $WT diff --name-only b5655a5 $C)
for f in $FILES; do echo "$(git -C $WT cat-file -p $C:$f | sha256sum | cut -c1-64)  $f"; done > "$OUT/.local8"
ssh -o ConnectTimeout=15 $H "cd /opt/alphacouncil-platform/releases/026699b906 && sha256sum $(echo $FILES)" > "$OUT/.server8"
cat "$OUT/.server8"; diff "$OUT/.local8" "$OUT/.server8"; ex $?; rm -f "$OUT/.local8" "$OUT/.server8"

step "3. every committed file on beta equals the commit" "sha256 of each non-symlink path in git ls-tree, both sides, then diff"
git -C $WT ls-tree -r $C --format='%(objectmode) %(path)' | grep -v '^120000 ' | cut -d' ' -f2- > "$OUT/.paths"
echo "paths: $(wc -l < "$OUT/.paths")"
python -X utf8 -c "
import subprocess, sys, hashlib
sys.stdout.reconfigure(newline='\n')  # LF, as sha256sum on the server writes
wt, c, paths = sys.argv[1], sys.argv[2], open(sys.argv[3], encoding='utf-8').read().splitlines()
for p in paths:
    b = subprocess.run(['git', '-C', wt, 'cat-file', '-p', f'{c}:{p}'], capture_output=True).stdout
    print(f'{hashlib.sha256(b).hexdigest()}  {p}')
" "$WT" "$C" "$OUT/.paths" > "$OUT/tree-sha256.txt"
ssh -o ConnectTimeout=15 $H "cd /opt/alphacouncil-platform/releases/026699b906 && xargs -d '\n' sha256sum" < "$OUT/.paths" > "$OUT/.server-tree"
echo "local hashes: $(wc -l < "$OUT/tree-sha256.txt"), server hashes: $(wc -l < "$OUT/.server-tree")"
diff -q "$OUT/tree-sha256.txt" "$OUT/.server-tree"; ex $?
rm -f "$OUT/.paths" "$OUT/.server-tree"

step "4. none of the prototype on beta" "test -e presenter.py; grep debate_engine settings.py"
ssh -o ConnectTimeout=15 $H "test -e /opt/alphacouncil-platform/releases/026699b906/api/app/debate/presenter.py && echo presenter.py PRESENT || echo presenter.py absent; echo debate_engine in settings.py: \$(grep -c debate_engine /opt/alphacouncil-platform/releases/026699b906/api/app/settings.py)"; ex $?

step "5. the code that serves the values is unchanged" "git diff --quiet b5655a5 \$C -- api/app/routers web/src"
git -C $WT diff --quiet b5655a5 $C -- api/app/routers web/src; ex $?

step "6. beta answers (through the tunnel)" "curl api health and six pages"
curl -s --max-time 20 http://127.0.0.1:8200/v1/health; echo
for u in http://localhost:3201/home http://localhost:3201/en http://localhost:3201/ar http://localhost:3201/en/t/2222/financials http://localhost:3201/ar/t/2222/financials http://localhost:3201/methodology; do
  curl -s -o /dev/null --max-time 60 -w "%{http_code}  $u\n" "$u"
done

step "7. beta's API values for 2222 (what the panel shows, rounded)" "GET /v1/tickers/2222/fundamentals"
curl -s --max-time 30 http://127.0.0.1:8200/v1/tickers/2222/fundamentals | python -X utf8 -c "
import sys, json
d = json.load(sys.stdin)
print('fundamentals as_of:', d['freshness']['as_of'])
for g in d['groups']:
    print(f\"{g['group']}: score {g['score']}\", [(m['key'], m['sector_percentile']) for m in g['metrics'] if m['sector_percentile'] is not None])
"

step "8. the candidate captures were taken before tonight's data refresh" "file times of the review-74 captures"
for f in viewports.json en-1440-2222.png; do echo "$(TZ=UTC stat -c '%y' "$REPO/docs/screenshots/sector-standing-2026-11-07/$f" | cut -c1-19) UTC  sector-standing-2026-11-07/$f"; done

step "9. P9's notes on beta use the new wording" "GET /v1/tickers/2222/evidence, count phrases"
curl -s --max-time 30 http://127.0.0.1:8200/v1/tickers/2222/evidence | python -X utf8 -c "
import sys, re
t = sys.stdin.read()
print('\"sector standing\":', len(re.findall(r'sector standing', t, re.I)), '| \"sector percentile\":', len(re.findall(r'sector percentile', t, re.I)))
"

step "10. production's preflight now (read-only; approves nothing)" "DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=\$C deploy-production.sh --check"
(cd $WT && DEPLOY_BRANCH=release/sector-standing DEPLOY_SHA=$C bash $REPO/scripts/deploy-production.sh --check); ex $?
