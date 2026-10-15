import { create } from "zustand";
import { persist } from "zustand/middleware";

// Pane ranges from the plan: sidebar 190–230px, Copilot 320–360px.
export const SIDEBAR = { min: 190, max: 230, initial: 210 } as const;
export const COPILOT = { min: 320, max: 360, initial: 340 } as const;

const STORAGE_KEY = "ac-layout";

const clamp = (value: number, range: { min: number; max: number }) =>
  Math.round(Math.min(range.max, Math.max(range.min, value)));

type LayoutState = {
  sidebarWidth: number;
  sidebarCollapsed: boolean;
  copilotWidth: number;
  copilotOpen: boolean;
  copilotFullscreen: boolean;
  mobileCopilotOpen: boolean;
  searchOpen: boolean;
  setSidebarWidth: (px: number) => void;
  toggleSidebar: () => void;
  setCopilotWidth: (px: number) => void;
  toggleCopilot: () => void;
  toggleCopilotFullscreen: () => void;
  setMobileCopilotOpen: (open: boolean) => void;
  setSearchOpen: (open: boolean) => void;
};

// Persisted in this browser for now. Once /api has accounts, the same fields
// move to the user's server-side preferences so they follow the user.
export const useLayout = create<LayoutState>()(
  persist(
    (set) => ({
      sidebarWidth: SIDEBAR.initial,
      sidebarCollapsed: false,
      copilotWidth: COPILOT.initial,
      copilotOpen: true,
      copilotFullscreen: false,
      mobileCopilotOpen: false,
      searchOpen: false,
      setSidebarWidth: (px) => set({ sidebarWidth: clamp(px, SIDEBAR) }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setCopilotWidth: (px) => set({ copilotWidth: clamp(px, COPILOT) }),
      toggleCopilot: () =>
        set((s) => ({ copilotOpen: !s.copilotOpen, copilotFullscreen: false })),
      toggleCopilotFullscreen: () =>
        set((s) => ({ copilotOpen: true, copilotFullscreen: !s.copilotFullscreen })),
      setMobileCopilotOpen: (open) => set({ mobileCopilotOpen: open }),
      setSearchOpen: (open) => set({ searchOpen: open }),
    }),
    {
      name: STORAGE_KEY,
      skipHydration: true,
      partialize: (s) => ({
        sidebarWidth: s.sidebarWidth,
        sidebarCollapsed: s.sidebarCollapsed,
        copilotWidth: s.copilotWidth,
        copilotOpen: s.copilotOpen,
      }),
    },
  ),
);

/** Mirrors layout state onto <html> so CSS sizes the panes. */
export function applyLayoutToDocument(s: LayoutState) {
  const root = document.documentElement;
  root.style.setProperty("--sidebar-w", `${s.sidebarWidth}px`);
  root.style.setProperty("--copilot-w", `${s.copilotWidth}px`);
  root.dataset.sidebar = s.sidebarCollapsed ? "collapsed" : "expanded";
  root.dataset.copilot = !s.copilotOpen ? "closed" : s.copilotFullscreen ? "full" : "open";
}

/**
 * Runs in <head> before first paint and applies the saved pane sizes, so a
 * reload never flashes the default layout. Keep in sync with applyLayoutToDocument.
 */
export const LAYOUT_BOOT_SCRIPT = `(function(){try{var s=JSON.parse(localStorage.getItem(${JSON.stringify(
  STORAGE_KEY,
)})||"null");s=s&&s.state;if(!s)return;var d=document.documentElement;if(s.sidebarWidth)d.style.setProperty("--sidebar-w",s.sidebarWidth+"px");if(s.copilotWidth)d.style.setProperty("--copilot-w",s.copilotWidth+"px");d.dataset.sidebar=s.sidebarCollapsed?"collapsed":"expanded";d.dataset.copilot=s.copilotOpen===false?"closed":"open";}catch(e){}})()`;
