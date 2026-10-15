"use client";

import { useTranslations } from "next-intl";
import { PanelLoading, PanelUnavailable } from "@/components/panel/Panel";
import { ApiError } from "@/lib/api/client";
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
  if (isPending) return <PanelLoading rows={rows} />;
  if (error) return <PanelUnavailable detail={error instanceof ApiError ? error.message : undefined} />;
  if (empty) return <PanelUnavailable detail={emptyText} />;
  return <>{children}</>;
}

/** Rows of [label, value] as tab-separated text for "Copy data". */
export function toTsv(rows: (string | number | boolean | null | undefined)[][]): string {
  return rows.map((r) => r.map((c) => (c == null ? "" : String(c))).join("\t")).join("\n");
}
