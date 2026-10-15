"use client";

import { useTranslations } from "next-intl";
import { Dialog } from "radix-ui";
import { TickerPicker } from "@/components/ticker/TickerPicker";
import { useRouter } from "@/i18n/navigation";
import { useLayout } from "@/lib/layout-store";

/** Cmd/Ctrl+K: find a ticker by symbol, English name or Arabic name. */
export function SearchDialog() {
  const t = useTranslations("search");
  const open = useLayout((s) => s.searchOpen);
  const setOpen = useLayout((s) => s.setSearchOpen);
  const router = useRouter();

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-bg/75" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed top-[12vh] left-1/2 z-50 flex w-[min(600px,calc(100vw-32px))] -translate-x-1/2 flex-col overflow-hidden rounded-panel border border-line bg-panel"
        >
          <Dialog.Title className="sr-only">{t("title")}</Dialog.Title>
          {/* Mounted only while open, so the query box starts empty each time. */}
          <TickerPicker
            onPick={(hit) => {
              setOpen(false);
              router.push(`/t/${encodeURIComponent(hit.slug)}`);
            }}
            trailing={<kbd className="num rounded-chip border border-line px-1 text-label text-muted">Esc</kbd>}
          />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
