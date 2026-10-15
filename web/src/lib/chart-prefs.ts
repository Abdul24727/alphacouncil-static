import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChartMode, ChartRange, Indicator } from "@/components/stock/PriceChart";

type ChartPrefs = {
  mode: ChartMode;
  range: ChartRange;
  indicators: Indicator[];
  setMode: (mode: ChartMode) => void;
  setRange: (range: ChartRange) => void;
  toggleIndicator: (i: Indicator) => void;
};

/** Price panel settings, remembered in this browser (per-user once accounts exist). */
export const useChartPrefs = create<ChartPrefs>()(
  persist(
    (set) => ({
      mode: "line",
      range: "1Y",
      indicators: [],
      setMode: (mode) => set({ mode }),
      setRange: (range) => set({ range }),
      toggleIndicator: (i) =>
        set((s) => ({ indicators: s.indicators.includes(i) ? s.indicators.filter((x) => x !== i) : [...s.indicators, i] })),
    }),
    { name: "ac-chart", skipHydration: true },
  ),
);
