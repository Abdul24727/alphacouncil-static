"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, unwrap } from "@/lib/api/client";

// Market-wide views

export function useMarketOverview(lang?: "en" | "ar") {
  return useQuery({
    queryKey: ["market", "overview", lang],
    // `lang` puts news in the page's language first.
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/market/overview", { params: { query: { lang } }, signal })),
  });
}

export function useExchanges() {
  return useQuery({
    queryKey: ["market", "exchanges"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/market/exchanges", { signal })),
  });
}

export function useScreener() {
  return useQuery({
    queryKey: ["screener"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/screener", { signal })),
    staleTime: 5 * 60_000,
  });
}

// Templates

export function useEarningsSeason(days: number) {
  return useQuery({
    queryKey: ["templates", "earnings", days],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/templates/earnings-season", { params: { query: { days } }, signal })),
  });
}

export function useDividendHunter(minYield: number) {
  return useQuery({
    queryKey: ["templates", "dividends", minYield],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/templates/dividend-hunter", { params: { query: { min_yield: minYield, limit: 100 } }, signal })),
  });
}

export function useSectors() {
  return useQuery({
    queryKey: ["templates", "sectors"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/templates/sectors", { signal })),
    staleTime: 10 * 60_000,
  });
}

export function useSectorCompare(a: string | null, b: string | null) {
  return useQuery({
    queryKey: ["templates", "sectors", a, b],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/templates/sector-vs-sector", { params: { query: { a: a!, b: b! } }, signal })),
    enabled: !!a && !!b,
  });
}

// Portfolio (signed in)

export function usePortfolio(enabled: boolean) {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/portfolio", { signal })),
    enabled,
  });
}

export function useAlerts(enabled: boolean) {
  return useQuery({
    queryKey: ["portfolio", "alerts"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/portfolio/alerts", { signal })),
    enabled,
  });
}

export function usePortfolioMutations() {
  const qc = useQueryClient();
  const setPortfolio = (data: unknown) => qc.setQueryData(["portfolio"], data);
  const setAlerts = (data: unknown) => qc.setQueryData(["portfolio", "alerts"], data);
  // A delete answers 404 when the item is already gone (another tab): show the list as it is now.
  const refetchIfGone = (key: string[]) => (e: Error) => {
    if (e instanceof ApiError && e.status === 404) void qc.invalidateQueries({ queryKey: key });
  };
  return {
    upsert: useMutation({
      mutationFn: async (body: { ticker: string; quantity: number; avg_cost?: number | null }) =>
        unwrap(await api.POST("/v1/portfolio/holdings", { body })),
      onSuccess: setPortfolio,
    }),
    remove: useMutation({
      mutationFn: async (id: number) =>
        unwrap(await api.DELETE("/v1/portfolio/holdings/{holding_id}", { params: { path: { holding_id: id } } })),
      onSuccess: setPortfolio,
      onError: refetchIfGone(["portfolio"]),
    }),
    addAlert: useMutation({
      mutationFn: async (body: { ticker: string; kind: "above" | "below"; price: number }) =>
        unwrap(await api.POST("/v1/portfolio/alerts", { body })),
      onSuccess: setAlerts,
    }),
    removeAlert: useMutation({
      mutationFn: async (id: number) =>
        unwrap(await api.DELETE("/v1/portfolio/alerts/{alert_id}", { params: { path: { alert_id: id } } })),
      onSuccess: setAlerts,
      onError: refetchIfGone(["portfolio", "alerts"]),
    }),
  };
}
