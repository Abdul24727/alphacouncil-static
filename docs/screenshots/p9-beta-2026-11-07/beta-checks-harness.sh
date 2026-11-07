#!/usr/bin/env bash
# Read-only checks of beta after the P9 release (ea51de796c), 2026-11-07.
# Needs the tunnels: ssh -f -N -L 3201:[::1]:3200 -L 8200:127.0.0.1:8200 root@alphacouncil.tech
# Nothing here uploads, builds, switches, restarts or deletes on a server. GET requests only. No model is called.
set -u
C=ea51de796cf3bbdbea21a45f35682335eab5a2f8
BASE=026699b906ea3a513b4f2dbfc37672fa68ee9d42
WT=/c/AlphaCouncil-Staging/deploy-p9
REPO=/c/projects/alphacouncil-platform
OUT="$REPO/docs/screenshots/p9-beta-2026-11-07"
PY=$REPO/api/.venv/Scripts/python.exe
H=root@alphacouncil.tech
step() { echo; echo "### $1"; echo "\$ $2"; }
ex() { echo "[exit $1]"; }

echo "beta checks for $C, run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"

step "1. what beta and production run (read-only ssh)" "readlink, ls releases, systemctl is-active"
ssh -o ConnectTimeout=15 $H "echo beta: \$(readlink -f /opt/alphacouncil-platform/current); echo beta releases: \$(ls -1t /opt/alphacouncil-platform/releases); echo beta services: \$(systemctl is-active acp-api acp-web); echo prod: \$(readlink -f /opt/alphacouncil-platform/prod/current); echo prod releases: \$(ls -1t /opt/alphacouncil-platform/prod/releases); echo prod services: \$(systemctl is-active acp-prod-api acp-prod-web)"; ex $?

step "2. what the release changes from production's commit" "git diff --name-status \$BASE \$C; git diff --quiet \$BASE \$C -- web api/app/routers"
git -C $WT diff --name-status $BASE $C; ex $?
git -C $WT diff --quiet $BASE $C -- web api/app/routers; ex $?

step "3. the four changed files on beta equal the commit (sha256)" "git cat-file -p \$C:<f> | sha256sum  vs  sha256sum on the server"
FILES=$(git -C $WT diff --name-only $BASE $C)
for f in $FILES; do echo "$(git -C $WT cat-file -p $C:$f | sha256sum | cut -c1-64)  $f"; done > "$OUT/.local4"
ssh -o ConnectTimeout=15 $H "cd /opt/alphacouncil-platform/releases/ea51de796c && sha256sum $(echo $FILES)" > "$OUT/.server4"
cat "$OUT/.server4"; diff "$OUT/.local4" "$OUT/.server4"; ex $?; rm -f "$OUT/.local4" "$OUT/.server4"

step "4. every committed file on beta equals the commit" "sha256 of each non-symlink path in git ls-tree, both sides, then diff"
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
ssh -o ConnectTimeout=15 $H "cd /opt/alphacouncil-platform/releases/ea51de796c && xargs -d '\n' sha256sum" < "$OUT/.paths" > "$OUT/.server-tree"
echo "local hashes: $(wc -l < "$OUT/tree-sha256.txt"), server hashes: $(wc -l < "$OUT/.server-tree")"
diff -q "$OUT/tree-sha256.txt" "$OUT/.server-tree"; ex $?
rm -f "$OUT/.paths" "$OUT/.server-tree"

step "5. none of the prototype on beta" "test -e presenter.py; grep debate_engine settings.py"
ssh -o ConnectTimeout=15 $H "test -e /opt/alphacouncil-platform/releases/ea51de796c/api/app/debate/presenter.py && echo presenter.py PRESENT || echo presenter.py absent; echo debate_engine in settings.py: \$(grep -c debate_engine /opt/alphacouncil-platform/releases/ea51de796c/api/app/settings.py)"; ex $?

step "6. beta answers (through the tunnel)" "curl api health and six pages"
curl -s --max-time 20 http://127.0.0.1:8200/v1/health; echo
for u in http://localhost:3201/home http://localhost:3201/ar http://localhost:3201/t/4330 http://localhost:3201/ar/t/2222/financials http://localhost:3201/methodology http://localhost:3201/pricing; do
  curl -s -o /dev/null --max-time 60 -w "%{http_code}  $u\n" "$u"
done

step "7. P9's notes for all 714 tickers, after the release, against the sweep taken before it" "p9-notes-sweep.py p9-notes-after.json; p9-notes-compare.py p9-notes-before.json p9-notes-after.json"
cat "$OUT/sweep-before-serving.txt"
echo "after sweep serving: $(ssh -o ConnectTimeout=15 $H readlink -f /opt/alphacouncil-platform/current)"
python -X utf8 -I "$OUT/p9-notes-sweep.py" "$OUT/p9-notes-after.json"; ex $?
python -X utf8 -I "$OUT/p9-notes-compare.py" "$OUT/p9-notes-before.json" "$OUT/p9-notes-after.json"; ex $?

step "8. what the room is told, from beta's own P9 (the candidate's pack code, run here; no model)" "GET /evidence for 4330 ALFIRDOU 232 8010 2222; no_statements_note"
(cd $WT/api && $PY -X utf8 -c "
import json, urllib.request, app.debate.pack as pack
print('pack code from:', pack.__file__)
for t in ['4330', 'ALFIRDOU', '232', '8010', '2222']:
    d = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8200/v1/tickers/{t}/evidence', timeout=60).read())
    print(f'\n== {t}: statements', [(s['section'], len(s['rows'])) for s in d['statements']], '| quarter rows', len(d['quarters']['rows']) if d.get('quarters') else 0)
    if d.get('quarters'):
        print('   QUARTERS NOTE:', d['quarters']['note'])
    for lim in d['limitations']:
        print('   LIMITATION:', lim)
    print('   PACK NOTE:', pack.no_statements_note({'P9': d}))
"); ex $?

step "9. production is untouched, and its preflight for this commit (read-only; approves nothing)" "DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=\$C deploy-production.sh --check"
git -C $REPO diff --quiet c3bcff6 -- scripts/deploy-production.sh; echo "deploy-production.sh equals c3bcff6's: exit $?"
(cd $WT && DEPLOY_BRANCH=release/p9-no-statements DEPLOY_SHA=$C bash $REPO/scripts/deploy-production.sh --check); ex $?

step "10. the monitor (status only: reads, saves and sends nothing)" "python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status"
ssh -o ConnectTimeout=15 $H "python3 -I /usr/local/lib/acp-monitor/prod-monitor.py status"; ex $?
