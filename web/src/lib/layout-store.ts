import { create } from "zustand";
import { persist } from "zustand/middleware";

// Pane ranges from the plan: sidebar 190–230px, Copilot 320–360px.
export const SIDEBAR = { min: 190, max: 230, initial: 210 } as const;
export const COPILOT = { min: 320, max: 360, initial: 340 } as const;

const STORAGE_KEY = "ac-layout";
// "1" while this browser's last answer from /v1/auth/me was a signed-in member (AppShell keeps
// it). Lets LAYOUT_BOOT_SCRIPT tell a visitor from a member before the first paint.
const MEMBER_KEY = "ac-member";

const clamp = (value: number, range: { min: number; max: number }) =>
  Math.round(Math.min(range.max, Math.max(range.min, value)));

type LayoutState = {
  sidebarWidth: number;
  sidebarCollapsed: boolean;
  copilotWidth: number;
  copilotOpen: boolean;
  /** Signed in (true), signed out (false), or not known yet (null: the boot mark decides). */
  member: boolean | null;
  /** A signed-out visitor's Copilot: closed on every visit, never persisted or synced. */
  guestCopilotOpen: boolean;
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
  setMember: (member: boolean) => void;
};

/** Whether the last /v1/auth/me in this browser was a member. Client only. */
export function hasMemberMark(): boolean {
  try {
    return localStorage.getItem(MEMBER_KEY) === "1";
  } catch {
    return false;
  }
}

export function setMemberMark(member: boolean) {
  try {
    if (member) localStorage.setItem(MEMBER_KEY, "1");
    else localStorage.removeItem(MEMBER_KEY);
  } catch {
    // Storage blocked: the pane just follows /v1/auth/me once it answers.
  }
}

/**
 * Signed-out visitors get the Copilot closed by default (design fix 7, owner 2026-11-21): the
 * data first, with one "Ask the Copilot" button. Members keep their persisted, synced
 * `copilotOpen` exactly as before.
 */
const isGuest = (s: Pick<LayoutState, "member">) => (s.member === null ? !hasMemberMark() : !s.member);

// Persisted in this browser for now. Once /api has accounts, the same fields
// move to the user's server-side preferences so they follow the user.
export const useLayout = create<LayoutState>()(
  persist(
    (set) => ({
      sidebarWidth: SIDEBAR.initial,
      sidebarCollapsed: false,
      copilotWidth: COPILOT.initial,
      copilotOpen: true,
      member: null,
      guestCopilotOpen: false,
      copilotFullscreen: false,
      mobileCopilotOpen: false,
      searchOpen: false,
      setSidebarWidth: (px) => set({ sidebarWidth: clamp(px, SIDEBAR) }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setCopilotWidth: (px) => set({ copilotWidth: clamp(px, COPILOT) }),
      toggleCopilot: () =>
        set((s) =>
          isGuest(s)
            ? { guestCopilotOpen: !s.guestCopilotOpen, copilotFullscreen: false }
            : { copilotOpen: !s.copilotOpen, copilotFullscreen: false },
        ),
      toggleCopilotFullscreen: () =>
        set((s) =>
          isGuest(s)
            ? { guestCopilotOpen: true, copilotFullscreen: !s.copilotFullscreen }
            : { copilotOpen: true, copilotFullscreen: !s.copilotFullscreen },
        ),
      setMobileCopilotOpen: (open) => set({ mobileCopilotOpen: open }),
      setSearchOpen: (open) => set({ searchOpen: open }),
      setMember: (member) => set((s) => (s.member === member ? s : { member, copilotFullscreen: s.member === null ? s.copilotFullscreen : false })),
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
  const open = isGuest(s) ? s.guestCopilotOpen : s.copilotOpen;
  root.dataset.copilot = !open ? "closed" : s.copilotFullscreen ? "full" : "open";
}

/**
 * Runs in <head> before first paint and applies the saved pane sizes, so a
 * reload never flashes the default layout or display settings. Keep in sync with
 * applyLayoutToDocument and applySettingsToDocument.
 */
export const LAYOUT_BOOT_SCRIPT = `(function(){try{var s=JSON.parse(localStorage.getItem(${JSON.stringify(
  STORAGE_KEY,
)})||"null");s=s&&s.state;var d=document.documentElement;if(s){if(s.sidebarWidth)d.style.setProperty("--sidebar-w",s.sidebarWidth+"px");if(s.copilotWidth)d.style.setProperty("--copilot-w",s.copilotWidth+"px");d.dataset.sidebar=s.sidebarCollapsed?"collapsed":"expanded";}var m=localStorage.getItem(${JSON.stringify(MEMBER_KEY)})==="1";d.dataset.copilot=!m||(s&&s.copilotOpen===false)?"closed":"open";}catch(e){}try{var g=JSON.parse(localStorage.getItem("ac-settings")||"null");g=g&&g.state;if(g){var r=document.documentElement;if(g.fontSize)r.dataset.font=g.fontSize;r.dataset.controls=g.controlsOnHover?"hover":"always";}}catch(e){}})()`;
