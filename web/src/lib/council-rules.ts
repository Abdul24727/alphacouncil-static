/**
 * Arguments for the `stock.council.rules.*` messages. The thresholds come from the API
 * (api/app/council.py THRESHOLDS), so the in-app council and /methodology state exactly
 * the numbers the votes use. Passed as strings so digits stay Latin in Arabic too.
 */
export function ruleArgs(thresholds: Record<string, number> | undefined): Record<string, string> {
  return Object.fromEntries(Object.entries(thresholds ?? {}).map(([k, v]) => [k, String(v)]));
}
