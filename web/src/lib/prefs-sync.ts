"use client";

import { useEffect } from "react";
import { api } from "@/lib/api/client";
import { useMe } from "@/lib/auth";
import { useChartPrefs } from "@/lib/chart-prefs";
import { useLayout } from "@/lib/layout-store";
import { useSettings } from "@/lib/settings-store";

type Saved = {
  layout?: Partial<{ sidebarWidth: number; sidebarCollapsed: boolean; copilotWidth: number; copilotOpen: boolean }>;
  chart?: Partial<{ mode: string; range: string; indicators: string[] }>;
  decimals?: "auto" | 2 | 3;
  fontSize?: "sm" | "md" | "lg";
  controlsOnHover?: boolean;
};

function collect(): Saved {
  const l = useLayout.getState();
  const c = useChartPrefs.getState();
  const s = useSettings.getState();
  return {
    layout: { sidebarWidth: l.sidebarWidth, sidebarCollapsed: l.sidebarCollapsed, copilotWidth: l.copilotWidth, copilotOpen: l.copilotOpen },
    chart: { mode: c.mode, range: c.range, indicators: c.indicators },
    decimals: s.decimals,
    fontSize: s.fontSize,
    controlsOnHover: s.controlsOnHover,
  };
}

function apply(saved: Saved) {
  if (saved.layout) useLayout.setState(saved.layout);
  if (saved.chart) useChartPrefs.setState(saved.chart as Partial<ReturnType<typeof useChartPrefs.getState>>);
  const { decimals, fontSize, controlsOnHover } = saved;
  useSettings.setState({
    ...(decimals !== undefined ? { decimals } : {}),
    ...(fontSize !== undefined ? { fontSize } : {}),
    ...(controlsOnHover !== undefined ? { controlsOnHover } : {}),
  });
}

/**
 * Signed in: the account's saved panes, chart and display settings win over
 * this browser's, and every later change is saved back (debounced). A new
 * account starts from whatever this browser already had.
 */
export function usePrefsSync() {
  const userId = useMe().data?.id;

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    let ready = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const save = () => void api.PUT("/v1/me/prefs", { body: { data: collect() as Record<string, unknown> } });
    const push = () => {
      if (!ready) return;
      clearTimeout(timer);
      timer = setTimeout(save, 800);
    };

    void api.GET("/v1/me/prefs").then(({ data }) => {
      if (cancelled) return;
      const saved = (data?.data ?? {}) as Saved;
      if (Object.keys(saved).length) apply(saved);
      else save();
      ready = true;
    });

    const unsubs = [useLayout.subscribe(push), useChartPrefs.subscribe(push), useSettings.subscribe(push)];
    return () => {
      cancelled = true;
      clearTimeout(timer);
      unsubs.forEach((u) => u());
    };
  }, [userId]);
}
