// What the Google sign-in sends back (?error= on /login, ?google=terms on /signup; api/app/oauth.py).
// A plain module: the server-rendered pages read the query, the form shows the message.
export const GOOGLE_NOTICES = [
  "google_terms",
  "google_expired",
  "google_cancelled",
  "google_failed",
  "google_unverified",
  "google_unavailable",
] as const;

export type GoogleNotice = (typeof GOOGLE_NOTICES)[number];

export function googleNotice(value: unknown): GoogleNotice | undefined {
  return GOOGLE_NOTICES.find((n) => n === value);
}
