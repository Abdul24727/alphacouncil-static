#!/usr/bin/env bash
# Review 93's step, the hosting part only: public records for the site's address (DNS and the IP registry's RDAP).
# No server access. The account and payment counts were not read: the session's permission check refused a read of
# production's database, so they stay with the owner.
set -u
echo "public hosting records for alphacouncil.tech, read $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"
IP=$(nslookup alphacouncil.tech 2>/dev/null | awk '/^Address/ {a=$2} END {print a}')
echo
echo "alphacouncil.tech resolves to: $IP"
echo
echo "reverse DNS of $IP:"
nslookup "$IP" 2>/dev/null | grep -i "name" || echo "(none)"
echo
echo "RDAP (the IP registry's public record for $IP), selected fields:"
curl -sS --max-time 30 -L "https://rdap.org/ip/$IP" | python -X utf8 -c "
import json, sys
d = json.load(sys.stdin)
print('  network:', d.get('handle'), '|', d.get('name'), '| country:', d.get('country'), '| range:', d.get('startAddress'), '-', d.get('endAddress'))
for r in d.get('remarks', [])[:3]:
    print('  remark:', ' '.join(r.get('description', []))[:160])
def walk(es, depth=0):
    for e in es:
        v = (e.get('vcardArray') or [None, []])[1]
        fn = [x[3] for x in v if x[0] == 'fn']
        adr = [x[1].get('label') or x[3] for x in v if x[0] == 'adr']
        a = str(adr[0]).replace(chr(10), ', ')[:140] if adr else '-'
        print('  ' + '  ' * depth + 'entity:', e.get('handle'), '| roles:', ','.join(e.get('roles', [])), '| name:', fn[0] if fn else '-', '| address:', a)
        walk(e.get('entities', []), depth + 1)
walk(d.get('entities', []))
"
echo "[exit $?]"
