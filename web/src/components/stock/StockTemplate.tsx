"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useLayoutEffect, useRef } from "react";
import { FreshnessLight } from "@/components/panel/Panel";
import { CopilotOpenButton } from "@/components/shell/WorkHeader";
import { TickerNames } from "@/components/ticker/TickerPicker";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { currencyLabel, fmtDate, fmtNumber, fmtPct, signClass } from "@/lib/format";
import { useTickerDetail } from "@/lib/queries";
import { GROUP_COLOR, useGroupTicker, useTickerGroups } from "@/lib/ticker-groups";

export const STOCK_TABS = ["overview", "financials", "council", "ownership", "calendar"] as const;
export type StockTab = (typeof STOCK_TABS)[number];

function tabOf(pathname: string): StockTab {
  const seg = pathname.split("/")[3] as StockTab | undefined;
  return seg && STOCK_TABS.includes(seg) ? seg : "overview";
}

const hrefFor = (slug: string, tab: StockTab) =>
  `/t/${encodeURIComponent(slug)}${tab === "overview" ? "" : `/${tab}`}`;

/**
 * Tadawul Stock template frame. Group 1's ticker follows the URL; changing it
 * from any panel (ticker switcher, peers row) navigates to that ticker on the
 * same tab, so every panel in the group follows.
 */
export function StockTemplate({ slug, children }: { slug: string; children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const setGroupTicker = useTickerGroups((s) => s.setGroupTicker);
  const urlSlug = useRef(slug);
  const tab = useRef<StockTab>(tabOf(pathname));

  // URL -> group, before paint so panels never fetch a previous ticker.
  useLayoutEffect(() => {
    urlSlug.current = slug;
    tab.current = tabOf(pathname);
    setGroupTicker(1, slug);
  }, [slug, pathname, setGroupTicker]);

  // Group -> URL, only for changes made inside the page.
  useEffect(
    () =>
      useTickerGroups.subscribe((s, prev) => {
        const next = s.tickers[1];
        if (next && next !== prev.tickers[1] && next !== urlSlug.current) {
          router.replace(hrefFor(next, tab.current), { scroll: false });
        }
      }),
    [router],
  );

  return (
    <>
      <TickerHeader />
      <StockTabs active={tabOf(pathname)} />
      <div className="@container min-h-0 flex-1 overflow-y-auto">{children}</div>
    </>
  );
}

function TickerHeader() {
  const t = useTranslations("stock");
  const locale = useLocale();
  const tx = useTranslations("exchanges");
  const slug = useGroupTicker(1);
  const { data, isError, error } = useTickerDetail(slug);
  const q = data?.quote;
  const ref = data?.ticker;
  const price = fmtNumber(q?.last_price);
  const change = fmtPct(q?.day_change_pct, 2, true);

  return (
    <header className="flex min-h-14 shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-4 py-2">
      <div className="flex min-w-0 items-center gap-3">
        <span
          title={t("group1")}
          className="flex h-7 shrink-0 items-center gap-1.5 rounded-chip border border-line px-2"
        >
          <span aria-hidden className={`size-2 rounded-[2px] ${GROUP_COLOR[1]}`} />
          <span className="num text-[12px]">{ref?.symbol ?? slug ?? "—"}</span>
        </span>
        <h1 className="headline min-w-0 text-[20px] leading-tight">
          {ref ? <TickerNames nameEn={ref.name_en} nameAr={ref.name_ar} single /> : <span className="text-muted">{isError ? (error as Error).message : " "}</span>}
        </h1>
        {ref && (
          <span className="label-caps hidden shrink-0 text-muted sm:inline">
            {tx.has(ref.exchange) ? tx(ref.exchange) : ref.exchange}
          </span>
        )}
      </div>

      <div className="ms-auto flex shrink-0 items-baseline gap-3">
        {q?.freshness !== undefined && (
          <span className="self-center">
            <FreshnessLight freshness={q?.freshness ?? null} />
          </span>
        )}
        <span className="num text-[20px] text-text">{price ?? t("noPrice")}</span>
        {ref?.currency && price && <span className="label-caps text-muted">{currencyLabel(ref.currency, locale)}</span>}
        {change && <span className={`num text-[13px] ${signClass(q?.day_change_pct)}`}>{change}</span>}
        {q?.as_of_date && (
          <span className="hidden text-muted lg:inline">
            {t("asOf")} <span className="num">{fmtDate(q.as_of_date, locale)}</span>
          </span>
        )}
      </div>
      <CopilotOpenButton />
    </header>
  );
}

function StockTabs({ active }: { active: StockTab }) {
  const t = useTranslations("stock.tabs");
  const ts = useTranslations("stock");
  const slug = useGroupTicker(1);
  if (!slug) return null;
  return (
    <nav aria-label={ts("pagesNav")} className="flex h-10 shrink-0 items-stretch gap-1 overflow-x-auto border-b border-line px-2">
      {STOCK_TABS.map((tab) => (
        <Link
          key={tab}
          href={hrefFor(slug, tab)}
          scroll={false}
          aria-current={tab === active ? "page" : undefined}
          className={`relative flex items-center px-3 whitespace-nowrap ${
            tab === active
              ? "text-text after:absolute after:inset-x-2 after:bottom-0 after:h-0.5 after:bg-signal"
              : "text-muted hover:text-text"
          }`}
        >
          {t(tab)}
        </Link>
      ))}
    </nav>
  );
}
