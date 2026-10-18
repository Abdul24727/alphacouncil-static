"use client";

import { useEffect } from "react";
import { VerifyEmailBanner } from "@/components/auth/VerifyEmailView";
import { useChartPrefs } from "@/lib/chart-prefs";
import { applyLayoutToDocument, useLayout } from "@/lib/layout-store";
import { usePrefsSync } from "@/lib/prefs-sync";
import { applySettingsToDocument, useSettings } from "@/lib/settings-store";
import { CopilotPane } from "./CopilotPane";
import { MobileTabBar } from "./MobileTabBar";
import { SearchDialog } from "./SearchDialog";
import { Sidebar } from "./Sidebar";

/** Signed-in shell: sidebar · work area · Copilot, mirrored in Arabic. */
export function AppShell({ children }: { children: React.ReactNode }) {
  useLayoutSync();
  usePrefsSync();
  useShortcuts();

  return (
    <div className="flex h-dvh overflow-hidden">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden max-md:pb-14 md:copilot-full:hidden">
        <VerifyEmailBanner />
        {children}
      </main>
      <CopilotPane />
      <MobileTabBar />
      <SearchDialog />
    </div>
  );
}

/** Restore saved pane sizes, then mirror every change onto <html>. */
function useLayoutSync() {
  useEffect(() => {
    const unsubscribe = useLayout.subscribe(applyLayoutToDocument);
    const unsubSettings = useSettings.subscribe(applySettingsToDocument);
    void useLayout.persist.rehydrate();
    void useChartPrefs.persist.rehydrate();
    void useSettings.persist.rehydrate();
    return () => {
      unsubscribe();
      unsubSettings();
    };
  }, []);
}

function useShortcuts() {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return;
      const s = useLayout.getState();
      const mobile = window.matchMedia("(max-width: 767px)").matches;
      switch (e.key.toLowerCase()) {
        case "k":
          e.preventDefault();
          s.setSearchOpen(!s.searchOpen);
          break;
        case "b":
          e.preventDefault();
          s.toggleSidebar();
          break;
        case "l":
          e.preventDefault();
          if (mobile) s.setMobileCopilotOpen(!s.mobileCopilotOpen);
          else s.toggleCopilot();
          break;
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
