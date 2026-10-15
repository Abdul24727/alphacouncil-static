"use client";

import { ChatBubbleIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { useLayout } from "@/lib/layout-store";
import { Kbd } from "./Kbd";

/** Title row at the top of the work area. Phase 2 adds the ticker header and page tabs below it. */
export function WorkHeader({ title, children }: { title: string; children?: React.ReactNode }) {
  const t = useTranslations("copilot");
  const toggleCopilot = useLayout((s) => s.toggleCopilot);

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-line px-4">
      <h1 className="headline truncate text-panel-title">{title}</h1>
      {children}
      <button
        type="button"
        onClick={toggleCopilot}
        className="ms-auto hidden h-7 items-center gap-2 rounded-panel border border-line px-2 text-muted hover:text-text md:copilot-closed:flex"
      >
        <ChatBubbleIcon />
        {t("open")}
        <Kbd k="L" />
      </button>
    </header>
  );
}
