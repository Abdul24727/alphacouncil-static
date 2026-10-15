"use client";

import { useSyncExternalStore } from "react";

const subscribe = () => () => {};
const isMac = () => /Mac|iPhone|iPad/.test(navigator.platform);

/** Shortcut hint: "⌘K" on Apple devices, "Ctrl K" elsewhere. */
export function Kbd({ k }: { k: string }) {
  const mac = useSyncExternalStore(subscribe, isMac, () => false);
  return (
    <kbd className="num rounded-chip border border-line px-1 text-label leading-4 text-muted">
      {mac ? `⌘${k}` : `Ctrl ${k}`}
    </kbd>
  );
}
