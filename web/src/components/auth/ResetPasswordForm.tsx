"use client";

import { useTranslations } from "next-intl";
import { useState, useSyncExternalStore } from "react";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useResetPassword } from "@/lib/auth";
import { tokenFromHash } from "@/lib/reset-token";
import { fieldClass } from "./AuthForm";

const subscribeHash = (onChange: () => void) => {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
};

/** The page an emailed "Forgot password?" link opens: set a new password with its token. */
export function ResetPasswordForm() {
  const t = useTranslations("auth");
  const resetPassword = useResetPassword();
  // Only the browser has the fragment: the server (and the first render) say "not read yet".
  const token = useSyncExternalStore(
    subscribeHash,
    () => tokenFromHash(window.location.hash),
    () => undefined,
  );
  const [error, setError] = useState<"mismatch" | "short" | "expired" | "rate" | "generic" | null>(null);
  const [done, setDone] = useState(false);

  // Uncontrolled fields read on submit: anything typed before the page hydrates is kept.
  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    const form = new FormData(e.currentTarget);
    const password = String(form.get("password") ?? "");
    if (password.length < 10) return setError("short");
    if (password !== String(form.get("confirm") ?? "")) return setError("mismatch");
    if (!token) return;
    try {
      await resetPassword.mutateAsync({ token, password });
      setDone(true);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      // The API answers 403 (never 401) for a used or expired link; see api/app/auth.py AUTH_FAILED.
      setError(status === 403 ? "expired" : status === 422 ? "short" : status === 429 ? "rate" : "generic");
    }
  };

  const newLink = (
    <Link href="/forgot-password" className="text-signal hover:underline">
      {t("reset.newLink")}
    </Link>
  );

  if (done)
    return (
      <div role="status" className="flex w-full flex-col gap-3">
        <h1 className="headline text-[28px] leading-none">{t("reset.doneTitle")}</h1>
        <p className="text-text-soft">{t("reset.done")}</p>
        <Link
          href="/portfolio"
          className="flex h-10 items-center justify-center rounded-panel bg-signal font-semibold text-signal-ink"
        >
          {t("reset.continue")}
        </Link>
      </div>
    );

  if (token === null)
    return (
      <div className="flex w-full flex-col gap-3">
        <h1 className="headline text-[28px] leading-none">{t("reset.title")}</h1>
        <p role="alert" className="text-text-soft">
          {t("reset.missing")}
        </p>
        <p>{newLink}</p>
      </div>
    );

  const message = error === "rate" ? t("errors.rate") : error === "generic" ? t("errors.generic") : error && t(`reset.${error}`);

  return (
    // method="post": a submit before the page has hydrated must not put the password in the URL.
    <form method="post" onSubmit={submit} className="flex w-full flex-col gap-3" noValidate>
      <h1 className="headline text-[28px] leading-none">{t("reset.title")}</h1>
      <label className="flex flex-col gap-1">
        <span className="label-caps text-muted">{t("reset.password")}</span>
        <input
          className={fieldClass}
          type="password"
          dir="ltr"
          required
          minLength={10}
          name="password"
          autoComplete="new-password"
        />
        <span className="text-[12px] text-muted">{t("passwordHint")}</span>
      </label>
      <label className="flex flex-col gap-1">
        <span className="label-caps text-muted">{t("reset.confirm")}</span>
        <input
          className={fieldClass}
          type="password"
          dir="ltr"
          required
          minLength={10}
          name="confirm"
          autoComplete="new-password"
        />
      </label>
      {message && (
        <p role="alert" className="text-loss">
          {message} {error === "expired" && newLink}
        </p>
      )}
      <button
        type="submit"
        disabled={resetPassword.isPending || !token}
        className="h-10 rounded-panel bg-signal font-semibold text-signal-ink disabled:opacity-50"
      >
        {t("reset.cta")}
      </button>
    </form>
  );
}
