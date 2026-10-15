import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Decimals = "auto" | 2 | 3;
export type FontSize = "sm" | "md" | "lg";

type Settings = {
  decimals: Decimals;
  fontSize: FontSize;
  controlsOnHover: boolean;
  set: (patch: Partial<Pick<Settings, "decimals" | "fontSize" | "controlsOnHover">>) => void;
};

/** Display settings; synced to the account when signed in (lib/prefs-sync). */
export const useSettings = create<Settings>()(
  persist(
    (set) => ({
      decimals: "auto",
      fontSize: "md",
      controlsOnHover: false,
      set: (patch) => set(patch),
    }),
    { name: "ac-settings", skipHydration: true },
  ),
);

/** Mirror settings onto <html> so CSS applies them (font size, controls on hover). */
export function applySettingsToDocument(s: Pick<Settings, "fontSize" | "controlsOnHover">) {
  const root = document.documentElement;
  root.dataset.font = s.fontSize;
  root.dataset.controls = s.controlsOnHover ? "hover" : "always";
}
