"use client";

import { useTranslations } from "next-intl";
import { Num, priceDigits } from "@/components/stock/common";
import { TickerNames } from "@/components/ticker/TickerPicker";
import { useRouter } from "@/i18n/navigation";
import type { components } from "@/lib/api/schema";
import { fmtNumber, fmtPct, signClass } from "@/lib/format";

type TickerRef = components["schemas"]["TickerRef"];
type LastClose = components["schemas"]["LastClose"];

/** Exchange code -> localised short name. */
export function useExchangeName() {
  const tx = useTranslations("exchanges");
  return (code: string) => (tx.has(code) ? tx(code) : code);
}

export function useOpenTicker() {
  const router = useRouter();
  return (t: Pick<TickerRef, "slug">) => router.push(`/t/${encodeURIComponent(t.slug)}`);
}

/** Symbol + name cell used across market tables. */
export function TickerCell({ ticker }: { ticker: TickerRef }) {
  return (
    <div className="flex min-w-0 items-baseline gap-2">
      <span className="num w-[4.75rem] shrink-0 truncate text-[12px] text-text" title={ticker.symbol}>
        {ticker.symbol}
      </span>
      <TickerNames nameEn={ticker.name_en} nameAr={ticker.name_ar} single />
    </div>
  );
}

export function PriceCell({ price, currency }: { price: LastClose; currency: string | null | undefined }) {
  return <Num value={fmtNumber(price.close, priceDigits(currency))} />;
}

export function ChangeCell({ value }: { value: number | null | undefined }) {
  return <Num value={fmtPct(value, 2, true)} className={signClass(value)} />;
}

/** A clickable table row that opens the ticker's stock page. */
export function TickerRow({ ticker, children }: { ticker: TickerRef; children: React.ReactNode }) {
  const open = useOpenTicker();
  return (
    <tr
      tabIndex={0}
      data-ticker-row={ticker.slug}
      onClick={() => open(ticker)}
      onKeyDown={(e) => e.key === "Enter" && open(ticker)}
      className="cursor-pointer border-t border-line hover:bg-panel-raised focus-visible:bg-panel-raised"
    >
      {children}
    </tr>
  );
}

export function Th({ children, end = false, className = "" }: { children?: React.ReactNode; end?: boolean; className?: string }) {
  return <th className={`label-caps py-1.5 font-normal text-muted ${end ? "text-end" : "text-start"} ${className}`}>{children}</th>;
}
