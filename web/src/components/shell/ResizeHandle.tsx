"use client";

import { COPILOT, SIDEBAR, useLayout } from "@/lib/layout-store";

type Pane = "sidebar" | "copilot";

/**
 * Drag (or arrow-key) handle on a pane's inner edge. The sidebar grows toward
 * the work area and the Copilot grows away from it, mirrored in RTL.
 */
export function ResizeHandle({ pane, className = "" }: { pane: Pane; className?: string }) {
  const width = useLayout((s) => (pane === "sidebar" ? s.sidebarWidth : s.copilotWidth));
  const range = pane === "sidebar" ? SIDEBAR : COPILOT;

  const setWidth = (px: number) => {
    const s = useLayout.getState();
    if (pane === "sidebar") s.setSidebarWidth(px);
    else s.setCopilotWidth(px);
  };

  // +1 when moving the pointer right should widen the pane.
  const sign = () => {
    const rtl = document.documentElement.dir === "rtl";
    return (pane === "sidebar" ? 1 : -1) * (rtl ? -1 : 1);
  };

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    const handle = e.currentTarget;
    const startX = e.clientX;
    const start = width;
    const dir = sign();
    handle.setPointerCapture(e.pointerId);
    document.body.style.cursor = "col-resize";

    const onMove = (ev: PointerEvent) => setWidth(start + dir * (ev.clientX - startX));
    const onUp = () => {
      handle.removeEventListener("pointermove", onMove);
      handle.removeEventListener("pointerup", onUp);
      document.body.style.cursor = "";
    };
    handle.addEventListener("pointermove", onMove);
    handle.addEventListener("pointerup", onUp);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const step = (e.key === "ArrowRight" ? 10 : -10) * sign();
    setWidth(width + step);
  };

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label={pane === "sidebar" ? "Resize sidebar" : "Resize Copilot"}
      aria-valuemin={range.min}
      aria-valuemax={range.max}
      aria-valuenow={width}
      tabIndex={0}
      onPointerDown={onPointerDown}
      onKeyDown={onKeyDown}
      className={`absolute inset-y-0 z-20 w-1.5 cursor-col-resize touch-none transition-colors hover:bg-signal/50 focus-visible:bg-signal/50 ${className}`}
    />
  );
}
