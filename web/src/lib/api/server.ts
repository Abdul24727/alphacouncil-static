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
