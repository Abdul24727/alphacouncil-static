import { create } from "zustand";
import { usePanelRegistry } from "./panel-registry";

/** A panel attached to the Copilot as context. Its data is read fresh when a question is sent. */
export type AttachedPanel = {
  id: string;
  title: string;
  ticker?: string;
};

type CopilotState = {
  attached: AttachedPanel[];
  attach: (panel: AttachedPanel) => void;
  detach: (id: string) => void;
  clear: () => void;
};

export const useCopilot = create<CopilotState>()((set) => ({
  attached: [],
  attach: (panel) => set((s) => ({ attached: [...s.attached.filter((p) => p.id !== panel.id), panel] })),
  detach: (id) => set((s) => ({ attached: s.attached.filter((p) => p.id !== id) })),
  clear: () => set({ attached: [] }),
}));

/** Attached panels with their current data, as sent to /api/v1/copilot/chat. */
export function attachedWithData() {
  const registry = usePanelRegistry.getState().panels;
  return useCopilot.getState().attached.map((p) => {
    const live = registry[p.id];
    return { ...p, ticker: live?.ticker ?? p.ticker, data: live?.getData?.() ?? null };
  });
}
