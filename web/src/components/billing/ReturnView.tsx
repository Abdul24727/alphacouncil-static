"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useConfirmPayment } from "@/lib/billing";
import { fmtDate } from "@/lib/format";

const PRIMARY = "flex h-10 items-center justify-center rounded-panel bg-signal font-semibold text-signal-ink";

/** /billing/return?id=…: where Moyasar sends the payer. The server asks Moyasar what happened;
 *  the query string (status, message) is never trusted. */
export function ReturnView() {
  const t = useTranslations("checkout.return");
  const locale = useLocale();
  const id = useSearchParams().get("id");
  const confirm = useConfirmPayment();
  const asked = useRef(false);
  const [result, setResult] = useState<{ ok: true; through: string | null } | { ok: false; message: string } | null>(null);

  useEffect(() => {
    if (!id || !/^[A-Za-z0-9_-]{1,64}$/.test(id) || asked.current) return;
    asked.current = true;
    confirm.mutateAsync(id).then(
      (s) => setResult({ ok: true, through: s.paid_through ?? null }),
      (err) => setResult({ ok: false, message: err instanceof ApiError ? err.message : t("failed") }),
    );
  }, [id, confirm, t]);

  if (!id) return <Failed message={t("missing")} />;
  if (!result)
    return (
      <p role="status" className="text-muted">
        {t("working")}
      </p>
    );
  if (!result.ok) return <Failed message={result.message} />;
  return (
    <div role="status" className="flex w-full flex-col gap-3" data-pro-started>
      <h1 className="headline text-[28px] leading-none">{t("doneTitle")}</h1>
      <p className="text-text-soft">{t("done", { date: fmtDate(result.through?.slice(0, 10), locale) ?? "—" })}</p>
      <Link href="/home" className={PRIMARY}>
        {t("continue")}
      </Link>
      <Link href="/settings#billing" className="text-signal hover:underline">
        {t("manage")}
      </Link>
    </div>
  );
}

function Failed({ message }: { message: string }) {
  const t = useTranslations("checkout.return");
  return (
    <div className="flex w-full flex-col gap-3">
      <h1 className="headline text-[28px] leading-none">{t("failedTitle")}</h1>
      <p role="alert" className="text-loss">
        {message}
      </p>
      <Link href="/checkout" className={PRIMARY}>
        {t("again")}
      </Link>
    </div>
  );
}
