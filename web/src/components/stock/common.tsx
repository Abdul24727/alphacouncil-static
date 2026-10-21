"use client";

import { useTranslations } from "next-intl";
import { PanelLoading, PanelUnavailable, usePanelRefresh } from "@/components/panel/Panel";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { autoPriceDigits } from "@/lib/format";
import { isProRequired } from "@/lib/billing";
import { useSettings } from "@/lib/settings-store";

/** Price decimals: "auto" follows the currency and, given a price, its own decimals (lib/format); Settings can fix 2 or 3. */
export function priceDigits(currency: string | null | undefined, value?: number | null) {
  const pref = useSettings.getState().decimals;
  if (pref !== "auto") return pref;
  return autoPriceDigits(currency, value);
}

export const hasArabic = (s: string | null | undefined) => !!s && /[؀-ۿ]/.test(s);

/**
 * "In English" / "بالإنجليزية": marks text the database stores only in the other language, shown
 * as stored (never translated). `data-lang-tag` lets scripts/check-arabic.mjs accept the text it marks.
 */
export function LangTag({ lang, className = "" }: { lang: "en" | "ar"; className?: string }) {
  const t = useTranslations("stock.news.in");
  return (
    <span data-lang-tag className={`label-caps shrink-0 text-muted ${className}`}>
      {t(lang)}
    </span>
  );
}

/**
 * A formatted number, or a labelled "n/a" when the database has no value. With `reason` (what
 * the data says about the gap, e.g. "Not in our price data") the reason is shown instead,
 * and `detail` explains it on hover.
 */
export function Num({
  value,
  className = "",
  reason,
  detail,
}: {
  value: string | null | undefined;
  className?: string;
  reason?: string | null;
  detail?: string;
}) {
  const t = useTranslations("stock");
  const tp = useTranslations("placeholder");
  if (value == null && reason) {
    return (
      <span className="text-[12px] text-muted" title={detail ?? tp("unavailable")} data-unavailable-reason>
        {reason}
      </span>
    );
  }
  if (value == null) {
    return (
      <span className="label-caps text-muted" title={tp("unavailable")}>
        {t("na")}
      </span>
    );
  }
  return <span className={`num ${className}`}>{value}</span>;
}

/** Loading / error / empty states shared by every query-backed panel body. */
export function QueryState({
  isPending,
  error,
  empty,
  emptyText,
  rows,
  children,
}: {
  isPending: boolean;
  error: unknown;
  empty?: boolean;
  emptyText?: string;
  rows?: number;
  children: React.ReactNode;
}) {
  const refresh = usePanelRefresh();
  const errorText = useErrorText();
  if (isPending) return <PanelLoading rows={rows} />;
  // Pro-only data on the Free plan: say what it is and where Pro is, not "unavailable".
  if (isProRequired(error)) return <ProLocked />;
  // A failed load says why and offers the panel's refresh (requests time out after 30 s).
  if (error) return <PanelUnavailable detail={errorText(error)} onRetry={refresh} />;
  if (empty) return <PanelUnavailable detail={emptyText} />;
  return <>{children}</>;
}

/** What a Pro-only panel shows on the Free plan. */
export function ProLocked({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("plan");
  return (
    <div className={`flex flex-col items-start justify-start gap-1.5 pt-1 ${compact ? "" : "min-h-24"}`} data-pro-locked>
      <span className="label-caps rounded-chip border border-signal/50 px-1.5 text-signal">{t("pro")}</span>
      <span className="text-text-soft">{t("lockedLead")}</span>
      <Link href="/pricing" className="text-signal hover:underline">
        {t("seePro")}
      </Link>
    </div>
  );
}

function useErrorText() {
  const t = useTranslations("placeholder");
  return (error: unknown) =>
    error instanceof DOMException && error.name === "TimeoutError"
      ? t("timedOut")
      : t("failed", { status: error instanceof ApiError ? String(error.status) : "—" });
}

/** Rows of [label, value] as tab-separated text for "Copy data". */
export function toTsv(rows: (string | number | boolean | null | undefined)[][]): string {
  return rows.map((r) => r.map((c) => (c == null ? "" : String(c))).join("\t")).join("\n");
}
