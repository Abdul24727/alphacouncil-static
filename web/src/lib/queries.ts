"use client";

import { useQuery } from "@tanstack/react-query";
import { api, unwrap } from "@/lib/api/client";

// One hook per endpoint. Keys start with the ticker slug, so every panel of a
// ticker group shares the cache and switching the group refetches together.

export function useTickerDetail(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "detail"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerPeers(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "peers"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/peers", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerNews(slug: string | undefined, limit = 12, lang?: "en" | "ar") {
  return useQuery({
    queryKey: ["ticker", slug, "news", limit, lang],
    queryFn: async ({ signal }) =>
      unwrap(
        // `lang` puts items in the page's language first (topped up with the other).
        await api.GET("/v1/tickers/{ref}/news", { params: { path: { ref: slug! }, query: { limit, lang } }, signal }),
      ),
    enabled: !!slug,
  });
}

export function useTickerEvents(slug: string | undefined, limit = 20) {
  return useQuery({
    queryKey: ["ticker", slug, "events", limit],
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET("/v1/tickers/{ref}/events", { params: { path: { ref: slug! }, query: { limit } }, signal }),
      ),
    enabled: !!slug,
  });
}


export function useTickerCouncil(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "council"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/council", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerFundamentals(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "fundamentals"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/fundamentals", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerStatements(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "statements"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/statements", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerCorporate(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "corporate"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/corporate", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerInsights(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "insights"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/insights", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
  });
}

export function useTickerPrices(slug: string | undefined) {
  return useQuery({
    queryKey: ["ticker", slug, "prices"],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/tickers/{ref}/prices", { params: { path: { ref: slug! } }, signal })),
    enabled: !!slug,
    staleTime: 5 * 60_000,
  });
}
