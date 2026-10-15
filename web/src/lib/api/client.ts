import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// Same-origin: next.config.ts rewrites /api/v1/* to the FastAPI service.
// Regenerate the types with `npm run gen:api` after changing the API.
export const api = createClient<paths>({ baseUrl: "/api" });

type S = components["schemas"];
export type TickerHit = S["TickerHit"];
export type TickerRef = S["TickerRef"];
export type TickerDetail = S["TickerDetail"];
export type Freshness = S["Freshness"];
export type Peers = S["Peers"];
export type PeerRow = S["PeerRow"];
export type NewsItem = S["NewsItem"];

/** Error carrying the API's `detail` so panels can say why data is unavailable. */
export class ApiError extends Error {
  constructor(
    public status: number,
    detail: string,
  ) {
    super(detail);
  }
}

export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.data !== undefined) return result.data;
  const err = result.error as { detail?: unknown } | undefined;
  const detail = typeof err?.detail === "string" ? err.detail : `HTTP ${result.response.status}`;
  throw new ApiError(result.response.status, detail);
}
