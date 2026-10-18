"use client";

import { useLocale, useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import { Link } from "@/i18n/navigation";
import { useMe } from "@/lib/auth";
import { useBilling, useCancelRenewal, usePlan, useResumeRenewal } from "@/lib/billing";
import { fmtDate } from "@/lib/format";

const PRIMARY = "inline-flex rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink";
const SECONDARY = "rounded-panel border border-line px-3 py-1.5 text-text hover:bg-panel-raised disabled:opacity-50";

/** Settings › Billing (#billing: the receipts and reminders link here). */
export function BillingPanel({ className }: { className?: string }) {
  const t = useTranslations("billing");
  const locale = useLocale();
  const me = useMe();
  const plan = usePlan();
  const billing = useBilling(!!me.data);
  const cancel = useCancelRenewal();
  const resume = useResumeRenewal();
  const b = billing.data;
  const date = (iso: string | null | undefined) => fmtDate(iso?.slice(0, 10), locale) ?? "—";

  return (
    <Panel id="settings.billing" title={t("title")} className={className}>
      <div id="billing" className="flex flex-col items-start gap-3" data-billing>
        {plan.data && !plan.data.billing_open ? (
          <p className="text-text-soft">{t("earlyAccess")}</p>
        ) : !me.data ? (
          <p className="text-text-soft">{t("signIn")}</p>
        ) : !b ? (
          <p className="text-muted">…</p>
        ) : (
          <>
            <p className="text-text" data-plan={b.plan}>
              {t("plan")} <span className="font-semibold">{b.plan === "pro" ? t("pro") : t("free")}</span>
            </p>
            {b.plan === "pro" && b.status === "past_due" && <p className="text-stale">{t("pastDue", { date: date(b.paid_through) })}</p>}
            {b.plan === "pro" && b.status !== "past_due" && (
              <p className="text-text-soft">
                {b.renews
                  ? t("renews", { date: date(b.paid_through), card: `${(b.card_brand ?? "").toUpperCase()} •••• ${b.card_last4 ?? ""}` })
                  : t("ends", { date: date(b.paid_through) })}
              </p>
            )}
            <div className="flex flex-wrap gap-2">
              {b.plan === "pro" && b.renews && (
                <button type="button" className={SECONDARY} disabled={cancel.isPending} onClick={() => cancel.mutate()}>
                  {t("cancel")}
                </button>
              )}
              {b.plan === "pro" && !b.renews && b.status === "canceled" && b.card_last4 && (
                <button type="button" className={SECONDARY} disabled={resume.isPending} onClick={() => resume.mutate()}>
                  {t("resume")}
                </button>
              )}
              {b.checkout_open && (b.plan === "free" || b.status === "past_due" || (!b.renews && b.status !== "canceled")) && (
                <Link href="/checkout" className={PRIMARY}>
                  {b.plan === "free" ? t("upgrade", { price: plan.data?.price_sar ?? "" }) : t("newCard")}
                </Link>
              )}
            </div>
            {b.plan === "pro" && b.renews && <p className="text-[12px] text-muted">{t("cancelNote")}</p>}
          </>
        )}
      </div>
    </Panel>
  );
}
