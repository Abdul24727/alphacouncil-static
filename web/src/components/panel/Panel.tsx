"use client";

import {
  ChatBubbleIcon,
  CheckIcon,
  CopyIcon,
  DotsHorizontalIcon,
  EnterFullScreenIcon,
  ExitFullScreenIcon,
  ReloadIcon,
} from "@radix-ui/react-icons";
import { useLocale, useTranslations } from "next-intl";
import { DropdownMenu, Tooltip } from "radix-ui";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import type { Freshness } from "@/lib/api/client";
import { useCopilot } from "@/lib/copilot-store";
import { usePanelRegistry } from "@/lib/panel-registry";
import { fmtDate, fmtStamp } from "@/lib/format";
import { GROUP_COLOR, type GroupId } from "@/lib/ticker-groups";
import { TickerSwitcher } from "@/components/ticker/TickerSwitcher";

type PanelProps = {
  /** Stable id: Copilot citations scroll to `#panel-<id>`. */
  id: string;
  title: string;
  group?: GroupId | null;
  /** The group chip doubles as the ticker switcher (default when a group is set). */
  switchable?: boolean;
  /** undefined = this panel has no freshness concept; null = unknown. */
  freshness?: Freshness | null;
  ticker?: string;
  /** Tab-separated rows for "Copy data". */
  copyData?: () => string | null;
  /** What the Copilot receives when this panel is attached. */
  copilotData?: () => unknown;
  onRefresh?: () => void;
  /** Extra header controls. */
  actions?: React.ReactNode;
  /** Panel-specific menu entries (checkbox entries when `checked` is set). */
  menuItems?: PanelMenuItem[];
  className?: string;
  bodyClassName?: string;
  children: React.ReactNode;
};

export type PanelMenuItem = { key: string; label: string; checked?: boolean; onSelect: () => void };

