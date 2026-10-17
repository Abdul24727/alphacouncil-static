"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Link, useRouter } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useSignIn, useSignUp } from "@/lib/auth";

export const fieldClass =
  "h-10 w-full rounded-panel border border-line bg-bg px-3 text-[14px] text-text outline-none focus:border-muted";

export function AuthForm({ mode, next }: { mode: "login" | "signup"; next?: string }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const signIn = useSignIn();
  const signUp = useSignUp();
  const [error, setError] = useState<string | null>(null);
  const busy = signIn.isPending || signUp.isPending;

  // Uncontrolled fields read on submit: anything typed before the page hydrates is kept.
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    const form = new FormData(e.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");
    const name = String(form.get("name") ?? "").trim();
    if (!email || !password) return setError(t("errors.invalid"));
    const accepted = form.get("accept") === "on";
    if (mode === "signup" && !accepted) return setError(t("errors.terms"));
    try {
      if (mode === "login") await signIn.mutateAsync({ email, password });
      else
        await signUp.mutateAsync({
          email,
          password,
          display_name: name || undefined,
          locale: document.documentElement.lang === "ar" ? "ar" : "en",
          accept_terms: accepted,
        });
      router.replace(next && next.startsWith("/") && !next.startsWith("//") ? next : "/portfolio");
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(
        // The API answers 403 (never 401) for a failed sign-in; see api/app/auth.py AUTH_FAILED.
        status === 401 || status === 403
          ? t("errors.credentials")
          : status === 409
            ? t("errors.exists")
            : status === 422
              ? t("errors.invalid")
              : status === 429
                ? t("errors.rate")
                : t("errors.generic"),
      );
    }
  };

  const field = fieldClass;

  return (
    // method="post": a submit before the page has hydrated must not put the password in the URL.
    <form method="post" onSubmit={submit} className="flex w-full flex-col gap-3" noValidate>
      <h1 className="headline text-[28px] leading-none">{t(mode === "login" ? "loginTitle" : "signupTitle")}</h1>
      {mode === "signup" && (
        <label className="flex flex-col gap-1">
          <span className="label-caps text-muted">{t("name")}</span>
          <input className={field} name="name" autoComplete="name" maxLength={80} />
        </label>
      )}
      <label className="flex flex-col gap-1">
        <span className="label-caps text-muted">{t("email")}</span>
        <input
          className={field}
          type="email"
          dir="ltr"
          required
          name="email"
          autoComplete="email"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="label-caps text-muted">{t("password")}</span>
        <input
          className={field}
          type="password"
          dir="ltr"
          required
          minLength={mode === "signup" ? 10 : undefined}
          name="password"
          autoComplete={mode === "signup" ? "new-password" : "current-password"}
        />
        {mode === "signup" && <span className="text-[12px] text-muted">{t("passwordHint")}</span>}
      </label>
      {mode === "login" && (
        <Link href="/forgot-password" className="-mt-1 self-end text-[13px] text-signal hover:underline">
          {t("forgotLink")}
        </Link>
      )}
      {mode === "signup" && (
        // The old site's registration acceptance, word for word (api/app/legal.py records its version).
        <label className="flex items-start gap-2 text-text-soft">
          <input type="checkbox" name="accept" className="mt-0.5 size-4 shrink-0 accent-signal" />
          <span>
            {t.rich("accept", {
              terms: (c) => (
                <Link href="/legal/terms" target="_blank" className="text-signal hover:underline">
                  {c}
                </Link>
              ),
              privacy: (c) => (
                <Link href="/legal/privacy" target="_blank" className="text-signal hover:underline">
                  {c}
                </Link>
              ),
            })}
          </span>
        </label>
      )}
      {error && (
        <p role="alert" className="text-loss">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={busy}
        className="h-10 rounded-panel bg-signal font-semibold text-signal-ink disabled:opacity-50"
      >
        {t(mode === "login" ? "loginCta" : "signupCta")}
      </button>
      <p className="text-muted">
        {mode === "login" ? t("noAccount") : t("haveAccount")}{" "}
        <Link href={mode === "login" ? "/signup" : "/login"} className="text-signal hover:underline">
          {t(mode === "login" ? "signupLink" : "loginLink")}
        </Link>
      </p>
    </form>
  );
}
