#!/usr/bin/env bash
# Every public address docs/lawyer-review-pack-2026-11-06.md names, read signed out with GET only (no cookies, no
# credentials, no form). For each: the first answer (status and redirect target), then the final answer after
# following redirects. Beta is asked without its password, so it should refuse.
set -u
B=https://alphacouncil.tech
UA="AlphaCouncil lawyer-pack check"
echo "lawyer-pack address check, $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"
echo "production: $(curl -sS -A "$UA" --max-time 30 $B/api/v1/health)"
echo
printf '%-44s %-5s %-44s %s\n' "address (as the pack names it)" "first" "redirect to" "final"
check() {
  local u="$1"
  local first final
  first=$(curl -s -o /dev/null -A "$UA" --max-time 30 -w '%{http_code} %{redirect_url}' "$u")
  final=$(curl -s -o /dev/null -L -A "$UA" --max-time 30 -w '%{http_code} %{url_effective}' "$u")
  printf '%-44s %-5s %-44s %s\n' "${u#https://}" "${first%% *}" "$(echo "${first#* }" | sed "s#^$B##")" "$(echo "$final" | sed "s# $B# #")"
}
# section 1: the site, both languages
check $B
check $B/ar
# section 3, signed out: home, Markets, Screener, one company and its tabs
for p in home markets screener t/2222 t/2222/financials t/2222/ownership t/2222/calendar t/2222/council t/2222/advisors; do
  check $B/$p; check $B/ar/$p
done
# section 3 and 4: the six legal texts, in English and Arabic, and the legal index the footer leads to
for d in "" /terms /privacy /refunds /ai-financial-disclaimer /cookies /merchant; do
  check $B/legal$d; check $B/ar/legal$d
done
# section 3: pricing, sign-up, sign-in, checkout, settings
for p in pricing methodology signup login checkout settings; do
  check $B/$p; check $B/ar/$p
done
# section 3 step 8: the beta copy, asked without its password
check https://beta.alphacouncil.tech
# section 1 and 2: the www address (Step 9)
check https://www.alphacouncil.tech
