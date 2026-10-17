"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useForgotPassword } from "@/lib/auth";
import { fieldClass } from "./AuthForm";

/** "Forgot password?": asks for the email and says a link is on its way if an account uses it.
 *  The answer is the same for every address (api/app/auth.py forgot_password). */
export function ForgotPasswordForm() {
  const t = useTranslations("auth");
  const forgot = useForgotPassword();
  const [error, setError] = useState<string | null>(null);
  const [sentTo, setSentTo] = useState<string | null>(null);

  // Uncontrolled field read on submit: anything typed before the page hydrates is kept.
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    const email = String(new FormData(e.currentTarget).get("email") ?? "").trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return setError(t("forgot.invalid"));
    try {
      await forgot.mutateAsync({ email, locale: document.documentElement.lang === "ar" ? "ar" : "en" });
      setSentTo(email);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(status === 429 ? t("errors.rate") : status === 422 ? t("forgot.invalid") : t("errors.generic"));
    }
  };

  if (sentTo)
    return (
      <div role="status" className="flex w-full flex-col gap-3">
        <h1 className="headline text-[28px] leading-none">{t("forgot.sentTitle")}</h1>
        <p className="text-text-soft">
          {t.rich("forgot.sent", {
            email: sentTo,
            b: (c) => (
              <bdi dir="ltr" className="text-text">
                {c}
              </bdi>
            ),
          })}
        </p>
        <p className="text-muted">{t("forgot.sentHint")}</p>
        <div className="flex items-center justify-between gap-3">
          <Link href="/login" className="text-signal hover:underline">
            {t("forgot.back")}
          </Link>
          <button type="button" onClick={() => setSentTo(null)} className="text-muted hover:text-text">
            {t("forgot.again")}
          </button>
        </div>
      </div>
    );

  return (
    // method="post": a submit before the page has hydrated must not put the email in the URL.
    <form method="post" onSubmit={submit} className="flex w-full flex-col gap-3" noValidate>
      <h1 className="headline text-[28px] leading-none">{t("forgot.title")}</h1>
      <p className="text-text-soft">{t("forgot.intro")}</p>
      <label className="flex flex-col gap-1">
        <span className="label-caps text-muted">{t("email")}</span>
        <input className={fieldClass} type="email" dir="ltr" required name="email" autoComplete="email" />
      </label>
      {error && (
        <p role="alert" className="text-loss">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={forgot.isPending}
        className="h-10 rounded-panel bg-signal font-semibold text-signal-ink disabled:opacity-50"
      >
        {t("forgot.cta")}
      </button>
      <p className="text-muted">
        <Link href="/login" className="text-signal hover:underline">
          {t("forgot.back")}
        </Link>
      </p>
    </form>
  );
}
