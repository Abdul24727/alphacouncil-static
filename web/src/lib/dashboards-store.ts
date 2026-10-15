import { create } from "zustand";
import { persist } from "zustand/middleware";

export type PinnedTable = {
  kind: "table";
  id: string;
  title: string;
  columns: string[];
  rows: (string | number | null)[][];
  unverified: number[][];
  source: string;
  pinnedAt: string;
};

export type PinnedChart = {
  kind: "chart";
  id: string;
  title: string;
  ticker: string;
  range: "1M" | "3M" | "6M" | "1Y" | "5Y";
  pinnedAt: string;
};

export type Pinned = PinnedTable | PinnedChart;

type Dashboards = {
  pinned: Pinned[];
  pin: (item: Pinned) => void;
  unpin: (id: string) => void;
  isPinned: (id: string) => boolean;
};

/** Copilot results pinned as panels on My dashboards. Browser-local until accounts exist. */
export const useDashboards = create<Dashboards>()(
  persist(
    (set, get) => ({
      pinned: [],
      pin: (item) => set((s) => ({ pinned: [...s.pinned.filter((p) => p.id !== item.id), item] })),
      unpin: (id) => set((s) => ({ pinned: s.pinned.filter((p) => p.id !== id) })),
      isPinned: (id) => get().pinned.some((p) => p.id === id),
    }),
    { name: "ac-dashboards" },
  ),
);
