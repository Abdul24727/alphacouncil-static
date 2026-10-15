"use client";

import { MagnifyingGlassIcon } from "@radix-ui/react-icons";
import { useLocale, useTranslations } from "next-intl";
import { useId, useState } from "react";
import type { TickerHit } from "@/lib/api/client";
import { useTickerSearch } from "@/lib/use-ticker-search";

/** Search box + keyboard-navigable result list; used by Cmd/Ctrl+K and panel ticker switchers. */
export function TickerPicker({
  onPick,
  compact = false,
  trailing,
}: {
  onPick: (hit: TickerHit) => void;
  compact?: boolean;
  trailing?: React.ReactNode;
}) {
  const t = useTranslations("search");
  const listId = useId();
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const { term, results, search } = useTickerSearch(q, { limit: compact ? 6 : 8 });

  // Move the highlight back to the first row whenever the result set changes.
  const resultsKey = results.map((r) => r.ticker_key).join(",");
  const [shownKey, setShownKey] = useState(resultsKey);
  if (shownKey !== resultsKey) {
    setShownKey(resultsKey);
    setActive(0);
  }

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
      onPick(results[active]);
    }
  };

  let status: string | null = null;
  if (!term) status = t("hint");
  else if (search.isError) status = t("error");
  else if (search.isPending) status = t("loading");
  else if (!results.length && !search.isFetching) status = t("empty");

  return (
    <>
      <div className={`flex items-center gap-2 border-b border-line px-3 ${compact ? "h-9" : "h-11"}`}>
        <MagnifyingGlassIcon className="shrink-0 text-muted" />
        <input
          autoFocus
          role="combobox"
          aria-expanded={results.length > 0}
          aria-controls={listId}
          aria-activedescendant={results.length ? `${listId}-${active}` : undefined}
          aria-label={t("title")}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={t("placeholder")}
          className={`h-full min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted ${compact ? "" : "text-[14px]"}`}
        />
        {trailing}
      </div>

      {results.length > 0 && (
        <ul id={listId} role="listbox" className={`overflow-y-auto p-1 ${compact ? "max-h-72" : "max-h-[60vh]"}`}>
          {results.map((hit, i) => (
            <TickerOption
              key={hit.ticker_key}
              id={`${listId}-${i}`}
              hit={hit}
              selected={i === active}
              onHover={() => setActive(i)}
              onPick={() => onPick(hit)}
            />
          ))}
        </ul>
      )}

      {status && (
        <p role="status" className="px-3 py-3 text-muted">
          {status}
        </p>
      )}
    </>
  );
}

function TickerOption({
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
  const tx = useTranslations("exchanges");
  const exchange = tx.has(hit.exchange) ? tx(hit.exchange) : hit.exchange;

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
      <TickerNames nameEn={hit.name_en} nameAr={hit.name_ar} />
      <span className="label-caps text-muted">{exchange}</span>
    </li>
  );
}

/**
 * Company name in the reader's language, the other language underneath.
 * Each line keeps its own direction (truncation ends on the correct side) but
 * aligns to the start of the UI direction.
 */
export function TickerNames({
  nameEn,
  nameAr,
  single = false,
}: {
  nameEn: string | null | undefined;
  nameAr: string | null | undefined;
  single?: boolean;
}) {
  const locale = useLocale();
  const en = nameEn ? { text: nameEn, lang: "en", dir: "ltr" } : null;
  const ar = nameAr ? { text: nameAr, lang: "ar", dir: "rtl" } : null;
  const [primary, secondary] = locale === "ar" ? [ar ?? en, ar ? en : null] : [en ?? ar, en ? ar : null];
  const align = locale === "ar" ? "text-right" : "text-left";

  return (
    <span className="min-w-0">
      {primary && (
        <span lang={primary.lang} dir={primary.dir} className={`block truncate text-text ${align}`}>
          {primary.text}
        </span>
      )}
      {secondary && !single && (
        <span lang={secondary.lang} dir={secondary.dir} className={`block truncate text-muted ${align}`}>
          {secondary.text}
        </span>
      )}
    </span>
  );
}
