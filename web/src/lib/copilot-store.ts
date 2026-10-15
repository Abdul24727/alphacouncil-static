import { create } from "zustand";

/** A panel attached to the Copilot as context (Phase 4 reads `data` when answering). */
export type AttachedPanel = {
  id: string;
  title: string;
  ticker?: string;
  data?: unknown;
};

type CopilotState = {
  attached: AttachedPanel[];
  attach: (panel: AttachedPanel) => void;
  detach: (id: string) => void;
  isAttached: (id: string) => boolean;
};

export const useCopilot = create<CopilotState>()((set, get) => ({
  attached: [],
  attach: (panel) =>
    set((s) => ({ attached: [...s.attached.filter((p) => p.id !== panel.id), panel] })),
  detach: (id) => set((s) => ({ attached: s.attached.filter((p) => p.id !== id) })),
  isAttached: (id) => get().attached.some((p) => p.id === id),
}));
