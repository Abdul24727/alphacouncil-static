"use client";

import { useTranslations } from "next-intl";
import { Popover } from "radix-ui";
import { useState } from "react";
import { useTickerDetail } from "@/lib/queries";
import { GROUP_COLOR, type GroupId, useGroupTicker, useTickerGroups } from "@/lib/ticker-groups";
import { TickerPicker } from "./TickerPicker";

/**
 * The panel header's group-colour chip (BRAND.md header order: freshness light ·
 * group colour · title). It shows the group's ticker; picking another ticker
 * switches every panel in the group.
 */
export function TickerSwitcher({ group }: { group: GroupId }) {
  const t = useTranslations("ticker");
  const tp = useTranslations("panel");
  const slug = useGroupTicker(group);
  const symbol = useTickerDetail(slug).data?.ticker.symbol;
  const setGroupTicker = useTickerGroups((s) => s.setGroupTicker);
  const [open, setOpen] = useState(false);

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`${tp("group", { group })} · ${t("switch")}`}
          title={t("switch")}
          data-ticker-switcher={group}
          className="flex h-6 shrink-0 items-center gap-1.5 rounded-chip px-1 hover:bg-panel-raised"
        >
          <span aria-hidden className={`size-2 rounded-[2px] ${GROUP_COLOR[group]}`} />
          <span className="num text-[11px] text-text-soft">{symbol ?? slug ?? "—"}</span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="start"
          sideOffset={6}
          className="z-50 flex w-[min(380px,calc(100vw-24px))] flex-col overflow-hidden rounded-panel border border-line bg-panel"
        >
          <TickerPicker
            compact
            onPick={(hit) => {
              setGroupTicker(group, hit.slug);
              setOpen(false);
            }}
          />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
