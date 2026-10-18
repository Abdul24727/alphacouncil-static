"use client";

import { useLocale, useTranslations } from "next-intl";
import { googleStartUrl } from "@/lib/auth";

/** Google's standard "G" (Google's sign-in branding asks for it, in its colours). */
function GoogleG() {
  return (
    <svg viewBox="0 0 48 48" aria-hidden className="size-[18px] shrink-0">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
  );
}

const BUTTON =
  "flex h-10 w-full items-center justify-center gap-2.5 rounded-panel border border-line bg-panel-raised font-medium text-text hover:border-muted";

/** "Continue with Google". On sign-up the terms box must be ticked first (onTermsMissing). */
export function GoogleButton({ mode, next, onTermsMissing }: { mode: "login" | "signup"; next?: string; onTermsMissing?: () => void }) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const target = next && next.startsWith("/") && !next.startsWith("//") ? next : "/portfolio";
  if (mode === "login") {
    return (
      <a href={googleStartUrl({ next: target, locale })} className={BUTTON} data-google>
        <GoogleG />
        {t("google")}
      </a>
    );
  }
  return (
    <button
      type="button"
      className={BUTTON}
      data-google
      onClick={(e) => {
        const box = e.currentTarget.form?.elements.namedItem("accept");
        if (!(box instanceof HTMLInputElement) || !box.checked) return onTermsMissing?.();
        window.location.assign(googleStartUrl({ next: target, locale, accept: true }));
      }}
    >
      <GoogleG />
      {t("google")}
    </button>
  );
}
