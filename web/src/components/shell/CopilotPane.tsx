"use client";

import { Cross2Icon, EnterFullScreenIcon, ExitFullScreenIcon, PaperPlaneIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { Tooltip } from "radix-ui";
import { useLayout } from "@/lib/layout-store";
import { Kbd } from "./Kbd";
import { ResizeHandle } from "./ResizeHandle";

/**
 * Right-hand Copilot frame (left in Arabic). Phase 4 fills it: context chips,
 * reasoning, answers citing panels, pin to dashboard, follow-ups.
 */
export function CopilotPane() {
  const t = useTranslations("copilot");
  const fullscreen = useLayout((s) => s.copilotFullscreen);
  const mobileOpen = useLayout((s) => s.mobileCopilotOpen);
  const toggleCopilot = useLayout((s) => s.toggleCopilot);
  const toggleFullscreen = useLayout((s) => s.toggleCopilotFullscreen);
  const setMobileOpen = useLayout((s) => s.setMobileCopilotOpen);

  const close = () => {
    if (window.matchMedia("(max-width: 767px)").matches) setMobileOpen(false);
    else toggleCopilot();
  };

  return (
    <aside
      aria-label={t("title")}
      className={`relative flex w-[var(--copilot-w)] shrink-0 flex-col border-s border-line bg-panel md:copilot-closed:hidden md:copilot-full:w-auto md:copilot-full:flex-1 ${
        mobileOpen ? "max-md:fixed max-md:inset-0 max-md:z-40 max-md:w-full" : "max-md:hidden"
      }`}
    >
      <header className="flex h-12 shrink-0 items-center gap-1 border-b border-line ps-3 pe-2">
        <h2 className="headline text-[17px] leading-none">{t("title")}</h2>
        <div className="ms-auto flex items-center gap-0.5">
          <IconButton
            label={fullscreen ? t("exitFullscreen") : t("fullscreen")}
            onClick={toggleFullscreen}
            className="max-md:hidden"
          >
            {fullscreen ? <ExitFullScreenIcon /> : <EnterFullScreenIcon />}
          </IconButton>
          <IconButton label={t("close")} shortcut="L" onClick={close}>
            <Cross2Icon />
          </IconButton>
        </div>
      </header>

      <section aria-label={t("context")} className="flex shrink-0 items-center gap-2 border-b border-line px-3 py-2">
        <span className="label-caps text-muted">{t("context")}</span>
        <span className="rounded-chip border border-dashed border-line px-1.5 py-0.5 text-muted">
          {t("noContext")}
        </span>
      </section>

      <div className="flex min-h-0 flex-1 flex-col justify-end overflow-y-auto p-3">
        <p className="max-w-[36ch] text-muted">{t("comingSoon")}</p>
      </div>

      <form className="shrink-0 border-t border-line p-2" onSubmit={(e) => e.preventDefault()}>
        <div className="flex items-end gap-2 rounded-panel border border-line bg-bg p-2">
          <textarea
            rows={2}
            disabled
            placeholder={t("placeholder")}
            aria-label={t("placeholder")}
            className="min-h-10 flex-1 resize-none bg-transparent outline-none placeholder:text-muted disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled
            aria-label="Send"
            className="grid size-7 place-items-center rounded-panel bg-signal text-signal-ink disabled:opacity-40"
          >
            <PaperPlaneIcon className="rtl:-scale-x-100" />
          </button>
        </div>
      </form>

      <ResizeHandle pane="copilot" className="start-[-3px] max-md:hidden copilot-full:hidden" />
    </aside>
  );
}

function IconButton({
  label,
  shortcut,
  onClick,
  className = "",
  children,
}: {
  label: string;
  shortcut?: string;
  onClick: () => void;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          className={`grid size-7 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text ${className}`}
        >
          {children}
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          sideOffset={6}
          className="z-50 flex items-center gap-2 rounded-chip border border-line bg-panel-raised px-2 py-1 text-text"
        >
          {label}
          {shortcut && <Kbd k={shortcut} />}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
