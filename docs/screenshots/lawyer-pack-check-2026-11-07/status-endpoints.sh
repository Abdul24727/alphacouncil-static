#!/usr/bin/env bash
# Review 91's capture: both public AI status addresses, in full, signed out, GET only. They report the service's
# configuration (computed from settings and whether a key is present); neither runs a model.
set -u
B=https://alphacouncil.tech
UA="AlphaCouncil lawyer-pack check"
echo "public AI status addresses, $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC'), signed out"
for p in /api/v1/copilot/status /api/v1/debate/status; do
  echo
  echo "\$ GET $B$p"
  curl -sS -A "$UA" --max-time 30 -w '\n[http %{http_code}]\n' "$B$p"
done
echo
echo "the fields that matter here:"
curl -sS -A "$UA" --max-time 30 "$B/api/v1/copilot/status" | python -X utf8 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"  copilot: stand_in={d['stand_in']}  model={d['model']}  sign_in_required={d['sign_in_required']}\")
"
curl -sS -A "$UA" --max-time 30 "$B/api/v1/debate/status" | python -X utf8 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"  room:    stand_in={d['stand_in']}  models={d['models']}  rounds={d['rounds']}  seats={len(d['seats'])}\")
"
