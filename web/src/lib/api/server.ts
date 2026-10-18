import "server-only";
import { connection } from "next/server";
import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// Server components call the API directly (no rewrite hop). Same origin setting as
// next.config.ts: the deploy sets API_ORIGIN for both the build and the server.
const api = createClient<paths>({ baseUrl: process.env.API_ORIGIN ?? "http://127.0.0.1:8000" });

type S = components["schemas"];
export type Plans = S["Plans"];
export type Methodology = S["Methodology"];
export type ExchangeSummary = S["ExchangeSummary"];
export type UniverseEntry = S["UniverseEntry"];
export type TickerRef = S["TickerRef"];

/**
 * Public pages render what the API returns, or null when it cannot answer; the page then
 * shows "Data unavailable" rather than a number from anywhere else. Uncached: these calls
 * run per request, so callers sit behind <Suspense>.
 */
async function get<T>(call: () => Promise<{ data?: T; error?: unknown }>): Promise<T | null> {
  // Request time, not prerender: the client reads the clock and randomness per request.
  await connection();
  try {
    const { data } = await call();
    return data ?? null;
  } catch {
    return null;
  }
}

export const getPlans = () => get(() => api.GET("/v1/plans", { cache: "no-store" }));
export const getMethodology = () => get(() => api.GET("/v1/methodology", { cache: "no-store" }));
export const getExchanges = () => get(() => api.GET("/v1/market/exchanges", { cache: "no-store" }));
export const getTickerList = () => get(() => api.GET("/v1/tickers", { cache: "no-store" }));

/**
 * A stock page's company and symbol for its metadata. "unknown" only when the API says the
 * ticker does not exist (404); null when the API could not answer.
 */
export async function getTickerRef(ref: string): Promise<TickerRef | "unknown" | null> {
  await connection();
  try {
    const { data, response } = await api.GET("/v1/tickers/{ref}", {
      params: { path: { ref } },
      cache: "no-store",
    });
    if (data) return data.ticker;
    return response.status === 404 ? "unknown" : null;
  } catch {
    return null;
  }
}
