"use client";

import { useTranslations } from "next-intl";
import { PanelLoading, PanelUnavailable, usePanelRefresh } from "@/components/panel/Panel";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { isProRequired } from "@/lib/billing";
import { useSettings } from "@/lib/settings-store";

/** KWD, BHD and OMR trade in fils / baisa, so prices need three decimals ("auto"); Settings can fix 2 or 3. */
export function priceDigits(currency: string | null | undefined) {
  const pref = useSettings.getState().decimals;
  if (pref !== "auto") return pref;
  return currency && ["KWD", "BHD", "OMR"].includes(currency) ? 3 : 2;
}

export const hasArabic = (s: string | null | undefined) => !!s && /[؀-ۿ]/.test(s);

/** A formatted number, or a labelled "n/a" when the database has no value. */
export function Num({ value, className = "" }: { value: string | null | undefined; className?: string }) {
  const t = useTranslations("stock");
  const tp = useTranslations("placeholder");
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
    <div className={`flex h-full flex-col items-start justify-center gap-1.5 ${compact ? "" : "min-h-24"}`} data-pro-locked>
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
