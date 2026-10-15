import { create } from "zustand";

/** A panel on screen that the Copilot can read: @-mention lists these, attaching reads `getData`. */
export type RegisteredPanel = {
  id: string;
  title: string;
  ticker?: string;
  getData?: () => unknown;
};

type Registry = {
  panels: Record<string, RegisteredPanel>;
  register: (p: RegisteredPanel) => void;
  unregister: (id: string, getData?: () => unknown) => void;
};

export const usePanelRegistry = create<Registry>()((set) => ({
  panels: {},
  register: (p) => set((s) => ({ panels: { ...s.panels, [p.id]: p } })),
  // Only remove the entry this instance registered (a hidden route may share the id).
  unregister: (id, getData) =>
    set((s) => {
      if (!s.panels[id] || (getData && s.panels[id].getData !== getData)) return s;
      const { [id]: _, ...rest } = s.panels;
      void _;
      return { panels: rest };
    }),
}));

/** Scroll to the visible copy of a panel and flash its border. False when it is not on screen. */
export function revealPanel(id: string): boolean {
  const el = [...document.querySelectorAll<HTMLElement>(`[data-panel="${CSS.escape(id)}"]`)].find((e) =>
    e.checkVisibility(),
  );
  if (!el) return false;
  el.scrollIntoView({ behavior: "smooth", block: "start" });
  el.dataset.flash = "1";
  window.setTimeout(() => delete el.dataset.flash, 1600);
  return true;
}
