"use client";

import "moyasar-payment-form/dist/moyasar.css";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useMe, useResendVerification } from "@/lib/auth";
import { useBilling, usePlan, useStartCheckout } from "@/lib/billing";

type FormConfig = {
  publishable_key: string;
  amount: number;
  currency: string;
  description: string;
  callback_url: string;
  metadata: Record<string, string>;
};

const PRIMARY = "flex h-10 w-full items-center justify-center rounded-panel bg-signal font-semibold text-signal-ink disabled:opacity-50";
function legal(href: string) {
  return function LegalLink(c: React.ReactNode) {
    return (
      <Link href={href} target="_blank" className="text-signal hover:underline">
        {c}
      </Link>
    );
  };
}

/** /checkout: Pro's terms, the checkout acceptance, then Moyasar's card form. */
export function CheckoutView() {
  const t = useTranslations("checkout");
  const me = useMe();
  const plan = usePlan();
  const billing = useBilling(!!me.data);

  if (me.isPending || plan.isPending) return <p className="text-muted">…</p>;
  if (!me.data)
    return (
      <Notice title={t("title")} body={t("signInFirst")}>
        <Link href="/login?next=/checkout" className={PRIMARY}>
          {t("signIn")}
        </Link>
      </Notice>
    );
  if (!plan.data?.checkout_open)
    return (
      <Notice title={t("title")} body={t("closed")}>
        <Link href="/pricing" className="text-signal hover:underline">
          {t("pricing")}
        </Link>
      </Notice>
    );
  if (billing.data?.plan === "pro" && billing.data.renews && billing.data.status === "active")
    return (
      <Notice title={t("title")} body={t("already")}>
        <Link href="/settings#billing" className={PRIMARY}>
          {t("manage")}
        </Link>
      </Notice>
    );
  if (!me.data.email_verified) return <ConfirmEmailFirst email={me.data.email} />;
  return <Pay price={plan.data.price_sar} />;
}

function Notice({ title, body, children }: { title: string; body: string; children?: React.ReactNode }) {
  return (
    <div className="flex w-full flex-col gap-3">
      <h1 className="headline text-[28px] leading-none">{title}</h1>
      <p className="text-text-soft">{body}</p>
      {children}
    </div>
  );
}

function ConfirmEmailFirst({ email }: { email: string }) {
  const t = useTranslations("checkout");
  const tv = useTranslations("auth.verify");
  const resend = useResendVerification();
  return (
    <Notice title={t("title")} body={t("confirmFirst", { email })}>
      {resend.isSuccess ? (
        <p role="status" className="text-text-soft">
          {tv("sent")}
        </p>
      ) : (
        <button type="button" className={PRIMARY} disabled={resend.isPending} onClick={() => resend.mutate()}>
          {tv("resend")}
        </button>
      )}
    </Notice>
  );
}

function Pay({ price }: { price: number }) {
  const t = useTranslations("checkout");
  const locale = useLocale();
  const start = useStartCheckout();
  const [config, setConfig] = useState<FormConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    if (new FormData(e.currentTarget).get("accept") !== "on") return setError(t("needsTerms"));
    try {
      setConfig(await start.mutateAsync({ accept_terms: true, locale: locale === "ar" ? "ar" : "en" }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("failed"));
    }
  };

  return (
    <div className="flex w-full flex-col gap-4" data-checkout>
      <h1 className="headline text-[28px] leading-none">{t("title")}</h1>
      <div className="rounded-panel border border-line p-3">
        <p className="flex items-baseline justify-between gap-3">
          <span className="headline text-[20px]">{t("pro")}</span>
          <span className="text-text">{t("price", { price })}</span>
        </p>
        <ul className="mt-2 flex list-disc flex-col gap-1 ps-4 text-[13px] text-text-soft marker:text-muted">
          <li>{t("renewal")}</li>
          <li>{t("cancelAnytime")}</li>
          <li>{t.rich("guarantee", { link: legal("/legal/refunds") })}</li>
          <li>{t("vat")}</li>
        </ul>
      </div>
      {config ? (
        <MoyasarForm config={config} />
      ) : (
        // method="post": nothing here is secret, but the form never submits natively either way.
        <form method="post" onSubmit={submit} className="flex flex-col gap-3" noValidate>
          {/* The old site's checkout acceptance, word for word (api/app/legal.py CHECKOUT). */}
          <label className="flex items-start gap-2 text-text-soft">
            <input type="checkbox" name="accept" className="mt-0.5 size-4 shrink-0 accent-signal" />
            <span>
              {t.rich("accept", {
                terms: legal("/legal/terms"),
                privacy: legal("/legal/privacy"),
                refunds: legal("/legal/refunds"),
                disclaimer: legal("/legal/ai-financial-disclaimer"),
              })}
            </span>
          </label>
          {error && (
            <p role="alert" className="text-loss">
              {error}
            </p>
          )}
          <button type="submit" className={PRIMARY} disabled={start.isPending}>
            {t("continue")}
          </button>
        </form>
      )}
      <p className="text-[12px] text-muted">{t("secure")}</p>
    </div>
  );
}

/** Moyasar's own form: card details go from it to Moyasar, never to our server. The card is
 *  saved as a token for the monthly renewal (save_card). */
function MoyasarForm({ config }: { config: FormConfig }) {
  const locale = useLocale();
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let cancelled = false;
    void import("moyasar-payment-form").then((mod) => {
      const m = mod as unknown as { default?: { init?: unknown; default?: unknown }; init?: unknown };
      const Moyasar = (typeof m.default?.init === "function" ? m.default : (m.default?.default ?? m)) as {
        init: (c: Record<string, unknown>) => void;
      };
      if (cancelled || !host.current) return;
      Moyasar.init({
        element: host.current,
        amount: config.amount,
        currency: config.currency,
        description: config.description,
        publishable_api_key: config.publishable_key,
        callback_url: config.callback_url,
        metadata: config.metadata,
        methods: ["creditcard"],
        supported_networks: ["mada", "visa", "mastercard"],
        credit_card: { save_card: true },
        language: locale === "ar" ? "ar" : "en",
        fixed_width: false,
      });
    });
    return () => {
      cancelled = true;
    };
  }, [config, locale]);
  return <div ref={host} className="mysr-form" data-moyasar-form />;
}
