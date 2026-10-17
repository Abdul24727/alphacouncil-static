/** The token of a "Forgot password?" link. The API puts it in the fragment
 *  (/reset-password#token=…), which browsers never send to a server, so only this page sees it. */
export function tokenFromHash(hash: string): string | null {
  const token = new URLSearchParams(hash.replace(/^#/, "")).get("token");
  return token && /^[\w-]{20,200}$/.test(token) ? token : null;
}
