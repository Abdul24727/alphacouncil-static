"use client";

import { ChatBubbleIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { useLayout } from "@/lib/layout-store";
import { Kbd } from "./Kbd";

/** Title row at the top of the work area. */
export function WorkHeader({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-line px-4">
      <h1 className="headline truncate text-panel-title">{title}</h1>
      {children}
      <CopilotOpenButton />
    </header>
  );
}

/** Shown at the end of a header row while the Copilot pane is closed (desktop). */
export function CopilotOpenButton() {
  const t = useTranslations("copilot");
  const toggleCopilot = useLayout((s) => s.toggleCopilot);
  return (
    <button
      type="button"
      onClick={toggleCopilot}
      className="ms-auto hidden h-7 shrink-0 items-center gap-2 rounded-panel border border-line px-2 text-muted hover:text-text md:copilot-closed:flex"
    >
      <ChatBubbleIcon />
      {t("open")}
      <Kbd k="L" />
    </button>
  );
}
