"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

function useDebounced<T>(value: T, ms: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return debounced;
}

/** Debounced ticker search by symbol, English or Arabic name. */
export function useTickerSearch(query: string, { enabled = true, limit = 8 } = {}) {
  const term = useDebounced(query.trim(), 120);
  const search = useQuery({
    queryKey: ["tickers", "search", term, limit],
    queryFn: async ({ signal }) => {
      const { data, error } = await api.GET("/v1/tickers/search", {
        params: { query: { q: term, limit } },
        signal,
      });
      if (error || !data) throw new Error("search failed");
      return data;
    },
    enabled: enabled && term.length > 0,
    placeholderData: keepPreviousData,
  });
  const results = term ? (search.data?.results ?? []) : [];
  return { term, results, search };
}