export function Panel({
  id,
  title,
  group,
  switchable = true,
  freshness,
  ticker,
  copyData,
  copilotData,
  onRefresh,
  actions,
  menuItems,
  className = "",
  bodyClassName = "p-3",
  children,
}: PanelProps) {
  const t = useTranslations("panel");
  const [full, setFull] = useState(false);
  const attached = useCopilot((s) => s.attached.some((p) => p.id === id));
  const attach = useCopilot((s) => s.attach);
  const detach = useCopilot((s) => s.detach);

  useEffect(() => {
    if (!full) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setFull(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [full]);

  // Register with the Copilot so @-mentions can list this panel and attaching reads fresh data.
  const getData = useRef(copilotData);
  useEffect(() => {
    getData.current = copilotData;
  });
  useEffect(() => {
    const read = () => getData.current?.();
    usePanelRegistry.getState().register({ id, title, ticker, getData: read });
    return () => usePanelRegistry.getState().unregister(id, read);
  }, [id, title, ticker]);

  const toggleCopilot = () => (attached ? detach(id) : attach({ id, title, ticker }));

  return (
    <>
      {full && <div aria-hidden className="fixed inset-0 z-40 bg-bg/80" onClick={() => setFull(false)} />}
      <section
        id={`panel-${id}`}
        aria-label={title}
        data-panel={id}
        className={`flex min-w-0 scroll-mt-3 flex-col rounded-panel border border-line bg-panel transition-[border-color] duration-500 data-[flash]:border-signal ${
          full ? "fixed inset-3 z-50" : className
        }`}
      >
        <header className="flex h-11 shrink-0 items-center gap-2 border-b border-line ps-3 pe-1.5">
          {freshness !== undefined && <FreshnessLight freshness={freshness} />}
          {group &&
            (switchable ? (
              <TickerSwitcher group={group} />
            ) : (
              <span
                aria-label={t("group", { group })}
                title={t("group", { group })}
                className={`size-2 shrink-0 rounded-[2px] ${GROUP_COLOR[group]}`}
              />
            ))}
          <h2 className="headline min-w-0 truncate text-panel-title" title={title}>
            {title}
          </h2>
          <div className="panel-controls ms-auto flex shrink-0 items-center gap-0.5">
            {actions}
            <HeaderButton
              label={attached ? t("removeFromCopilot") : t("addToCopilot")}
              onClick={toggleCopilot}
              pressed={attached}
            >
              <ChatBubbleIcon />
            </HeaderButton>
            <HeaderButton label={full ? t("exitFullscreen") : t("fullscreen")} onClick={() => setFull(!full)}>
              {full ? <ExitFullScreenIcon /> : <EnterFullScreenIcon />}
            </HeaderButton>
            <PanelMenu copyData={copyData} onRefresh={onRefresh} items={menuItems} />
          </div>
        </header>
        <div className={`min-h-0 flex-1 ${full ? "overflow-auto" : ""} ${bodyClassName}`}>
          <PanelRefresh.Provider value={onRefresh}>{children}</PanelRefresh.Provider>
        </div>
      </section>
    </>
  );
}

export function FreshnessLight({ freshness }: { freshness: Freshness | null }) {
  const locale = useLocale();
  const t = useTranslations("panel");
  const state = freshness?.stale == null ? "unknown" : freshness.stale ? "stale" : "fresh";
  const color = { fresh: "bg-gain", stale: "bg-stale", unknown: "bg-neutral-seat" }[state];

  const updated = fmtStamp(freshness?.updated_at ?? freshness?.as_of, locale);
  const next = fmtStamp(freshness?.next_at, locale);
  const asOf = fmtDate(freshness?.as_of, locale);

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <span
          role="img"
          tabIndex={0}
          aria-label={t(`freshness.${state}`)}
          data-freshness={state}
          className={`size-2 shrink-0 rounded-full ${color}`}
        />
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          sideOffset={6}
          className="z-50 flex flex-col gap-0.5 rounded-chip border border-line bg-panel-raised px-2 py-1.5 text-text"
        >
          {freshness ? (
            <>
              <span className="num">
                {t("updated")} {updated ?? "—"} · {t("next")} {next ?? "—"}
              </span>
              <span className="text-muted">
                {t(`freshness.${state}`)}
                {asOf && (
                  <>
                    {" · "}
                    {t("asOf")} <span className="num">{asOf}</span>
                  </>
                )}
              </span>
            </>
          ) : (
            <span className="text-muted">{t("freshness.unknown")}</span>
          )}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

function HeaderButton({
  label,
  onClick,
  pressed,
  children,
}: {
  label: string;
  onClick: () => void;
  pressed?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <button
          type="button"
          aria-label={label}
          aria-pressed={pressed}
          onClick={onClick}
          className={`grid size-7 place-items-center rounded-panel hover:bg-panel-raised ${
            pressed ? "text-signal" : "text-muted hover:text-text"
          }`}
        >
          {children}
        </button>
      </Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content sideOffset={6} className="z-50 rounded-chip border border-line bg-panel-raised px-2 py-1 text-text">
          {label}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

function PanelMenu({
  copyData,
  onRefresh,
  items,
}: {
  copyData?: () => string | null;
  onRefresh?: () => void;
  items?: PanelMenuItem[];
}) {
  const t = useTranslations("panel");
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const text = copyData?.();
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const item =
    "flex h-8 cursor-pointer items-center gap-2 rounded-chip px-2 outline-none data-[disabled]:cursor-not-allowed data-[disabled]:text-muted data-[highlighted]:bg-panel-raised";

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          aria-label={t("menu")}
          className="grid size-7 place-items-center rounded-panel text-muted hover:bg-panel-raised hover:text-text"
        >
          <DotsHorizontalIcon />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={4}
          className="z-50 min-w-40 rounded-panel border border-line bg-panel p-1 text-text"
        >
          <DropdownMenu.Item className={item} disabled={!copyData} onSelect={copy}>
            {copied ? <CheckIcon className="text-gain" /> : <CopyIcon />}
            {copied ? t("copied") : t("copyData")}
          </DropdownMenu.Item>
          <DropdownMenu.Item className={item} disabled={!onRefresh} onSelect={() => onRefresh?.()}>
            <ReloadIcon />
            {t("refresh")}
          </DropdownMenu.Item>
          {items && items.length > 0 && <DropdownMenu.Separator className="my-1 h-px bg-line" />}
          {items?.map((it) =>
            it.checked === undefined ? (
              <DropdownMenu.Item key={it.key} className={item} onSelect={it.onSelect}>
                <span className="size-[15px]" />
                {it.label}
              </DropdownMenu.Item>
            ) : (
              <DropdownMenu.CheckboxItem
                key={it.key}
                className={item}
                checked={it.checked}
                // Keep the menu open so several indicators can be toggled in a row.
                onSelect={(e) => e.preventDefault()}
                onCheckedChange={it.onSelect}
              >
                <span className="grid size-[15px] place-items-center rounded-[3px] border border-line">
                  <DropdownMenu.ItemIndicator>
                    <CheckIcon className="text-signal" />
                  </DropdownMenu.ItemIndicator>
                </span>
                {it.label}
              </DropdownMenu.CheckboxItem>
            ),
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}

/** Loading state: grey bars, never placeholder numbers. */
export function PanelLoading({ rows = 4 }: { rows?: number }) {
  return (
    <div aria-busy className="flex flex-col gap-2">
      {Array.from({ length: rows }, (_, i) => (
        <span key={i} className="h-3 animate-pulse rounded-chip bg-panel-raised" style={{ width: `${90 - i * 12}%` }} />
      ))}
    </div>
  );
}

/** The panel's refresh, so a failed load inside it can offer "Try again". */
const PanelRefresh = createContext<(() => void) | undefined>(undefined);
export const usePanelRefresh = () => useContext(PanelRefresh);

/** BRAND.md: missing data is a labelled placeholder, never an estimate. */
export function PanelUnavailable({ detail, onRetry }: { detail?: string; onRetry?: () => void }) {
  const t = useTranslations("placeholder");
  return (
    <div className="flex h-full min-h-20 flex-col items-start justify-center gap-1">
      <span className="label-caps text-muted">{t("unavailable")}</span>
      {detail && <span className="text-muted">{detail}</span>}
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-1 rounded-chip border border-line px-2 py-0.5 text-text hover:bg-panel-raised">
          {t("retry")}
        </button>
      )}
    </div>
  );
}
