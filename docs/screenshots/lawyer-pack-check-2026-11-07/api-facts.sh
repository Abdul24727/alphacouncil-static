#!/usr/bin/env bash
# Public, signed-out facts the lawyer pack states, read from the live API with GET only.
set -u
B=https://alphacouncil.tech
UA="AlphaCouncil lawyer-pack check"
echo "lawyer-pack API facts, $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"
echo
echo "\$ GET $B/api/v1/health"
curl -sS -A "$UA" --max-time 30 "$B/api/v1/health"; echo
echo
echo "\$ GET $B/api/v1/tickers   (companies and exchanges)"
curl -sS -A "$UA" --max-time 60 "$B/api/v1/tickers" | python -X utf8 -c "
import collections, json, sys
rows = json.load(sys.stdin)
ex = collections.Counter(r['exchange'] for r in rows)
print(f'{len(rows)} companies on {len(ex)} exchanges:', ', '.join(f'{k} {v}' for k, v in ex.most_common()))
"
echo
echo "\$ GET $B/api/v1/copilot/status   (the Copilot's model)"
curl -sS -A "$UA" --max-time 30 "$B/api/v1/copilot/status"; echo
echo
echo "\$ GET $B/api/v1/debate/status   (the room's seats and Pro's monthly sessions; signed out)"
curl -sS -A "$UA" --max-time 30 "$B/api/v1/debate/status" | python -X utf8 -c "
import json, sys
d = json.load(sys.stdin)
print('plan', d['plan'], '| signed_in', d['signed_in'], '| limit', d['limit'], '| pro_limit', d['pro_limit'])
for s in d['seats']:
    print(f\"  {s['role']:8} {s['name_en']} / {s['name_ar']} | {s['portrait']}\")
"
echo
echo "\$ GET $B/api/capabilities   (the address Moyasar was shown, legal questions (c))"
curl -sS -A "$UA" --max-time 30 -o /dev/null -w '%{http_code}\n' "$B/api/capabilities"
