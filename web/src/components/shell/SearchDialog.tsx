"use client";

import { MagnifyingGlassIcon } from "@radix-ui/react-icons";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { Dialog } from "radix-ui";
import { useEffect, useState } from "react";
import { useRouter } from "@/i18n/navigation";
import { api, type TickerHit } from "@/lib/api/client";
import { useLayout } from "@/lib/layout-store";

function useDebounced<T>(value: T, ms: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return debounced;
}

/** Cmd/Ctrl+K: find a ticker by symbol, English name or Arabic name. */
export function SearchDialog() {
  const t = useTranslations("search");
  const open = useLayout((s) => s.searchOpen);
  const setOpen = useLayout((s) => s.setSearchOpen);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const router = useRouter();
  const term = useDebounced(q.trim(), 120);

  const search = useQuery({
    queryKey: ["tickers", "search", term],
    queryFn: async ({ signal }) => {
      const { data, error } = await api.GET("/v1/tickers/search", {
        params: { query: { q: term, limit: 8 } },
        signal,
      });
      if (error || !data) throw new Error("search failed");
      return data;
    },
    enabled: open && term.length > 0,
    placeholderData: keepPreviousData,
  });

  const results = term ? (search.data?.results ?? []) : [];
  // Move the highlight back to the first row whenever the result set changes.
  const resultsKey = results.map((r) => r.ticker_key).join(",");
  const [shownKey, setShownKey] = useState(resultsKey);
  if (shownKey !== resultsKey) {
    setShownKey(resultsKey);
    setActive(0);
  }

  const close = (next: boolean) => {
    setOpen(next);
    if (!next) setQ("");
  };

  const go = (hit: TickerHit) => {
    close(false);
    router.push(`/t/${encodeURIComponent(hit.slug)}`);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!results.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(results[active]);
    }
  };

  let status: string | null = null;
  if (!term) status = t("hint");
  else if (search.isError) status = t("error");
  else if (search.isPending) status = t("loading");
  else if (!results.length && !search.isFetching) status = t("empty");

  return (
    <Dialog.Root open={open} onOpenChange={close}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-bg/75" />
        <Dialog.Content
          aria-describedby={undefined}
          className="fixed top-[12vh] left-1/2 z-50 flex w-[min(600px,calc(100vw-32px))] -translate-x-1/2 flex-col overflow-hidden rounded-panel border border-line bg-panel"
        >
          <Dialog.Title className="sr-only">{t("title")}</Dialog.Title>
          <div className="flex h-11 items-center gap-2 border-b border-line px-3">
            <MagnifyingGlassIcon className="shrink-0 text-muted" />
            <input
              autoFocus
              role="combobox"
              aria-expanded={results.length > 0}
              aria-controls="ticker-results"
              aria-activedescendant={results.length ? `ticker-${active}` : undefined}
              aria-label={t("title")}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={t("placeholder")}
              className="h-full min-w-0 flex-1 bg-transparent text-[14px] outline-none placeholder:text-muted"
            />
            <kbd className="num rounded-chip border border-line px-1 text-label text-muted">Esc</kbd>
          </div>

          {results.length > 0 && (
            <ul id="ticker-results" role="listbox" className="max-h-[60vh] overflow-y-auto p-1">
              {results.map((hit, i) => (
                <SearchRow
                  key={hit.ticker_key}
                  id={`ticker-${i}`}
                  hit={hit}
                  selected={i === active}
                  onHover={() => setActive(i)}
                  onPick={() => go(hit)}
                />
              ))}
            </ul>
          )}

          {status && (
            <p role="status" className="px-3 py-3 text-muted">
              {status}
            </p>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function SearchRow({
  id,
  hit,
  selected,
  onHover,
  onPick,
}: {
  id: string;
  hit: TickerHit;
  selected: boolean;
  onHover: () => void;
  onPick: () => void;
}) {
  const locale = useLocale();
  const tx = useTranslations("exchanges");
  const exchange = tx.has(hit.exchange) ? tx(hit.exchange) : hit.exchange;

  // Lead with the name in the reader's language; show the other underneath.
  // Each line keeps its own direction (so truncation ends on the right side)
  // but aligns to the row's start in the UI direction.
  const en = hit.name_en ? { text: hit.name_en, lang: "en", dir: "ltr" } : null;
  const ar = hit.name_ar ? { text: hit.name_ar, lang: "ar", dir: "rtl" } : null;
  const [primary, secondary] = locale === "ar" ? [ar ?? en, ar ? en : null] : [en ?? ar, en ? ar : null];
  const align = locale === "ar" ? "text-right" : "text-left";

  return (
    <li
      id={id}
      role="option"
      aria-selected={selected}
      onMouseMove={onHover}
      onClick={onPick}
      className="grid cursor-pointer grid-cols-[76px_minmax(0,1fr)_auto] items-center gap-3 rounded-panel px-2 py-1.5 aria-selected:bg-panel-raised"
    >
      <span className={`num text-[12px] ${selected ? "text-signal" : "text-text"}`}>{hit.symbol}</span>
      <span className="min-w-0">
        {primary && (
          <span lang={primary.lang} dir={primary.dir} className={`block truncate text-text ${align}`}>
            {primary.text}
          </span>
        )}
        {secondary && (
          <span lang={secondary.lang} dir={secondary.dir} className={`block truncate text-muted ${align}`}>
            {secondary.text}
          </span>
        )}
      </span>
      <span className="label-caps text-muted">{exchange}</span>
    </li>
  );
}
